-- ===========================================================================
--  TerraFront — des points pour les mini-jeux (9 octobre 2026)
--
--  Commune du jour : la trouver rapporte des points, d'autant plus qu'on la
--  trouve en peu d'essais : 1 essai 50, 2 essais 40, 3 essais 30, 4 essais 20,
--  5 essais 15, 6 essais 10. Rien si elle n'est pas trouvée. Une seule fois
--  par jour (table cdj_gains, clé joueur + jour).
--
--  Radar : une VICTOIRE en duel classé rapporte 20 points, 5 victoires
--  payées par jour au plus (100 points). Rien pour une défaite, une égalité
--  ou un défi amical (sinon deux amis pourraient se faire gagner des points
--  à tour de rôle). Le joueur dont la partie attendait gagne aussi s'il
--  l'emporte quand elle se règle.
--
--  Les points vont sur le solde (le même qu'en Bourse ; en saison 2, celui
--  de Terra). Rien de rétroactif : seules les parties jouées après ce
--  fichier rapportent.
--
--  Méthode : remplacement de lignes précises dans les définitions en
--  production (cdj_essayer, cdj_partie, radar_clore_si_fini, radar_vue,
--  radar_resume).
--  Si une ligne attendue n'est pas trouvée exactement une fois, RIEN n'est
--  modifié et le fichier s'arrête avec un message.
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

create table if not exists public.cdj_gains(
  joueur_id uuid not null,
  jour      date not null,
  essais    smallint not null,
  gain      integer not null,
  le        timestamptz not null default now(),
  primary key (joueur_id, jour)
);
alter table public.cdj_gains enable row level security;
revoke all on public.cdj_gains from public, anon, authenticated;

alter table public.radar_parties add column if not exists gain integer;
alter table public.radar_parties add column if not exists gain_le timestamptz;

create or replace function public.cdj_gain(p_essais integer)
 returns integer language sql immutable set search_path to 'public'
as $f$
  select case p_essais when 1 then 50 when 2 then 40 when 3 then 30
                       when 4 then 20 when 5 then 15 when 6 then 10 else 0 end;
$f$;

-- Radar : paie une partie gagnee, dans la limite du jour
create or replace function public.radar_gagner(p_partie bigint, p_score numeric)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_joueur uuid;
  v_deja integer;
  v_gain integer := 20;
  v_minuit timestamptz := date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris';
begin
  if p_score is distinct from 1 then return; end if;
  select joueur_id into v_joueur from radar_parties where id = p_partie and gain is null;
  if v_joueur is null then return; end if;
  select count(*) into v_deja from radar_parties
   where joueur_id = v_joueur and gain > 0 and gain_le >= v_minuit;
  if v_deja >= 5 then return; end if;
  update radar_parties set gain = v_gain, gain_le = now() where id = p_partie;
  perform set_config('terrafront.motif', 'radar', true);
  update joueurs set solde = coalesce(solde, 0) + v_gain where id = v_joueur;
end;
$f$;

revoke all on function public.cdj_gain(integer) from public, anon, authenticated;
revoke all on function public.radar_gagner(bigint, numeric) from public, anon, authenticated;

do $g$
declare
  r record;
  v_def text;
  n integer;
begin
  for r in select * from (values
  -- 1. Commune du jour : payer quand l'essai trouve la commune
  ('public.cdj_essayer(text)', 1,
   $a$  insert into cdj_essais(joueur_id, jour, n, commune_code, km)
  values (v_uid, v_jour.jour, v_nb + 1, p_code, v_km);
$a$,
   $a$  insert into cdj_essais(joueur_id, jour, n, commune_code, km)
  values (v_uid, v_jour.jour, v_nb + 1, p_code, v_km);

  -- trouvee : les points, une seule fois par jour
  if v_km = 0 then
    insert into cdj_gains(joueur_id, jour, essais, gain)
    values (v_uid, v_jour.jour, v_nb + 1, cdj_gain(v_nb + 1))
    on conflict do nothing;
    if found then
      perform set_config('terrafront.motif', 'cdj', true);
      update joueurs set solde = coalesce(solde, 0) + cdj_gain(v_nb + 1) where id = v_uid;
    end if;
  end if;
$a$),
  ('public.cdj_essayer(text)', 2,
   $a$  return cdj_etat(v_uid, v_jour);$a$,
   $a$  return cdj_etat(v_uid, v_jour) || jsonb_build_object('gain',
    (select g.gain from cdj_gains g where g.joueur_id = v_uid and g.jour = v_jour.jour));$a$),
  ('public.cdj_partie()', 1,
   $a$  return cdj_etat(v_uid, cdj_jour_courant());$a$,
   $a$  return cdj_etat(v_uid, cdj_jour_courant()) || jsonb_build_object('gain',
    (select g.gain from cdj_gains g where g.joueur_id = v_uid and g.jour = (cdj_jour_courant()).jour));$a$),
  -- 2. Radar : payer les victoires d'un duel classe
  ('public.radar_clore_si_fini(bigint)', 1,
   $a$  update radar_parties set elo_avant = eb, elo_apres = vb, vu = false,
         resultat = case v_score when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end
   where id = s.id;
$a$,
   $a$  update radar_parties set elo_avant = eb, elo_apres = vb, vu = false,
         resultat = case v_score when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end
   where id = s.id;

  -- les points de la victoire (20, 5 victoires payees par jour)
  perform radar_gagner(p.id, v_score);
  perform radar_gagner(s.id, 1 - v_score);
$a$),
  ('public.radar_vue(bigint)', 1,
   $a$    'amical', p.amical,
    'cible', case when p.cible_id is not null$a$,
   $a$    'amical', p.amical,
    'gain', p.gain,
    'cible', case when p.cible_id is not null$a$),
  ('public.radar_resume(bigint)', 2,
   $a$    'regle_le', m.fin_le);$a$,
   $a$    'regle_le', m.fin_le,
    'gain', p.gain);$a$)
  ) t(fonction, etape, avant, apres)
  order by fonction, etape
  loop
    v_def := pg_get_functiondef(r.fonction::regprocedure);
    if position(r.apres in v_def) > 0 then
      raise notice '% (etape %) : deja en place', r.fonction, r.etape;
      continue;
    end if;
    n := (length(v_def) - length(replace(v_def, r.avant, ''))) / length(r.avant);
    if n <> 1 then
      raise exception '% (etape %) : texte a remplacer present % fois au lieu de 1. Rien n''a ete modifie.',
        r.fonction, r.etape, n;
    end if;
    execute replace(v_def, r.avant, r.apres);
  end loop;
end
$g$;

-- Contrôle ---------------------------------------------------------------------------------
select position('cdj_gains' in pg_get_functiondef('public.cdj_essayer(text)'::regprocedure)) > 0 as cdj_paie,
       position('cdj_gains' in pg_get_functiondef('public.cdj_partie()'::regprocedure)) > 0 as cdj_affiche,
       position('radar_gagner' in pg_get_functiondef('public.radar_clore_si_fini(bigint)'::regprocedure)) > 0 as radar_paie,
       position('''gain''' in pg_get_functiondef('public.radar_vue(bigint)'::regprocedure)) > 0
         and position('''gain''' in pg_get_functiondef('public.radar_resume(bigint)'::regprocedure)) > 0 as radar_affiche,
       has_function_privilege('authenticated', 'public.radar_gagner(bigint,numeric)', 'execute') as radar_gagner_ouvert_doit_etre_false;
