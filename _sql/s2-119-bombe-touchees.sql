-- s2-119 (8/11/2026) : pour l'animation de l'impact (patch377), la bombe garde
-- les communes dont elle a soufflé la garnison.
--   - colonne bombes.touchees (jsonb : [{c: code, j: joueur}]) remplie par bombe_lacher ;
--   - bombe_touchees(p_id) : la liste pour le jeu, avec « à moi » au lieu de l'id du joueur.
-- Les 3 bombes déjà lâchées n'ont pas cette liste : leur animation se joue sans garnisons.

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

begin;

alter table public.bombes add column if not exists touchees jsonb;

do $$
declare d text;
begin
  d := pg_get_functiondef('public.bombe_lacher(text)'::regprocedure);
  d := pg_temp.remp(d,
$a$    returning g.joueur_id, g.energie)
  insert into bombes_degats(bombe_id, joueur_id, garnisons, energie)
  select v_id, d.joueur_id, count(*), coalesce(sum(d.energie), 0) from d group by d.joueur_id;$a$,
$a$    returning g.joueur_id, g.energie, g.commune_code),
  ins as (
    insert into bombes_degats(bombe_id, joueur_id, garnisons, energie)
    select v_id, d.joueur_id, count(*), coalesce(sum(d.energie), 0) from d group by d.joueur_id
    returning 1)
  update bombes set touchees = (select jsonb_agg(jsonb_build_object('c', d.commune_code, 'j', d.joueur_id)) from d)   -- s2-119 : pour l'animation
   where id = v_id;$a$, 1, 'bombe_lacher');
  execute d;
end $$;

create or replace function public.bombe_touchees(p_id bigint)
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  -- s2-119 : les garnisons soufflées par une bombe, pour son animation
  select coalesce((select jsonb_agg(jsonb_build_object('c', e ->> 'c', 'moi', (e ->> 'j')::uuid = auth.uid()))
                     from bombes b, jsonb_array_elements(coalesce(b.touchees, '[]'::jsonb)) e
                    where b.id = p_id and auth.uid() is not null), '[]'::jsonb);
$f$;
revoke execute on function public.bombe_touchees(bigint) from public, anon;
grant execute on function public.bombe_touchees(bigint) to authenticated;

commit;

-- Contrôle : t | t | t
select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'bombes' and column_name = 'touchees') as colonne_ok,
       position('s2-119' in pg_get_functiondef('public.bombe_lacher(text)'::regprocedure)) > 0 as lacher_ok,
       has_function_privilege('authenticated', 'public.bombe_touchees(bigint)', 'execute')
         and not has_function_privilege('anon', 'public.bombe_touchees(bigint)', 'execute') as droits_ok;
