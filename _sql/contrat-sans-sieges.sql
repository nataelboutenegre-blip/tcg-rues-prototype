-- ===========================================================================
--  TerraFront — contrat : les communes assiégées ne sont plus proposées
--  (23 octobre 2026)
--
--  Depuis siege-contrat-bloque.sql, signer_contrat refuse un lot qui contient
--  une commune assiégée (au moins une victoire d'affilée de l'attaquant dans
--  les dernières 24 h). Mais contrat_candidates continuait de les proposer :
--  le joueur composait un lot impossible et recevait une erreur, et un
--  contrat en lot (×5, ×10) s'arrêtait en route.
--
--  contrat_candidates (Front) écarte maintenant ces communes. Elles reviennent
--  dans la liste dès que le siège retombe. Terra n'a pas de siège : inchangé.
--
--  Modifiée sur place (une ligne insérée avant « order by ») ; si ce repère
--  n'est pas trouvé exactement une fois, rien n'est modifié.
--  Rejouable. Contrôle attendu : true
-- ===========================================================================

do $do$
declare
  d text := pg_get_functiondef('public.contrat_candidates(text)'::regprocedure);
  v_avant text := E'   order by c.population asc nulls first, p.commune_code;';
  n integer;
begin
  if position('commune_assiegee' in d) > 0 then
    raise notice 'contrat_candidates : déjà fait';
    return;
  end if;
  n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise exception 'contrat_candidates : repère trouvé % fois (attendu 1). Rien n''a été modifié. Envoie-moi ce message.', n;
  end if;
  execute replace(d, v_avant,
    E'     -- assiégée : signer_contrat la refuserait\n'
 || E'     and not commune_assiegee(p.commune_code)\n'
 || v_avant);
  raise notice 'contrat_candidates : modifiée';
end
$do$;

-- contrôle : true
select position('commune_assiegee' in pg_get_functiondef('public.contrat_candidates(text)'::regprocedure)) > 0 as sieges_ecartes;
