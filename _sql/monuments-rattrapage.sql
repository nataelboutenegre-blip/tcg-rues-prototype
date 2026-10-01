-- ===========================================================================
--  TerraFront — Le rattrapage des dix emblèmes sans commune
--
--  CE QUE LE DIAGNOSTIC A MONTRÉ
--    Sur les dix, un seul est récupérable. Les neuf autres n'ont pas de place
--    dans le jeu, et c'est une bonne nouvelle : rien n'est cassé.
--
--    — 7 sont outre-mer (Kourou, Cayenne, La Désirade, Saint-Philippe,
--      Salazie, Camopi, Saint-Claude en Guadeloupe). Les communes d'outre-mer
--      ne sont pas dans la base du jeu, donc il n'y a rien à quoi les
--      rattacher. Le contrôle ci-dessous donne le chiffre exact.
--
--      ATTENTION à la dernière ligne du diagnostic : il proposait de
--      rattacher la Soufrière au code 39478. C'est FAUX, et c'est un défaut
--      de mon diagnostic, qui cherchait par nom quand le code échouait :
--      Saint-Claude existe aussi dans le Jura. La Soufrière est un volcan de
--      Guadeloupe. On ne la rattache pas.
--
--    — « Celine » à Paris n'est pas un emblème mais une maison de couture,
--      et l'image Wikimedia est une vitrine à Madrid. Écartée.
--
--    — Le MuCEM est dans le 2e arrondissement de Marseille (13202), qui
--      porte déjà la cathédrale Sainte-Marie-Majeure. Un emblème par
--      commune : on garde la Major, plus emblématique de la ville.
--
--    — Le musée des Beaux-Arts de Lyon est place des Terreaux, donc dans le
--      1er arrondissement (69381), qui n'a pas encore d'emblème. Celui-là se
--      rattrape, et c'est tout l'objet de ce fichier.
--
--  POURQUOI LE LANCER AVANT LES IMAGES
--    Le script des images lit la table : s'il tourne après ce fichier, il
--    descend aussi la photo du musée dans la même passe.
-- ===========================================================================


-- Le code et l'absence d'emblème sont vérifiés dans la requête elle-même :
-- si le 1er arrondissement de Lyon n'était pas dans communes, le fichier
-- n'insérerait rien plutôt que d'échouer.
insert into public.monuments (commune_code, nom, type, langues, image, wikidata)
select '69381', 'musée des Beaux-Arts de Lyon', 'musée d''art', 29,
       'Facade Musee des Beaux-Arts de Lyon n02.jpg', 'Q511'
 where exists (select 1 from public.communes where code = '69381')
on conflict (commune_code) do nothing;


-- ---------------------------------------------------------------------------
--  Contrôle
-- ---------------------------------------------------------------------------
select 'A. communes d''outre-mer dans la base' as controle,
       (select count(*)::text from public.communes
         where departement like '97%' or code like '97%') as valeur
union all
select 'B. le 1er arrondissement de Lyon existe',
       case when exists (select 1 from public.communes where code = '69381')
            then 'oui, ' || (select nom from public.communes where code = '69381')
            else 'NON' end
union all
select 'C. son emblème est posé',
       coalesce((select nom from public.monuments where commune_code = '69381'), 'NON')
union all
select 'D. total des emblèmes',
       (select count(*)::text from public.monuments)
union all
select 'E. emblèmes sans image à descendre',
       (select count(*)::text from public.monuments
         where image is not null and photo is null)
order by 1;
