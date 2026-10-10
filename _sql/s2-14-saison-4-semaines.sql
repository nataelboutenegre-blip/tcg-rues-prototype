-- ===========================================================================
--  TerraFront — saison 2 : une saison de Front dure 4 semaines
--  (décision de Nataël, 10 octobre 2026)
--
--  Jusqu'ici, le compte à rebours de fin de saison s'armait quand il ne
--  restait que 3 000 communes libres. En saison 2, la saison a une DATE DE
--  FIN fixée à l'avance (saisons.fin_prevue) : le compte à rebours s'arme
--  tout seul 5 jours avant (saisons.jours_rebours), comme avant.
--
--  saison_courante() est modifiée à partir de sa définition en production :
--   - si fin_prevue est renseignée : compte à rebours à fin_prevue − 5 jours ;
--   - sinon : la règle des 3 000 communes libres, inchangée (saison 1).
--  SANS EFFET EN SAISON 1 : la saison 1 n'a pas de fin_prevue tant que son
--  compte à rebours n'est pas armé. La date de la saison 2 est posée le jour
--  J par jour-j-4-ouverture.sql.
--
--  Ce fichier n'appelle PAS saison_courante() (qui arme le compte à rebours).
--  Rejouable. Finit par un contrôle.
-- ===========================================================================
do $g$
declare
  v_def text;
  v_avant text := $a$  if v_etat = 'en_cours' and v_libres <= v_seuil then$a$;
  v_apres text := $a$  -- saison 2 : date de fin fixee a l'avance, compte a rebours N jours avant
  if v_etat = 'en_cours' and v_fin is not null
     and now() >= v_fin - (v_jours || ' days')::interval then
    update saisons sa
       set etat = 'compte_a_rebours'
     where sa.id = v_id and sa.etat = 'en_cours'
    returning sa.etat into v_etat;
  elsif v_etat = 'en_cours' and v_fin is null and v_libres <= v_seuil then$a$;
  n integer;
begin
  v_def := pg_get_functiondef('public.saison_courante()'::regprocedure);
  if position('date de fin fixee' in v_def) > 0 then
    raise notice 'saison_courante : deja en place';
    return;
  end if;
  n := (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise exception 'saison_courante : texte a remplacer present % fois au lieu de 1. Rien n''a ete modifie.', n;
  end if;
  execute replace(v_def, v_avant, v_apres);
end
$g$;

-- Contrôle (sans appeler saison_courante) ---------------------------------------------------
select position('date de fin fixee' in pg_get_functiondef('public.saison_courante()'::regprocedure)) > 0 as duree_fixe_en_place,
       (select etat from public.saisons where etat <> 'terminee' order by debut desc limit 1) as saison_en_cours_etat;
