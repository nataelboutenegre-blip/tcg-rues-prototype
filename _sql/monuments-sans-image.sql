-- ===========================================================================
--  TerraFront — Quels monuments n'ont pas d'image, et pourquoi
--
--  POURQUOI
--    229 images sur 239 ont été posées. Le script en a écarté dix, et il a
--    affiché leurs noms à la fin — mais une sortie de terminal se perd. La
--    base, elle, garde la trace.
--
--  CE QU'ON LIT
--    La colonne « fichier Wikimedia » dit où est le problème :
--      — un nom de fichier présent, mais pas de photo : le script a écarté
--        l'image faute d'auteur lisible. C'est voulu : citer la source est
--        une obligation, pas une politesse. Ces dix-là resteront avec une
--        icône, à moins d'aller chercher une autre image à la main.
--      — aucun nom de fichier : Wikidata n'en proposait pas. Rien à
--        reprendre, il faudrait en trouver une ailleurs.
--
--  Lecture seule. Ce fichier ne modifie rien.
-- ===========================================================================

select m.nom                                   as monument,
       c.nom                                   as commune,
       c.departement                           as dept,
       m.langues                               as langues,
       coalesce(m.image, '(aucun)')            as fichier_wikimedia,
       case when m.image is null then 'Wikidata ne propose aucune image'
            else 'image trouvée mais auteur illisible, écartée' end as diagnostic
  from public.monuments m
  join public.communes c on c.code = m.commune_code
 where m.photo is null
 order by m.langues desc nulls last, c.nom;
