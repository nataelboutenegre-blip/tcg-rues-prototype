-- =====================================================================
--  TerraFront — Commune du jour, 3 : jouer sans compte
--
--  Un visiteur sans compte joue la commune d'HIER, jamais celle du jour.
--  Pourquoi : un mode sans compte se relance à volonté. S'il donnait la
--  commune du jour, n'importe qui pourrait y lire les distances (deux
--  suffisent à la situer), puis jouer avec son vrai compte et « trouver »
--  du premier coup. Celle d'hier n'a plus rien de secret.
--
--  Rien n'est enregistré : le navigateur renvoie la liste de ses essais,
--  le serveur recalcule tout. Même réponse que cdj_partie(), avec
--  'invite': true.
--
--  Le fichier sort aussi la construction des indices dans cdj_indices(),
--  pour que la partie normale et la partie invitée disent exactement la
--  même chose. cdj_etat() est réécrite pour l'utiliser, sans autre
--  changement.
--
--  À lancer APRÈS cdj-1-fonctions.sql. Rejouable.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Les indices, en un seul endroit
-- ---------------------------------------------------------------------
create or replace function public.cdj_indices(p_code text, p_ouverts int)
returns jsonb
language plpgsql stable security definer
set search_path to 'public'
as $$
declare
  c communes;
  v_fait text;
  v_rang int;
begin
  select * into c from communes where code = p_code;

  -- l'anecdote : le meilleur fait qui ne donne pas le nom, sinon le rang
  -- de population dans le département
  if p_ouverts >= 5 then
    select f->>'t' into v_fait
      from jsonb_array_elements(coalesce(c.faits, '[]'::jsonb)) f
     where (f->>'t') !~ '«|lettres|caractères'
     order by (f->>'r')::int
     limit 1;
    if v_fait is null then
      select count(*) + 1 into v_rang from communes
       where departement = c.departement and population > c.population;
      v_fait := case when v_rang = 1 then 'La commune la plus peuplée de son département.'
                     else 'La ' || v_rang || 'e commune la plus peuplée de son département.' end;
    end if;
  end if;

  return jsonb_build_array(
    jsonb_build_object('cle', 'population', 'valeur', case when p_ouverts >= 1 then
      case when c.population < 10000 then 'entre 5 000 et 10 000 habitants'
           when c.population < 20000 then 'entre 10 000 et 20 000 habitants'
           when c.population < 50000 then 'entre 20 000 et 50 000 habitants'
           when c.population < 100000 then 'entre 50 000 et 100 000 habitants'
           else 'plus de 100 000 habitants' end end),
    jsonb_build_object('cle', 'region',      'valeur', case when p_ouverts >= 2 then cdj_region(c.departement) end),
    jsonb_build_object('cle', 'gentile',     'valeur', case when p_ouverts >= 3 then c.gentile end),
    jsonb_build_object('cle', 'departement', 'valeur', case when p_ouverts >= 4 then c.departement end),
    jsonb_build_object('cle', 'anecdote',    'valeur', case when p_ouverts >= 5 then v_fait end));
end;
$$;

-- ---------------------------------------------------------------------
-- 2. La partie normale, réécrite pour utiliser cdj_indices (même résultat)
-- ---------------------------------------------------------------------
create or replace function public.cdj_etat(p_uid uuid, p_jour public.cdj_jours)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  c communes;
  v_essais jsonb;
  v_nb int;
  v_trouve boolean;
  v_fini boolean;
  v_serie int := 0;
  v_d date;
begin
  select * into c from communes where code = p_jour.commune_code;

  select coalesce(jsonb_agg(jsonb_build_object(
           'code', e.commune_code, 'nom', x.nom, 'dept', x.departement,
           'lat', x.latitude, 'lon', x.longitude, 'km', e.km,
           'cap', case when e.km = 0 then null
                       else cdj_cap(x.latitude, x.longitude, c.latitude, c.longitude) end)
         order by e.n), '[]'::jsonb),
         count(*), coalesce(bool_or(e.km = 0), false)
    into v_essais, v_nb, v_trouve
    from cdj_essais e join communes x on x.code = e.commune_code
   where e.joueur_id = p_uid and e.jour = p_jour.jour;

  v_fini := v_trouve or v_nb >= 6;

  -- la série : jours trouvés d'affilée, jusqu'à aujourd'hui ou hier
  v_d := p_jour.jour;
  if not v_trouve then v_d := v_d - 1; end if;
  while exists (select 1 from cdj_essais where joueur_id = p_uid and jour = v_d and km = 0) loop
    v_serie := v_serie + 1;
    v_d := v_d - 1;
  end loop;

  return jsonb_build_object(
    'jour', p_jour.jour,
    'numero', p_jour.numero,
    'silhouette', (select points from cdj_silhouettes where code = c.code),
    'essais', v_essais,
    'max', 6,
    'fini', v_fini,
    'trouve', v_trouve,
    'indices', cdj_indices(c.code, case when v_fini then 5 else least(5, v_nb) end),
    'serie', v_serie,
    'joueurs', (select count(distinct joueur_id) from cdj_essais where jour = p_jour.jour),
    'trouves', (select count(*) from cdj_essais where jour = p_jour.jour and km = 0),
    'reponse', case when v_fini then jsonb_build_object(
                 'code', c.code, 'nom', c.nom, 'dept', c.departement,
                 'pop', c.population, 'lat', c.latitude, 'lon', c.longitude) end);
end;
$$;

-- ---------------------------------------------------------------------
-- 3. La partie sans compte : la commune d'hier, rien d'enregistré
-- ---------------------------------------------------------------------
create or replace function public.cdj_invite(p_codes text[] default '{}')
returns jsonb
language plpgsql stable security definer
set search_path to 'public'
as $$
declare
  v_jour cdj_jours;
  c communes;
  x communes;
  v_code text;
  v_vus text[] := '{}';
  v_essais jsonb := '[]'::jsonb;
  v_nb int := 0;
  v_trouve boolean := false;
  v_fini boolean;
  v_km int;
begin
  select * into v_jour from cdj_jours
   where jour < (now() at time zone 'Europe/Paris')::date
   order by jour desc limit 1;
  if not found then
    raise exception 'Pas encore de commune à rejouer. Reviens demain.';
  end if;
  select * into c from communes where code = v_jour.commune_code;

  -- on rejoue les essais envoyés, dans l'ordre : inconnus et doublons
  -- ignorés, six au plus, rien après la bonne réponse
  foreach v_code in array coalesce(p_codes, '{}') loop
    exit when v_nb >= 6 or v_trouve;
    continue when v_code = any(v_vus);
    select * into x from communes where code = v_code and latitude is not null;
    continue when not found;
    v_vus := v_vus || v_code;
    v_nb := v_nb + 1;
    if x.code = c.code then
      v_km := 0; v_trouve := true;
    else
      v_km := greatest(1, round(cdj_km(x.latitude, x.longitude, c.latitude, c.longitude))::int);
    end if;
    v_essais := v_essais || jsonb_build_object(
      'code', x.code, 'nom', x.nom, 'dept', x.departement,
      'lat', x.latitude, 'lon', x.longitude, 'km', v_km,
      'cap', case when v_km = 0 then null
                  else cdj_cap(x.latitude, x.longitude, c.latitude, c.longitude) end);
  end loop;

  v_fini := v_trouve or v_nb >= 6;

  return jsonb_build_object(
    'invite', true,
    'jour', v_jour.jour,
    'numero', v_jour.numero,
    'silhouette', (select points from cdj_silhouettes where code = c.code),
    'essais', v_essais,
    'max', 6,
    'fini', v_fini,
    'trouve', v_trouve,
    'indices', cdj_indices(c.code, case when v_fini then 5 else least(5, v_nb) end),
    'serie', 0,
    'joueurs', (select count(distinct joueur_id) from cdj_essais where jour = v_jour.jour),
    'trouves', (select count(*) from cdj_essais where jour = v_jour.jour and km = 0),
    'reponse', case when v_fini then jsonb_build_object(
                 'code', c.code, 'nom', c.nom, 'dept', c.departement,
                 'pop', c.population, 'lat', c.latitude, 'lon', c.longitude) end);
end;
$$;

-- ---------------------------------------------------------------------
-- 4. Les droits
-- ---------------------------------------------------------------------
revoke all on function public.cdj_indices(text, int) from public, anon, authenticated;
revoke all on function public.cdj_invite(text[])    from public;
grant execute on function public.cdj_invite(text[]) to anon, authenticated;
