-- ===========================================================================
--  s3-13 — le pass de la saison 3 (« Brumes d'automne », 22/11 → 13/12/2026)
--  - deux nouveaux types de récompense : 'paquet' (s'ouvre depuis le pass) et
--    'lingots' (le trop-plein part en TP, comme au Mess) ;
--  - des niveaux bonus après le dernier niveau (bonus_tp tous les bonus_xp) ;
--  - la ligne « saison-3 », ses 20 récompenses et l'article pass-s3 (3,99 €) ;
--  - un aperçu pour le modérateur tant que le pass n'est pas ouvert.
--  Le pass reste FERMÉ : debut = null, article inactif. L'ouverture se fait
--  avec _jour-j/s3-13b-pass-ouverture.sql. Rejouable.
--  Contrôle attendu (dernière ligne) : 20 | 10 | false | false
-- ===========================================================================

alter table public.pass_recompenses drop constraint if exists pass_recompenses_type_check;
alter table public.pass_recompenses add constraint pass_recompenses_type_check
  check (type = any (array['tp', 'energie', 'titre', 'dos', 'habillage', 'skin', 'paquet', 'lingots']));

alter table public.pass_saisons add column if not exists bonus_xp integer;
alter table public.pass_saisons add column if not exists bonus_tp integer;

create table if not exists public.pass_bonus (
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  saison    text not null references public.pass_saisons(saison) on delete cascade,
  n         integer not null default 0 check (n >= 0),
  maj       timestamptz not null default now(),
  primary key (joueur_id, saison));
alter table public.pass_bonus enable row level security;   -- lu et écrit par les fonctions seulement
revoke all on public.pass_bonus from anon, authenticated;

-- ---------- la saison 3 ----------
insert into public.euros_articles (id, type, nom, description, prix_centimes, reserve_og, saison, actif, ordre)
values ('pass-s3', 'pass', 'Pass Brumes d''automne', 'Les 10 récompenses du pass de la saison 3', 399, false, 'saison-3', false, 900)
on conflict (id) do nothing;

insert into public.pass_saisons (saison, nom, article_id, debut, fin, niveaux, xp_niveau, xp_quete, plafond_actions, bonus_xp, bonus_tp)
values ('saison-3', 'Brumes d''automne', 'pass-s3', null, '2026-12-13 09:00:00+00', 20, 1000, 100, 500, 1000, 100)
on conflict (saison) do nothing;

insert into public.pass_recompenses (saison, niveau, payant, type, valeur, quantite, nom, dispo) values
  ('saison-3',  1, false, 'tp',        null,                        100, '100 TerraPoints', true),
  ('saison-3',  2, true,  'titre',     'pass-s3-mecene',              0, 'Titre « Mécène d''automne »', true),
  ('saison-3',  3, false, 'energie',   null,                         10, '+10 énergie', true),
  ('saison-3',  4, true,  'habillage', 'pass-s2-paquet-vendanges',    0, 'Paquet Vendanges', true),
  ('saison-3',  5, false, 'paquet',    'paquet-garanti',              1, 'Paquet garanti', true),
  ('saison-3',  6, true,  'dos',       'pass-s2-dos-feuilles-or',     0, 'Dos Feuilles d''or', true),
  ('saison-3',  7, false, 'titre',     'pass-s3-recrue',              0, 'Titre « Recrue d''automne »', true),
  ('saison-3',  8, true,  'titre',     'pass-s3-vignes',              0, 'Titre « Seigneur des vignes »', true),
  ('saison-3',  9, false, 'lingots',   null,                          5, '5 lingots', true),
  ('saison-3', 10, true,  'skin',      'pass-s2-skin-brume',          0, 'Skin Brume', true),
  ('saison-3', 11, false, 'paquet',    'paquet-departement',          1, 'Paquet du département', true),
  ('saison-3', 12, true,  'habillage', 'pass-s2-paquet-sous-bois',    0, 'Paquet Sous-bois', true),
  ('saison-3', 13, false, 'dos',       'pass-s2-dos-automne',         0, 'Dos Automne', true),
  ('saison-3', 14, true,  'titre',     'pass-s3-brumes',              0, 'Titre « Gardien des brumes »', true),
  ('saison-3', 15, false, 'energie',   null,                         15, '+15 énergie', true),
  ('saison-3', 16, true,  'dos',       'pass-s2-dos-braises',         0, 'Dos Braises d''automne', true),
  ('saison-3', 17, false, 'paquet',    'paquet-garanti',              1, 'Paquet garanti', true),
  ('saison-3', 18, true,  'titre',     'pass-s3-legende',             0, 'Titre « Légende de la saison 3 »', true),
  ('saison-3', 19, false, 'titre',     'pass-s3-veteran',             0, 'Titre « Vétéran de la saison 3 »', true),
  ('saison-3', 20, true,  'skin',      'pass-s2-skin-vendanges',      0, 'Skin Vendanges', true)
on conflict (saison, niveau) do nothing;

-- ---------- l'état du pass : niveaux bonus + aperçu du modérateur ----------
create or replace function public.pass_etat()
 returns jsonb
 language plpgsql
 stable security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  p pass_saisons%rowtype;
  v_xp integer; v_niv integer; v_q integer; v_a integer; v_possede boolean;
  v_apercu boolean := false; v_bonus integer := 0;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from pass_recent();
  if p.saison is null and discussion_est_moderateur(v_uid) then
    -- s3-13 : le modérateur voit le prochain pass avant son ouverture (lecture seule)
    select s.* into p from pass_saisons s where s.debut is null and s.fin > now() order by s.fin desc limit 1;
    v_apercu := p.saison is not null;
  end if;
  if p.saison is null then return jsonb_build_object('actif', false); end if;
  select coalesce(sum(x.quetes + x.actions), 0) into v_xp from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison;
  select coalesce(sum(x.quetes), 0), coalesce(sum(x.actions), 0) into v_q, v_a
    from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison and x.jour = quete_jour();
  v_niv := least(p.niveaux, v_xp / p.xp_niveau);
  v_possede := exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = p.article_id);
  if coalesce(p.bonus_xp, 0) > 0 and coalesce(p.bonus_tp, 0) > 0 then
    v_bonus := greatest(0, (v_xp - p.niveaux * p.xp_niveau) / p.bonus_xp
                 - coalesce((select b.n from pass_bonus b where b.joueur_id = v_uid and b.saison = p.saison), 0));
  end if;
  return jsonb_build_object(
    'actif', now() < p.fin, 'saison', p.saison, 'nom', p.nom, 'debut', p.debut, 'fin', p.fin,
    'niveaux', p.niveaux, 'xp_niveau', p.xp_niveau, 'xp', v_xp, 'niveau', v_niv,
    'dans_niveau', case when v_niv >= p.niveaux then p.xp_niveau else v_xp - v_niv * p.xp_niveau end,
    'jour_quetes', v_q, 'jour_actions', v_a, 'xp_quete', p.xp_quete, 'plafond_actions', p.plafond_actions,
    'possede', v_possede, 'article', p.article_id,
    'prix', (select a.prix_centimes from euros_articles a where a.id = p.article_id),
    'en_vente', coalesce((select a.actif from euros_articles a where a.id = p.article_id), false),
    'recompenses', (select jsonb_agg(jsonb_build_object(
        'niveau', r.niveau, 'payant', r.payant, 'type', r.type, 'valeur', r.valeur, 'quantite', r.quantite,
        'nom', r.nom, 'dispo', r.dispo,
        'recu', exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = r.saison and c.niveau = r.niveau))
        order by r.niveau) from pass_recompenses r where r.saison = p.saison))
    || jsonb_build_object('bonus_xp', coalesce(p.bonus_xp, 0), 'bonus_tp', coalesce(p.bonus_tp, 0), 'bonus_dus', v_bonus, 'apercu', v_apercu);
end;
$function$;

-- ---------- réclamer : + les lingots ; les paquets s'ouvrent à part ----------
create or replace function public.pass_reclamer(p_niveau integer default null::integer)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  p pass_saisons%rowtype;
  r pass_recompenses%rowtype;
  v_niv integer; v_possede boolean; v numeric; n integer := 0;
  l numeric; l2 numeric; v_donne integer; v_repli integer := 0;
begin   -- s2-lot5 : plafond des bonus = réglage
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from pass_recent();
  if p.saison is null then raise exception 'Pas de pass en cours'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select least(p.niveaux, coalesce(sum(x.quetes + x.actions), 0)::integer / p.xp_niveau) into v_niv
    from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison;
  v_possede := exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = p.article_id);

  for r in select * from pass_recompenses rr where rr.saison = p.saison
            and (p_niveau is null or rr.niveau = p_niveau) order by rr.niveau loop
    if r.type = 'paquet' then   -- s3-13 : un paquet s'ouvre avec pass_ouvrir_paquet
      if p_niveau is not null then raise exception 'Ce paquet s''ouvre depuis le pass'; end if;
      continue;
    end if;
    if p_niveau is not null then
      if r.niveau > v_niv then raise exception 'Niveau pas encore atteint'; end if;
      if r.payant and not v_possede then raise exception 'Cette récompense est dans le pass'; end if;
      if not r.dispo then raise exception 'Cette récompense arrive bientôt'; end if;
      if exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = p.saison and c.niveau = r.niveau) then
        raise exception 'Récompense déjà récupérée';
      end if;
    else
      continue when r.niveau > v_niv or (r.payant and not v_possede) or not r.dispo
                 or exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = p.saison and c.niveau = r.niveau);
    end if;

    if r.type = 'tp' then
      perform set_config('terrafront.motif', 'pass', true);
      update joueurs set solde = coalesce(solde, 0) + r.quantite where id = v_uid;
    elsif r.type = 'energie' then
      select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
      update joueurs set front_energie = least(front_energie_reglage('plafond'), v + r.quantite), front_energie_maj = now() where id = v_uid;
    elsif r.type = 'lingots' then   -- s3-13 : jusqu'au plafond de la réserve, le reste en TP (taux du Mess)
      l := lingots_figer(v_uid);
      l2 := greatest(l, least(lingots_max(v_uid), l + r.quantite));
      v_donne := greatest(0, floor(l2) - floor(l))::integer;
      update joueurs set lingots = l2 where id = v_uid;
      if v_donne < r.quantite then
        v_repli := v_repli + (r.quantite - v_donne) * coalesce((mess_cfg() -> 'ration' ->> 'tp_par_lingot')::integer, 15);
      end if;
    elsif r.type in ('dos', 'habillage', 'skin') then
      insert into euros_inventaire(joueur_id, article_id) values (v_uid, r.valeur) on conflict do nothing;
    end if;   -- un titre : rien à faire, titres_possibles lit pass_reclames
    insert into pass_reclames(joueur_id, saison, niveau) values (v_uid, p.saison, r.niveau);
    n := n + 1;
  end loop;
  if v_repli > 0 then
    perform set_config('terrafront.motif', 'pass', true);
    update joueurs set solde = coalesce(solde, 0) + v_repli where id = v_uid;
  end if;
  if p_niveau is null and n = 0 then raise exception 'Rien à réclamer pour l''instant'; end if;
  return pass_etat() || jsonb_build_object('reclamees', n, 'tp_repli', v_repli);
end;
$function$;

-- ---------- ouvrir un paquet gagné dans le pass ----------
-- Même tirage que boutique_ouvrir_paquet (paquet garanti, paquet du département),
-- sans prix et hors des 3 paquets de boutique par jour. Les cartes sont rangées
-- comme des cartes de boutique (origine 'boutique').
create or replace function public.pass_ouvrir_paquet(p_niveau integer, p_departement text default null::text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  p pass_saisons%rowtype;
  r pass_recompenses%rowtype;
  v_niv integer;
  x record;
  res jsonb := '[]'::jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from pass_recent();
  if p.saison is null then raise exception 'Pas de pass en cours'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into r from pass_recompenses rr where rr.saison = p.saison and rr.niveau = p_niveau;
  if not found or r.type <> 'paquet' then raise exception 'Pas de paquet à ce niveau'; end if;
  select least(p.niveaux, coalesce(sum(xx.quetes + xx.actions), 0)::integer / p.xp_niveau) into v_niv
    from pass_xp xx where xx.joueur_id = v_uid and xx.saison = p.saison;
  if r.niveau > v_niv then raise exception 'Niveau pas encore atteint'; end if;
  if r.payant and not exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = p.article_id) then
    raise exception 'Cette récompense est dans le pass';
  end if;
  if not r.dispo then raise exception 'Cette récompense arrive bientôt'; end if;
  if exists(select 1 from pass_reclames c where c.joueur_id = v_uid and c.saison = p.saison and c.niveau = r.niveau) then
    raise exception 'Récompense déjà récupérée';
  end if;
  if r.valeur = 'paquet-departement' then
    if p_departement is null or not exists(select 1 from communes c where c.departement = p_departement)
       or est_canton(p_departement) then
      raise exception 'Choisis un departement';
    end if;
  elsif r.valeur is distinct from 'paquet-garanti' then
    raise exception 'Paquet inconnu';
  end if;

  insert into pass_reclames(joueur_id, saison, niveau) values (v_uid, p.saison, r.niveau);

  for x in
    with tirage as (
      select t.code from (
        (select c.code from communes c
          where r.valeur = 'paquet-departement' and c.departement = p_departement
          order by random() limit 5)
        union all
        (select c.code from (select c2.code from communes c2
                              where r.valeur = 'paquet-garanti' and c2.tier in ('rare', 'epique', 'legendaire') and not est_canton(c2.departement)
                              order by random() limit 1) c)
        union all
        (select c.code from (select c3.code from communes c3
                              where r.valeur = 'paquet-garanti' and not est_canton(c3.departement)
                              order by random() limit 4) c)
      ) t
    ), compte as (
      select tirage.code, count(*)::integer n,
             (count(*) filter (where aurore_tirage(tirage.code)))::integer naur
        from tirage group by tirage.code
    ), avant as (
      select t.commune_code, t.exemplaires from terra_collection t
       where t.joueur_id = v_uid and t.commune_code in (select compte.code from compte)
    ), ajout as (
      insert into terra_collection as tc (joueur_id, commune_code, exemplaires, aurore, origine)
      select v_uid, compte.code, compte.n, compte.naur, 'boutique' from compte
      on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + excluded.exemplaires,
                                                          aurore = tc.aurore + excluded.aurore
      returning tc.commune_code, tc.exemplaires
    )
    select c.code::text as code, c.nom::text as nom, c.departement::text as departement, c.tier::text as tier,
           c.population::integer as population, coalesce(av.exemplaires, 0) = 0 as nouvelle,
           a2.exemplaires::integer as exemplaires, c.rang::integer as rang, c.palier_total::integer as palier_total,
           c.latitude::double precision as latitude, c.longitude::double precision as longitude, co.naur > 0 as aurore
      from ajout a2
      join communes c on c.code = a2.commune_code
      join compte co on co.code = a2.commune_code
      left join avant av on av.commune_code = a2.commune_code
  loop
    res := res || jsonb_build_array(to_jsonb(x) || jsonb_build_object('brillante', brillante_tirer(v_uid, x.code, 'boutique')));
  end loop;
  return res;
end;
$function$;

-- ---------- les niveaux bonus ----------
create or replace function public.pass_bonus_reclamer()
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  p pass_saisons%rowtype;
  v_xp integer; v_dus integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from pass_recent();
  if p.saison is null then raise exception 'Pas de pass en cours'; end if;
  if coalesce(p.bonus_xp, 0) <= 0 or coalesce(p.bonus_tp, 0) <= 0 then raise exception 'Pas de niveaux bonus cette saison'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select coalesce(sum(x.quetes + x.actions), 0)::integer into v_xp from pass_xp x where x.joueur_id = v_uid and x.saison = p.saison;
  v_dus := greatest(0, (v_xp - p.niveaux * p.xp_niveau) / p.bonus_xp
             - coalesce((select b.n from pass_bonus b where b.joueur_id = v_uid and b.saison = p.saison), 0));
  if v_dus = 0 then raise exception 'Rien à réclamer pour l''instant'; end if;
  insert into pass_bonus as b (joueur_id, saison, n) values (v_uid, p.saison, v_dus)
  on conflict (joueur_id, saison) do update set n = b.n + excluded.n, maj = now();
  perform set_config('terrafront.motif', 'pass', true);
  update joueurs set solde = coalesce(solde, 0) + v_dus * p.bonus_tp where id = v_uid;
  return pass_etat() || jsonb_build_object('bonus_reclames', v_dus, 'bonus_gain', v_dus * p.bonus_tp);
end;
$function$;

revoke all on function public.pass_ouvrir_paquet(integer, text) from public, anon;
revoke all on function public.pass_bonus_reclamer() from public, anon;
grant execute on function public.pass_ouvrir_paquet(integer, text) to authenticated, service_role;
grant execute on function public.pass_bonus_reclamer() to authenticated, service_role;

select (select count(*) from public.pass_recompenses where saison = 'saison-3') as recompenses,
       (select count(*) from public.pass_recompenses where saison = 'saison-3' and payant) as payantes,
       (select debut is not null from public.pass_saisons where saison = 'saison-3') as ouvert,
       (select actif from public.euros_articles where id = 'pass-s3') as en_vente;
