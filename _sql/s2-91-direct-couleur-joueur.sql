-- ===========================================================================
--  TerraFront — s2-91 : la carte en direct connaît la couleur de jeu de chaque joueur
--  (3/11/2026, avec direct.js v4). Demande de Nataël : « enlever la surbrillance de
--  mes communes, il faut que ce soit neutre, juste ma couleur de jeu ».
--  direct_etat() et direct_depuis() rendent, pour chaque joueur, la couleur qu'il a
--  choisie dans le jeu (joueurs.couleur, null s'il n'en a pas choisi : la page prend
--  alors la même couleur automatique que le jeu). La page ne s'en sert que pour TES
--  communes (reconnues par ta session du jeu ou ?joueur=Pseudo) ; les autres restent
--  aux couleurs de leur clan.
--  Prérequis : s2-90. Rejouable. Contrôle (une ligne) : true | true
-- ===========================================================================
do $$ begin
  if to_regprocedure('public.direct_ouvert()') is null then
    raise exception 'Lance d''abord s2-90-carte-en-direct.sql';
  end if;
end $$;

begin;

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
    'joueurs', coalesce((select json_agg(json_build_array(ji.joueur_id, j.pseudo, m.clan_id, j.couleur) order by ji.i)
                           from ji left join joueurs j on j.id = ji.joueur_id
                           left join clan_membres m on m.joueur_id = ji.joueur_id), '[]'::json),
    'p', coalesce((select json_agg(json_build_array(p.commune_code, ji.i)) from p join ji using (joueur_id)), '[]'::json))
  where direct_ouvert();
$f$;

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
    'joueurs', coalesce((select json_agg(json_build_array(j.id, j.pseudo, m.clan_id, j.couleur))
                           from joueurs j left join clan_membres m on m.joueur_id = j.id
                          where j.id in (select x.joueur_id from carte_changements x where x.id > p_id - 100)), '[]'::json));
end; $f$;

revoke all on function public.direct_etat(), public.direct_depuis(bigint) from public;
grant execute on function public.direct_etat(), public.direct_depuis(bigint) to anon, authenticated;

commit;

-- Contrôle : true | true
select has_function_privilege('anon', 'public.direct_etat()', 'execute')         as etat_ok,
       position('j.couleur' in pg_get_functiondef('public.direct_etat()'::regprocedure)) > 0 as couleur_ok;
