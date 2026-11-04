-- ===========================================================================
--  TerraFront — s3-1 : préparer le serveur à la Suisse (4/11/2026).
--  Ne change RIEN pour la France aujourd'hui : à lancer quand on veut, avant
--  l'insertion des communes suisses (jour J de la saison 3, 22/11).
--
--  Le jeu disait « métropole = département de 2 caractères »
--  (length(departement) = 2). Un canton suisse fait aussi 2 lettres (GE, VD,
--  ZH…) : sans ce fichier, les communes suisses entreraient partout dès leur
--  insertion. Relu fonction par fonction (lectures lecture-suisse-fonctions-1
--  et -2 du 4/11) :
--
--  1. est_metropole(dep) : vrai pour 01 à 95, 2A, 2B ; faux pour l'outre-mer
--     (971…) et les cantons. est_canton(dep) : deux lettres.
--  2. La Suisse N'ENTRE PAS (décision de Nataël du 4/11 : pas encore dans les
--     mini-jeux ; et ce qui reste français) :
--     - cdj_jour_courant (Commune du jour)        - radar_tirer_communes (Radar)
--     - quetes_liste (quête « Complète un département », Terra)
--     - terra_signer_contrat (les contrats donnent une commune de métropole)
--     - totaux_paliers (tableau des raretés de France, « n° x / 302 »)
--     - rebasculer_paliers, rebasculer_paliers_s2 (outils de rareté France :
--       relancés, ils renuméroteraient les cartes suisses avec les françaises)
--  3. La Suisse ENTRE, sans rien changer (la longueur 2 la compte déjà) :
--     draw_commune et poids_tirage (paquets du Front), taux_actuels,
--     front_territoires (les cantons comptent comme des départements),
--     front_scores, saison_courante et prendre_mesure (le pot).
--  4. cdj_region : les cantons forment la région « Suisse » (avant : ils
--     seraient tombés dans « Outre-mer », y compris pour le bonus de région).
--  Plus ou moins et Rafale ne sont pas concernés (filtres côté jeu ou sur les
--  photos) : la Suisse n'y entrera pas sans le vouloir.
--  Modifiées en place à partir de leur définition en production : si un
--  texte attendu manque, rien ne change. Rejouable.
--  Contrôle attendu : true | true | 8 | 0
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

-- 1. les deux tests -----------------------------------------------------------
create or replace function public.est_metropole(p_dep text)
 returns boolean language sql immutable parallel safe
as $f$
  -- s3-1 : département de France métropolitaine (01 à 95, 2A, 2B)
  select coalesce(p_dep ~ '^([0-9]{2}|2[AB])$', false);
$f$;
create or replace function public.est_canton(p_dep text)
 returns boolean language sql immutable parallel safe
as $f$
  -- s3-1 : canton suisse (deux lettres)
  select coalesce(p_dep ~ '^[A-Z]{2}$', false);
$f$;
grant execute on function public.est_metropole(text) to anon, authenticated, service_role;
grant execute on function public.est_canton(text) to anon, authenticated, service_role;

-- 2. ce qui reste français ------------------------------------------------------
do $$
declare
  r record;
  d text;
begin
  for r in select * from (values
      ('public.cdj_jour_courant()',                                             'length(c.departement) = 2', 2),
      ('public.radar_tirer_communes()',                                         'length(c.departement) = 2', 1),
      ('public.quetes_liste(uuid)',                                             'length(c.departement) = 2', 1),
      ('public.terra_signer_contrat(text[], text)',                             'length(c.departement) = 2', 3),
      ('public.totaux_paliers()',                                               'length(c.departement) = 2', 1),
      ('public.rebasculer_paliers(integer, integer, integer, boolean)',          'length(c.departement) = 2', 1),
      ('public.rebasculer_paliers_s2(integer, integer, integer, integer, boolean)', 'length(c.departement) = 2', 1),
      ('public.rebasculer_paliers_s2(integer, integer, integer, integer, boolean)', 'length(departement) = 2',   1)
    ) as x(sig, avant, nb)
  loop
    d := pg_get_functiondef(r.sig::regprocedure);
    if position(r.avant in d) = 0 and position('est_metropole(' in d) > 0 then
      raise notice '% : déjà à jour', r.sig;
      continue;
    end if;
    d := pg_temp.remp(d, r.avant,
           case when r.avant like 'length(c.%' then 'est_metropole(c.departement)' else 'est_metropole(departement)' end,
           r.nb, r.sig);
    execute d;
  end loop;
end $$;

-- 4. la région « Suisse » --------------------------------------------------------
do $$
declare d text := pg_get_functiondef('public.cdj_region(text)'::regprocedure);
begin
  if position('Suisse' in d) > 0 then raise notice 'cdj_region : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    '    else ''Outre-mer''',
    '    when est_canton(p_dep) then ''Suisse''   -- s3-1
    else ''Outre-mer''',
    1, 'cdj_region');
  execute d;
end $$;

commit;

-- Contrôle : true | true | 8 | 0
select est_metropole('75') and est_metropole('2A') and est_metropole('01')
       and not est_metropole('GE') and not est_metropole('971') and not est_metropole(null)   as tests_ok,
       cdj_region('GE') = 'Suisse' and cdj_region('35') = 'Bretagne' and cdj_region('971') = 'Outre-mer'
                                                                                            as regions_ok,
       (select count(*) from pg_proc p
         where p.pronamespace = 'public'::regnamespace
           and p.proname in ('cdj_jour_courant', 'radar_tirer_communes', 'quetes_liste', 'terra_signer_contrat',
                             'totaux_paliers', 'rebasculer_paliers', 'rebasculer_paliers_s2', 'cdj_region')
           and (p.prosrc like '%est_metropole(%' or p.prosrc like '%est_canton(%'))::integer        as fonctions_a_jour,
       (select count(*) from communes c where length(c.departement) = 2 and not est_metropole(c.departement))::integer
                                                                                            as communes_hors_metropole_a_2;
