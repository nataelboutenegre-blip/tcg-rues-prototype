-- ===========================================================================
--  s2-25-dos-visible.sql — le dos de carte équipé d'un joueur, visible par
--  les autres (quand on retourne une carte de sa vitrine). Rejouable.
--  Ne renvoie que l'identifiant du dos (null = le dos d'origine).
--  Contrôle attendu : true | false
-- ===========================================================================

begin;

create or replace function public.dos_equipe(p_joueur uuid)
 returns text
 language plpgsql
 stable security definer
 set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return (select r.dos from boutique_reglages r where r.joueur_id = p_joueur);
end;
$f$;

revoke all on function public.dos_equipe(uuid) from public, anon;
grant execute on function public.dos_equipe(uuid) to authenticated;

commit;

-- contrôle : true | false
select has_function_privilege('authenticated', 'public.dos_equipe(uuid)', 'execute') as lecture_ok,
       has_function_privilege('anon', 'public.dos_equipe(uuid)', 'execute')          as anon_doit_etre_false;
