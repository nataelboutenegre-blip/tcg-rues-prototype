-- ===========================================================================
--  TerraFront — Outre-mer v1, FONDATION : séparation métropole / outre-mer
--  (27 octobre 2026)
--
--  Prépare la base à recevoir les 129 communes DOM SANS rien changer tant
--  qu'aucune n'est chargée (les filtres sont des no-op aujourd'hui : il
--  n'existe aucune commune de département `^9[78]`). À passer AVANT le
--  chargement des DOM.
--
--  Convention : métropole ⟺ departement longueur 2 (01-95 + 2A/2B) ;
--  outre-mer ⟺ longueur 3 (971-978). Idiome déjà utilisé par
--  radar_tirer_communes et cdj_jour_courant.
--
--  Modifié À PARTIR DE LA DÉFINITION EN BASE (pas du dépôt), chaque
--  remplacement contrôlé à EXACTEMENT 1 occurrence. Idempotent (re-jouable :
--  chaque fonction est sautée si le filtre y est déjà). Finit par un contrôle.
--
--  CE QUI N'EST PAS TOUCHÉ, ET POURQUOI :
--   - cloturer_saison : son seul usage de `communes` (terra_amorce) fait
--     count ... group by departement PUIS joint possessions ; les DOM, codes
--     départementaux disjoints et jamais possédés en v1, n'y matchent rien.
--     Prouvé au banc : chiffres métropole identiques avec/sans DOM. INCHANGÉE.
--   - terra_ouvrir_paquet : on VEUT les DOM dans le pot (~1,5 %). INCHANGÉE.
--   - objectifs, profil_joueur : passent par possessions (jamais de DOM en v1).
--   - radar/cdj/pom : déjà gardés (length=2, photo not null).
--
--  CHOIX PRODUIT v1 (validés) :
--   - terra_signer_contrat : contrats = métropole seule (DOM exclus).
--   - score/collection Terra : les DOM COMPTENT (vraies cartes) -> rien à
--     filtrer côté terra_classement / collection.
-- ===========================================================================
create or replace function pg_temp.remp(p_def text, p_avant text, p_apres text, p_etq text)
returns text language plpgsql as $$
declare n int;
begin
  n := (length(p_def) - length(replace(p_def, p_avant, ''))) / nullif(length(p_avant), 0);
  if n is distinct from 1 then
    raise exception 'Repère « % » trouvé % fois (attendu 1) : rien changé', p_etq, n;
  end if;
  return replace(p_def, p_avant, p_apres);
end $$;

do $do$
declare d text;
begin
  -- 1. saison_courante : total communes (global) -> communes libres -> rebours
  d := pg_get_functiondef('public.saison_courante()'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'from communes c;',
      'from communes c where length(c.departement) = 2;',
      'saison_courante');
    execute d;
  end if;

  -- 2. prendre_mesure : total communes (stat quotidienne « libres »)
  d := pg_get_functiondef('public.prendre_mesure()'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'from communes;',
      'from communes where length(departement) = 2;',
      'prendre_mesure');
    execute d;
  end if;

  -- 3. totaux_paliers : affichage « /34739, /302, /1013 » par tier
  d := pg_get_functiondef('public.totaux_paliers()'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'group by c.tier;',
      'where length(c.departement) = 2 group by c.tier;',
      'totaux_paliers');
    execute d;
  end if;

  -- 4. taux_actuels : communes libres par tier (Front)
  d := pg_get_functiondef('public.taux_actuels()'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'where po.commune_code is null',
      'where po.commune_code is null and length(c.departement) = 2',
      'taux_actuels');
    execute d;
  end if;

  -- 5. front_territoires : tailles de départements (score Front)
  d := pg_get_functiondef('public.front_territoires()'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'from communes c group by c.departement',
      'from communes c where length(c.departement) = 2 group by c.departement',
      'front_territoires');
    execute d;
  end if;

  -- 6. quetes_liste : quête « compléter un département » (métropole en v1)
  d := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
$x$and t.exemplaires > 0
     group by c.departement$x$,
$x$and t.exemplaires > 0
     where length(c.departement) = 2
     group by c.departement$x$,
      'quetes_liste');
    execute d;
  end if;

  -- 7. rebasculer_paliers (S1) : ne pas reclasser les DOM (rareté figée)
  d := pg_get_functiondef('public.rebasculer_paliers(integer,integer,integer,boolean)'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
$x$'commun' end as apres
    from communes c;$x$,
$x$'commun' end as apres
    from communes c where length(c.departement) = 2;$x$,
      'rebasculer_paliers');
    execute d;
  end if;

  -- 8. rebasculer_paliers_s2 : idem + partition rang/palier par zone
  d := pg_get_functiondef('public.rebasculer_paliers_s2(integer,integer,integer,integer,boolean)'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
$x$'commun' end as apres
    from communes c;$x$,
$x$'commun' end as apres
    from communes c where length(c.departement) = 2;$x$,
      'rebasculer_paliers_s2 (bascule2)');
    d := pg_temp.remp(d,
$x$from communes)
  update communes c set rang$x$,
$x$from communes where length(departement) = 2)
  update communes c set rang$x$,
      'rebasculer_paliers_s2 (rangs)');
    execute d;
  end if;

  -- 9. terra_signer_contrat : contrats métropole seule (DOM exclus en v1)
  d := pg_get_functiondef('public.terra_signer_contrat(text[],text)'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
$x$where c.tier = p_vers
     and not exists$x$,
$x$where c.tier = p_vers and length(c.departement) = 2
     and not exists$x$,
      'terra_signer_contrat (tirage principal)');
    d := pg_temp.remp(d,
      'from communes c where c.tier = p_vers order by random() limit 1;',
      'from communes c where c.tier = p_vers and length(c.departement) = 2 order by random() limit 1;',
      'terra_signer_contrat (tirage secours)');
    d := pg_temp.remp(d,
      'where c.tier = p_vers and c.code <> v_code',
      'where c.tier = p_vers and length(c.departement) = 2 and c.code <> v_code',
      'terra_signer_contrat (decor)');
    execute d;
  end if;
end $do$;

-- Contrôle : chacune des 9 fonctions contient maintenant le filtre métropole.
select
  pg_get_functiondef('public.saison_courante()'::regprocedure)        ~ 'length\((c\.)?departement\) = 2' as saison_courante,
  pg_get_functiondef('public.prendre_mesure()'::regprocedure)         ~ 'length\((c\.)?departement\) = 2' as prendre_mesure,
  pg_get_functiondef('public.totaux_paliers()'::regprocedure)         ~ 'length\((c\.)?departement\) = 2' as totaux_paliers,
  pg_get_functiondef('public.taux_actuels()'::regprocedure)           ~ 'length\((c\.)?departement\) = 2' as taux_actuels,
  pg_get_functiondef('public.front_territoires()'::regprocedure)      ~ 'length\((c\.)?departement\) = 2' as front_territoires,
  pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)       ~ 'length\((c\.)?departement\) = 2' as quetes_liste,
  pg_get_functiondef('public.rebasculer_paliers(integer,integer,integer,boolean)'::regprocedure) ~ 'length\((c\.)?departement\) = 2' as rebasculer_paliers,
  (select count(*) from regexp_matches(pg_get_functiondef('public.rebasculer_paliers_s2(integer,integer,integer,integer,boolean)'::regprocedure), 'length\((c\.)?departement\) = 2', 'g')) = 2 as rebasculer_s2_2x,
  (select count(*) from regexp_matches(pg_get_functiondef('public.terra_signer_contrat(text[],text)'::regprocedure), 'length\((c\.)?departement\) = 2', 'g')) = 3 as terra_contrat_3x;
