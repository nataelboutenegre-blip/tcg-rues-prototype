-- ===========================================================================
--  s2-70 — Plus ou moins : des rangs plus serrés, comme Rafale (aperçu validé
--  le 30/10 à 20 h 46 : « parfait »). Les Elo de Plus ou moins tiennent entre
--  930 et 1 050 : avec des paliers de 100, tout le monde était Cartographe.
--
--    Arpenteur   < 960        Géomètre   1 010
--    Topographe    960 (nouveau)   Recenseur  1 030
--    Cartographe   990        Préfet     réservé au n°1 (comme « As du volant »)
--  Le n°1 : au moins 5 duels et plus de 1 000 Elo (même règle que Rafale) ;
--  à égalité, celui qui y est arrivé le premier. Le classement le met en tête.
--  À élargir plus tard si les Elo s'écartent : il suffit de relancer pom_rang.
--
--  pom_d_etat est modifiée à partir de son texte en base : si un repère manque,
--  rien ne change. Prend effet tout de suite (le patch281 ajoute la jauge et
--  les couleurs). Rejouable. Contrôle attendu : Topographe | Recenseur | true
-- ===========================================================================
begin;

create or replace function public.pom_rang(p_elo integer)
returns text language sql immutable set search_path to 'public'
as $$ select case when p_elo >= 1030 then 'Recenseur' when p_elo >= 1010 then 'Géomètre'
                  when p_elo >= 990 then 'Cartographe' when p_elo >= 960 then 'Topographe'
                  else 'Arpenteur' end; $$;

create or replace function public.pom_premier()
returns uuid language sql stable security definer set search_path to 'public'
as $$ select joueur_id from pom_joueurs where parties >= 5 and elo > 1000 order by elo desc, maj limit 1; $$;

revoke all on function public.pom_rang(integer), public.pom_premier() from public, anon, authenticated;

create or replace function pg_temp.remplacer(p_def text, p_avant text, p_apres text, p_etiquette text)
returns text language plpgsql as $$
declare n integer := (length(p_def) - length(replace(p_def, p_avant, ''))) / length(p_avant);
begin
  if n <> 1 then raise exception '% : repère trouvé % fois au lieu d''une, rien n''a changé', p_etiquette, n; end if;
  return replace(p_def, p_avant, p_apres);
end $$;

do $do$
declare d text := pg_get_functiondef('public.pom_d_etat()'::regprocedure);
begin
  if position('pom_premier' in d) > 0 then raise notice 'pom_d_etat : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, $a$'rang', pom_rang(v_elo),$a$,
                            $a$'rang', case when v_uid = pom_premier() then 'Préfet' else pom_rang(v_elo) end,$a$, 'rang du joueur');
  d := pg_temp.remplacer(d, $a$pom_rang(r.elo) as rang$a$,
                            $a$case when r.joueur_id = pom_premier() then 'Préfet' else pom_rang(r.elo) end as rang$a$, 'rang du classement');
  d := pg_temp.remplacer(d, $a$where r.parties > 0 order by r.elo desc limit 10$a$,
                            $a$where r.parties > 0 order by r.elo desc, r.maj limit 10$a$, 'ordre du classement');
  d := pg_temp.remplacer(d, $a$(select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from ($a$,
                            $a$(select coalesce(jsonb_agg(x order by x.elo desc, (x.rang = 'Préfet') desc), '[]'::jsonb) from ($a$, 'ordre final');
  execute d;
end $do$;

commit;

-- Contrôle : Topographe | Recenseur | true
select public.pom_rang(970) as rang_970, public.pom_rang(1045) as rang_1045,
       position('pom_premier' in pg_get_functiondef('public.pom_d_etat()'::regprocedure)) > 0 as classement;
