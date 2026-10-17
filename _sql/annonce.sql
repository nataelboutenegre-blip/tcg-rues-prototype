-- ===========================================================================
--  TerraFront — bandeau d'annonce en haut du jeu (17 octobre 2026)
--  Le texte vit dans config_jeu (clé 'annonce') : on l'affiche ou on
--  l'enlève sans toucher au code. Rejouable.
--
--  POUR CHANGER LE TEXTE : modifie la ligne marquée ▼ puis relance le
--  fichier. POUR ENLEVER LE BANDEAU : mets un texte vide ('').
--  Les joueurs le voient au prochain chargement, ou dans les 5 minutes.
-- ===========================================================================
create or replace function public.annonce()
 returns text language sql stable security definer set search_path to 'public'
as $f$
  select nullif(trim(coalesce((select valeur::jsonb #>> '{}' from config_jeu where cle = 'annonce'), '')), '');
$f$;
revoke all on function public.annonce() from public;
grant execute on function public.annonce() to anon, authenticated;

insert into public.config_jeu(cle, valeur)
values ('annonce', to_jsonb(
  -- ▼ le texte du bandeau
  '🛠️ Maintenance ce soir à 21 h 30 : le jeu sera coupé quelques minutes pour passer sur un serveur plus puissant et réduire les lenteurs.'::text
)::text)
on conflict (cle) do update set valeur = excluded.valeur;

select public.annonce() as bandeau_affiche;
