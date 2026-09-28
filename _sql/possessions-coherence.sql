-- ---------------------------------------------------------------------------
--  possessions-coherence.sql — lecture seule
--
--  Trois nombres censes etre egaux ont donne trois valeurs differentes :
--  les communes sans proprietaire impliquaient 5 166 possessions, la table
--  en compte 5 517, et historique avait 5 531 lignes encore ouvertes.
--
--  Tout est compte dans UNE SEULE requete, donc au meme instant : c'est
--  la condition pour que l'ecart soit reel et pas un artefact de deux
--  mesures prises a huit minutes d'intervalle.
--
--  Le bloc A est celui qui compte. Si « codes distincts » est inferieur a
--  « lignes », alors une meme commune appartient a plusieurs joueurs — et
--  dans un jeu a un proprietaire par commune, c'est un probleme qui passe
--  devant la cloture.
-- ---------------------------------------------------------------------------
with p as (
  select count(*)::int                        as lignes,
         count(distinct commune_code)::int    as codes_distincts,
         count(distinct joueur_id)::int       as joueurs
    from possessions
),
c as (
  select (select count(*) from communes)::int as total,
         (select count(*) from communes co
            left join possessions po on po.commune_code = co.code
           where po.commune_code is null)::int as libres
),
orphelines as (
  -- lignes de possessions dont le code ne correspond a aucune commune
  select count(*)::int as n
    from possessions po
    left join communes co on co.code = po.commune_code
   where co.code is null
),
doublons as (
  select coalesce(count(*), 0)::int as communes_en_double,
         coalesce(sum(n - 1), 0)::int as lignes_en_trop
    from (select commune_code, count(*) as n
            from possessions group by commune_code having count(*) > 1) t
),
exemples as (
  select coalesce(string_agg(l, chr(10) order by l), '(aucun)') as detail
    from (
      select po.commune_code || ' — ' || co.nom || ' (' || co.tier || ') detenue par '
             || string_agg(coalesce(j.pseudo, '?'), ', ' order by j.pseudo) as l
        from possessions po
        left join communes co on co.code = po.commune_code
        left join joueurs j on j.id = po.joueur_id
       where po.commune_code in (select commune_code from possessions
                                  group by commune_code having count(*) > 1)
       group by po.commune_code, co.nom, co.tier
       limit 8
    ) t
),
contrainte as (
  select coalesce(string_agg(
           con.conname || ' (' || con.contype::text || ') sur ('
           || (select string_agg(a.attname, ', ' order by k.ord)
                 from unnest(con.conkey) with ordinality k(attnum, ord)
                 join pg_attribute a on a.attrelid = con.conrelid
                                    and a.attnum = k.attnum)
           || ')', chr(10) order by con.conname), '(aucune)') as detail
    from pg_constraint con
   where con.conrelid = 'public.possessions'::regclass
     and con.contype in ('p', 'u')
),
idx as (
  select coalesce(string_agg(indexdef, chr(10) order by indexname), '(aucun)') as detail
    from pg_indexes
   where schemaname = 'public' and tablename = 'possessions'
),
h as (
  select count(*)::int as ouvertes
    from historique where released_at is null
)

select 'A. possessions' as quoi,
       lignes || ' lignes, ' || codes_distincts || ' codes distincts, '
       || joueurs || ' joueurs'
       || case when lignes = codes_distincts
               then '   -> aucune commune detenue en double'
               else '   -> ECART DE ' || (lignes - codes_distincts)
                    || ' : des communes ont plusieurs proprietaires' end as valeur
  from p
union all
select 'B. communes',
       total || ' au total, ' || libres || ' libres, donc ' || (total - libres)
       || ' avec un proprietaire'
  from c
union all
select 'C. les trois nombres cote a cote',
       'possessions ' || (select lignes from p)
       || '  |  communes avec proprietaire ' || (select total - libres from c)
       || '  |  historique encore ouvert ' || (select ouvertes from h)
union all
select 'D. lignes orphelines (code inconnu de communes)', n::text from orphelines
union all
select 'E. communes en double',
       communes_en_double || ' communes concernees, ' || lignes_en_trop
       || ' lignes en trop'
  from doublons
union all
select 'F. exemples de doublons', detail from exemples
union all
select 'G. contraintes d''unicite sur possessions', detail from contrainte
union all
select 'H. index sur possessions', detail from idx
order by 1;
