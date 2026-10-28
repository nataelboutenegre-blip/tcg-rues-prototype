-- ===========================================================================
--  s2-53 — Pass de saison « Brumes d'automne » (saison 2)
--  (28/10, aperçu et contenu validés par Nataël : « très bien ! »)
--
--  - 20 niveaux de 1 000 XP. Niveaux impairs : pour tous. Niveaux pairs :
--    avec le pass (article en euros 'pass-s2', 3,99 €, achat unique).
--  - XP : quête du jour réclamée +100 ; actions, plafonnées à 500 XP par
--    jour : conquête +30, défense +30, duel Radar / Rafale classé fini +20,
--    Commune du jour trouvée +20, paquet Terra ouvert +10.
--    L'XP ne compte qu'entre l'ouverture du pass (s2-53b) et la fin de saison.
--  - Récompenses réclamées une par une (ou toutes) : TP, énergie (plafond 60
--    comme les quêtes), titres (dans le choix du titre du profil), objets
--    (dos, habillages, skins : rangés dans la garde-robe).
--    Les 7 objets à dessiner sont marqués « bientôt » (dispo = false) : on les
--    ouvrira un par un quand ils seront prêts.
--  Branchements : des déclencheurs sur quetes_reclamees, quetes_compteurs,
--  cdj_gains, radar_parties, rafale_parties (aucune fonction du jeu n'est
--  modifiée, sauf titres_possibles, vérifiée avant).
--  Rien n'est ouvert : le pass démarre avec s2-53b-pass-ouverture.sql.
--  Rejouable. Contrôle attendu : 20 | 7 | true | true | true | false
-- ===========================================================================
begin;

create table if not exists public.pass_saisons(
  saison          text primary key,
  nom             text not null,
  article_id      text not null,
  debut           timestamptz,                 -- null : pas encore ouvert
  fin             timestamptz not null,
  niveaux         integer not null default 20,
  xp_niveau       integer not null default 1000,
  xp_quete        integer not null default 100,
  plafond_actions integer not null default 500
);
create table if not exists public.pass_recompenses(
  saison   text not null references public.pass_saisons(saison) on delete cascade,
  niveau   integer not null,
  payant   boolean not null,
  type     text not null check (type in ('tp', 'energie', 'titre', 'dos', 'habillage', 'skin')),
  valeur   text,                                -- id du titre ou de l'objet
  quantite integer not null default 0,
  nom      text not null,
  dispo    boolean not null default true,
  primary key (saison, niveau)
);
create table if not exists public.pass_xp(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  saison    text not null,
  jour      date not null,
  quetes    integer not null default 0,
  actions   integer not null default 0,
  primary key (joueur_id, saison, jour)
);
create table if not exists public.pass_reclames(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  saison    text not null,
  niveau    integer not null,
  le        timestamptz not null default now(),
  primary key (joueur_id, saison, niveau)
);
alter table public.pass_saisons     enable row level security;
alter table public.pass_recompenses enable row level security;
alter table public.pass_xp          enable row level security;
alter table public.pass_reclames    enable row level security;
revoke all on public.pass_saisons, public.pass_recompenses, public.pass_xp, public.pass_reclames from public, anon, authenticated;

-- la saison 2 et son pass ------------------------------------------------------
insert into public.pass_saisons(saison, nom, article_id, fin)
select s.id, 'Brumes d''automne', 'pass-s2', coalesce(s.fin_prevue, timestamptz '2026-11-22 10:00 Europe/Paris')
  from public.saison_courante() s
on conflict (saison) do nothing;

-- l'article du pass, et les objets à gagner (rangés comme des objets de la boutique, jamais en vente pour l'instant)
insert into public.euros_articles(id, type, nom, description, prix_centimes, saison, actif, ordre)
select 'pass-s2', 'pass', 'Pass Brumes d''automne', 'Les 10 récompenses du pass de la saison 2', 399, p.saison, false, 900
  from public.pass_saisons p where p.article_id = 'pass-s2'
on conflict (id) do nothing;
insert into public.euros_articles(id, type, nom, description, prix_centimes, actif, ordre) values
  ('pass-s2-paquet-vendanges', 'habillage', 'Paquet Vendanges',      'Pass Brumes d''automne, niveau 4',  299, false, 910),
  ('pass-s2-dos-feuilles-or',  'dos',       'Dos Feuilles d''or',     'Pass Brumes d''automne, niveau 6',  299, false, 920),
  ('pass-s2-skin-brume',       'skin',      'Skin Brume',            'Pass Brumes d''automne, niveau 10', 299, false, 930),
  ('pass-s2-paquet-sous-bois', 'habillage', 'Paquet Sous-bois',      'Pass Brumes d''automne, niveau 12', 299, false, 940),
  ('pass-s2-dos-automne',      'dos',       'Dos Automne',           'Pass Brumes d''automne, niveau 13', 299, false, 950),
  ('pass-s2-dos-braises',      'dos',       'Dos Braises d''automne', 'Pass Brumes d''automne, niveau 16', 299, false, 960),
  ('pass-s2-skin-vendanges',   'skin',      'Skin Vendanges',        'Pass Brumes d''automne, niveau 20', 299, false, 970)
on conflict (id) do nothing;

insert into public.pass_recompenses(saison, niveau, payant, type, valeur, quantite, nom, dispo)
select p.saison, r.niveau, r.payant, r.type, r.valeur, r.quantite, r.nom, r.dispo
  from public.pass_saisons p,
  (values
    (1,  false, 'tp',        null,                       100, '100 TerraPoints',              true),
    (2,  true,  'titre',     'pass-s2-mecene',           0,   'Titre « Mécène d''automne »',  true),
    (3,  false, 'energie',   null,                       10,  '+10 énergie',                  true),
    (4,  true,  'habillage', 'pass-s2-paquet-vendanges', 0,   'Paquet Vendanges',             false),
    (5,  false, 'tp',        null,                       150, '150 TerraPoints',              true),
    (6,  true,  'dos',       'pass-s2-dos-feuilles-or',  0,   'Dos Feuilles d''or',           false),
    (7,  false, 'titre',     'pass-s2-recrue',           0,   'Titre « Recrue d''automne »',  true),
    (8,  true,  'titre',     'pass-s2-vignes',           0,   'Titre « Seigneur des vignes »', true),
    (9,  false, 'energie',   null,                       10,  '+10 énergie',                  true),
    (10, true,  'skin',      'pass-s2-skin-brume',       0,   'Skin Brume',                   false),
    (11, false, 'tp',        null,                       200, '200 TerraPoints',              true),
    (12, true,  'habillage', 'pass-s2-paquet-sous-bois', 0,   'Paquet Sous-bois',             false),
    (13, false, 'dos',       'pass-s2-dos-automne',      0,   'Dos Automne',                  false),
    (14, true,  'titre',     'pass-s2-brumes',           0,   'Titre « Gardien des brumes »', true),
    (15, false, 'energie',   null,                       15,  '+15 énergie',                  true),
    (16, true,  'dos',       'pass-s2-dos-braises',      0,   'Dos Braises d''automne',       false),
    (17, false, 'tp',        null,                       300, '300 TerraPoints',              true),
    (18, true,  'titre',     'pass-s2-legende',          0,   'Titre « Légende de la saison 2 »', true),
    (19, false, 'titre',     'pass-s2-veteran',          0,   'Titre « Vétéran de la saison 2 »', true),
    (20, true,  'skin',      'pass-s2-skin-vendanges',   0,   'Skin Vendanges',               false)
  ) as r(niveau, payant, type, valeur, quantite, nom, dispo)
 where p.article_id = 'pass-s2'
on conflict (saison, niveau) do nothing;

-- le pass en cours (ouvert, pas fini) ; « recent » : on peut encore réclamer 7 jours après la fin
create or replace function public.pass_en_cours()
 returns setof public.pass_saisons language sql stable security definer set search_path to 'public'
as $f$
  select * from pass_saisons where debut is not null and now() >= debut and now() < fin order by debut desc limit 1;
$f$;
create or replace function public.pass_recent()
 returns setof public.pass_saisons language sql stable security definer set search_path to 'public'
as $f$
  select * from pass_saisons where debut is not null and now() >= debut and now() < fin + interval '7 days' order by debut desc limit 1;
$f$;

-- ajouter de l'XP : p_quete = une quête du jour réclamée ; p_actions = XP d'action (plafonnée par jour)
create or replace function public.pass_ajouter(p_uid uuid, p_quete boolean, p_actions integer)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare p pass_saisons%rowtype;
begin
  if p_uid is null then return; end if;
  select * into p from pass_en_cours();
  if p.saison is null then return; end if;
  insert into pass_xp(joueur_id, saison, jour, quetes, actions)
  values (p_uid, p.saison, quete_jour(), case when p_quete then p.xp_quete else 0 end, least(p.plafond_actions, greatest(0, coalesce(p_actions, 0))))
  on conflict (joueur_id, saison, jour) do update
    set quetes  = pass_xp.quetes + excluded.quetes,
        actions = least(p.plafond_actions, pass_xp.actions + greatest(0, coalesce(p_actions, 0)));
end;
$f$;

-- les déclencheurs (ils ne bloquent jamais le jeu : une erreur ici est ignorée)
create or replace function public.pass_trg_quete()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  if new.jour <> date '2000-01-01' then
    begin perform pass_ajouter(new.joueur_id, true, 0); exception when others then null; end;
  end if;
  return null;
end;
$f$;
create or replace function public.pass_trg_compteur()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare v_delta integer := new.n - case when tg_op = 'UPDATE' then old.n else 0 end;
        v_xp integer := case new.cle when 'conquete' then 30 when 'defense' then 30 when 'terra_paquet' then 10 else 0 end;
begin
  if v_delta > 0 and v_xp > 0 then
    begin perform pass_ajouter(new.joueur_id, false, v_delta * v_xp); exception when others then null; end;
  end if;
  return null;
end;
$f$;
create or replace function public.pass_trg_cdj()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  begin perform pass_ajouter(new.joueur_id, false, 20); exception when others then null; end;
  return null;
end;
$f$;
create or replace function public.pass_trg_duel()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  if new.fini and not coalesce(new.amical, false)
     and (tg_op = 'INSERT' or not coalesce(old.fini, false)) then
    begin perform pass_ajouter(new.joueur_id, false, 20); exception when others then null; end;
  end if;
  return null;
end;
$f$;

drop trigger if exists pass_quete on public.quetes_reclamees;
create trigger pass_quete after insert on public.quetes_reclamees for each row execute function public.pass_trg_quete();
drop trigger if exists pass_compteur on public.quetes_compteurs;
create trigger pass_compteur after insert or update of n on public.quetes_compteurs for each row execute function public.pass_trg_compteur();
drop trigger if exists pass_cdj on public.cdj_gains;
create trigger pass_cdj after insert on public.cdj_gains for each row execute function public.pass_trg_cdj();
drop trigger if exists pass_radar on public.radar_parties;
create trigger pass_radar after insert or update of fini on public.radar_parties for each row execute function public.pass_trg_duel();
drop trigger if exists pass_rafale on public.rafale_parties;
create trigger pass_rafale after insert or update of fini on public.rafale_parties for each row execute function public.pass_trg_duel();

-- l'état du pass pour le joueur ------------------------------------------------
create or replace function public.pass_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  p pass_saisons%rowtype;
  v_xp integer; v_niv integer; v_q integer; v_a integer; v_possede boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from pass_recent();
  if p.saison is null then return jsonb_build_object('actif', false); end if;
  select coalesce(sum(x.quetes + x.actions), 0) into v_xp from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison;
  select coalesce(sum(x.quetes), 0), coalesce(sum(x.actions), 0) into v_q, v_a
    from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison and x.jour = quete_jour();
  v_niv := least(p.niveaux, v_xp / p.xp_niveau);
  v_possede := exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = p.article_id);
  return jsonb_build_object(
    'actif', now() < p.fin, 'saison', p.saison, 'nom', p.nom, 'debut', p.debut, 'fin', p.fin,
    'niveaux', p.niveaux, 'xp_niveau', p.xp_niveau, 'xp', v_xp, 'niveau', v_niv,
    'dans_niveau', case when v_niv >= p.niveaux then p.xp_niveau else v_xp - v_niv * p.xp_niveau end,
    'jour_quetes', v_q, 'jour_actions', v_a, 'xp_quete', p.xp_quete, 'plafond_actions', p.plafond_actions,
    'possede', v_possede, 'article', p.article_id,
    'prix', (select a.prix_centimes from euros_articles a where a.id = p.article_id),
    'en_vente', coalesce((select a.actif from euros_articles a where a.id = p.article_id), false),
    'recompenses', (select jsonb_agg(jsonb_build_object(
        'niveau', r.niveau, 'payant', r.payant, 'type', r.type, 'valeur', r.valeur, 'quantite', r.quantite,
        'nom', r.nom, 'dispo', r.dispo,
        'recu', exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = r.saison and c.niveau = r.niveau))
        order by r.niveau) from pass_recompenses r where r.saison = p.saison));
end;
$f$;

-- réclamer une récompense (p_niveau), ou toutes celles qui sont prêtes (p_niveau null)
create or replace function public.pass_reclamer(p_niveau integer default null)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  p pass_saisons%rowtype;
  r pass_recompenses%rowtype;
  v_niv integer; v_possede boolean; v numeric; n integer := 0;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from pass_recent();
  if p.saison is null then raise exception 'Pas de pass en cours'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select least(p.niveaux, coalesce(sum(x.quetes + x.actions), 0)::integer / p.xp_niveau) into v_niv
    from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison;
  v_possede := exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = p.article_id);

  for r in select * from pass_recompenses rr where rr.saison = p.saison
            and (p_niveau is null or rr.niveau = p_niveau) order by rr.niveau loop
    if p_niveau is not null then
      if r.niveau > v_niv then raise exception 'Niveau pas encore atteint'; end if;
      if r.payant and not v_possede then raise exception 'Cette récompense est dans le pass'; end if;
      if not r.dispo then raise exception 'Cette récompense arrive bientôt'; end if;
      if exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = p.saison and c.niveau = r.niveau) then
        raise exception 'Récompense déjà récupérée';
      end if;
    else
      continue when r.niveau > v_niv or (r.payant and not v_possede) or not r.dispo
                 or exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = p.saison and c.niveau = r.niveau);
    end if;

    if r.type = 'tp' then
      perform set_config('terrafront.motif', 'pass', true);
      update joueurs set solde = coalesce(solde, 0) + r.quantite where id = v_uid;
    elsif r.type = 'energie' then
      select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
      update joueurs set front_energie = least(60, v + r.quantite), front_energie_maj = now() where id = v_uid;
    elsif r.type in ('dos', 'habillage', 'skin') then
      insert into euros_inventaire(joueur_id, article_id) values (v_uid, r.valeur) on conflict do nothing;
    end if;   -- un titre : rien à faire, titres_possibles lit pass_reclames
    insert into pass_reclames(joueur_id, saison, niveau) values (v_uid, p.saison, r.niveau);
    n := n + 1;
  end loop;
  if p_niveau is null and n = 0 then raise exception 'Rien à réclamer pour l''instant'; end if;
  return pass_etat() || jsonb_build_object('reclamees', n);
end;
$f$;

revoke all on function public.pass_en_cours(), public.pass_recent(), public.pass_ajouter(uuid, boolean, integer),
  public.pass_trg_quete(), public.pass_trg_compteur(), public.pass_trg_cdj(), public.pass_trg_duel() from public, anon, authenticated;
revoke all on function public.pass_etat(), public.pass_reclamer(integer) from public, anon;
grant execute on function public.pass_etat(), public.pass_reclamer(integer) to authenticated;

-- les titres du pass rejoignent le choix du titre ------------------------------
do $do$
declare d text := pg_get_functiondef('public.titres_possibles(uuid)'::regprocedure);
begin
  if position('pass_reclames' in d) > 0 then return; end if;
  if position($a$from (values ('parrain', 'parrain')) as t(titre, badge)$a$ in d) = 0 then
    raise exception 'titres_possibles ne ressemble pas à la version attendue : rien n''a changé';
  end if;
  execute $x$
create or replace function public.titres_possibles(p_joueur uuid)
 returns text[] language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(array_agg(x.titre order by x.titre), '{}')
    from (select t.titre
            from (values ('parrain', 'parrain')) as t(titre, badge)
           where exists (select 1 from joueur_badges b where b.joueur_id = p_joueur and b.badge = t.badge)
          union
          -- s2-53 : les titres gagnés dans un pass de saison
          select r.valeur
            from pass_reclames c join pass_recompenses r on r.saison = c.saison and r.niveau = c.niveau
           where c.joueur_id = p_joueur and r.type = 'titre') x;
$f$
$x$;
end $do$;

commit;

select (select count(*) from public.pass_recompenses)                                         as recompenses_20,
       (select count(*) from public.pass_recompenses where not dispo)                          as objets_bientot_7,
       has_function_privilege('authenticated', 'public.pass_etat()', 'execute')                 as etat_ok,
       has_function_privilege('authenticated', 'public.pass_reclamer(integer)', 'execute')      as reclamer_ok,
       position('pass_reclames' in pg_get_functiondef('public.titres_possibles(uuid)'::regprocedure)) > 0 as titres_ok,
       exists(select 1 from public.pass_saisons where debut is not null)                       as ouvert_doit_etre_false;
