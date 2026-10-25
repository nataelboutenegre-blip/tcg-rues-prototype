-- ===========================================================================
--  TerraFront — les clans pour le Discord (lecture seule, ne change rien).
--  Copie le résultat (le JSON) dans _discord/clans.json, puis lance
--  python3 _discord/clans-discord.py
-- ===========================================================================
select jsonb_pretty(coalesce(jsonb_agg(jsonb_build_object(
         'tag', c.tag,
         'nom', c.nom,
         'couleur', c.couleur,
         'membres', coalesce((select jsonb_agg(j.pseudo order by j.pseudo)
                                from public.clan_membres m join public.joueurs j on j.id = m.joueur_id
                               where m.clan_id = c.id), '[]'::jsonb))
       order by c.tag), '[]'::jsonb)) as clans_discord
  from public.clans c;
