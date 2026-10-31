-- ===========================================================================
--  s2-72 — Les lingots se gagnent aussi en combattant (Front, saison 2)
--  Décision de Nataël, 1er novembre 2026 (« ok bonne idée ! ») : les
--  bâtiments ne doivent pas récompenser l'attente seule.
--
--  En plus de la production des Fonderies (inchangée) :
--    - conquête d'une commune     : +2 lingots
--    - défense réussie            : +1 lingot
--    - au plus +10 lingots par jour venant des combats (jour de Paris)
--  Seules comptent les victoires que le score compte déjà (front_victoires,
--  compte = vrai) : une fois par commune et par type, 2 par jour au plus
--  contre le même adversaire, 10 par jour au plus. Les garde-fous
--  anti-complices du score s'appliquent donc aussi aux lingots.
--  La réserve reste plafonnée (30 avec une Fonderie ou aucune, 45 avec deux) :
--  ce qui dépasse est perdu, comme la production.
--
--  Ne touche ni attaquer(), ni defendre(), ni le score : un déclencheur sur
--  front_victoires. Il ne peut jamais bloquer un combat ni effacer une
--  victoire (en cas d'erreur : rien n'est donné, tout le reste se fait).
--  Réglages : config_jeu 'batiments' (lingots_combat_ouvert, lingots_conquete,
--  lingots_defense, lingots_combat_jour), modifiables sans toucher au code.
--  Couper : lingots_combat_ouvert = 0 (voir s2-72-lingots-combat-couper.sql).
--  Pas d'effet rétroactif : seules les victoires après ce fichier rapportent.
--  Rejouable. Contrôle attendu : true | 2 | 1 | 10 | true | true | un nombre > 0
--  (la dernière colonne compte les défenses déjà notées par le score cette
--  saison : si elle vaut 0, les défenses ne rapporteront rien, me le dire).
-- ===========================================================================
begin;

-- 1. Réglages (ajoutés seulement s'ils n'existent pas encore) ---------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"lingots_combat_ouvert": 1, "lingots_conquete": 2,
       "lingots_defense": 1, "lingots_combat_jour": 10}'::jsonb)::text
 where cle = 'batiments' and not (valeur::jsonb ? 'lingots_combat_jour');

-- 2. Le registre des gains (un gain par victoire au plus) ---------------------
create table if not exists public.lingots_gains(
  id           bigserial primary key,
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  saison       text not null,
  jour         date not null,                 -- jour de Paris
  source       text not null check (source in ('conquete', 'defense')),
  victoire_id  bigint not null unique,        -- front_victoires.id
  quantite     integer not null,              -- ce qui est vraiment entré (après plafonds)
  le           timestamptz not null default now()
);
create index if not exists lingots_gains_jour on public.lingots_gains(joueur_id, jour);
alter table public.lingots_gains enable row level security;
revoke all on public.lingots_gains from public, anon, authenticated;
revoke all on sequence public.lingots_gains_id_seq from public, anon, authenticated;

-- 3. Le déclencheur -----------------------------------------------------------
create or replace function public.lingots_combat_victoire()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_jour    date := (now() at time zone 'Europe/Paris')::date;
  v_gain    numeric;
  v_deja    numeric;
  v_plafond numeric;
  v_avant   numeric;
  v_mx      numeric;
  v_nouveau numeric;
  v_entre   integer;
begin
  if not new.compte then return null; end if;
  if coalesce(batiment_reglage('lingots_combat_ouvert'), 0) <> 1 then return null; end if;
  if new.saison is distinct from saison_en_cours_id() then return null; end if;

  v_gain := case new.type when 'conquete' then coalesce(batiment_reglage('lingots_conquete'), 2)
                          when 'defense'  then coalesce(batiment_reglage('lingots_defense'), 1) end;
  if coalesce(v_gain, 0) <= 0 then return null; end if;

  -- front_noter_victoire tient déjà le verrou du joueur : pas de course au plafond
  v_plafond := coalesce(batiment_reglage('lingots_combat_jour'), 10);
  select coalesce(sum(g.quantite), 0) into v_deja
    from lingots_gains g where g.joueur_id = new.joueur_id and g.jour = v_jour;
  v_gain := least(v_gain, greatest(0, v_plafond - v_deja));
  if v_gain <= 0 then return null; end if;

  -- figer la réserve (production comprise), puis ajouter sans dépasser le plafond
  v_avant := lingots_figer(new.joueur_id);
  v_mx    := lingots_max(new.joueur_id);
  v_nouveau := least(v_mx, v_avant + v_gain);
  if v_nouveau <= v_avant then return null; end if;   -- réserve pleine : rien n'entre, rien n'est décompté
  v_entre := ceil(v_nouveau - v_avant)::integer;

  update joueurs set lingots = v_nouveau where id = new.joueur_id;
  insert into lingots_gains(joueur_id, saison, jour, source, victoire_id, quantite)
  values (new.joueur_id, new.saison, v_jour, new.type, new.id, v_entre);
  return null;
exception when others then
  -- jamais bloquer un combat, jamais effacer la victoire pour des lingots
  raise warning 'lingots_combat_victoire : %', sqlerrm;
  return null;
end;
$f$;
revoke all on function public.lingots_combat_victoire() from public, anon, authenticated;

drop trigger if exists lingots_combat_victoire on public.front_victoires;
create trigger lingots_combat_victoire after insert on public.front_victoires
  for each row when (new.compte)
  execute function public.lingots_combat_victoire();

-- 4. Pour le jeu : ce que j'ai gagné en combattant aujourd'hui ---------------
create or replace function public.lingots_combat_moi()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
    'ouvert',   coalesce(batiment_reglage('lingots_combat_ouvert'), 0) = 1,
    'conquete', coalesce(batiment_reglage('lingots_conquete'), 2)::integer,
    'defense',  coalesce(batiment_reglage('lingots_defense'), 1)::integer,
    'plafond',  coalesce(batiment_reglage('lingots_combat_jour'), 10)::integer,
    'aujourdhui', coalesce((select sum(g.quantite) from lingots_gains g
                             where g.joueur_id = auth.uid()
                               and g.jour = (now() at time zone 'Europe/Paris')::date), 0)::integer,
    'dernier',  (select jsonb_build_object('source', g.source, 'quantite', g.quantite, 'le', g.le)
                   from lingots_gains g where g.joueur_id = auth.uid()
                  order by g.le desc limit 1))
  where auth.uid() is not null;
$f$;
revoke all on function public.lingots_combat_moi() from public, anon;
grant execute on function public.lingots_combat_moi() to authenticated;

commit;

-- Contrôle : true | 2 | 1 | 10 | true | true | un nombre > 0
select coalesce(batiment_reglage('lingots_combat_ouvert'), 0) = 1                         as ouvert,
       batiment_reglage('lingots_conquete')::integer                                       as conquete,
       batiment_reglage('lingots_defense')::integer                                        as defense,
       batiment_reglage('lingots_combat_jour')::integer                                    as plafond_jour,
       exists (select 1 from pg_trigger where tgname = 'lingots_combat_victoire' and not tgisinternal) as declencheur,
       has_function_privilege('authenticated', 'public.lingots_combat_moi()', 'execute')   as lecture_joueurs,
       (select count(*) from front_victoires v where v.type = 'defense' and v.compte
          and v.saison = saison_en_cours_id())                                             as defenses_comptees_saison;
