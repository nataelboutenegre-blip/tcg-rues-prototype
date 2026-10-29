-- ===========================================================================
--  s2-61 — l'interrupteur de patch262 (idées d'Oshannir, validées le 29/10)
--
--  À LANCER AU MOMENT DE L'ANNONCE, comme s2-60 pour « Ta boutique » :
--  le code est déjà en ligne mais reste caché tant que cette fonction
--  n'existe pas.
--
--  Ce que ça allume (à la prochaine ouverture du jeu) :
--    - barre_stable  : sur téléphone, en Terra le QG passe en 4e place comme
--                      en Front ; le bouton Plus affiche les messages du clan
--                      et les échanges reçus ; l'intro du Tirage en une ligne ;
--    - recap_arrivee : après 3 h d'absence, la feuille « Depuis ta dernière
--                      visite » (sièges, paquets, récolte, quêtes, Commune du
--                      jour, clan).
--
--  Pour en éteindre un sans toucher au code, remplacer 1 par 0 dans la ligne
--  'interface' de config_jeu (ou relancer ce fichier après l'avoir modifié).
--  Rejouable. Contrôle attendu : true | true | true
-- ===========================================================================
begin;

insert into public.config_jeu (cle, valeur)
values ('interface', '{"barre_stable": 1, "recap_arrivee": 1}')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.interface_options()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'interface'), '{}'::jsonb);
$f$;

revoke all on function public.interface_options() from public, anon;
grant execute on function public.interface_options() to authenticated;

commit;

select (public.interface_options() ->> 'barre_stable')::int = 1                       as barre_stable,
       (public.interface_options() ->> 'recap_arrivee')::int = 1                      as recap_arrivee,
       has_function_privilege('authenticated', 'public.interface_options()', 'execute') as ok;
