-- ===========================================================================
--  TerraFront — distinctions de fin de saison et badge OG (14 octobre 2026)
--  Idée de LeoLesel (distinctions), badge OG : Nataël.
--
--  1. Table joueur_badges (joueur, badge, saison, valeur).
--  2. distinctions_calcul(saison) : qui gagne quoi, À PARTIR DES DONNÉES
--     ACTUELLES (lecture seule). UNE distinction par joueur au plus (14 octobre) :
--     la catégorie où l'avance est la plus nette d'abord. Les ex aequo en tête
--     partagent le badge. Les joueurs exclus du classement (est_exclu_classement)
--     n'ont pas de distinction ; ils ont l'OG s'ils ont joué.
--  3. badges_joueur(joueur) : les badges d'un joueur, pour sa fiche.
--
--  Les distinctions :
--    conquerant     le plus de conquêtes                (journal conquete, acteur)
--    rempart        le plus de défenses réussies        (journal defense, acteur)
--    cible          le plus attaqué                     (conquêtes subies + défenses faites)
--    obstine        le plus d'assauts ratés             (journal defense, cible)
--    malchanceux    le plus de communes perdues         (journal conquete, cible)
--    marchand       le plus de ventes à la Bourse       (journal achat, cible = le vendeur)
--    diplomate      le plus d'échanges conclus          (journal echange, une ligne par joueur et par échange)
--    collectionneur le plus de communes                 (possessions, au moment du calcul)
--    geographe      la plus longue série de Communes du jour trouvées
--    navigateur     le meilleur Elo Radar (5 duels au moins)
--    og             a ouvert au moins un paquet (a reçu au moins une commune)
--
--  Ce fichier n'attribue RIEN : il installe et montre le résultat actuel.
--  L'attribution se fait avec badges-2-attribuer-saison-1.sql, juste avant
--  la clôture (après, les possessions et le Radar sont remis à zéro).
--  Rejouable.
-- ===========================================================================

create table if not exists public.joueur_badges(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  badge        text not null,
  saison       text not null,
  valeur       integer,
  attribue_le  timestamptz not null default now(),
  primary key (joueur_id, badge, saison)
);
alter table public.joueur_badges enable row level security;
revoke all on public.joueur_badges from public, anon, authenticated;

create or replace function public.distinctions_chiffres()
 returns table(badge text, joueur_id uuid, valeur integer)
 language sql stable security definer set search_path to 'public'
as $f$
  with j as (
    select id, pseudo, est_exclu_classement(pseudo) as exclu from joueurs
  ),
  chiffres as (
    select 'conquerant'::text as badge, acteur as jid, count(*)::int as v from journal where type = 'conquete' and acteur is not null group by acteur
    union all select 'rempart', acteur, count(*)::int from journal where type = 'defense' and acteur is not null group by acteur
    union all select 'cible', x.jid, count(*)::int from (
        select cible as jid from journal where type = 'conquete' and cible is not null
        union all select acteur from journal where type = 'defense' and acteur is not null) x group by x.jid
    union all select 'obstine', cible, count(*)::int from journal where type = 'defense' and cible is not null group by cible
    union all select 'malchanceux', cible, count(*)::int from journal where type = 'conquete' and cible is not null group by cible
    union all select 'marchand', cible, count(*)::int from journal where type = 'achat' and cible is not null group by cible
    -- un échange écrit deux lignes (une par joueur, chacun acteur de la sienne) :
    -- on ne compte que les lignes où le joueur est l'acteur (corrigé le 14 octobre)
    union all select 'diplomate', acteur, count(*)::int from journal where type = 'echange' and acteur is not null group by acteur
    union all select 'collectionneur', p.joueur_id, count(*)::int from possessions p where p.joueur_id is not null group by p.joueur_id
    union all select 'navigateur', r.joueur_id, r.elo from radar_joueurs r where r.parties >= 5
    union all select 'geographe', s.joueur_id, max(s.n)::int from (
        select t.joueur_id, count(*) as n from (
          select e.joueur_id, e.jour, e.jour - (row_number() over (partition by e.joueur_id order by e.jour))::int as bloc
            from (select distinct joueur_id, jour from cdj_essais where km = 0) e) t
        group by t.joueur_id, t.bloc) s group by s.joueur_id
  ),
  eligibles as (
    select c.badge, c.jid, c.v from chiffres c join j on j.id = c.jid where not j.exclu and c.v > 0
  )
  select e.badge, e.jid, e.v from eligibles e;
$f$;

-- Une distinction par joueur (décision du 14 octobre) : à chaque tour, la
-- catégorie dont le meilleur joueur encore libre a l'avance la plus nette
-- (son chiffre divisé par celui du suivant) est attribuée ; ce joueur et
-- cette catégorie sortent du jeu. Les ex aequo en tête partagent le badge.
create or replace function public.distinctions_calcul(p_saison text default 'saison-1')
 returns table(badge text, joueur_id uuid, pseudo text, valeur integer)
 language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  v_badges text[] := array['conquerant','rempart','cible','obstine','malchanceux','marchand','diplomate','collectionneur','geographe','navigateur'];
  v_pris uuid[] := '{}';
  r record;
begin
  create temp table if not exists tmp_dist(badge text, jid uuid, v integer) on commit drop;
  truncate tmp_dist;
  insert into tmp_dist select * from distinctions_chiffres();
  loop
    select x.badge, x.v1 into r from (
      select d.badge,
             max(d.v) as v1,
             (select max(d2.v) from tmp_dist d2 where d2.badge = d.badge and not (d2.jid = any(v_pris))
                and d2.v < max(d.v)) as v2
        from tmp_dist d
       where d.badge = any(v_badges) and not (d.jid = any(v_pris))
       group by d.badge) x
     order by case when x.v2 is null then 1e12 else x.v1::numeric / greatest(x.v2, 1) end desc, x.v1 desc, x.badge
     limit 1;
    exit when r.badge is null;
    return query select r.badge, d.jid, j.pseudo, d.v from tmp_dist d join joueurs j on j.id = d.jid
                  where d.badge = r.badge and d.v = r.v1 and not (d.jid = any(v_pris));
    v_pris := v_pris || array(select d.jid from tmp_dist d where d.badge = r.badge and d.v = r.v1 and not (d.jid = any(v_pris)));
    v_badges := array_remove(v_badges, r.badge);
  end loop;
  return query select 'og'::text, j.id, j.pseudo, null::int from joueurs j
                where exists (select 1 from historique h where h.joueur_id = j.id);
end;
$f$;
revoke all on function public.distinctions_chiffres() from public, anon, authenticated;
revoke all on function public.distinctions_calcul(text) from public, anon, authenticated;

-- les badges d'un joueur, pour sa fiche (ouvert à tous les joueurs connectés)
create or replace function public.badges_joueur(p_joueur uuid)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(jsonb_agg(jsonb_build_object('badge', b.badge, 'saison', b.saison, 'valeur', b.valeur)
                            order by b.saison, b.badge), '[]'::jsonb)
    from joueur_badges b where b.joueur_id = p_joueur;
$f$;
revoke all on function public.badges_joueur(uuid) from public, anon;
grant execute on function public.badges_joueur(uuid) to authenticated;

-- Contrôle : ce que donnerait la saison 1 AUJOURD'HUI (rien n'est attribué)
select badge, count(*) as joueurs,
       string_agg(pseudo || coalesce(' (' || valeur || ')', ''), ', ' order by pseudo) filter (where badge <> 'og') as gagnants
  from public.distinctions_calcul('saison-1')
 group by badge
 order by badge = 'og', badge;

