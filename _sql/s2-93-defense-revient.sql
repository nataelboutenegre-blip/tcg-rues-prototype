-- ===========================================================================
--  TerraFront — s2-93 : une défense revient toutes les 24 h
--  (3/11/2026, idée de H34VEN sur Discord, validée par Oshannir et Nataël).
--
--  Aujourd'hui : deux défenses par attaque (s2-46). Une fois les deux
--  utilisées, plus rien à faire tant que la série de l'attaquant ne retombe
--  pas à zéro : une attaque laissée en plan à 2 victoires reste une menace
--  qu'on ne peut plus repousser.
--  Après : une défense utilisée revient 24 h après la dernière défense, jusqu'à
--  deux. Ça ne change rien face à quelqu'un qui attaque toute la journée.
--
--  1. sieges.derniere_defense : l'heure de la dernière défense sur ce siège.
--     Pour les sièges où des défenses sont déjà utilisées, on prend l'heure du
--     dernier round (la défense le suit toujours) : une attaque abandonnée
--     depuis plus de 24 h rend donc une défense tout de suite.
--  2. defenses_rendre() : rend les défenses dues (toutes les 10 min par
--     pg_cron, et juste avant chaque défense pour ne pas attendre le passage).
--  3. defendre() : rend d'abord ce qui est dû, note l'heure de chaque défense.
--     Modifiée en place à partir de sa définition en production (textes de
--     s2-46 vérifiés : s'il en manque un, rien ne change).
--  4. sieges_contre_moi() : nouvelle colonne defense_revient (quand la
--     prochaine défense revient), pour l'écran Défense (patch334). Comme les
--     colonnes de retour changent, elle est supprimée puis recréée à partir de
--     sa définition en production, droits remis.
--  Ne touche ni aux chances, ni aux coûts, ni à la garnison, ni à attaquer().
--  Rejouable. Contrôle attendu : true | true | true | true | (défenses rendues).
-- ===========================================================================
begin;

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

-- 1. l'heure de la dernière défense -------------------------------------------
alter table public.sieges add column if not exists derniere_defense timestamptz;
update public.sieges
   set derniere_defense = coalesce(dernier_round, now())
 where coalesce(defenses_faites, 0) > 0 and derniere_defense is null;

-- 2. rendre les défenses dues ---------------------------------------------------
create or replace function public.defenses_rendre(p_commune text default null, p_attaquant uuid default null)
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  n integer;
begin
  with dus as (
    select s.commune_code, s.attacker_id,
           least(s.defenses_faites, floor(extract(epoch from now() - s.derniere_defense) / 86400)::integer) as k
      from sieges s
     where s.derniere_defense is not null
       and coalesce(s.defenses_faites, 0) > 0
       and s.derniere_defense <= now() - interval '24 hours'
       and (p_commune is null or (s.commune_code = p_commune and s.attacker_id = p_attaquant))
  )
  update sieges s
     set defenses_faites = s.defenses_faites - d.k,
         -- le reste du délai en cours est gardé : la suivante revient 24 h plus tard
         derniere_defense = case when s.defenses_faites - d.k > 0 then s.derniere_defense + d.k * interval '24 hours' end,
         defense_utilisee = (s.victoires_consecutives > 0 and s.defenses_faites - d.k >= 2)
    from dus d
   where s.commune_code = d.commune_code and s.attacker_id = d.attacker_id and d.k > 0;
  get diagnostics n = row_count;
  return n;
end;
$f$;
revoke all on function public.defenses_rendre(text, uuid) from public, anon, authenticated;

-- 3. defendre : rendre d'abord, noter l'heure ensuite --------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure);
  if position('s2-93' in d) > 0 then raise notice 'defendre : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'select s.victoires_consecutives, coalesce(s.defenses_faites, 0) >= 2 into v_victoires, v_deja',
                       'perform public.defenses_rendre(p_commune_code, p_attaquant);   -- s2-93 : les défenses dues reviennent'
                    || E'\n  select s.victoires_consecutives, coalesce(s.defenses_faites, 0) >= 2 into v_victoires, v_deja',
                       1, 'defendre (lecture)');
  d := pg_temp.remp(d, 'defenses_faites = case when v_restantes > 0 then coalesce(defenses_faites, 0) + 1 else 0 end,',
                       'defenses_faites = case when v_restantes > 0 then coalesce(defenses_faites, 0) + 1 else 0 end,'
                    || E'\n        derniere_defense = case when v_restantes > 0 then now() end,   -- s2-93',
                       1, 'defendre (écriture)');
  d := pg_temp.remp(d, 'Tu as déjà utilisé tes deux défenses contre cette attaque',
                       'Tu as déjà utilisé tes deux défenses contre cette attaque : une revient 24 h après ta dernière défense',
                       1, 'defendre (message)');
  execute d;
end $$;

-- 4. sieges_contre_moi : quand la prochaine défense revient ---------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.sieges_contre_moi()'::regprocedure);
  if position('defense_revient' in d) > 0 then raise notice 'sieges_contre_moi : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'defense_utilisee boolean)', 'defense_utilisee boolean, defense_revient timestamp with time zone)',
                       1, 'sieges_contre_moi (colonnes)');
  if (select count(*) from regexp_matches(d, 's\.defense_utilisee(\s+)from sieges s', 'g')) <> 1 then
    raise exception 'sieges_contre_moi : texte « s.defense_utilisee … from sieges s » introuvable — rien n''a changé';
  end if;
  d := regexp_replace(d, 's\.defense_utilisee(\s+)from sieges s',
         's.defense_utilisee,' || E'\n         '
         || 'case when s.defense_utilisee and s.derniere_defense is not null then s.derniere_defense + interval ''24 hours'' end   -- s2-93'
         || '\1from sieges s');
  drop function public.sieges_contre_moi();
  execute d;
  revoke all on function public.sieges_contre_moi() from public, anon;
  grant execute on function public.sieges_contre_moi() to authenticated, service_role;
end $$;

commit;

-- 5. toutes les 10 minutes ---------------------------------------------------
do $do$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.unschedule(jobid) from cron.job where jobname = 'defenses-rendre';
    perform cron.schedule('defenses-rendre', '*/10 * * * *', 'select public.defenses_rendre()');
  else
    raise notice 's2-93 : pg_cron absent, les défenses ne reviendront qu''au moment de défendre';
  end if;
end $do$;

-- les attaques abandonnées depuis plus de 24 h rendent leur défense tout de suite
-- Contrôle : true | true | true | true | (défenses rendues maintenant)
select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'sieges' and column_name = 'derniere_defense') as colonne_ok,
       position('s2-93' in pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure)) > 0                  as defendre_ok,
       position('defense_revient' in pg_get_functiondef('public.sieges_contre_moi()'::regprocedure)) > 0              as liste_ok,
       has_function_privilege('authenticated', 'public.sieges_contre_moi()', 'execute')                               as droits_ok,
       public.defenses_rendre()                                                                                        as defenses_rendues;
