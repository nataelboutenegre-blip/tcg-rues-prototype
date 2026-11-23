-- s3-59 (23/11/2026) : l'historique des bâtiments pris et perdus cette saison (idée d'Arkhannou).
-- Rien de nouveau à enregistrer : depuis s2-142, chaque conquête qui détruit des bâtiments écrit une ligne
-- « pertes » dans journal (acteur = le preneur, cible = l'ancien propriétaire, infos.b = les bâtiments).
-- Cette fonction lit ces lignes pour le joueur connecté, depuis le début de la saison en cours.
create or replace function public.batiments_pris_perdus()
returns jsonb language sql stable security definer set search_path to 'public' as $$
  with s as (select debut from saisons where id = saison_en_cours_id()),
  l as (
    select j.cree_le, j.commune_code, j.commune_nom, j.tier, j.infos,
           case when j.acteur = auth.uid() then 'pris' else 'perdu' end sens,
           case when j.acteur = auth.uid() then j.cible else j.acteur end autre
      from journal j, s
     where j.type = 'pertes' and j.cree_le >= s.debut
       and (j.acteur = auth.uid() or j.cible = auth.uid())
     order by j.cree_le desc limit 200)
  select jsonb_build_object(
    'pris', (select count(*) from l where sens = 'pris'),
    'perdus', (select count(*) from l where sens = 'perdu'),
    'liste', coalesce((select jsonb_agg(jsonb_build_object('le', l.cree_le, 'sens', l.sens, 'code', l.commune_code, 'nom', l.commune_nom,
               'tier', l.tier, 'b', l.infos->'b', 'autre', coalesce(jo.pseudo, 'un joueur')) order by l.cree_le desc)
               from l left join joueurs jo on jo.id = l.autre), '[]'::jsonb))
  where auth.uid() is not null;
$$;
revoke all on function public.batiments_pris_perdus() from public, anon;
grant execute on function public.batiments_pris_perdus() to authenticated;
-- Contrôle : select batiments_pris_perdus();  → null hors connexion
