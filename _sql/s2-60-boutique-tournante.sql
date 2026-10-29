-- ===========================================================================
--  s2-60 — Terra : « Ta boutique », la boutique qui tourne
--  Idée d'Oshannir (comme « Ta boutique » de LoL), aperçu validé par Nataël
--  le 29/10 (« très bien ! »).
--
--  Chaque joueur a SA boutique : uniquement des communes qu'il n'a pas.
--    - du jour      : 2 communes + 2 peu communes, change à minuit (Paris) ;
--    - de la semaine : 1 rare, 1 épique, 1 légendaire, change le lundi à minuit.
--  Chaque carte a une remise de 20 à 70 % sur son prix de base :
--    commune 60, peu commune 120, rare 500, épique 1 200, légendaire 3 000 TP.
--  Une carte s'achète une fois. Payée en TP : elle est « bloquée » comme les
--  autres achats en points (ne s'échange pas, pas de Bourse ; revente au jeu
--  possible si elle devient un doublon). Ne compte pas dans les 3 paquets de
--  boutique par jour.
--  La sélection est tirée à la première visite de la période puis gardée
--  (table boutique_vitrine) : acheter une carte ne fait pas apparaître une
--  autre carte à la place.
--  Réglages dans config_jeu 'boutique_tournante' (prix, nombre de cartes,
--  remises, interrupteur 'ouverte'), modifiables sans code.
--
--  Fonctions (joueur connecté) : ma_boutique(), ma_boutique_acheter(periode, case).
--  Rejouable. Contrôle attendu : true | 60 | 3000 | true
-- ===========================================================================
begin;

insert into public.config_jeu (cle, valeur) values
  ('boutique_tournante', '{"ouverte": 1, "prix_commun": 60, "prix_peucommun": 120, "prix_rare": 500,
     "prix_epique": 1200, "prix_legendaire": 3000, "jour_commun": 2, "jour_peucommun": 2,
     "semaine_rare": 1, "semaine_epique": 1, "semaine_legendaire": 1, "remise_min": 20, "remise_max": 70}')
on conflict (cle) do nothing;

create or replace function public.bt_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'boutique_tournante'),
    case p_cle when 'ouverte' then 1 when 'prix_commun' then 60 when 'prix_peucommun' then 120
               when 'prix_rare' then 500 when 'prix_epique' then 1200 when 'prix_legendaire' then 3000
               when 'jour_commun' then 2 when 'jour_peucommun' then 2 when 'semaine_rare' then 1
               when 'semaine_epique' then 1 when 'semaine_legendaire' then 1
               when 'remise_min' then 20 when 'remise_max' then 70 end);
$f$;

create table if not exists public.boutique_vitrine(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  periode      text not null check (periode in ('jour', 'semaine')),
  debut        date not null,               -- le jour, ou le lundi de la semaine (Paris)
  case_n       integer not null,
  commune_code text not null references public.communes(code),
  base         integer not null,
  remise       integer not null,
  prix         integer not null,
  achete_le    timestamptz,
  primary key (joueur_id, periode, debut, case_n)
);
create index if not exists boutique_vitrine_date on public.boutique_vitrine(debut);
alter table public.boutique_vitrine enable row level security;
revoke all on public.boutique_vitrine from public, anon, authenticated;

-- le début de la période en cours (jour de Paris, ou lundi de la semaine)
create or replace function public.bt_debut(p_periode text)
 returns date language sql stable set search_path to 'public'
as $f$
  select case p_periode when 'jour' then (now() at time zone 'Europe/Paris')::date
                        else date_trunc('week', (now() at time zone 'Europe/Paris'))::date end;
$f$;

-- tire la vitrine d'une période si elle n'existe pas encore
create or replace function public.bt_tirer(p_uid uuid, p_periode text)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_debut date := bt_debut(p_periode);
  v_tiers text[] := case p_periode when 'jour' then array['commun', 'peucommun'] else array['rare', 'epique', 'legendaire'] end;
  v_t text;
  v_n integer;
  v_case integer := 0;
  v_min integer := bt_reglage('remise_min')::integer;
  v_max integer := bt_reglage('remise_max')::integer;
  r record;
begin
  -- verrou par joueur : deux onglets ouverts ne tirent pas deux vitrines
  perform pg_advisory_xact_lock(hashtext('bt_tirer' || p_uid::text || p_periode));
  if exists (select 1 from boutique_vitrine v where v.joueur_id = p_uid and v.periode = p_periode and v.debut = v_debut) then
    return;
  end if;
  foreach v_t in array v_tiers loop
    v_n := coalesce(bt_reglage((case p_periode when 'jour' then 'jour_' else 'semaine_' end) || v_t)::integer, 0);
    for r in
      select c.code
        from communes c
       where c.tier = v_t
         and not exists (select 1 from terra_collection t
                          where t.joueur_id = p_uid and t.commune_code = c.code and t.exemplaires > 0)
       order by md5(p_uid::text || v_debut::text || p_periode || c.code)
       limit v_n
    loop
      v_case := v_case + 1;
      insert into boutique_vitrine(joueur_id, periode, debut, case_n, commune_code, base, remise, prix)
      select p_uid, p_periode, v_debut, v_case, r.code, b.base, m.remise, round(b.base * (100 - m.remise) / 100.0)::integer
        from (select bt_reglage('prix_' || v_t)::integer as base) b,
             (select v_min + 10 * (abs(hashtext(p_uid::text || v_debut::text || r.code)::bigint) % ((v_max - v_min) / 10 + 1)) as remise) m;
    end loop;
  end loop;
  -- ménage : les vitrines de plus de 3 semaines
  if random() < 0.05 then delete from boutique_vitrine where debut < (now() at time zone 'Europe/Paris')::date - 21; end if;
end;
$f$;

create or replace function public.ma_boutique()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_jour date := bt_debut('jour');
  v_sem date := bt_debut('semaine');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() or bt_reglage('ouverte') <> 1 then
    return jsonb_build_object('ouverte', false);
  end if;
  perform bt_tirer(v_uid, 'jour');
  perform bt_tirer(v_uid, 'semaine');
  return jsonb_build_object(
    'ouverte', true,
    'solde', (select coalesce(solde, 0) from joueurs where id = v_uid),
    -- fins de période en secondes (le client affiche « change dans… »)
    'fin_jour', floor(extract(epoch from ((v_jour + 1)::timestamp at time zone 'Europe/Paris') - now()))::integer,
    'fin_semaine', floor(extract(epoch from ((v_sem + 7)::timestamp at time zone 'Europe/Paris') - now()))::integer,
    'cartes', coalesce((
      select jsonb_agg(jsonb_build_object(
          'periode', v.periode, 'case', v.case_n, 'code', c.code, 'nom', c.nom, 'dept', c.departement,
          'tier', c.tier, 'pop', c.population, 'rang', c.rang, 'palier_total', c.palier_total,
          'base', v.base, 'remise', v.remise, 'prix', v.prix,
          'achete', v.achete_le is not null,
          -- obtenue autrement entre-temps (paquet, échange…) : plus à vendre
          'possede', v.achete_le is null and exists (select 1 from terra_collection t
                       where t.joueur_id = v_uid and t.commune_code = c.code and t.exemplaires > 0),
          -- un album commencé et pas encore réclamé que cette carte fait avancer
          'album', (select k.nom from collection_communes cc join collections k on k.id = cc.collection_id
                     where cc.code = c.code and k.active
                       and not exists (select 1 from collection_recompenses r where r.joueur_id = v_uid and r.collection_id = k.id)
                       and exists (select 1 from collection_communes c2 join terra_collection t2
                                     on t2.commune_code = c2.code and t2.joueur_id = v_uid and t2.exemplaires > 0
                                    where c2.collection_id = k.id)
                     order by k.ordre limit 1))
        order by case v.periode when 'jour' then 0 else 1 end, v.case_n)
        from boutique_vitrine v join communes c on c.code = v.commune_code
       where v.joueur_id = v_uid
         and ((v.periode = 'jour' and v.debut = v_jour) or (v.periode = 'semaine' and v.debut = v_sem))), '[]'::jsonb));
end;
$f$;

create or replace function public.ma_boutique_acheter(p_periode text, p_case integer)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v boutique_vitrine%rowtype;
  v_solde integer;
  v_carte jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() or bt_reglage('ouverte') <> 1 then raise exception 'La boutique est fermée'; end if;
  select coalesce(solde, 0) into v_solde from joueurs where id = v_uid for update;
  select * into v from boutique_vitrine
   where joueur_id = v_uid and periode = p_periode and debut = bt_debut(p_periode) and case_n = p_case
   for update;
  if v.commune_code is null then raise exception 'Cette carte n''est plus en boutique'; end if;
  if v.achete_le is not null then raise exception 'Tu as déjà acheté cette carte'; end if;
  if exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = v.commune_code and t.exemplaires > 0) then
    raise exception 'Tu as déjà cette commune';
  end if;
  if v_solde < v.prix then raise exception 'Solde insuffisant'; end if;

  perform set_config('terrafront.motif', 'boutique', true);   -- étiquette les TP et bloque la carte
  update joueurs set solde = solde - v.prix where id = v_uid;
  perform terra_ajouter(v_uid, v.commune_code, 'boutique');
  update boutique_vitrine set achete_le = now()
   where joueur_id = v_uid and periode = v.periode and debut = v.debut and case_n = v.case_n;

  select jsonb_build_object('code', c.code, 'nom', c.nom, 'dept', c.departement, 'tier', c.tier,
                            'pop', c.population, 'rang', c.rang, 'palier_total', c.palier_total, 'prix', v.prix)
    into v_carte from communes c where c.code = v.commune_code;
  return ma_boutique() || jsonb_build_object('achat', v_carte);
end;
$f$;

revoke all on function public.bt_reglage(text), public.bt_debut(text), public.bt_tirer(uuid, text) from public, anon, authenticated;
revoke all on function public.ma_boutique(), public.ma_boutique_acheter(text, integer) from public, anon;
grant execute on function public.ma_boutique(), public.ma_boutique_acheter(text, integer) to authenticated;

commit;

select public.bt_reglage('ouverte') = 1                                   as ouverte,
       public.bt_reglage('prix_commun')::int                              as prix_commune,
       public.bt_reglage('prix_legendaire')::int                          as prix_legendaire,
       has_function_privilege('authenticated', 'public.ma_boutique_acheter(text, integer)', 'execute') as achat_ok;
