-- s2-113 (7/11/2026) : la protection contre les séries noires (demande de Nataël, 14 h 22).
-- Après 2 assauts perdus aux dés d'affilée sur une même commune, les assauts
-- suivants sur cette commune ont +15 points de chances (90 % au plus), jusqu'à
-- la prochaine victoire aux dés.
--   - « perdu aux dés » : une victoire annulée par une garnison compte comme
--     gagnée aux dés, elle remet le compteur à zéro ;
--   - jamais contre une commune en garnison (même principe que le bonus de
--     débutant : ce ne doit pas être plus simple d'attaquer une garnison) ;
--   - le compteur vit dans le siège : il repart de zéro quand le siège expire
--     (24 h sans assaut) ou quand la commune est prise ;
--   - les défenses ne sont pas concernées.
-- Mesure (5/11 au 7/11 midi) : 1 370 rounds sur 8 795 (15,6 %) auraient eu le
-- bonus, chez 31 joueurs sur 44 ; environ 200 victoires de plus en 2,5 jours,
-- soit 4 à 5 % de conquêtes en plus au maximum.
-- Réglage : config_jeu 'serie_noire' (actif, pertes, bonus).
-- Testé sur la prod dans un bloc annulé.

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

alter table public.sieges add column if not exists pertes_suite integer not null default 0;

insert into public.config_jeu (cle, valeur)
values ('serie_noire', '{"actif": true, "pertes": 2, "bonus": 0.15}')
on conflict (cle) do nothing;

-- le coup de pouce pour ce joueur sur cette commune (0 s'il n'y en a pas)
create or replace function public.serie_noire_bonus(p_uid uuid, p_code text)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  with cfg as (select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'serie_noire'), '{}'::jsonb) as v)
  select case
    when saison2_active()
     and coalesce((cfg.v->>'actif')::boolean, true)
     and exists (select 1 from sieges s
                  where s.attacker_id = p_uid and s.commune_code = p_code
                    and s.dernier_round > siege_limite()
                    and s.pertes_suite >= coalesce((cfg.v->>'pertes')::int, 2))
     and not garnison_active(p_code)
    then coalesce((cfg.v->>'bonus')::numeric, 0.15)
    else 0 end
    from cfg;
$f$;

revoke execute on function public.serie_noire_bonus(uuid, text) from public, anon, authenticated;

-- l'aperçu d'une attaque
do $$
declare d text := pg_get_functiondef('public.apercu_attaque(text, text)'::regprocedure);
begin
  if position('s2-113' in d) > 0 then raise notice 'apercu_attaque : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'  v_chance := chance_debutant(debutant_actif(v_uid), v_uid, p_commune_code, v_chance);   -- s2-111 : bonus de débutant',
'  v_chance := chance_debutant(debutant_actif(v_uid), v_uid, p_commune_code, v_chance);   -- s2-111 : bonus de débutant
  v_chance := least(0.90, v_chance + serie_noire_bonus(v_uid, p_commune_code));   -- s2-113 : série noire', 1, 'apercu_attaque');
  execute d;
end $$;

-- l'aperçu de la liste des cibles
do $$
declare d text := pg_get_functiondef('public.apercu_attaques(text[], text)'::regprocedure);
begin
  if position('s2-113' in d) > 0 then raise notice 'apercu_attaques : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'round(chance_debutant(v_deb, v_uid, c.code, greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code))))',
'round(least(0.90, chance_debutant(v_deb, v_uid, c.code, greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code)))) + serie_noire_bonus(v_uid, c.code))   -- s2-113
', 1, 'apercu_attaques');
  execute d;
end $$;

-- l'assaut : le coup de pouce, puis le compteur
do $$
declare d text := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
begin
  if position('s2-113' in d) > 0 then raise notice 'attaquer : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'  v_par_garnison boolean := false;   -- s2-46',
'  v_par_garnison boolean := false;   -- s2-46
  v_de boolean;   -- s2-113 : le résultat aux dés, avant la garnison', 1, 'attaquer (déclaration)');
  d := pg_temp.remp(d,
'  v_chance := chance_debutant(debutant_actif(v_attaquant_id), v_attaquant_id, p_commune_code, v_chance);   -- s2-111 : bonus de débutant',
'  v_chance := chance_debutant(debutant_actif(v_attaquant_id), v_attaquant_id, p_commune_code, v_chance);   -- s2-111 : bonus de débutant
  v_chance := least(0.90, v_chance + serie_noire_bonus(v_attaquant_id, p_commune_code));   -- s2-113 : série noire', 1, 'attaquer (bonus)');
  d := pg_temp.remp(d,
'  v_gagne := random() < v_chance;',
'  v_gagne := random() < v_chance;
  v_de := v_gagne;   -- s2-113', 1, 'attaquer (dés)');
  d := pg_temp.remp(d,
'  insert into sieges (attacker_id, commune_code, victoires_consecutives, dernier_round)
  values (v_attaquant_id, p_commune_code, v_nouvelles_victoires, now())
  on conflict (attacker_id, commune_code)
  do update set victoires_consecutives = v_nouvelles_victoires,
                dernier_round = now(),',
'  insert into sieges (attacker_id, commune_code, victoires_consecutives, dernier_round, pertes_suite)
  values (v_attaquant_id, p_commune_code, v_nouvelles_victoires, now(), case when v_de then 0 else 1 end)
  on conflict (attacker_id, commune_code)
  do update set victoires_consecutives = v_nouvelles_victoires,
                dernier_round = now(),
                pertes_suite = case when v_de then 0 else sieges.pertes_suite + 1 end,   -- s2-113', 1, 'attaquer (compteur)');
  execute d;
end $$;

commit;

-- Contrôle attendu : t | t | t | t | t | t
select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'sieges' and column_name = 'pertes_suite') as colonne_ok,
       position('s2-113' in pg_get_functiondef('public.apercu_attaque(text, text)'::regprocedure)) > 0    as apercu_ok,
       position('s2-113' in pg_get_functiondef('public.apercu_attaques(text[], text)'::regprocedure)) > 0 as liste_ok,
       position('s2-113' in pg_get_functiondef('public.attaquer(text, text)'::regprocedure)) > 0          as assaut_ok,
       not has_function_privilege('authenticated', 'public.serie_noire_bonus(uuid, text)', 'execute')   as aide_privee,
       exists (select 1 from public.config_jeu where cle = 'serie_noire')                                as reglages_ok;
