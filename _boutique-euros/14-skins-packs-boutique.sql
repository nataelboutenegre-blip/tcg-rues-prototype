-- ===========================================================================
--  TerraFront — boutique en euros : 14. skins et packs « collection » en vente
--  26 octobre 2026. À passer APRÈS 13-skins.sql, AVANT de pousser patch202.
--  Rejouable.
--
--  - Un pack (type « collection ») donne plusieurs articles (colonne contenu) :
--    le dos et le skin d'une même collection, ~25 % moins cher.
--  - Ce que le joueur a déjà est déduit du prix du pack, calculé par le
--    serveur (s'il a le dos, il paie le skin au prix « pack moins dos »).
--  - Livraison : le pack et ce qu'il contient entrent dans l'inventaire avec
--    la même commande ; un remboursement les retire ensemble.
--  - Les skins et les packs deviennent actifs : visibles des seuls testeurs
--    tant que la boutique est fermée.
-- ===========================================================================
begin;

create or replace function pg_temp.remplacer(p_def text, p_avant text, p_apres text, p_etiquette text)
returns text language plpgsql as $$
declare n integer;
begin
  n := (length(p_def) - length(replace(p_def, p_avant, ''))) / length(p_avant);
  if n <> 1 then
    raise exception 'Repère « % » trouvé % fois (attendu 1) : rien n''a été modifié', p_etiquette, n;
  end if;
  return replace(p_def, p_avant, p_apres);
end $$;

alter table public.euros_articles add column if not exists contenu text[];

do $do$
declare n text;
begin
  for n in select c.conname from pg_constraint c
            where c.conrelid = 'public.euros_articles'::regclass and c.contype = 'c'
              and pg_get_constraintdef(c.oid) like '%''habillage''%'
              and pg_get_constraintdef(c.oid) not like '%''collection''%'
  loop
    execute format('alter table public.euros_articles drop constraint %I', n);
  end loop;
  if not exists(select 1 from pg_constraint where conname = 'euros_articles_type_ok') then
    alter table public.euros_articles add constraint euros_articles_type_ok check (type in
      ('dos', 'skin', 'cadre', 'habillage', 'effet', 'drapeau', 'motif', 'banniere', 'pass', 'collection'));
  end if;
end $do$;

insert into public.euros_articles(id, type, nom, description, prix_centimes, reserve_og, actif, ordre, contenu) values
  ('pack-gravure', 'collection', 'Collection Gravure',    'Le dos et le skin Gravure',    399, false, true, 300, array['dos-gravure', 'skin-gravure']),
  ('pack-neon',    'collection', 'Collection Néon',       'Le dos et le skin Néon',       599, false, true, 310, array['dos-neon', 'skin-neon']),
  ('pack-maree',   'collection', 'Collection Marée',      'Le dos et le skin Marée',      599, false, true, 320, array['dos-maree', 'skin-maree']),
  ('pack-comete',  'collection', 'Collection Comète',     'Le dos et le skin Comète',     699, false, true, 330, array['dos-comete', 'skin-comete']),
  ('pack-juillet', 'collection', 'Collection 14 Juillet', 'Le dos et le skin 14 Juillet', 699, false, true, 340, array['dos-juillet', 'skin-juillet']),
  ('pack-orfondu', 'collection', 'Collection Or fondu',   'Le dos et le skin Or fondu',   699, false, true, 350, array['dos-orfondu', 'skin-orfondu']),
  ('pack-feu',     'collection', 'Collection Puy de feu', 'Le dos Puy de feu et le skin Brasier', 899, false, true, 360, array['dos-feu', 'skin-feu']),
  ('pack-orage',   'collection', 'Collection Orage',      'Le dos et le skin Orage',      899, false, true, 370, array['dos-orage', 'skin-orage']),
  ('pack-prisme',  'collection', 'Collection Prisme',     'Le dos et le skin Prisme',     999, false, true, 380, array['dos-prisme', 'skin-prisme'])
on conflict (id) do nothing;

-- les skins passent en vente (boutique toujours fermée : testeurs seulement)
update public.euros_articles set actif = true where type = 'skin';

-- livraison : le contenu d'un pack entre aussi dans l'inventaire
do $do$
declare d text := pg_get_functiondef('public.euros_livrer(uuid)'::regprocedure);
begin
  if d like '%contenu%' then raise notice 'euros_livrer : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'on conflict (joueur_id, article_id) do nothing;',
    'on conflict (joueur_id, article_id) do nothing;' || chr(10)
    || '    insert into euros_inventaire(joueur_id, article_id, commande_id)' || chr(10)
    || '    select c.joueur_id, x, c.id from euros_articles a, unnest(a.contenu) x' || chr(10)
    || '     where a.id = c.article_id and a.contenu is not null' || chr(10)
    || '    on conflict (joueur_id, article_id) do nothing;', 'livrer');
  execute d;
end $do$;

-- commande : ce que le joueur a déjà est déduit du prix d'un pack
do $do$
declare d text := pg_get_functiondef('public.euros_preparer_commande(text,text,boolean,boolean,boolean,text,date)'::regprocedure);
begin
  if d like '%contenu%' then raise notice 'euros_preparer_commande : déjà fait'; return; end if;
  d := pg_temp.remplacer(d,
    '  if exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id) then',
    '  if a.contenu is not null then' || chr(10)
    || '    if not exists(select 1 from unnest(a.contenu) x' || chr(10)
    || '                   where not exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = x)) then' || chr(10)
    || '      raise exception ''Tu as deja tout ce que contient cette collection'';' || chr(10)
    || '    end if;' || chr(10)
    || '    a.prix_centimes := greatest(50, a.prix_centimes - coalesce((select sum(b.prix_centimes) from euros_articles b' || chr(10)
    || '      where b.id = any(a.contenu) and exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = b.id)), 0));' || chr(10)
    || '  end if;' || chr(10)
    || '  if exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id) then', 'preparer');
  execute d;
end $do$;

-- catalogue : le contenu, le prix pour moi, et « possédé » si j'ai déjà tout
do $do$
declare d text := pg_get_functiondef('public.euros_catalogue()'::regprocedure);
begin
  if d like '%contenu%' then raise notice 'euros_catalogue : déjà fait'; return; end if;
  d := pg_temp.remplacer(d,
    '''possede'', exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id),',
    '''possede'', exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id)' || chr(10)
    || '                 or (a.contenu is not null and not exists(select 1 from unnest(a.contenu) x' || chr(10)
    || '                      where not exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = x))),' || chr(10)
    || '               ''contenu'', a.contenu,' || chr(10)
    || '               ''prix_moi'', case when a.contenu is null then a.prix_centimes' || chr(10)
    || '                 else greatest(50, a.prix_centimes - coalesce((select sum(b.prix_centimes) from euros_articles b' || chr(10)
    || '                   where b.id = any(a.contenu) and exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = b.id)), 0)) end,',
    'catalogue');
  execute d;
end $do$;

commit;

-- ---------- contrôle : attendu  9 | 9 | 9 | true | true | true ----------
select (select count(*) from public.euros_articles where type = 'collection' and actif)          as packs,
       (select count(*) from public.euros_articles where type = 'skin' and actif)                as skins_en_vente,
       (select count(*) from public.euros_articles p where p.type = 'collection'
          and (select count(*) from public.euros_articles x where x.id = any(p.contenu)) = 2)    as contenus_ok,
       pg_get_functiondef('public.euros_livrer(uuid)'::regprocedure) like '%contenu%'             as livrer_ok,
       pg_get_functiondef('public.euros_preparer_commande(text,text,boolean,boolean,boolean,text,date)'::regprocedure) like '%contenu%' as preparer_ok,
       pg_get_functiondef('public.euros_catalogue()'::regprocedure) like '%contenu%'              as catalogue_ok;
