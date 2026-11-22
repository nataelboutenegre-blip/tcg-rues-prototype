-- s3-44 : les promos du week-end (décision de Nataël le 19/11 : −30 %, du vendredi au dimanche, des collections
-- qui tournent selon la règle des 30 jours). Voir claude/promos-week-end.md. Va avec patch487 (affichage).
-- Claude n'est pas juriste : la règle appliquée est celle de l'art. L112-1-1 du code de la consommation
-- (prix barré = prix le plus bas pratiqué dans les 30 jours avant la réduction).
--
-- 1. euros_prix_historique : chaque prix d'article, avec sa date (un déclencheur note les changements).
--    Départ : les 9 anciennes collections au 26/10 (fichier 14-skins-packs-boutique.sql, prix inchangés
--    depuis), les 5 de la S3 au 22/11 à 10 h 07 (étape 4 bis).
-- 2. euros_promos : une ligne par promo (article, début, fin, remise, prix de référence, prix promo).
--    euros_promo_planifier() refuse : un article qui n'est pas une collection en vente ; un article vendu
--    depuis moins de 30 jours ; une promo qui recommence moins de 30 jours après la précédente ; deux promos
--    qui se chevauchent. Prix promo = prix de référence − 30 %, arrondi en dessous à x,x9 €.
-- 3. euros_preparer_commande : le prix de la commande (et donc de Stripe) est le prix promo pendant la promo.
--    euros_catalogue : chaque article dit s'il est en promo (prix, prix barré, fin, remise).
-- Retour arrière : delete from euros_promos where debut > now();  (les promos passées restent pour l'historique)

create table if not exists public.euros_prix_historique (
  id            bigserial primary key,
  article_id    text not null,
  prix_centimes integer not null,
  du            timestamptz not null default now()
);
create index if not exists euros_prix_historique_art on public.euros_prix_historique (article_id, du);
alter table public.euros_prix_historique enable row level security;

insert into public.euros_prix_historique (article_id, prix_centimes, du)
select a.id, a.prix_centimes,
       case when a.id ~ '(givre|aquarelle|topo|vitrail|kintsugi)$' then timestamptz '2026-11-22 10:07+01'
            else timestamptz '2026-10-26 12:00+01' end
  from public.euros_articles a
 where a.type = 'collection'
   and not exists (select 1 from public.euros_prix_historique h where h.article_id = a.id);

create or replace function public.euros_prix_noter() returns trigger
language plpgsql security definer set search_path to 'public' as $$
begin
  if tg_op = 'INSERT' or new.prix_centimes is distinct from old.prix_centimes then
    insert into euros_prix_historique (article_id, prix_centimes) values (new.id, new.prix_centimes);
  end if;
  return new;
end $$;
drop trigger if exists euros_prix_noter on public.euros_articles;
create trigger euros_prix_noter after insert or update of prix_centimes on public.euros_articles
  for each row execute function public.euros_prix_noter();

create table if not exists public.euros_promos (
  id             bigserial primary key,
  article_id     text not null references public.euros_articles(id),
  debut          timestamptz not null,
  fin            timestamptz not null check (fin > debut),
  remise_pct     integer not null default 30 check (remise_pct between 1 and 90),
  prix_reference integer not null,
  prix_promo     integer not null,
  cree_le        timestamptz not null default now()
);
create index if not exists euros_promos_art on public.euros_promos (article_id, debut);
alter table public.euros_promos enable row level security;
alter table public.euros_commandes add column if not exists promo_id bigint;

-- le prix le plus bas pratiqué dans les 30 jours avant p_avant (prix catalogue et promos)
create or replace function public.euros_prix_reference(p_article text, p_avant timestamptz) returns integer
language sql stable security definer set search_path to 'public' as $$
  select min(p) from (
    (select h.prix_centimes as p from euros_prix_historique h
      where h.article_id = p_article and h.du <= p_avant - interval '30 days' order by h.du desc limit 1)
    union all
    select h.prix_centimes from euros_prix_historique h
     where h.article_id = p_article and h.du > p_avant - interval '30 days' and h.du < p_avant
    union all
    select pr.prix_promo from euros_promos pr
     where pr.article_id = p_article and pr.fin > p_avant - interval '30 days' and pr.debut < p_avant
  ) x;
$$;
create or replace function public.euros_arrondi_x9(p_centimes integer) returns integer
language sql immutable as $$ select greatest(9, (floor((p_centimes - 9) / 10.0) * 10 + 9)::int); $$;

create or replace function public.euros_promo_planifier(p_article text, p_debut timestamptz, p_fin timestamptz, p_remise integer default 30)
returns public.euros_promos
language plpgsql security definer set search_path to 'public' as $$
declare a euros_articles%rowtype; v_ref integer; r euros_promos%rowtype;
begin
  select * into a from euros_articles where id = p_article;
  if a.id is null or a.type <> 'collection' or not a.actif then raise exception '% : pas une collection en vente', p_article; end if;
  if not exists (select 1 from euros_prix_historique where article_id = p_article and du <= p_debut - interval '30 days') then
    raise exception '% : en vente depuis moins de 30 jours au %', p_article, p_debut;
  end if;
  if exists (select 1 from euros_promos where article_id = p_article and fin > p_debut - interval '30 days' and debut < p_fin + interval '30 days') then
    raise exception '% : une autre promo à moins de 30 jours', p_article;
  end if;
  v_ref := euros_prix_reference(p_article, p_debut);
  if v_ref is null then raise exception '% : prix de référence inconnu', p_article; end if;
  insert into euros_promos (article_id, debut, fin, remise_pct, prix_reference, prix_promo)
  values (p_article, p_debut, p_fin, p_remise, v_ref, euros_arrondi_x9(floor(v_ref * (100 - p_remise) / 100.0)::int))
  returning * into r;
  return r;
end $$;
revoke all on function public.euros_promo_planifier(text, timestamptz, timestamptz, integer) from public, anon, authenticated;

create or replace function public.euros_promo_active(p_article text) returns public.euros_promos
language sql stable security definer set search_path to 'public' as $$
  select * from euros_promos where article_id = p_article and now() >= debut and now() < fin order by debut desc limit 1;
$$;

-- le catalogue : la promo en cours de chaque article
create or replace function public.euros_catalogue()
 returns jsonb
 language plpgsql
 stable security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  v_age integer;
  v_plafond integer := (euros_reglage('plafond_mineur_centimes'))::integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_age := euros_age(v_uid);
  return jsonb_build_object(
    'cgv_version', euros_reglage('cgv_version'),
    'naissance_connue', v_age is not null,
    'mineur', v_age is not null and v_age < 18,
    'plafond_restant', case when v_age is not null and v_age < 18
                            then greatest(0, v_plafond - euros_depense_du_mois(v_uid)) end,
    'og', euros_est_og(v_uid),
    'ouverte', coalesce((euros_reglage('boutique_ouverte'))::boolean, false),
    'peut_acheter', euros_peut_acheter(v_uid),
    'articles', coalesce((
      select jsonb_agg(jsonb_build_object(
               'id', a.id, 'type', a.type, 'nom', a.nom, 'description', a.description,
               'prix_centimes', a.prix_centimes, 'reserve_og', a.reserve_og, 'saison', a.saison,
               'possede', exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id)
                 or (a.contenu is not null and not exists(select 1 from unnest(a.contenu) x
                      where not exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = x))),
               'contenu', a.contenu,
               'prix_moi', case when a.contenu is null then coalesce(pr.prix_promo, a.prix_centimes)
                 else greatest(50, coalesce(pr.prix_promo, a.prix_centimes) - coalesce((select sum(b.prix_centimes) from euros_articles b
                   where b.id = any(a.contenu) and exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = b.id)), 0)) end,
               'promo', case when pr.id is null then null
                 else jsonb_build_object('prix', pr.prix_promo, 'barre', pr.prix_reference, 'remise', pr.remise_pct, 'fin', pr.fin) end,   -- s3-44
               'livraison_le', (select c.livrer_apres from euros_commandes c
                                 where c.joueur_id = v_uid and c.article_id = a.id and c.statut = 'payee'
                                 order by c.cree_le desc limit 1))
             order by (pr.id is null), a.ordre)
        from euros_articles a
        left join lateral (select * from euros_promos p where p.article_id = a.id and now() >= p.debut and now() < p.fin
                            order by p.debut desc limit 1) pr on true
       where a.actif and euros_peut_acheter(v_uid)), '[]'::jsonb));
end;
$function$;

-- la commande : le prix promo pendant la promo
do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.euros_preparer_commande(text,text,boolean,boolean,boolean,text,date)'::regprocedure);
  n := replace(d, '  v_imm boolean;
begin', '  v_imm boolean;
  v_promo euros_promos%rowtype;   -- s3-44
begin');
  n := replace(n, '  if a.contenu is not null then
    if not exists', '  v_promo := euros_promo_active(a.id);   -- s3-44 : la promo du week-end
  if v_promo.id is not null then a.prix_centimes := v_promo.prix_promo; end if;
  if a.contenu is not null then
    if not exists');
  n := replace(n, '  insert into euros_commandes(joueur_id, article_id, nom_article, prix_centimes, livraison,
                              cgv_version, case_cgv, case_immediate, case_renonciation, mineur)
  values (v_uid, a.id, a.nom, a.prix_centimes, p_livraison,
          p_cgv_version, true, v_imm and p_case_immediate, v_imm and p_case_renonciation, v_age < 18)',
'  insert into euros_commandes(joueur_id, article_id, nom_article, prix_centimes, livraison,
                              cgv_version, case_cgv, case_immediate, case_renonciation, mineur, promo_id)
  values (v_uid, a.id, a.nom, a.prix_centimes, p_livraison,
          p_cgv_version, true, v_imm and p_case_immediate, v_imm and p_case_renonciation, v_age < 18, v_promo.id)');
  if n = d or (length(n) - length(replace(n, 's3-44', ''))) / 5 < 2 or position('v_promo.id)' in n) = 0 then
    raise exception 's3-44 : euros_preparer_commande a changé, rien n''est fait';
  end if;
  execute n;
end $$;

-- contrôle : true · true · 14
select position('s3-44' in pg_get_functiondef('public.euros_preparer_commande(text,text,boolean,boolean,boolean,text,date)'::regprocedure)) > 0 as commande_ok,
       position('s3-44' in pg_get_functiondef('public.euros_catalogue()'::regprocedure)) > 0 as catalogue_ok,
       (select count(distinct article_id) from euros_prix_historique) as articles_historises;
