-- siege-contrat-bloque.sql — 5e porte : une commune assiégée ne peut plus
-- partir dans un contrat (à passer après siege-vente-bloquee.sql). Rejouable.
-- Contrôle attendu : true

begin;

create or replace function pg_temp.remplacer(p_def text, p_avant text, p_apres text, p_etiquette text)
returns text language plpgsql as $$
declare n integer;
begin
  n := (length(p_def) - length(replace(p_def, p_avant, ''))) / length(p_avant);
  if n <> 1 then
    raise exception 'Repère « % » trouvé % fois (attendu 1) : rien n''a été modifié', p_etiquette, n;
  end if;
  return replace(p_def, p_avant, p_apres);
end $$;

do $do$
declare d text := pg_get_functiondef('public.signer_contrat(text[], text)'::regprocedure);
begin
  if d like '%commune_assiegee%' then raise notice 'signer_contrat : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, E'  -- --- le tirage, avant toute suppression',
    E'  if exists (select 1 from unnest(p_codes) x where commune_assiegee(x)) then\n'
 || E'    raise exception ''Une des communes est assiegee : retire-la du contrat tant que le siege dure'';\n'
 || E'  end if;\n\n  -- --- le tirage, avant toute suppression', 'signer_contrat');
  execute d;
end $do$;

commit;

-- contrôle : true
select pg_get_functiondef('public.signer_contrat(text[], text)'::regprocedure) like '%commune_assiegee%' as contrat_protege;
