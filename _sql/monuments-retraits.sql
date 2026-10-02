-- ===========================================================================
--  TerraFront — Retrait de trois camps de concentration de la liste
--
--  CE QUE J'AI RATÉ
--    En constituant la liste des monuments, j'ai écarté à la main dix
--    entrées qui étaient des attentats, des tueries et un crime de guerre,
--    dont Oradour-sur-Glane. J'en ai laissé passer trois :
--
--      — le camp de concentration de Natzweiler-Struthof (Natzwiller, 67)
--      — le camp de Gurs (Gurs, 64)
--      — le camp de Drancy (Drancy, 93)
--
--    Wikidata les classe comme des lieux parce qu'ils ont des coordonnées,
--    et mon filtre par notoriété ne distingue pas un château d'un camp
--    d'internement. C'est mon erreur, et elle est en ligne depuis hier :
--    ces trois cartes sont dans l'album, avec un propriétaire ou la mention
--    « personne ne l'a » en dessous.
--
--    Drancy et Gurs sont les camps d'où partaient les convois de déportation.
--    Ce ne sont pas des monuments, ce sont des lieux de mémoire des victimes.
--    Ils n'ont rien à faire dans une collection qu'on possède, qu'on échange
--    et pour laquelle on se bat.
--
--  CE QUE FAIT CE FICHIER
--    Il les retire de la table monuments. Les communes elles-mêmes restent
--    dans le jeu, évidemment : seule l'étiquette de monument disparaît.
--    Le catalogue passe de 239 à 236.
--
--    Le nom est vérifié en plus du code, pour qu'une erreur de code ne
--    puisse pas supprimer la mauvaise ligne.
--
--  CE QUI RESTE À FAIRE À LA MAIN
--    Si des images avaient été posées pour ces trois-là, les fichiers
--    restent dans le bucket sans que rien ne les lise. Ils ne gênent pas,
--    mais ils peuvent être supprimés depuis Supabase Storage.
-- ===========================================================================

delete from public.monuments
 where (commune_code = '67314' and nom ilike '%Natzweiler%')
    or (commune_code = '64253' and nom ilike '%Gurs%')
    or (commune_code = '93029' and nom ilike '%Drancy%');


-- ---------------------------------------------------------------------------
--  Contrôle
-- ---------------------------------------------------------------------------
select 'A. les trois sont partis' as controle,
       case when not exists (
              select 1 from public.monuments
               where commune_code in ('67314', '64253', '93029'))
            then 'oui' else 'NON, il en reste' end as valeur
union all
select 'B. total des monuments',
       (select count(*)::text from public.monuments)
union all
select 'C. reste-t-il un lieu de ce type',
       coalesce((select string_agg(nom, ' · ')
                   from public.monuments
                  where nom ilike '%camp %' or nom ilike '%massacre%'
                     or nom ilike '%attentat%' or type ilike '%camp de concentration%'
                     or type ilike '%camp d%internement%'),
                'aucun')
union all
select 'D. monuments encore sans image',
       (select count(*)::text from public.monuments where photo is null)
order by 1;
