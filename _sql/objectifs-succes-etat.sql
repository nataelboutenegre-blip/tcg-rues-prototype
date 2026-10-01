-- ===========================================================================
--  TerraFront — Objectifs et Succès : relevé de l'existant
--
--  LECTURE SEULE. Ce fichier ne modifie rien, ne crée rien, ne supprime rien.
--  Il se contente de montrer ce qui est en base.
--
--  POURQUOI IL EXISTE
--    objectifs(), succes(), reclamer_objectif() et reclamer_departement()
--    datent d'avant la règle « tout SQL exécuté est committé dans le dépôt ».
--    Leur source n'est nulle part chez toi, donc je ne peux ni corriger le
--    bug signalé par Boule2Pain ni brancher les défis thématiques sans
--    d'abord lire ce qui existe.
--
--  N'APPELLE PAS saison_courante(). C'est volontaire : cette fonction arme
--  le compte à rebours de fin de saison dès qu'elle voit le pot sous le
--  seuil. Un relevé ne doit jamais déclencher la fin d'une saison.
--
--  À FAIRE : lancer, puis me coller les quatre résultats.
-- ===========================================================================


-- ---------------------------------------------------------------------------
--  A. Le code des quatre fonctions
-- ---------------------------------------------------------------------------
select p.proname as fonction,
       pg_get_functiondef(p.oid) as source
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('objectifs', 'succes', 'reclamer_objectif', 'reclamer_departement')
 order by p.proname;


-- ---------------------------------------------------------------------------
--  B. Les tables qui tournent autour
--     (tout ce dont le nom évoque un objectif, un succès ou une réclamation)
-- ---------------------------------------------------------------------------
select c.relname as table_ou_vue,
       case c.relkind when 'r' then 'table' when 'v' then 'vue'
                      when 'm' then 'vue materialisee' else c.relkind::text end as genre,
       string_agg(a.attname || ' ' || format_type(a.atttypid, a.atttypmod),
                  ', ' order by a.attnum) as colonnes
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
 where n.nspname = 'public'
   and c.relkind in ('r', 'v', 'm')
   and (c.relname like '%objectif%' or c.relname like '%succes%'
        or c.relname like '%reclam%' or c.relname like '%quete%')
 group by c.relname, c.relkind
 order by c.relname;


-- ---------------------------------------------------------------------------
--  C. Le bug de Boule2Pain : à quoi ressemble une défense dans le journal
--
--  Il dit qu'une défense réussie n'est pas comptée quand la commune subit
--  deux attaques en même temps. Deux causes possibles, et ce relevé les
--  sépare :
--    — soit le journal n'écrit qu'une ligne par commune et non par siège,
--      et alors la seconde défense n'existe nulle part ;
--    — soit les deux lignes sont là et c'est le comptage de l'objectif qui
--      les confond.
--
--  On regarde les 40 dernières défenses, avec le nombre d'assaillants
--  distincts sur la même commune dans l'heure qui précède.
-- ---------------------------------------------------------------------------
select j.cree_le,
       j.type,
       j.commune_code,
       j.acteur_id,
       j.cible_id,
       (select count(distinct k.acteur_id)
          from journal k
         where k.commune_code = j.commune_code
           and k.type in ('attaque', 'defense', 'conquete')
           and k.cree_le between j.cree_le - interval '1 hour' and j.cree_le
       ) as assaillants_dans_l_heure
  from journal j
 where j.type = 'defense'
 order by j.cree_le desc
 limit 40;


-- ---------------------------------------------------------------------------
--  D. Les types de lignes que le journal connaît, et leur volume
--     Sert à savoir sur quoi un objectif peut compter.
-- ---------------------------------------------------------------------------
select type, count(*) as lignes,
       min(cree_le) as premiere, max(cree_le) as derniere
  from journal
 group by type
 order by count(*) desc;
