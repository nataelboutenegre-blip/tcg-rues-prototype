-- ===========================================================================
--  TerraFront — s2-90 : la carte en direct (3/11/2026, avec la page direct/)
--  Saison 3, étape 2 (claude/saison-3.md). Aperçu validé par Nataël le 3/11
--  (apercu-carte-en-direct.png) ; « on laisse toutes [les conquêtes], et quand
--  on aura plus de monde on laissera les raretés supérieures » : réglage
--  config_jeu 'direct'.seuil (commun = tout ; rare = rares et plus…).
--
--  Une page PUBLIQUE (sans connexion), terrafront.fr/direct/, pour les streams :
--  la carte aux couleurs des clans, les conquêtes qui clignotent, le fil du
--  Front, les chiffres du jour et le classement des clans. Elle lit seulement :
--   - direct_catalogue() : la fiche fixe des communes (même cache que s2-89) ;
--   - direct_etat()      : qui possède quoi + les clans + les joueurs (pseudo, clan) ;
--   - direct_depuis(n)   : ce qui a changé depuis le n° n (carte_changements, s2-89) ;
--   - direct_fil(t)      : conquêtes, défenses réussies, Fonderies et Forteresses
--                          construites, bombes en préparation (département seul)
--                          et bombes lâchées ; jamais le Centre de recherche ;
--   - direct_chiffres()  : conquêtes du jour, communes libres, clans.
--  Tout est en lecture ; anon peut appeler. Couper : config_jeu 'direct'.ouvert = 0
--  (les fonctions rendent alors null et la page affiche « Le direct est en pause »).
--  Prérequis : s2-89 (carte_catalogue_cache, carte_changements).
--  Rejouable. Contrôle (une ligne) : true | true | true | true | true | (conquêtes du jour)
-- ===========================================================================
do $$ begin
  if to_regclass('public.carte_changements') is null or to_regclass('public.carte_catalogue_cache') is null then
    raise exception 'Lance d''abord s2-89-etat-compact-carte.sql';
  end if;
end $$;

begin;

insert into public.config_jeu (cle, valeur) values ('direct', '{"ouvert": 1, "seuil": "commun"}')
on conflict (cle) do nothing;

create or replace function public.direct_reglages()
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'direct'), '{}'::jsonb)
$f$;
revoke all on function public.direct_reglages() from public, anon, authenticated;

create or replace function public.direct_ouvert()
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  select coalesce((direct_reglages() ->> 'ouvert')::int, 0) = 1
$f$;
revoke all on function public.direct_ouvert() from public, anon, authenticated;

-- rang d'une rareté (commun 0 … légendaire 4)
create or replace function public.direct_rang(p_tier text)
 returns integer language sql immutable set search_path to 'public' as $f$
  select coalesce(array_position(array['commun','peucommun','rare','epique','legendaire'], p_tier) - 1, 0)
$f$;
revoke all on function public.direct_rang(text) from public, anon, authenticated;

-- ---------- le catalogue (même cache que le jeu) ----------
create or replace function public.direct_catalogue()
 returns json language sql stable security definer set search_path to 'public' as $f$
  select json_build_object('version', k.version, 'c', k.donnees)
    from carte_catalogue_cache k where k.id = 1 and direct_ouvert();
$f$;

-- ---------- l'état complet ----------
create or replace function public.direct_etat()
 returns json language sql stable security definer set search_path to 'public' as $f$
  with p as (select commune_code, joueur_id from possessions where joueur_id is not null),
       ji as (select joueur_id, (row_number() over (order by joueur_id) - 1)::int as i
                from (select distinct joueur_id from p) d)
  select json_build_object(
    'id', coalesce((select max(id) from carte_changements),
                   (select case when is_called then last_value else 0 end from carte_changements_id_seq)),
    'catalogue', (select version from carte_catalogue_cache where id = 1),
    'clans', coalesce((select json_agg(json_build_array(c.id, c.tag, c.nom, c.couleur)) from clans c), '[]'::json),
    'joueurs', coalesce((select json_agg(json_build_array(ji.joueur_id, j.pseudo, m.clan_id) order by ji.i)
                           from ji left join joueurs j on j.id = ji.joueur_id
                           left join clan_membres m on m.joueur_id = ji.joueur_id), '[]'::json),
    'p', coalesce((select json_agg(json_build_array(p.commune_code, ji.i)) from p join ji using (joueur_id)), '[]'::json))
  where direct_ouvert();
$f$;

-- ---------- ce qui a changé ----------
create or replace function public.direct_depuis(p_id bigint)
 returns json language plpgsql stable security definer set search_path to 'public' as $f$
declare v_min bigint; v_max bigint; v_n int;
begin
  if not direct_ouvert() then return null; end if;
  select min(id), max(id) into v_min, v_max from carte_changements;
  if v_max is null then
    if (select is_called and last_value > coalesce(p_id, 0) from carte_changements_id_seq) then
      return json_build_object('complet', true);
    end if;
    return json_build_object('id', coalesce(p_id, 0), 'ch', '[]'::json, 'joueurs', '[]'::json);
  end if;
  if p_id is null or v_min > p_id + 1 then return json_build_object('complet', true); end if;
  select count(*) into v_n from carte_changements where id > p_id - 100;
  if v_n > 5000 then return json_build_object('complet', true); end if;
  return json_build_object(
    'id', greatest(v_max, p_id),
    'ch', coalesce((select json_agg(json_build_array(x.id, x.commune_code, x.joueur_id) order by x.id)
                      from carte_changements x where x.id > p_id - 100), '[]'::json),
    'joueurs', coalesce((select json_agg(json_build_array(j.id, j.pseudo, m.clan_id))
                           from joueurs j left join clan_membres m on m.joueur_id = j.id
                          where j.id in (select x.joueur_id from carte_changements x where x.id > p_id - 100)), '[]'::json));
end; $f$;

-- ---------- le fil du Front ----------
-- [clé, type, le (s), acteur, tag du clan de l'acteur, cible, code, nom, rareté, département]
create or replace function public.direct_fil(p_apres timestamptz default null)
 returns json language sql stable security definer set search_path to 'public' as $f$
  with s as (select direct_rang(coalesce(direct_reglages() ->> 'seuil', 'commun')) as seuil),
  ev as (
    select 'j' || e.id as cle, e.type::text as type, e.cree_le as le, e.acteur, e.cible,
           e.commune_code::text as code, e.commune_nom::text as nom, e.tier::text as tier, null::text as dept
      from journal e, s
     where e.type in ('conquete', 'defense', 'fonderie', 'forteresse')
       and e.cree_le > coalesce(p_apres, now() - interval '6 hours')
       and (e.type not in ('conquete', 'defense') or direct_rang(e.tier) >= s.seuil)
    union all
    select 'p' || b.id, 'bombe_prep', b.commence_le, null, null, null, null, null, b.dept
      from bombes_preparations b
     where b.commence_le > coalesce(p_apres, now() - interval '6 hours')
    union all
    select 'b' || b.id, 'bombe', b.le, b.lanceur, null, b.cible_code, c.nom, null, c.departement
      from bombes b left join communes c on c.code = b.cible_code
     where b.le > coalesce(p_apres, now() - interval '6 hours')
  ),
  dernier as (select * from ev order by le desc limit 30)
  select coalesce(json_agg(json_build_array(d.cle, d.type, floor(extract(epoch from d.le))::bigint,
           ja.pseudo, ca.tag, jc.pseudo, d.code, d.nom, d.tier, coalesce(d.dept, cc.departement))
           order by d.le desc), '[]'::json)
    from dernier d
    left join joueurs ja on ja.id = d.acteur
    left join clan_membres ma on ma.joueur_id = d.acteur
    left join clans ca on ca.id = ma.clan_id
    left join joueurs jc on jc.id = d.cible
    left join communes cc on cc.code = d.code
   where direct_ouvert();
$f$;

-- ---------- les chiffres ----------
create or replace function public.direct_chiffres()
 returns json language sql stable security definer set search_path to 'public' as $f$
  with minuit as (select ((now() at time zone 'Europe/Paris')::date::timestamp at time zone 'Europe/Paris') as t),
  conq as (select e.acteur from journal e, minuit where e.type = 'conquete' and e.cree_le >= minuit.t),
  par_clan as (
    select c.id, c.tag, c.nom, c.couleur,
           (select count(*) from possessions p join clan_membres m on m.joueur_id = p.joueur_id where m.clan_id = c.id) as communes,
           (select count(*) from conq join clan_membres m on m.joueur_id = conq.acteur where m.clan_id = c.id) as conquetes
      from clans c)
  select json_build_object(
    'conquetes_jour', (select count(*) from conq),
    'libres', greatest(0, (select json_array_length(donnees) from carte_catalogue_cache where id = 1) - (select count(*) from possessions)),
    'clans', coalesce((select json_agg(json_build_array(x.id, x.tag, x.nom, x.couleur, x.communes, x.conquetes) order by x.communes desc)
                         from (select * from par_clan order by communes desc limit 8) x), '[]'::json))
  where direct_ouvert();
$f$;

revoke all on function public.direct_catalogue(), public.direct_etat(), public.direct_depuis(bigint),
                       public.direct_fil(timestamptz), public.direct_chiffres() from public;
grant execute on function public.direct_catalogue(), public.direct_etat(), public.direct_depuis(bigint),
                          public.direct_fil(timestamptz), public.direct_chiffres() to anon, authenticated;

commit;

-- Contrôle : true | true | true | true | true | (conquêtes du jour)
select has_function_privilege('anon', 'public.direct_etat()', 'execute')                 as etat_ok,
       has_function_privilege('anon', 'public.direct_depuis(bigint)', 'execute')         as depuis_ok,
       has_function_privilege('anon', 'public.direct_fil(timestamptz)', 'execute')       as fil_ok,
       has_function_privilege('anon', 'public.direct_catalogue()', 'execute')            as catalogue_ok,
       public.direct_ouvert()                                                             as ouvert,
       (public.direct_chiffres() ->> 'conquetes_jour')::int                               as conquetes_jour;
