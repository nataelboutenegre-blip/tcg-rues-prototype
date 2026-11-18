-- ===========================================================================
--  s3-23 (18/11/2026) — Bourse : garder la trace des ventes, et les signaler au-dessus de 5 × la revente
--  Décision de Nataël (« option 2 ») : on ne plafonne pas le prix ; l'analyse du matin
--  (analyse_jour, tâche programmée) signale les ventes au-dessus de 5 fois la revente
--  (transfert possible de TP entre comptes). Avant ce fichier, une vente ne laissait
--  aucune trace de la commune (l'annonce était effacée).
--  Contrôle attendu : true | true
-- ===========================================================================
create table if not exists public.bourse_ventes (
  id bigserial primary key,
  vendeur uuid not null, acheteur uuid not null, commune_code text not null, prix integer not null,
  le timestamptz not null default now());
create index if not exists bourse_ventes_le on public.bourse_ventes (le);
alter table public.bourse_ventes enable row level security;

do $do$
declare d text; a text;
begin
  d := pg_get_functiondef('public.terra_acheter(bigint)'::regprocedure);
  if position('s3-23' in d) = 0 then
    a := E'  delete from terra_annonces t where t.id = p_id;';
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-23 : terra_acheter a changé'; end if;
    execute replace(d, a, a || E'\n  insert into bourse_ventes (vendeur, acheteur, commune_code, prix) values (a.vendeur, v_uid, a.commune_code, a.prix);   -- s3-23');
  end if;
end $do$;

create or replace function public.analyse_jour(p_heures integer default 24)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
with fen as (select now() - make_interval(hours => p_heures) debut,
                    now() - make_interval(hours => p_heures) - interval '7 days' avant),
mv as (select m.* from mouvements_points m, fen where m.cree_le >= fen.avant),
-- 1. les TP créés par motif : dernières 24 h contre la moyenne quotidienne des 7 jours d'avant
motifs as (
  select m.motif,
         sum(m.montant) filter (where m.montant > 0 and m.cree_le >= f.debut) gain_24h,
         round(sum(m.montant) filter (where m.montant > 0 and m.cree_le < f.debut) / 7.0) gain_moyen_7j,
         sum(m.montant) filter (where m.montant < 0 and m.cree_le >= f.debut) depense_24h
    from mv m, fen f group by m.motif),
-- 2. les joueurs qui ont le plus gagné (gains bruts), avec le détail de leurs motifs
gains as (
  select m.joueur_id, sum(m.montant) filter (where m.montant > 0) brut, sum(m.montant) net
    from mv m, fen f where m.cree_le >= f.debut group by m.joueur_id),
med as (select percentile_cont(0.5) within group (order by brut) mediane from gains where brut > 0),
top as (
  select j.pseudo, g.brut, g.net, j.solde,
         (select jsonb_object_agg(x.motif, x.s) from (select m.motif, sum(m.montant) s from mv m, fen f
            where m.joueur_id = g.joueur_id and m.cree_le >= f.debut and m.montant > 0 group by m.motif order by 2 desc limit 4) x) motifs
    from gains g join joueurs j on j.id = g.joueur_id order by g.brut desc nulls last limit 8),
-- 3. la boutique : achats répétés (même article, même département)
bq as (
  select j.pseudo, ba.article_id, ba.departement, count(*) n, sum(ba.prix) depense
    from boutique_achats ba join joueurs j on j.id = ba.joueur_id, fen f
   where ba.le >= f.debut group by 1, 2, 3 having count(*) >= 3 order by 4 desc limit 10),
-- 4. les compteurs hors des bornes
bornes as (
  select jsonb_build_object(
    'solde_negatif', (select coalesce(jsonb_agg(jsonb_build_object('pseudo', pseudo, 'solde', solde)), '[]') from joueurs where solde < 0),
    'energie_au_dessus_plafond', (select coalesce(jsonb_agg(jsonb_build_object('pseudo', pseudo, 'energie', front_energie)), '[]') from joueurs
        where front_energie > coalesce((select (valeur::jsonb->>'plafond')::numeric from config_jeu where cle = 'energie_front'), 130) + 1),
    'roue_jetons_hors_bornes', (select coalesce(jsonb_agg(jsonb_build_object('pseudo', pseudo, 'jetons', roue_jetons)), '[]') from joueurs where roue_jetons > 3.01 or roue_jetons < 0),
    'jetons_paquets_hors_bornes', (select coalesce(jsonb_agg(jsonb_build_object('pseudo', pseudo, 'jetons', jetons_gratuits)), '[]') from joueurs where jetons_gratuits > 3.01 or jetons_gratuits < 0),
    'lingots_negatifs', (select coalesce(jsonb_agg(jsonb_build_object('pseudo', pseudo, 'lingots', lingots)), '[]') from joueurs where lingots < 0)
  ) b),
-- 5. s3-23 : la Bourse au-dessus de 5 fois la revente (transfert de TP entre comptes ?)
bourse as (
  select jv.pseudo vendeur, ja.pseudo acheteur, c.nom commune, c.tier, bv.prix, terra_prix_revente(c.tier) revente,
         round(bv.prix::numeric / nullif(terra_prix_revente(c.tier), 0), 1) fois
    from bourse_ventes bv join communes c on c.code = bv.commune_code
    join joueurs jv on jv.id = bv.vendeur join joueurs ja on ja.id = bv.acheteur, fen f
   where bv.le >= f.debut and bv.prix > 5 * terra_prix_revente(c.tier) and bv.prix >= 1000
   order by bv.prix desc limit 15)
select jsonb_build_object(
  'fenetre_heures', p_heures,
  'joueurs_actifs', (select count(*) from gains),
  'mediane_gain_brut', (select round(mediane) from med),
  'tp_par_motif', (select jsonb_agg(to_jsonb(motifs) order by gain_24h desc nulls last) from motifs where coalesce(gain_24h, 0) > 0 or coalesce(depense_24h, 0) < 0),
  'top_gains', (select jsonb_agg(to_jsonb(top)) from top),
  'boutique_repetee', (select coalesce(jsonb_agg(to_jsonb(bq)), '[]') from bq),
  'bornes', (select b from bornes),
  'bourse_chere', (select coalesce(jsonb_agg(to_jsonb(bourse)), '[]') from bourse)
);
$f$;
revoke all on function public.analyse_jour(integer) from public, anon, authenticated;

select position('s3-23' in pg_get_functiondef('public.terra_acheter(bigint)'::regprocedure)) > 0 achat,
       analyse_jour(24) ? 'bourse_chere' analyse;

-- (18/11, LANCÉ) + fermeture des objectifs de la saison 1, encore appelables par l'API
-- (≈ 410 TP par jour + paquets ; le jeu appelle reclamer_quete depuis la saison 2) :
revoke execute on function public.reclamer_objectif(text) from public, anon, authenticated;
