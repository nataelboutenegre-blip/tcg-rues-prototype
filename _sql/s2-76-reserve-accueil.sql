-- ===========================================================================
--  TerraFront — s2-76 : la réserve d'accueil du pot du Front (2/11/2026)
--  Décidé avec Nataël le 2/11 : « on laisse 3000 et on voit comme ça évolue ».
--
--  Le pot se vide vers le 7-8/11 (≈ 2 200 à 2 900 communes tirées par jour),
--  et les absents ne tiennent presque rien (265 communes à 7 jours).
--  Les 3 000 dernières communes libres sont donc réservées aux nouveaux :
--  quand il reste 3 000 communes libres ou moins, un compte de plus de
--  7 jours ne peut plus OUVRIR de paquet du Front. Le refus arrive avant de
--  prendre quoi que ce soit : son paquet gratuit reste dans sa réserve.
--  Un paquet déjà ouvert se termine normalement. Terra n'est pas concerné.
--
--  Réglage (config_jeu 'reserve_accueil') : ouvert (1/0), communes (3000),
--  jours (7). Pour couper : mettre ouvert à 0 (dernière ligne commentée).
--
--  Comment : une seule ligne ajoutée au début de ouvrir_paquet(text) et de
--  demarrer_paquet(text) (celles qui existent), le reste de leur définition
--  est gardé tel quel (pot-vide, verrou de saison…). Si le début attendu
--  n'est pas trouvé, rien n'est modifié.
--  Rejouable. Contrôle en une ligne.
-- ===========================================================================

insert into public.config_jeu (cle, valeur)
values ('reserve_accueil', '{"ouvert": 1, "communes": 3000, "jours": 7}')
on conflict (cle) do nothing;

-- vrai si ce joueur ne peut plus ouvrir de paquet du Front (réserve d'accueil)
create or replace function public.reserve_accueil_bloque(p_uid uuid)
 returns boolean language plpgsql stable security definer set search_path to 'public' as $f$
declare
  r jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'reserve_accueil'), '{}'::jsonb);
  v_cree timestamptz;
begin
  if p_uid is null or coalesce((r->>'ouvert')::int, 0) <> 1 then return false; end if;
  select u.created_at into v_cree from auth.users u where u.id = p_uid;
  if v_cree is not null and v_cree > now() - make_interval(days => coalesce((r->>'jours')::int, 7)) then return false; end if;
  return (select count(*) from communes c where not exists (select 1 from possessions po where po.commune_code = c.code))
         <= coalesce((r->>'communes')::int, 3000);
end; $f$;
revoke all on function public.reserve_accueil_bloque(uuid) from public, anon, authenticated;

-- ce que le jeu peut lire : la réserve est-elle active pour moi, et combien reste-t-il
create or replace function public.reserve_accueil_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  r jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'reserve_accueil'), '{}'::jsonb);
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return jsonb_build_object('ouvert', coalesce((r->>'ouvert')::int, 0) = 1,
    'communes', coalesce((r->>'communes')::int, 3000), 'jours', coalesce((r->>'jours')::int, 7),
    'bloque', reserve_accueil_bloque(auth.uid()));
end; $f$;
revoke all on function public.reserve_accueil_etat() from public, anon;
grant execute on function public.reserve_accueil_etat() to authenticated;

do $r$
declare
  f text;
  d text;
  v_ajout text := E'\nbegin\n  -- s2-76 : réserve d''accueil, refuser avant de prendre quoi que ce soit\n'
    || E'  if reserve_accueil_bloque(auth.uid()) then\n'
    || E'    raise exception ''Les dernières communes du pot sont réservées aux nouveaux joueurs : ton paquet est gardé. Pour gagner du terrain, attaque !'';\n'
    || E'  end if;\n';
begin
  foreach f in array array['public.ouvrir_paquet(text)', 'public.demarrer_paquet(text)'] loop
    if to_regprocedure(f) is null then raise notice '% : absente, rien à faire', f; continue; end if;
    d := pg_get_functiondef(to_regprocedure(f));
    if position('s2-76' in d) > 0 then raise notice '% : déjà en place', f; continue; end if;
    if position(E'\nbegin\n' in d) = 0 then
      raise exception '% : début de fonction introuvable. Rien n''a été modifié. Envoie-moi sa définition.', f;
    end if;
    execute regexp_replace(d, E'\nbegin\n', v_ajout);   -- la première seulement
    raise notice '% : modifiée', f;
  end loop;
end
$r$;

-- Contrôle : true | true | true | (communes libres) | (avant la réserve)
-- (« absente » à la place d'un true : la fonction n'existe pas, c'est normal)
select case when to_regprocedure('public.ouvrir_paquet(text)') is null then 'absente'
            else (position('s2-76' in pg_get_functiondef(to_regprocedure('public.ouvrir_paquet(text)'))) > 0)::text end   as ouvrir_ok,
       case when to_regprocedure('public.demarrer_paquet(text)') is null then 'absente'
            else (position('s2-76' in pg_get_functiondef(to_regprocedure('public.demarrer_paquet(text)'))) > 0)::text end as demarrer_ok,
       has_function_privilege('authenticated', 'public.reserve_accueil_etat()', 'execute')                            as etat_ok,
       (select count(*) from public.communes c where not exists (select 1 from public.possessions po where po.commune_code = c.code)) as libres,
       (select count(*) from public.communes c where not exists (select 1 from public.possessions po where po.commune_code = c.code)) - 3000 as avant_la_reserve;

-- Pour couper la réserve :
-- update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb)::text where cle = 'reserve_accueil';
