-- ===========================================================================
--  TerraFront — les Aurore du Front gardent leur éclat en Terra (25 octobre 2026)
--  En saison 1, une commune de la liste Aurore s'affichait en Aurore dans le
--  Front. Versée en Terra à la clôture, elle devenait une carte normale :
--  le joueur la croyait Aurore, et personne ne la voyait comme telle
--  (Thue et Mue de Maroli). Décision de Nataël : elle devient une Aurore en
--  Terra, avec une étiquette rouge « Front S1 » qui dit d'où elle vient.
--  - terra_collection.aurore_s1 : l'exemplaire Aurore vient du Front S1 ;
--  - terra_aurores_s1(joueur) : les codes concernés (pour l'étiquette).
--  Une Aurore ne s'échange pas et ne se vend pas : rien ne change pour la
--  Bourse. Rejouable. Contrôle : cartes_passees_en_aurore | joueurs.
-- ===========================================================================
begin;
alter table public.terra_collection add column if not exists aurore_s1 boolean not null default false;

update public.terra_collection t
   set aurore = greatest(t.aurore, 1), aurore_s1 = true
 where t.origine = 'saison-1' and t.exemplaires > 0 and t.aurore = 0 and not t.aurore_s1
   and t.commune_code in (select code from public.aurore_communes);

create or replace function public.terra_aurores_s1(p_joueur uuid)
 returns setof text language sql stable security definer set search_path to 'public'
as $f$ select t.commune_code::text from terra_collection t where t.joueur_id = p_joueur and t.aurore_s1 and t.exemplaires > 0 $f$;
revoke all on function public.terra_aurores_s1(uuid) from public, anon;
grant execute on function public.terra_aurores_s1(uuid) to authenticated;
commit;

select (select count(*) from public.terra_collection where aurore_s1)                    as cartes_passees_en_aurore,
       (select count(distinct joueur_id) from public.terra_collection where aurore_s1)  as joueurs;
