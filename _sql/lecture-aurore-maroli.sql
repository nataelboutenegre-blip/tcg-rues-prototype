-- ===========================================================================
--  TerraFront — LECTURE SEULE (27 octobre 2026)
--  D'où viennent les 6 communes Aurore de Maroli dans le Front ?
--  Pour chacune : depuis quand il la tient, la saison inscrite, et la
--  dernière trace dans le journal et dans front_victoires.
--  En plus : combien de communes il tient en tout, et combien d'Aurore
--  on attendrait « par hasard » pour un territoire de cette taille.
--  Ne modifie rien. Résultat à garder hors du dépôt.
-- ===========================================================================
with moi as (select id, pseudo from public.joueurs where pseudo = 'Maroli'),
total as (select count(*) as n from public.possessions p, moi where p.joueur_id = moi.id)
select c.nom                                                             as commune,
       c.tier,
       to_char(p.acquired_at at time zone 'Europe/Paris', 'DD/MM HH24:MI') as tenue_depuis,
       p.saison,
       (select j.type || ' le ' || to_char(j.cree_le at time zone 'Europe/Paris', 'DD/MM HH24:MI')
          from public.journal j
         where j.commune_code = p.commune_code and j.acteur::text in (moi.id::text, moi.pseudo)
         order by j.cree_le desc limit 1)                                as derniere_action_journal,
       (select v.type || ' (' || v.saison || ')'
          from public.front_victoires v
         where v.commune_code = p.commune_code and v.joueur_id = moi.id
         order by v.saison desc limit 1)                                 as victoire_front,
       total.n                                                           as communes_tenues_en_tout,
       round(total.n * 231.0 / 34868, 1)                                 as aurore_attendues_au_hasard
  from public.possessions p
  join moi on p.joueur_id = moi.id
  join public.aurore_communes a on a.code = p.commune_code
  join public.communes c on c.code = p.commune_code
  cross join total
 order by p.acquired_at;
