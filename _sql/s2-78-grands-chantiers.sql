-- ===========================================================================
--  TerraFront — s2-78 : les grands chantiers (module Monuments, Terra)
--  Décidé avec Nataël le 2/11/2026 (aperçu « Les grands chantiers » validé,
--  Tour Eiffel comprise).
--
--  Pourquoi restaurer (ressorts 1, 2 et 4 retenus) :
--    1. les visiteurs : un monument restauré rapporte des TP chaque jour ;
--    2. le nom gravé : le premier à restaurer un monument y laisse son nom ;
--    4. les merveilles : une à la fois pour tout le jeu, restaurée à plusieurs.
--
--  Règles :
--   - il faut avoir la commune du monument dans sa collection Terra ;
--     un chantier à la fois ; on peut l'abandonner (le travail est perdu) ;
--   - taille selon la notoriété (versions linguistiques de Wikipédia) :
--     grand à partir de 45 langues, moyen à partir de 30, petit en dessous ;
--     travail : petit 18 h, moyen 72 h, grand 216 h, soit 6 h, 1 jour et
--     3 jours avec l'équipe de départ (3 ouvriers) ;
--   - rythme de l'équipe = ouvriers x (1 + 15 % par niveau d'outils au-dessus
--     du premier) heures de travail par heure ;
--     un ouvrier de plus : 150 TP, puis x 1,5 à chaque fois (8 au plus) ;
--     outils : 200, 400, 800, 1 600 TP (niveau 5 au plus) ;
--   - le chantier avance tout seul, calculé par le serveur (heure de départ
--     et rythme) ; il se termine à l'heure prévue, même si personne ne
--     regarde ;
--   - nom gravé : le premier joueur dont le chantier se termine (à l'heure
--     de fin, pas à l'heure où il ouvre le jeu) ;
--   - visiteurs : petit 10, moyen 25, grand 60 TP par jour, 300 au plus par
--     jour ; ils s'accumulent jusqu'à une journée de recette, à récolter ;
--   - merveilles : une seule ouverte à la fois, 20 000 h de travail.
--     Envoyer son équipe met son propre chantier en pause. Mécène = au moins
--     24 h de travail données : +20 TP par jour (dans le plafond de 300).
--     Les 10 plus gros contributeurs sont gravés. À la fin, les équipes
--     reviennent sur leur chantier et la merveille suivante ouvre aussitôt.
--
--  Ouverture : config_jeu 'chantiers', « ouvert » à 0 au départ : seuls les
--  comptes testeurs (ceux de la boutique) y ont accès. Pour ouvrir à tout le
--  monde : s2-78b-chantiers-ouvrir.sql (il efface aussi les essais).
--
--  Fonctions pour le jeu (authenticated), toutes rendent l'état complet :
--    chantiers_etat()                 l'état (et termine ce qui doit l'être)
--    chantier_commencer(p_code)       démarre un chantier
--    chantier_abandonner()            abandonne le chantier en cours
--    chantier_inaugurer(p_code)       marque l'inauguration (vue par le joueur)
--    chantiers_recolter()             récolte les visiteurs
--    chantiers_embaucher()            un ouvrier de plus
--    chantiers_outils()               un niveau d'outils de plus
--    merveille_equipe(p_envoyer)      envoie l'équipe sur la merveille ou la rappelle
--
--  Rejouable. Finit par un contrôle (une ligne).
-- ===========================================================================
begin;

-- ---------------------------------------------------------------------------
--  Réglages
-- ---------------------------------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('chantiers', '{"ouvert": 0,
  "travail": {"petit": 18, "moyen": 72, "grand": 216},
  "visiteurs": {"petit": 10, "moyen": 25, "grand": 60},
  "plafond": 300, "ouvriers": 3, "ouvriers_max": 8, "outils_max": 5,
  "cout_ouvrier": 150, "cout_ouvrier_x": 1.5, "cout_outils": 200,
  "merveille": 20000, "mecene": 24, "mecene_tp": 20, "graves": 10}')
on conflict (cle) do nothing;

create or replace function public.chantiers_reglages()
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'chantiers'), '{}'::jsonb);
$f$;

-- ---------------------------------------------------------------------------
--  Tables
-- ---------------------------------------------------------------------------
-- Les monuments qui ont un chantier, et leur dessin
create table if not exists public.chantiers_monuments(
  commune_code text primary key references public.monuments(commune_code) on delete cascade,
  dessin       text not null,
  taille       text not null check (taille in ('petit', 'moyen', 'grand', 'merveille')),
  ordre        integer          -- merveilles : ordre d'ouverture
);

-- L'équipe de chaque joueur, et sa réserve de visiteurs
create table if not exists public.chantiers_equipes(
  joueur_id     uuid primary key references public.joueurs(id) on delete cascade,
  ouvriers      integer not null default 3,
  outils        integer not null default 1,
  stock         numeric not null default 0,      -- TP de visiteurs pas encore récoltés
  stock_maj     timestamptz not null default now(),
  recolte_total integer not null default 0,
  cree_le       timestamptz not null default now()
);

-- Le chantier en cours (un par joueur)
create table if not exists public.chantiers(
  joueur_id    uuid primary key references public.joueurs(id) on delete cascade,
  commune_code text not null references public.chantiers_monuments(commune_code),
  travail      numeric not null,                 -- heures de travail à fournir
  fait         numeric not null default 0,       -- heures faites jusqu'à « depuis »
  depuis       timestamptz not null default now(),
  en_pause     boolean not null default false,   -- équipe sur la merveille
  fin_prevue   timestamptz,                      -- null pendant la pause
  commence_le  timestamptz not null default now()
);
create index if not exists chantiers_fin_prevue on public.chantiers(fin_prevue) where fin_prevue is not null;

-- Les monuments restaurés (chacun restaure chez lui ; le premier est gravé)
create table if not exists public.chantiers_restaurations(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  commune_code text not null references public.chantiers_monuments(commune_code),
  restaure_le  timestamptz not null,
  premier      boolean not null default false,
  inaugure     boolean not null default false,
  primary key (joueur_id, commune_code)
);
create unique index if not exists chantiers_restaurations_premier
  on public.chantiers_restaurations(commune_code) where premier;

-- Les merveilles ouvertes ou finies (une seule ouverte à la fois)
create table if not exists public.chantiers_merveilles(
  commune_code text primary key references public.chantiers_monuments(commune_code),
  total        numeric not null,
  ouverte_le   timestamptz not null default now(),
  finie_le     timestamptz
);
create unique index if not exists chantiers_merveilles_une_ouverte
  on public.chantiers_merveilles((true)) where finie_le is null;

-- Ce que chaque équipe a donné à une merveille
create table if not exists public.chantiers_mecenes(
  merveille  text not null references public.chantiers_merveilles(commune_code) on delete cascade,
  joueur_id  uuid not null references public.joueurs(id) on delete cascade,
  heures     numeric not null default 0,         -- jusqu'à « depuis »
  depuis     timestamptz not null default now(),
  actif      boolean not null default false,     -- l'équipe y est en ce moment
  rythme     numeric not null default 0,         -- heures de travail par heure, quand actif
  primary key (merveille, joueur_id)
);
create index if not exists chantiers_mecenes_joueur on public.chantiers_mecenes(joueur_id);

alter table public.chantiers_monuments     enable row level security;
alter table public.chantiers_equipes       enable row level security;
alter table public.chantiers               enable row level security;
alter table public.chantiers_restaurations enable row level security;
alter table public.chantiers_merveilles    enable row level security;
alter table public.chantiers_mecenes       enable row level security;
revoke all on public.chantiers_monuments, public.chantiers_equipes, public.chantiers,
              public.chantiers_restaurations, public.chantiers_merveilles, public.chantiers_mecenes
  from public, anon, authenticated;

-- ---------------------------------------------------------------------------
--  Les monuments à restaurer : dessin, et taille selon la notoriété
--  (les codes absents de la table monuments sont ignorés)
-- ---------------------------------------------------------------------------
with liste(code, dessin, ordre) as (values
  -- les 10 merveilles, dans l'ordre d'ouverture
  ('75104', 'notredame', 1), ('50353', 'mont', 2), ('78646', 'versailles', 3), ('75107', 'eiffel', 4),
  ('41034', 'chambord', 5), ('11069', 'carcassonne', 6), ('30346', 'gard', 7), ('75117', 'arc', 8),
  ('37110', 'chenonceau', 9), ('12145', 'millau', 10),
  -- dessins propres
  ('33544', 'phare', null), ('70451', 'ronchamp', null),
  -- châteaux Renaissance
  ('49219', 'chateau', null), ('77186', 'chateau', null), ('41018', 'chateau', null), ('37003', 'chateau', null),
  ('78551', 'chateau', null), ('37014', 'chateau', null), ('37272', 'chateau', null), ('60141', 'chateau', null),
  ('92063', 'chateau', null), ('49328', 'chateau', null), ('37197', 'chateau', null), ('37123', 'chateau', null),
  ('41045', 'chateau', null), ('41050', 'chateau', null), ('36228', 'chateau', null), ('49050', 'chateau', null),
  -- châteaux forts
  ('84007', 'fort', null), ('94080', 'fort', null), ('17004', 'fort', null), ('37072', 'fort', null),
  ('49007', 'fort', null), ('67362', 'fort', null), ('60491', 'fort', null), ('27016', 'fort', null),
  ('37132', 'fort', null), ('02217', 'fort', null), ('09211', 'fort', null), ('09122', 'fort', null),
  ('89420', 'fort', null), ('45315', 'fort', null), ('25056', 'fort', null),
  -- palais classiques
  ('75108', 'palais', null), ('77269', 'palais', null), ('25021', 'palais', null), ('54395', 'palais', null),
  ('69381', 'palais', null), ('69123', 'palais', null), ('92064', 'palais', null), ('78517', 'palais', null),
  -- cathédrales gothiques
  ('28085', 'cathedrale', null), ('51454', 'cathedrale', null), ('75101', 'cathedrale', null), ('80021', 'cathedrale', null),
  ('18033', 'cathedrale', null), ('67482', 'cathedrale', null), ('60057', 'cathedrale', null), ('02408', 'cathedrale', null),
  ('81004', 'cathedrale', null), ('65286', 'cathedrale', null), ('69385', 'cathedrale', null), ('57463', 'cathedrale', null),
  ('24520', 'cathedrale', null), ('37261', 'cathedrale', null), ('45234', 'cathedrale', null), ('63113', 'cathedrale', null),
  ('89387', 'cathedrale', null), ('60471', 'cathedrale', null), ('87085', 'cathedrale', null), ('71014', 'cathedrale', null),
  ('11262', 'cathedrale', null), ('29232', 'cathedrale', null),
  -- églises à dôme
  ('75105', 'dome', null), ('75118', 'dome', null), ('13206', 'dome', null), ('13202', 'dome', null), ('24322', 'dome', null),
  -- abbayes romanes
  ('71137', 'abbaye', null), ('89446', 'abbaye', null), ('21389', 'abbaye', null), ('86246', 'abbaye', null),
  ('49140', 'abbaye', null), ('10426', 'abbaye', null), ('21564', 'abbaye', null), ('78356', 'abbaye', null),
  ('38442', 'abbaye', null), ('45270', 'abbaye', null), ('73273', 'abbaye', null), ('38469', 'abbaye', null),
  ('84050', 'abbaye', null), ('76378', 'abbaye', null), ('16015', 'abbaye', null),
  -- monuments antiques
  ('30189', 'antique', null), ('84087', 'antique', null), ('06150', 'antique', null), ('13004', 'antique', null),
  -- édifices à beffroi
  ('75103', 'edifice', null), ('92072', 'edifice', null), ('2A004', 'edifice', null)
)
insert into public.chantiers_monuments (commune_code, dessin, taille, ordre)
select l.code, l.dessin,
       case when l.ordre is not null then 'merveille'
            when coalesce(m.langues, 0) >= 45 then 'grand'
            when coalesce(m.langues, 0) >= 30 then 'moyen'
            else 'petit' end,
       l.ordre
  from liste l
  join public.monuments m on m.commune_code = l.code
on conflict (commune_code) do update
   set dessin = excluded.dessin, taille = excluded.taille, ordre = excluded.ordre;

-- ---------------------------------------------------------------------------
--  Petites fonctions internes
-- ---------------------------------------------------------------------------
-- qui a accès : tout le monde quand c'est ouvert, sinon les comptes testeurs
create or replace function public.chantiers_permis(p_uid uuid)
 returns boolean language plpgsql stable security definer set search_path to 'public' as $f$
declare
  g jsonb := chantiers_reglages();
  t jsonb;
begin
  if p_uid is null or not terra_ouverte() then return false; end if;
  if coalesce((g->>'ouvert')::int, 0) = 1 then return true; end if;
  if coalesce(g->'testeurs', '[]'::jsonb) ? p_uid::text then return true; end if;
  begin
    execute 'select public.euros_reglage(''testeurs'')' into t;
  exception when others then t := null;
  end;
  return coalesce(t, '[]'::jsonb) ? p_uid::text;
end; $f$;

-- heures de travail par heure
create or replace function public.chantiers_rythme(p_ouvriers integer, p_outils integer)
 returns numeric language sql immutable as $f$
  select greatest(1, p_ouvriers) * (1 + 0.15 * (greatest(1, p_outils) - 1))::numeric;
$f$;

create or replace function public.chantiers_cout_ouvrier(p_ouvriers integer)
 returns integer language sql stable security definer set search_path to 'public' as $f$
  with g as (select chantiers_reglages() as r)
  select case when p_ouvriers >= coalesce((r->>'ouvriers_max')::int, 8) then null
              else (round(coalesce((r->>'cout_ouvrier')::numeric, 150)
                          * power(coalesce((r->>'cout_ouvrier_x')::numeric, 1.5), greatest(0, p_ouvriers - coalesce((r->>'ouvriers')::int, 3))) / 5) * 5)::integer end
    from g;
$f$;

create or replace function public.chantiers_cout_outils(p_outils integer)
 returns integer language sql stable security definer set search_path to 'public' as $f$
  with g as (select chantiers_reglages() as r)
  select case when p_outils >= coalesce((r->>'outils_max')::int, 5) then null
              else (coalesce((r->>'cout_outils')::numeric, 200) * power(2::numeric, greatest(0, p_outils - 1)::numeric))::integer end
    from g;
$f$;

create or replace function public.chantiers_equipe_creer(p_uid uuid)
 returns void language sql security definer set search_path to 'public' as $f$
  insert into chantiers_equipes (joueur_id, ouvriers)
  values (p_uid, coalesce((chantiers_reglages()->>'ouvriers')::int, 3))
  on conflict (joueur_id) do nothing;
$f$;

-- recette brute des visiteurs (TP par jour, sans plafond)
create or replace function public.chantiers_recette_brute(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  with g as (select chantiers_reglages() as r)
  select coalesce((select sum(coalesce((g.r->'visiteurs'->>m.taille)::numeric, 0))
                     from chantiers_restaurations x
                     join chantiers_monuments m on m.commune_code = x.commune_code
                    where x.joueur_id = p_uid), 0)
       + coalesce((select count(*)
                     from chantiers_mecenes c
                     join chantiers_merveilles mv on mv.commune_code = c.merveille
                    where c.joueur_id = p_uid and mv.finie_le is not null
                      and c.heures >= coalesce((g.r->>'mecene')::numeric, 24)), 0)
         * coalesce((g.r->>'mecene_tp')::numeric, 20)
    from g;
$f$;

-- recette plafonnée (TP par jour) : c'est aussi la taille de la réserve
create or replace function public.chantiers_taux(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  select least(coalesce((chantiers_reglages()->>'plafond')::numeric, 300), chantiers_recette_brute(p_uid));
$f$;

-- arrête la réserve de visiteurs à maintenant (avant que la recette change)
create or replace function public.chantiers_regler_stock(p_uid uuid)
 returns void language plpgsql security definer set search_path to 'public' as $f$
declare
  v_taux numeric := chantiers_taux(p_uid);
begin
  perform chantiers_equipe_creer(p_uid);
  update chantiers_equipes
     set stock = least(v_taux, stock + v_taux * greatest(0, extract(epoch from now() - stock_maj)) / 86400.0),
         stock_maj = now()
   where joueur_id = p_uid;
end; $f$;

-- arrête le chantier et la contribution à maintenant (avant que le rythme change)
create or replace function public.chantiers_regler(p_uid uuid)
 returns void language plpgsql security definer set search_path to 'public' as $f$
declare
  v_r numeric;
begin
  select chantiers_rythme(e.ouvriers, e.outils) into v_r from chantiers_equipes e where e.joueur_id = p_uid;
  if v_r is null then return; end if;
  update chantiers
     set fait = least(travail, fait + v_r * greatest(0, extract(epoch from now() - depuis)) / 3600.0),
         depuis = now()
   where joueur_id = p_uid and not en_pause;
  update chantiers_mecenes
     set heures = heures + rythme * greatest(0, extract(epoch from now() - depuis)) / 3600.0,
         depuis = now()
   where joueur_id = p_uid and actif;
end; $f$;

-- applique le rythme actuel de l'équipe (après chantiers_regler)
create or replace function public.chantiers_rythme_appliquer(p_uid uuid)
 returns void language plpgsql security definer set search_path to 'public' as $f$
declare
  v_r numeric;
begin
  select chantiers_rythme(e.ouvriers, e.outils) into v_r from chantiers_equipes e where e.joueur_id = p_uid;
  if v_r is null then return; end if;
  update chantiers
     set fin_prevue = depuis + make_interval(secs => (greatest(0, travail - fait) / v_r * 3600.0)::double precision)
   where joueur_id = p_uid and not en_pause;
  update chantiers_mecenes set rythme = v_r where joueur_id = p_uid and actif;
end; $f$;

-- ---------------------------------------------------------------------------
--  Le finisseur : termine la merveille et les chantiers dont l'heure est
--  passée, dans l'ordre où ils ont fini (c'est ce qui décide du nom gravé).
--  Appelé au début de chaque fonction : il suffit que quelqu'un joue.
-- ---------------------------------------------------------------------------
create or replace function public.chantiers_finaliser()
 returns void language plpgsql security definer set search_path to 'public' as $f$
declare
  g jsonb := chantiers_reglages();
  m chantiers_merveilles%rowtype;
  r record;
  v_total numeric;
  v_rythme numeric;
  v_fin timestamptz;
begin
  perform pg_advisory_xact_lock(780078);

  -- 1) la merveille du moment
  select * into m from chantiers_merveilles where finie_le is null limit 1;
  if m.commune_code is not null then
    select coalesce(sum(c.heures + case when c.actif then c.rythme * greatest(0, extract(epoch from now() - c.depuis)) / 3600.0 else 0 end), 0),
           coalesce(sum(case when c.actif then c.rythme else 0 end), 0)
      into v_total, v_rythme
      from chantiers_mecenes c where c.merveille = m.commune_code;
    if v_total >= m.total then
      v_fin := now() - make_interval(secs => (case when v_rythme > 0 then (v_total - m.total) / v_rythme * 3600.0 else 0 end)::double precision);
      if v_fin < m.ouverte_le then v_fin := m.ouverte_le; end if;
      -- les heures s'arrêtent à la fin de la merveille
      update chantiers_mecenes c
         set heures = c.heures + case when c.actif then c.rythme * greatest(0, extract(epoch from v_fin - c.depuis)) / 3600.0 else 0 end,
             depuis = v_fin, actif = false
       where c.merveille = m.commune_code;
      -- les mécènes gagnent une recette : on arrête d'abord leur réserve
      for r in select c.joueur_id from chantiers_mecenes c
                where c.merveille = m.commune_code and c.heures >= coalesce((g->>'mecene')::numeric, 24) loop
        perform chantiers_regler_stock(r.joueur_id);
      end loop;
      update chantiers_merveilles set finie_le = v_fin where commune_code = m.commune_code;
      -- les équipes reviennent : leurs chantiers reprennent à la fin de la merveille
      update chantiers ch
         set en_pause = false, depuis = v_fin,
             fin_prevue = v_fin + make_interval(secs => (greatest(0, ch.travail - ch.fait) / chantiers_rythme(e.ouvriers, e.outils) * 3600.0)::double precision)
        from chantiers_equipes e
       where e.joueur_id = ch.joueur_id and ch.en_pause;
      -- la suivante ouvre aussitôt
      insert into chantiers_merveilles (commune_code, total, ouverte_le)
      select cm.commune_code, coalesce((g->>'merveille')::numeric, 20000), v_fin
        from chantiers_monuments cm
       where cm.taille = 'merveille'
         and not exists (select 1 from chantiers_merveilles x where x.commune_code = cm.commune_code)
       order by cm.ordre nulls last, cm.commune_code
       limit 1;
    end if;
  end if;

  -- 2) les chantiers terminés, dans l'ordre de leur fin
  for r in select ch.* from chantiers ch
            where ch.fin_prevue is not null and ch.fin_prevue <= now()
            order by ch.fin_prevue, ch.joueur_id loop
    perform chantiers_regler_stock(r.joueur_id);
    insert into chantiers_restaurations (joueur_id, commune_code, restaure_le, premier)
    values (r.joueur_id, r.commune_code, r.fin_prevue,
            not exists (select 1 from chantiers_restaurations x where x.commune_code = r.commune_code and x.premier))
    on conflict (joueur_id, commune_code) do nothing;
    delete from chantiers where joueur_id = r.joueur_id;
  end loop;
end; $f$;

-- ---------------------------------------------------------------------------
--  L'état complet, pour le jeu
-- ---------------------------------------------------------------------------
create or replace function public.chantiers_etat_json(p_uid uuid)
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  g jsonb := chantiers_reglages();
  e chantiers_equipes%rowtype;
  v_r numeric;
  v_mecene numeric := coalesce((g->>'mecene')::numeric, 24);
  v_graves integer := coalesce((g->>'graves')::int, 10);
  v_merv jsonb;
  m chantiers_merveilles%rowtype;
begin
  select * into e from chantiers_equipes where joueur_id = p_uid;
  if e.joueur_id is null then
    e.ouvriers := coalesce((g->>'ouvriers')::int, 3); e.outils := 1; e.stock := 0; e.stock_maj := now();
  end if;
  v_r := chantiers_rythme(e.ouvriers, e.outils);

  select * into m from chantiers_merveilles where finie_le is null limit 1;
  if m.commune_code is not null then
    with c as (
      select c.joueur_id, j.pseudo,
             c.heures + case when c.actif then c.rythme * greatest(0, extract(epoch from now() - c.depuis)) / 3600.0 else 0 end as h,
             c.actif, c.rythme
        from chantiers_mecenes c left join joueurs j on j.id = c.joueur_id
       where c.merveille = m.commune_code
    ), rangs as (
      select c.*, row_number() over (order by c.h desc, c.joueur_id) as rang from c where c.h > 0 or c.actif
    )
    select jsonb_build_object(
             'code', m.commune_code, 'total', m.total, 'ouverte_le', m.ouverte_le,
             'fait', round(coalesce((select sum(h) from c), 0), 3),
             'rythme', round(coalesce((select sum(rythme) from c where actif), 0), 4),
             'equipes', (select count(*) from rangs),
             'actives', (select count(*) from c where actif),
             'mecenes', (select count(*) from c where h >= v_mecene),
             'moi', (select jsonb_build_object('heures', round(h, 3), 'actif', actif, 'rythme', rythme, 'rang', rang)
                       from rangs where joueur_id = p_uid),
             'top', coalesce((select jsonb_agg(jsonb_build_object('pseudo', coalesce(pseudo, 'un joueur'), 'heures', round(h, 1),
                                                                  'moi', joueur_id = p_uid, 'rang', rang) order by rang)
                                from rangs where rang <= v_graves), '[]'::jsonb))
      into v_merv;
  end if;

  return jsonb_build_object(
    'permis', true,
    'ouvert', coalesce((g->>'ouvert')::int, 0) = 1,
    'maintenant', now(),
    'solde', (select j.solde from joueurs j where j.id = p_uid),
    'regles', jsonb_build_object(
       'travail', g->'travail', 'visiteurs', g->'visiteurs',
       'plafond', coalesce((g->>'plafond')::int, 300),
       'ouvriers_max', coalesce((g->>'ouvriers_max')::int, 8), 'outils_max', coalesce((g->>'outils_max')::int, 5),
       'merveille', coalesce((g->>'merveille')::int, 20000), 'mecene', v_mecene,
       'mecene_tp', coalesce((g->>'mecene_tp')::int, 20), 'graves', v_graves),
    'equipe', jsonb_build_object('ouvriers', e.ouvriers, 'outils', e.outils, 'rythme', round(v_r, 4),
       'cout_ouvrier', chantiers_cout_ouvrier(e.ouvriers), 'cout_outils', chantiers_cout_outils(e.outils)),
    'chantier', (select jsonb_build_object('code', ch.commune_code, 'travail', ch.travail, 'fait', round(ch.fait, 4),
                         'depuis', ch.depuis, 'en_pause', ch.en_pause, 'fin_prevue', ch.fin_prevue, 'commence_le', ch.commence_le)
                   from chantiers ch where ch.joueur_id = p_uid),
    'visiteurs', jsonb_build_object('par_jour', chantiers_taux(p_uid), 'brut', chantiers_recette_brute(p_uid),
       'stock', round(e.stock, 4), 'stock_maj', e.stock_maj, 'recolte_total', coalesce(e.recolte_total, 0)),
    'restaurations', coalesce((select jsonb_agg(jsonb_build_object('code', x.commune_code, 'le', x.restaure_le,
                                  'premier', x.premier, 'inaugure', x.inaugure) order by x.restaure_le)
                                 from chantiers_restaurations x where x.joueur_id = p_uid), '[]'::jsonb),
    'monuments', coalesce((select jsonb_agg(jsonb_build_object(
                     'code', cm.commune_code, 'embleme', mo.nom, 'commune', co.nom, 'dept', co.departement,
                     'dessin', cm.dessin, 'taille', cm.taille, 'ordre', cm.ordre, 'langues', mo.langues,
                     'a_moi', exists (select 1 from terra_collection t where t.joueur_id = p_uid
                                        and t.commune_code = cm.commune_code and t.exemplaires > 0),
                     'graveur', (select coalesce(j.pseudo, 'un joueur') from chantiers_restaurations x
                                   left join joueurs j on j.id = x.joueur_id
                                  where x.commune_code = cm.commune_code and x.premier),
                     'grave_le', (select x.restaure_le from chantiers_restaurations x
                                   where x.commune_code = cm.commune_code and x.premier)
                   ) order by cm.ordre nulls last, mo.langues desc nulls last, cm.commune_code)
                   from chantiers_monuments cm
                   join monuments mo on mo.commune_code = cm.commune_code
                   join communes co on co.code = cm.commune_code), '[]'::jsonb),
    'merveille', v_merv,
    'merveilles_finies', coalesce((select jsonb_agg(jsonb_build_object(
                     'code', mv.commune_code, 'finie_le', mv.finie_le,
                     'mes_heures', coalesce((select round(c.heures, 1) from chantiers_mecenes c
                                              where c.merveille = mv.commune_code and c.joueur_id = p_uid), 0),
                     'mecenes', (select count(*) from chantiers_mecenes c where c.merveille = mv.commune_code and c.heures >= v_mecene),
                     'graves', coalesce((select jsonb_agg(z.pseudo order by z.heures desc, z.joueur_id)
                                           from (select c.joueur_id, c.heures, coalesce(j.pseudo, 'un joueur') as pseudo
                                                   from chantiers_mecenes c left join joueurs j on j.id = c.joueur_id
                                                  where c.merveille = mv.commune_code and c.heures > 0
                                                  order by c.heures desc, c.joueur_id limit v_graves) z), '[]'::jsonb)
                   ) order by mv.finie_le)
                   from chantiers_merveilles mv where mv.finie_le is not null), '[]'::jsonb)
  );
end; $f$;

-- ---------------------------------------------------------------------------
--  Les fonctions du jeu
-- ---------------------------------------------------------------------------
create or replace function public.chantiers_etat()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then return jsonb_build_object('permis', false); end if;
  perform chantiers_finaliser();
  return chantiers_etat_json(v_uid);
end; $f$;

create or replace function public.chantier_commencer(p_code text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  g jsonb := chantiers_reglages();
  cm chantiers_monuments%rowtype;
  e chantiers_equipes%rowtype;
  v_r numeric;
  v_travail numeric;
  v_pause boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  select * into cm from chantiers_monuments where commune_code = p_code;
  if cm.commune_code is null then raise exception 'Ce monument n''a pas de chantier'; end if;
  if cm.taille = 'merveille' then raise exception 'Une merveille se restaure à plusieurs : envoie ton équipe sur la merveille du moment'; end if;
  if not exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = p_code and t.exemplaires > 0) then
    raise exception 'Il faut d''abord avoir % dans ta collection Terra', (select c.nom from communes c where c.code = p_code);
  end if;
  if exists (select 1 from chantiers_restaurations x where x.joueur_id = v_uid and x.commune_code = p_code) then
    raise exception 'Tu as déjà restauré ce monument';
  end if;
  perform chantiers_equipe_creer(v_uid);
  select * into e from chantiers_equipes where joueur_id = v_uid for update;
  if exists (select 1 from chantiers ch where ch.joueur_id = v_uid) then
    raise exception 'Tu as déjà un chantier en cours : termine-le ou abandonne-le d''abord';
  end if;
  v_r := chantiers_rythme(e.ouvriers, e.outils);
  v_travail := coalesce((g->'travail'->>cm.taille)::numeric, 72);
  v_pause := exists (select 1 from chantiers_mecenes c where c.joueur_id = v_uid and c.actif);
  insert into chantiers (joueur_id, commune_code, travail, fait, depuis, en_pause, fin_prevue)
  values (v_uid, p_code, v_travail, 0, now(), v_pause,
          case when v_pause then null else now() + make_interval(secs => (v_travail / v_r * 3600.0)::double precision) end);
  return chantiers_etat_json(v_uid);
end; $f$;

create or replace function public.chantier_abandonner()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  delete from chantiers where joueur_id = v_uid;
  return chantiers_etat_json(v_uid);
end; $f$;

create or replace function public.chantier_inaugurer(p_code text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  update chantiers_restaurations set inaugure = true where joueur_id = v_uid and commune_code = p_code;
  return chantiers_etat_json(v_uid);
end; $f$;

create or replace function public.chantiers_recolter()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  e chantiers_equipes%rowtype;
  v_taux numeric;
  v_stock numeric;
  v_n integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  perform chantiers_equipe_creer(v_uid);
  select * into e from chantiers_equipes where joueur_id = v_uid for update;
  v_taux := chantiers_taux(v_uid);
  v_stock := least(v_taux, e.stock + v_taux * greatest(0, extract(epoch from now() - e.stock_maj)) / 86400.0);
  v_n := floor(v_stock);
  if v_n < 1 then raise exception 'Rien à récolter pour l''instant'; end if;
  update chantiers_equipes
     set stock = v_stock - v_n, stock_maj = now(), recolte_total = recolte_total + v_n
   where joueur_id = v_uid;
  perform set_config('terrafront.motif', 'chantier_visiteurs', true);
  update joueurs set solde = coalesce(solde, 0) + v_n where id = v_uid;
  return chantiers_etat_json(v_uid) || jsonb_build_object('gain', v_n);
end; $f$;

create or replace function public.chantiers_embaucher()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  e chantiers_equipes%rowtype;
  v_cout integer;
  v_solde integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  perform chantiers_equipe_creer(v_uid);
  select * into e from chantiers_equipes where joueur_id = v_uid for update;
  v_cout := chantiers_cout_ouvrier(e.ouvriers);
  if v_cout is null then raise exception 'Ton équipe est complète'; end if;
  select j.solde into v_solde from joueurs j where j.id = v_uid for update;
  if coalesce(v_solde, 0) < v_cout then raise exception 'Il te faut % TP pour embaucher', v_cout; end if;
  perform chantiers_regler(v_uid);
  perform set_config('terrafront.motif', 'chantier_equipe', true);
  update joueurs set solde = solde - v_cout where id = v_uid;
  update chantiers_equipes set ouvriers = ouvriers + 1 where joueur_id = v_uid;
  perform chantiers_rythme_appliquer(v_uid);
  return chantiers_etat_json(v_uid) || jsonb_build_object('depense', v_cout);
end; $f$;

create or replace function public.chantiers_outils()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  e chantiers_equipes%rowtype;
  v_cout integer;
  v_solde integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  perform chantiers_equipe_creer(v_uid);
  select * into e from chantiers_equipes where joueur_id = v_uid for update;
  v_cout := chantiers_cout_outils(e.outils);
  if v_cout is null then raise exception 'Tu as déjà les meilleurs outils'; end if;
  select j.solde into v_solde from joueurs j where j.id = v_uid for update;
  if coalesce(v_solde, 0) < v_cout then raise exception 'Il te faut % TP pour ces outils', v_cout; end if;
  perform chantiers_regler(v_uid);
  perform set_config('terrafront.motif', 'chantier_outils', true);
  update joueurs set solde = solde - v_cout where id = v_uid;
  update chantiers_equipes set outils = outils + 1 where joueur_id = v_uid;
  perform chantiers_rythme_appliquer(v_uid);
  return chantiers_etat_json(v_uid) || jsonb_build_object('depense', v_cout);
end; $f$;

create or replace function public.merveille_equipe(p_envoyer boolean)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  e chantiers_equipes%rowtype;
  m chantiers_merveilles%rowtype;
  v_r numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not chantiers_permis(v_uid) then raise exception 'Les grands chantiers ne sont pas encore ouverts'; end if;
  perform chantiers_finaliser();
  perform chantiers_equipe_creer(v_uid);
  select * into e from chantiers_equipes where joueur_id = v_uid for update;
  v_r := chantiers_rythme(e.ouvriers, e.outils);
  if coalesce(p_envoyer, false) then
    select * into m from chantiers_merveilles where finie_le is null limit 1;
    if m.commune_code is null then raise exception 'Aucune merveille en chantier en ce moment'; end if;
    if not exists (select 1 from chantiers_mecenes c where c.merveille = m.commune_code and c.joueur_id = v_uid and c.actif) then
      -- le chantier perso s'arrête là où il en est
      update chantiers
         set fait = least(travail, fait + v_r * greatest(0, extract(epoch from now() - depuis)) / 3600.0),
             depuis = now(), en_pause = true, fin_prevue = null
       where joueur_id = v_uid and not en_pause;
      insert into chantiers_mecenes (merveille, joueur_id, heures, depuis, actif, rythme)
      values (m.commune_code, v_uid, 0, now(), true, v_r)
      on conflict (merveille, joueur_id) do update set depuis = now(), actif = true, rythme = v_r;
    end if;
  else
    update chantiers_mecenes
       set heures = heures + rythme * greatest(0, extract(epoch from now() - depuis)) / 3600.0,
           depuis = now(), actif = false
     where joueur_id = v_uid and actif;
    update chantiers
       set en_pause = false, depuis = now(),
           fin_prevue = now() + make_interval(secs => (greatest(0, travail - fait) / v_r * 3600.0)::double precision)
     where joueur_id = v_uid and en_pause;
  end if;
  return chantiers_etat_json(v_uid);
end; $f$;

-- ---------------------------------------------------------------------------
--  Droits
-- ---------------------------------------------------------------------------
revoke all on function public.chantiers_reglages()                  from public, anon, authenticated;
revoke all on function public.chantiers_permis(uuid)                from public, anon, authenticated;
revoke all on function public.chantiers_rythme(integer, integer)    from public, anon, authenticated;
revoke all on function public.chantiers_cout_ouvrier(integer)       from public, anon, authenticated;
revoke all on function public.chantiers_cout_outils(integer)        from public, anon, authenticated;
revoke all on function public.chantiers_equipe_creer(uuid)          from public, anon, authenticated;
revoke all on function public.chantiers_recette_brute(uuid)         from public, anon, authenticated;
revoke all on function public.chantiers_taux(uuid)                  from public, anon, authenticated;
revoke all on function public.chantiers_regler_stock(uuid)          from public, anon, authenticated;
revoke all on function public.chantiers_regler(uuid)                from public, anon, authenticated;
revoke all on function public.chantiers_rythme_appliquer(uuid)      from public, anon, authenticated;
revoke all on function public.chantiers_finaliser()                 from public, anon, authenticated;
revoke all on function public.chantiers_etat_json(uuid)             from public, anon, authenticated;

revoke all on function public.chantiers_etat()                      from public, anon;
revoke all on function public.chantier_commencer(text)              from public, anon;
revoke all on function public.chantier_abandonner()                 from public, anon;
revoke all on function public.chantier_inaugurer(text)              from public, anon;
revoke all on function public.chantiers_recolter()                  from public, anon;
revoke all on function public.chantiers_embaucher()                 from public, anon;
revoke all on function public.chantiers_outils()                    from public, anon;
revoke all on function public.merveille_equipe(boolean)             from public, anon;
grant execute on function public.chantiers_etat()                   to authenticated;
grant execute on function public.chantier_commencer(text)           to authenticated;
grant execute on function public.chantier_abandonner()              to authenticated;
grant execute on function public.chantier_inaugurer(text)           to authenticated;
grant execute on function public.chantiers_recolter()               to authenticated;
grant execute on function public.chantiers_embaucher()              to authenticated;
grant execute on function public.chantiers_outils()                 to authenticated;
grant execute on function public.merveille_equipe(boolean)          to authenticated;

-- ---------------------------------------------------------------------------
--  La première merveille ouvre (Notre-Dame de Paris)
-- ---------------------------------------------------------------------------
insert into public.chantiers_merveilles (commune_code, total, ouverte_le)
select cm.commune_code, coalesce((public.chantiers_reglages()->>'merveille')::numeric, 20000), now()
  from public.chantiers_monuments cm
 where cm.taille = 'merveille'
   and not exists (select 1 from public.chantiers_merveilles)
 order by cm.ordre nulls last
 limit 1;

commit;

-- contrôle : monuments à restaurer (environ 99), dont 10 merveilles, la
-- merveille ouverte (75104 = Notre-Dame), et l'ouverture (0 = testeurs seulement)
select (select count(*) from public.chantiers_monuments)                               as monuments,
       (select count(*) from public.chantiers_monuments where taille = 'merveille')    as merveilles,
       (select count(*) from public.chantiers_monuments where taille = 'grand')        as grands,
       (select count(*) from public.chantiers_monuments where taille = 'moyen')        as moyens,
       (select count(*) from public.chantiers_monuments where taille = 'petit')        as petits,
       (select commune_code from public.chantiers_merveilles where finie_le is null)   as merveille_ouverte,
       (select (valeur::jsonb->>'ouvert') from public.config_jeu where cle = 'chantiers') as ouvert;
