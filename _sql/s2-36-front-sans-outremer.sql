-- ===========================================================================
--  TerraFront — Outre-mer v1 : les paquets du FRONT ne tirent jamais un DOM
--  (27 octobre 2026)
--
--  Trouvé en préparant le chargement des DOM : en saison 2, le Front a
--  toujours ses paquets (tirer_carte -> draw_commune), qui piochent une
--  commune LIBRE au hasard. Une commune DOM n'appartient à personne, donc
--  elle est « libre » : sans ce correctif, elle pourrait tomber dans le Front,
--  alors qu'en v1 les DOM sont des cartes Terra seulement.
--
--  Vérifié dans le dépôt : draw_commune est la SEULE porte d'entrée vers
--  possessions encore ouverte (signer_contrat est fermée depuis s2-32 ;
--  attaquer refuse une commune qui n'appartient à personne ; les échanges et
--  transferts ne déplacent que des communes déjà possédées).
--
--  Deux fonctions, filtrées sur la métropole (length(departement) = 2) :
--   - draw_commune : la commune tirée ;
--   - poids_tirage : le stock par rareté qui fixe les chances (sinon les DOM
--     libres gonfleraient les chances de chaque palier).
--  draw_commune est modifiée à partir de sa définition EN BASE (export de
--  l'audit du 26/10) ; poids_tirage n'existe que dans legendaire-poids.sql.
--  Chaque remplacement contrôlé à 1 occurrence. Une seule transaction :
--  tout passe ou rien. Rejouable. Sans effet tant qu'aucun DOM n'est en base.
--
--  À passer AVANT s2-35-charger-outremer.sql.
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
  -- 1. draw_commune : la commune tirée pour un paquet Front
  d := pg_get_functiondef('public.draw_commune(text)'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'where c.tier = v_tier and p.commune_code is null',
      'where c.tier = v_tier and p.commune_code is null and length(c.departement) = 2',
      'draw_commune');
    execute d;
  end if;

  -- 2. poids_tirage : le stock libre par rareté (chances du paquet Front)
  d := pg_get_functiondef('public.poids_tirage()'::regprocedure);
  if d !~ 'length\((c\.)?departement\) = 2' then
    d := pg_temp.remp(d,
      'where p.commune_code is null;',
      'where p.commune_code is null and length(c.departement) = 2;',
      'poids_tirage');
    execute d;
  end if;
end $do$;

-- Contrôle : les deux doivent être true.
select
  pg_get_functiondef('public.draw_commune(text)'::regprocedure) ~ 'length\((c\.)?departement\) = 2' as draw_commune,
  pg_get_functiondef('public.poids_tirage()'::regprocedure)     ~ 'length\((c\.)?departement\) = 2' as poids_tirage;
