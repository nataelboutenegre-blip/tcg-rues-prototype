-- ===========================================================================
--  siege-suit-2-cibles.sql — suite de siege-suit-la-commune.sql (13 octobre)
--  « Proposer un échange » cachait les communes assiégées des autres joueurs
--  (echange-recherche.sql). Puisqu'on peut de nouveau les échanger, elles
--  reviennent dans la liste ; l'écran affichera « assiégée 2/3 » à côté.
--  Modifié à partir de la définition EN PRODUCTION. Rejouable.
--  Contrôle attendu : false
-- ===========================================================================
do $do$
declare d text; n integer;
  v_avant text := E'     and not commune_assiegee(p.commune_code)\n';
begin
  d := pg_get_functiondef('public.cibles_echange(text, text)'::regprocedure);
  n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
  if n = 0 then raise notice 'cibles_echange : deja fait'; return; end if;
  if n <> 1 then raise exception 'Repère trouvé % fois (attendu 1) : rien n''a été modifié', n; end if;
  execute replace(d, v_avant, '');
end $do$;

-- contrôle : false
select pg_get_functiondef('public.cibles_echange(text, text)'::regprocedure) like '%commune_assiegee%' as cache_encore_les_assiegees;
