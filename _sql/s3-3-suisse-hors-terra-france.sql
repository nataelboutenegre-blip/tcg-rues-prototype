-- ===========================================================================
--  TerraFront — s3-3 : les tirages de Terra et de Plus ou moins restent hors
--  de la Suisse (4/11/2026). Ne change RIEN aujourd'hui : à lancer avant
--  l'insertion des communes suisses (jour J de la saison 3).
--
--  Lectures 4 et 5 du 4/11 : 7 fonctions tirent des communes au hasard dans
--  toute la table, sans filtre de pays ; la Suisse y tomberait dès son
--  insertion. Décisions de Nataël : Terra = un paquet par pays (le paquet
--  suisse viendra à part), pas de Suisse dans les mini-jeux pour l'instant.
--  Chacune garde exactement ce qu'elle tire aujourd'hui (France et
--  outre-mer), seuls les cantons sont écartés (not est_canton, de s3-1) :
--   - terra_ouvrir_paquet   : le paquet Terra gratuit ou acheté ;
--   - boutique_ouvrir_paquet: le paquet garanti (la rare et les 4 autres) et
--                             le paquet d'un département (un canton est refusé :
--                             « Choisis un département ») ;
--   - bt_tirer              : « Ta boutique » (communes qui te manquent) ;
--   - pom_generer           : les duels de Plus ou moins ;
--   - contrat_defile        : les noms qui défilent pendant un contrat ;
--   - signer_contrat        : l'ancien contrat de la saison 1.
--  Pas touchées : boutique_ouvrir_collection (tire dans les albums, tous
--  français), les recherches par nom (bombe, échanges, suggestions : la
--  Suisse doit y apparaître), attaquer / defendre / journal (hasard des
--  combats). Rafale vérifie les noms dans le jeu (liste française).
--  Modifiées en place à partir de leur définition en production : si un
--  texte attendu manque, rien ne change. Rejouable.
--  Contrôle attendu : 6 | 0
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

create temporary table s33(ordre int, sig text, avant text, apres text, nb int) on commit drop;
insert into s33 values
  (1, 'public.terra_ouvrir_paquet(boolean)',
      'where c.code <> all((select halloween_codes_actifs())::text[]) order by random() limit 5',
      'where c.code <> all((select halloween_codes_actifs())::text[]) and not est_canton(c.departement) /* s3-3 */ order by random() limit 5', 1),
  (2, 'public.boutique_ouvrir_paquet(text, text)',
      'or not exists(select 1 from communes c where c.departement = p_departement) then',
      'or not exists(select 1 from communes c where c.departement = p_departement)
       or est_canton(p_departement) then   -- s3-3 : pas encore de paquet de canton', 1),
  (3, 'public.boutique_ouvrir_paquet(text, text)',
      'where a.id = ''paquet-garanti'' and c2.tier in (''rare'', ''epique'', ''legendaire'')',
      'where a.id = ''paquet-garanti'' and c2.tier in (''rare'', ''epique'', ''legendaire'') and not est_canton(c2.departement)', 1),
  (4, 'public.boutique_ouvrir_paquet(text, text)',
      '(select c.code from (select c3.code from communes c3
                            where a.id = ''paquet-garanti''',
      '(select c.code from (select c3.code from communes c3
                            where a.id = ''paquet-garanti'' and not est_canton(c3.departement)', 1),
  (5, 'public.bt_tirer(uuid, text)',
      '       where c.tier = v_t
',
      '       where c.tier = v_t and not est_canton(c.departement)   -- s3-3
', 1),
  (6, 'public.pom_generer()',
      'c.photo is not null',
      'c.photo is not null and not est_canton(c.departement)', 3),
  (7, 'public.pom_generer()',
      'where x.photo is not null and y.photo is not null',
      'where x.photo is not null and y.photo is not null and not est_canton(x.departement) and not est_canton(y.departement) /* s3-3 */', 1),
  (8, 'public.contrat_defile(text, integer)',
      '   where c.tier = p_tier
',
      '   where c.tier = p_tier and not est_canton(c.departement)   -- s3-3
', 1),
  (9, 'public.signer_contrat(text[], text)',
      '     where c.tier = p_vers and p.commune_code is null
',
      '     where c.tier = p_vers and p.commune_code is null and not est_canton(c.departement)   -- s3-3
', 1);

do $$
declare
  s text;
  r record;
  d text;
begin
  for s in select distinct sig from s33 loop
    d := pg_get_functiondef(s::regprocedure);
    if position('s3-3' in d) > 0 then raise notice '% : déjà à jour', s; continue; end if;
    for r in select * from s33 where sig = s order by ordre loop
      d := pg_temp.remp(d, r.avant, r.apres, r.nb, s);
    end loop;
    execute d;
  end loop;
end $$;

commit;

-- Contrôle : 6 | 0
select (select count(*) from pg_proc p
         where p.pronamespace = 'public'::regnamespace
           and p.proname in ('terra_ouvrir_paquet', 'boutique_ouvrir_paquet', 'bt_tirer', 'pom_generer',
                             'contrat_defile', 'signer_contrat')
           and p.prosrc like '%s3-3%')::integer                                                   as fonctions_a_jour,
       (select count(*) from communes c where est_canton(c.departement))::integer                as communes_suisses;
