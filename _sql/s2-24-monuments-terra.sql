-- ===========================================================================
--  TerraFront — saison 2 : l'album des Monuments passe dans Terra
--  (17 octobre 2026, décision : les monuments restent uniquement dans Terra)
--
--  monuments_terra() : même catalogue que monuments_catalogue(), mais
--  « à moi » veut dire « la commune est dans MA collection Terra ». Pas de
--  propriétaire : en Terra chacun a sa propre France, un monument ne se
--  prend ni ne se perd. libre = « pas encore trouvé ».
--
--  N'appelée que par le jeu en saison 2 (SAISON2 = true). La fonction de la
--  saison 1 (monuments_catalogue) n'est pas touchée. Lecture seule.
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

create or replace function public.monuments_terra()
returns table(
  commune_code text, nom text, embleme text, departement text, tier text,
  langues integer, image text, photo text,
  photo_auteur text, photo_licence text, photo_source text,
  a_moi boolean, proprietaire text, libre boolean)
language sql
stable security definer
set search_path to 'public'
as $function$
  select m.commune_code, c.nom, m.nom, c.departement, c.tier, m.langues,
         m.image, m.photo, m.photo_auteur, m.photo_licence, m.photo_source,
         (t.commune_code is not null)          as a_moi,
         null::text                            as proprietaire,
         (t.commune_code is null)              as libre
    from monuments m
    join communes c on c.code = m.commune_code
    left join terra_collection t
           on t.commune_code = m.commune_code and t.joueur_id = auth.uid() and t.exemplaires > 0
   order by m.langues desc nulls last, c.nom;
$function$;

revoke all on function public.monuments_terra() from public, anon;
grant execute on function public.monuments_terra() to authenticated;

-- contrôle : le nombre de monuments (le même que l'album actuel)
select count(*) as monuments_terra from public.monuments;
