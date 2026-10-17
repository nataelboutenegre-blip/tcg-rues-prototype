-- ===========================================================================
--  TerraFront — saison 2, Terra : les cartes achetées en points ne
--  s'échangent pas (17 octobre 2026, règle décidée le 3 octobre)
--
--  SANS EFFET EN SAISON 1 : Terra est fermé (terra_ouverte() faux), aucune
--  carte n'entre dans terra_collection avant le jour J.
--
--  Règles :
--   - BLOQUÉS : les exemplaires obtenus en dépensant des points (paquet
--     acheté 200 pts, paquet et collection de la Boutique) ;
--   - LIBRES : paquets gratuits, quêtes, récompenses de collection, cartes
--     versées de la saison 1, cartes reçues par échange ou achetées à la
--     Bourse (elles étaient libres chez l'autre joueur) ;
--   - l'Échange et la Bourse entre joueurs n'acceptent que des exemplaires
--     libres (on garde toujours au moins un exemplaire, et les Aurore) ;
--   - la revente AU JEU accepte les bloqués, et les vend en premier ;
--   - le contrat consomme d'abord les bloqués ; la commune reçue est
--     bloquée si au moins un des dix doublons l'était.
--
--  Comment : une colonne bloques sur terra_collection, tenue à jour par un
--  déclencheur. Il lit le motif de points déjà posé par les fonctions
--  (terrafront.motif = 'terra_paquet' ou 'boutique') : aucune fonction
--  d'achat n'est modifiée. Seules trois fonctions reçoivent une ligne
--  (« les bloqués d'abord ») et deux filtres d'échange changent.
--
--  Imprécision assumée : on ne sait pas si un exemplaire Aurore est aussi
--  bloqué. Le calcul compte les deux à part (aurore + bloques), donc il peut
--  refuser un échange qui aurait été permis, jamais l'inverse.
--
--  Tout se fait dans une transaction : si un repère manque, rien ne change.
--  Rejouable. Finit par un contrôle (une ligne, tout à true).
-- ===========================================================================

begin;

-- 1. La colonne ---------------------------------------------------------------
alter table public.terra_collection add column if not exists bloques integer not null default 0;
do $$ begin
  alter table public.terra_collection add constraint terra_collection_bloques_ok
    check (bloques >= 0 and bloques <= exemplaires);
exception when duplicate_object then null; end $$;

-- 2. Le déclencheur -----------------------------------------------------------
--  Entrée (exemplaires qui montent) : bloquée si le motif est un achat en
--  points, ou si un contrat vient de consommer un exemplaire bloqué.
--  Sortie (exemplaires qui baissent) : par défaut les LIBRES partent d'abord
--  (Échange, Bourse) ; avec terrafront.bloques_dabord = '1', les BLOQUÉS
--  partent d'abord (revente au jeu, contrat).
create or replace function public.terra_collection_bloques()
 returns trigger language plpgsql set search_path to 'public'
as $f$
declare
  v_avant_ex integer := case when tg_op = 'INSERT' then 0 else old.exemplaires end;
  v_avant_bl integer := case when tg_op = 'INSERT' then 0 else old.bloques end;
  v_delta    integer := new.exemplaires - v_avant_ex;
  v_motif    text    := coalesce(current_setting('terrafront.motif', true), '');
  v_pris     integer;
begin
  if v_delta > 0 then
    if v_motif in ('terra_paquet', 'boutique')
       or coalesce(current_setting('terrafront.contrat_bloque', true), '') = '1' then
      new.bloques := v_avant_bl + v_delta;
    else
      new.bloques := v_avant_bl;
    end if;
  elsif v_delta < 0 then
    if coalesce(current_setting('terrafront.bloques_dabord', true), '') = '1' then
      v_pris := least(v_avant_bl, -v_delta);
      new.bloques := v_avant_bl - v_pris;
      if v_pris > 0 then perform set_config('terrafront.contrat_bloque', '1', true); end if;
    else
      new.bloques := least(v_avant_bl, new.exemplaires);
    end if;
  else
    new.bloques := least(coalesce(new.bloques, v_avant_bl), new.exemplaires);
  end if;
  return new;
end;
$f$;
revoke all on function public.terra_collection_bloques() from public, anon, authenticated;

drop trigger if exists trg_terra_collection_bloques on public.terra_collection;
create trigger trg_terra_collection_bloques
  before insert or update of exemplaires on public.terra_collection
  for each row execute function public.terra_collection_bloques();

-- 3. Les doublons ÉCHANGEABLES (Échange, Bourse entre joueurs) -----------------
create or replace function public.terra_doublons(p_joueur uuid, p_code text)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select greatest(0, t.exemplaires - greatest(1, t.aurore + t.bloques))
                     from terra_collection t
                    where t.joueur_id = p_joueur and t.commune_code = p_code), 0);
$f$;
revoke all on function public.terra_doublons(uuid, text) from public, anon, authenticated;

create or replace function pg_temp.remplacer(p_def text, p_avant text, p_apres text, p_etiquette text)
returns text language plpgsql as $$
declare n integer;
begin
  n := (length(p_def) - length(replace(p_def, p_avant, ''))) / length(p_avant);
  if n <> 1 then
    raise exception 'Repère « % » trouvé % fois (attendu 1) : rien n''a été modifié', p_etiquette, n;
  end if;
  return replace(p_def, p_avant, p_apres);
end $$;

-- 4. Les cibles d'échange : seulement les doublons libres des autres ---------
do $do$
declare d text := pg_get_functiondef('public.terra_cibles_echange(text, text)'::regprocedure);
begin
  if d like '%t.aurore + t.bloques%' then raise notice 'terra_cibles_echange : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 't.exemplaires - greatest(1, t.aurore) > 0',
                            't.exemplaires - greatest(1, t.aurore + t.bloques) > 0', 'filtre');
  execute d;
end $do$;

-- 5. Revente au jeu : les bloqués partent d'abord --------------------------
do $do$
declare d text := pg_get_functiondef('public.terra_vendre(text, integer)'::regprocedure);
begin
  if d like '%bloques_dabord%' then raise notice 'terra_vendre : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'update terra_collection set exemplaires = exemplaires - p_n',
     E'perform set_config(''terrafront.bloques_dabord'', ''1'', true);\n  update terra_collection set exemplaires = exemplaires - p_n', 'vente');
  execute d;
end $do$;

do $do$
declare d text := pg_get_functiondef('public.terra_vendre_doublons(text[])'::regprocedure);
begin
  if d like '%bloques_dabord%' then raise notice 'terra_vendre_doublons : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, '  with cibles as (',
     E'  perform set_config(''terrafront.bloques_dabord'', ''1'', true);\n  with cibles as (', 'vente');
  execute d;
end $do$;

-- 6. Contrat : les bloqués partent d'abord, la carte reçue hérite ----------
do $do$
declare d text := pg_get_functiondef('public.terra_signer_contrat(text[], text)'::regprocedure);
begin
  if d like '%bloques_dabord%' then raise notice 'terra_signer_contrat : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, '  -- les dix doublons partent',
     E'  perform set_config(''terrafront.contrat_bloque'', '''', true);\n  perform set_config(''terrafront.bloques_dabord'', ''1'', true);\n  -- les dix doublons partent', 'contrat');
  execute d;
end $do$;

commit;

-- ---------- contrôle : true | true | true | true | true | true ----------
select exists (select 1 from information_schema.columns
                where table_name = 'terra_collection' and column_name = 'bloques')                              as colonne,
       exists (select 1 from pg_trigger where tgname = 'trg_terra_collection_bloques')                            as declencheur,
       pg_get_functiondef('public.terra_cibles_echange(text, text)'::regprocedure) like '%t.aurore + t.bloques%'   as echange,
       pg_get_functiondef('public.terra_vendre(text, integer)'::regprocedure) like '%bloques_dabord%'             as vente,
       pg_get_functiondef('public.terra_vendre_doublons(text[])'::regprocedure) like '%bloques_dabord%'           as vente_lot,
       pg_get_functiondef('public.terra_signer_contrat(text[], text)'::regprocedure) like '%bloques_dabord%'      as contrat;

-- ---------------------------------------------------------------------------
--  Pour le jeu : mes exemplaires bloqués (seulement les communes concernées).
--  À part de terra_collection_moi pour ne pas changer son type de retour.
-- ---------------------------------------------------------------------------
create or replace function public.terra_bloques_moi()
 returns table(code text, bloques integer)
 language sql stable security definer set search_path to 'public'
as $f$
  select t.commune_code::text, t.bloques
    from terra_collection t
   where t.joueur_id = auth.uid() and t.bloques > 0 and terra_ouverte();
$f$;
revoke all on function public.terra_bloques_moi() from public, anon;
grant execute on function public.terra_bloques_moi() to authenticated;
