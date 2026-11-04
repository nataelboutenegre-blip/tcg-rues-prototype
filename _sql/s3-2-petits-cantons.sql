-- ===========================================================================
--  TerraFront — s3-2 : le bonus d'un tout petit canton au prorata
--  (décision de Nataël du 4/11, « bonne idée ! »).
--
--  8 cantons suisses ont moins de 20 communes (Glaris 3, Bâle-Ville 3,
--  Appenzell Rhodes-Intérieures 5, Obwald 7, Nidwald 11, Zoug 11, Uri 19,
--  Appenzell Rhodes-Extérieures 20) ; le plus petit département français en a
--  20 (Paris, 20 arrondissements). Sans règle, tenir les 3 communes de
--  Bâle-Ville rapporterait +1 400, autant qu'un département entier.
--  Maintenant : le bonus d'un département ou d'un canton de moins de
--  20 communes est multiplié par (communes / 20), arrondi. Bâle-Ville entier :
--  1 400 × 3/20 = 210. Ça ne compte que pour le bonus du palier : le
--  canton reste « dominé » ou « contrôlé » pour la région comme avant.
--  Rien ne change pour la France (aucun département sous 20 communes).
--  Réglage : config_jeu 'score_s2'.prorata_communes (20 si absent ; 0 = pas de
--  prorata).
--  Modifiée en place à partir de sa définition en production. Rejouable.
--  Contrôle attendu : true | 20
-- ===========================================================================
begin;

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

do $$
declare d text := pg_get_functiondef('public.front_territoires()'::regprocedure);
begin
  if position('s3-2' in d) > 0 then raise notice 'front_territoires : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    '    select pa.joueur_id, pa.departement,',
    '    select pa.joueur_id, pa.departement, ta.n as taille,   -- s3-2',
    1, 'front_territoires (taille)');
  d := pg_temp.remp(d,
    '    select d.*, score_reglage(''palier_'' || d.palier) as pts',
    '    select d.*, round(score_reglage(''palier_'' || d.palier)
                      * case when coalesce(score_reglage(''prorata_communes''), 20) > 0
                             then least(1, d.taille / coalesce(score_reglage(''prorata_communes''), 20))
                             else 1 end) as pts   -- s3-2 : petit canton au prorata',
    1, 'front_territoires (prorata)');
  execute d;
end $$;

commit;

-- Contrôle : true | 20
select position('s3-2' in pg_get_functiondef('public.front_territoires()'::regprocedure)) > 0   as territoires_ok,
       coalesce(score_reglage('prorata_communes'), 20)::integer                                  as prorata_communes;
