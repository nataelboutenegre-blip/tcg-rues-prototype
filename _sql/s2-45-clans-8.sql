-- ===========================================================================
--  s2-45 — Clans : 8 membres au plus (au lieu de 6). Décision de Nataël,
--  27 octobre 2026. Même méthode que clans-ouverture : clan_inviter et
--  clan_repondre sont modifiées à partir de leur définition en production
--  (texte attendu une fois par fonction, sinon rien ne change).
--  Rejouable. Contrôle attendu : true | true.
-- ===========================================================================
begin;
do $$
declare f text; d text;
  avant text := $a$>= 6 then raise exception 'Le clan est complet (6 membres)'$a$;
  apres text := $a$>= 8 then raise exception 'Le clan est complet (8 membres)'$a$;
begin
  foreach f in array array['public.clan_inviter(text)', 'public.clan_repondre(uuid,boolean)'] loop
    d := pg_get_functiondef(f::regprocedure);
    if position(apres in d) > 0 then raise notice '% : déjà à 8', f; continue; end if;
    if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then
      raise exception '% : limite attendue introuvable, rien n''a changé', f;
    end if;
    execute replace(d, avant, apres);
  end loop;
end $$;
commit;

select position('(8 membres)' in pg_get_functiondef('public.clan_inviter(text)'::regprocedure)) > 0 as inviter_8,
       position('(8 membres)' in pg_get_functiondef('public.clan_repondre(uuid,boolean)'::regprocedure)) > 0 as repondre_8;
