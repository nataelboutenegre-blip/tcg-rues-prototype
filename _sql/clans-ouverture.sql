-- ===========================================================================
--  TerraFront — ouverture des clans (25 octobre 2026)
--  Décision de Nataël : 6 membres au plus (« comme l'Hexagone »), au lieu de 5.
--  1. clan_inviter et clan_repondre : la limite passe à 6, à partir de leur
--     définition en base (texte attendu une fois par fonction, sinon rien ne
--     change).
--  2. config_jeu 'clans_ouverts' = true : les fonctions des clans s'ouvrent.
--  Rejouable. Contrôle attendu : true | true | true.
-- ===========================================================================
begin;
do $$
declare f text; d text;
  avant text := $a$>= 5 then raise exception 'Le clan est complet (5 membres)'$a$;
  apres text := $a$>= 6 then raise exception 'Le clan est complet (6 membres)'$a$;
begin
  foreach f in array array['public.clan_inviter(text)', 'public.clan_repondre(uuid,boolean)'] loop
    d := pg_get_functiondef(f::regprocedure);
    if position(apres in d) > 0 then raise notice '% : déjà à 6', f; continue; end if;
    if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then
      raise exception '% : limite attendue introuvable, rien n''a changé', f;
    end if;
    execute replace(d, avant, apres);
  end loop;
end $$;

insert into public.config_jeu (cle, valeur) values ('clans_ouverts', 'true')
on conflict (cle) do update set valeur = excluded.valeur;
commit;

select public.clans_ouverts() as clans_ouverts,
       position('(6 membres)' in pg_get_functiondef('public.clan_inviter(text)'::regprocedure)) > 0 as inviter_6,
       position('(6 membres)' in pg_get_functiondef('public.clan_repondre(uuid,boolean)'::regprocedure)) > 0 as repondre_6;
