-- ===========================================================================
--  TerraFront — LECTURE SEULE (27 octobre 2026)
--  Les communes de la liste Aurore (233) tenues aujourd'hui dans le Front.
--  En Front, l'Aurore n'est pas un tirage : toute commune de la liste
--  s'affiche en Aurore chez celui qui la tient. Ne modifie rien.
--  Une ligne par joueur (le plus gros d'abord), puis une ligne TOTAL.
--  Résultat à garder hors du dépôt (pseudos).
-- ===========================================================================
with tenues as (
  select p.joueur_id, c.code, c.nom, c.tier
    from public.possessions p
    join public.aurore_communes a on a.code = p.commune_code
    join public.communes c on c.code = p.commune_code
)
select coalesce(j.pseudo, '?')                                             as joueur,
       count(*)                                                             as aurore_tenues,
       count(*) filter (where t.tier = 'legendaire')                        as dont_legendaires,
       string_agg(t.nom, ', ' order by t.nom)                              as communes
  from tenues t left join public.joueurs j on j.id = t.joueur_id
 group by j.pseudo
union all
select 'TOTAL', count(*), count(*) filter (where tier = 'legendaire'),
       (select count(*) from public.aurore_communes)::text || ' communes dans la liste, '
       || (select count(*) from public.aurore_communes a where not exists (select 1 from public.possessions p where p.commune_code = a.code))::text || ' libres'
  from tenues
order by 2 desc;
