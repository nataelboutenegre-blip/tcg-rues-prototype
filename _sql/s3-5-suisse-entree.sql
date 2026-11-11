-- ===========================================================================
--  TerraFront — s3-5 : la Suisse entre dans le jeu (JOUR J de la saison 3)
--
--  ⚠️  À LANCER SEULEMENT LE JOUR J, APRÈS LA CLÔTURE DE LA SAISON 2 et quand
--  le jeu est prêt à afficher la Suisse. Dès ce fichier, les 2 110 communes
--  suisses sortent des paquets du Front, comptent dans le pot et la réserve
--  d'accueil, et les cantons comptent comme des départements. Une fois que des
--  joueurs en ont tiré, revenir en arrière est compliqué : le répéter d'abord.
--
--  Prérequis (vérifiés : sinon rien ne se passe) :
--    - s3-1, s3-2 et s3-3 passés (lancés le 4/11) ;
--    - la saison 2 close (saisons.id = 'saison-2', état « terminee ») ;
--    - les 4 parties de la réserve passées (s3-4a à s3-4d : 2 110 communes,
--      26 cantons).
--
--  Ce que fait le fichier, en une seule transaction (tout passe ou rien) :
--    1. copie les communes de la réserve dans communes (code CH…, nom, canton,
--       population, position, rareté) ;
--    2. numérote les cartes suisses dans leur rareté, entre elles, comme
--       l'outre-mer : « n° 1 / 27 » pour Zurich, la plus peuplée des 27
--       légendaires. Les numéros de France ne bougent pas (« n° x / 302 »).
--  Photos, faits et gentilés : vides pour l'instant (photos plus tard).
--  Rejouable : une commune déjà entrée n'est pas recopiée.
--
--  Contrôle attendu :
--    2110 | legendaire 27, epique 218, rare 652, peucommun 953, commun 260
--         | 0 | 0 | true | Zurich : legendaire n° 1 / 27
-- ===========================================================================
begin;

do $$
declare
  v_n integer;
  v_c integer;
begin
  -- s3-1 : est_canton et les 8 fonctions qui restent françaises
  if to_regprocedure('public.est_canton(text)') is null then
    raise exception 's3-1 n''est pas passé (est_canton manque) : rien n''a changé';
  end if;
  select count(*) into v_n from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.proname in ('cdj_jour_courant', 'radar_tirer_communes', 'quetes_liste', 'terra_signer_contrat',
                       'totaux_paliers', 'rebasculer_paliers', 'rebasculer_paliers_s2', 'cdj_region')
     and (p.prosrc like '%est_metropole(%' or p.prosrc like '%est_canton(%');
  if v_n < 8 then
    raise exception 's3-1 n''est pas complet (% fonctions à jour sur 8) : rien n''a changé', v_n;
  end if;

  -- s3-2 : bonus des petits cantons au prorata
  if position('s3-2' in pg_get_functiondef('public.front_territoires()'::regprocedure)) = 0 then
    raise exception 's3-2 n''est pas passé (front_territoires) : rien n''a changé';
  end if;

  -- s3-3 : Terra, Ta boutique, Plus ou moins et contrats hors de la Suisse
  select count(*) into v_n from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.proname in ('terra_ouvrir_paquet', 'boutique_ouvrir_paquet', 'bt_tirer', 'pom_generer',
                       'contrat_defile', 'signer_contrat')
     and p.prosrc like '%s3-3%';
  if v_n < 6 then
    raise exception 's3-3 n''est pas passé (% fonctions à jour sur 6) : rien n''a changé', v_n;
  end if;

  -- la saison 2 doit être close : la clôture d'abord, la Suisse ensuite
  if not exists (select 1 from public.saisons where id = 'saison-2' and etat = 'terminee') then
    raise exception 'La saison 2 n''est pas close : lance d''abord la clôture, puis ce fichier. Rien n''a changé';
  end if;

  -- la réserve doit être complète
  if to_regclass('public.suisse_communes_attente') is null then
    raise exception 'La réserve suisse est vide : lance d''abord s3-4a, s3-4b, s3-4c et s3-4d. Rien n''a changé';
  end if;
  select count(*), count(distinct departement) into v_n, v_c from public.suisse_communes_attente;
  if v_n <> 2110 or v_c <> 26 then
    raise exception 'Réserve incomplète : % communes dans % cantons (il en faut 2110 dans 26) — relance les parties s3-4a à s3-4d. Rien n''a changé', v_n, v_c;
  end if;

  -- aucun code suisse déjà pris par autre chose
  select count(*) into v_n
    from public.communes c join public.suisse_communes_attente a using (code)
   where c.departement is distinct from a.departement;
  if v_n > 0 then
    raise exception '% code(s) CH déjà présents avec un autre canton : rien n''a changé', v_n;
  end if;
end $$;

-- 1. les communes entrent, avec leur numéro dans leur rareté, entre communes suisses
insert into public.communes (code, nom, departement, tier, population, rang, palier_total, latitude, longitude)
select code, nom, departement, tier, population,
       row_number() over (partition by tier order by population desc nulls last, code),
       count(*) over (partition by tier),
       latitude, longitude
  from public.suisse_communes_attente
on conflict (code) do nothing;

-- 2. les numéros encore une fois, sur ce qui est en base (utile si le fichier est rejoué)
with r as (
  select code,
         row_number() over (partition by tier order by population desc nulls last, code) as rg,
         count(*) over (partition by tier) as total
    from public.communes
   where est_canton(departement))
update public.communes c set rang = r.rg, palier_total = r.total
  from r
 where r.code = c.code
   and (c.rang is distinct from r.rg or c.palier_total is distinct from r.total);

-- 3. (ajout du 11/11) le catalogue de la carte (jeu et carte en direct) : sans ça, les communes suisses
--    n'apparaissent sur les cartes qu'après le passage de 4 h 17 (cron carte-catalogue)
select public.carte_catalogue_refaire();

commit;

-- Contrôle :
--   2110 | legendaire 27, epique 218, rare 652, peucommun 953, commun 260 | 0 | 0 | true | Zurich : legendaire n° 1 / 27
-- (melanges = un code CH rangé en France, ou l'inverse ; france_a_part = le tableau des raretés de France
--  ignore toujours la Suisse)
select (select count(*) from public.communes where est_canton(departement))::integer          as communes_suisses,
       (select string_agg(tier || ' ' || n, ', '
                          order by array_position(array['legendaire','epique','rare','peucommun','commun'], tier))
          from (select tier, count(*) as n from public.communes
                 where est_canton(departement) group by tier) t)                                as raretes,
       (select count(*) from public.communes
         where est_canton(departement)
           and (rang is null or palier_total is null or rang > palier_total))::integer          as numeros_faux,
       ((select count(*) from public.communes where est_metropole(departement) and code like 'CH%')
      + (select count(*) from public.communes where est_canton(departement) and code not like 'CH%'))::integer
                                                                                                as melanges,
       (select sum(total) from public.totaux_paliers())
         = (select count(*) from public.communes where est_metropole(departement))              as france_a_part,
       (select nom || ' : ' || tier || ' n° ' || rang || ' / ' || palier_total
          from public.communes where code = 'CH261')                                            as zurich;

-- Après vérification du jeu (quelques jours plus tard), la réserve peut partir :
--   drop table public.suisse_communes_attente;
