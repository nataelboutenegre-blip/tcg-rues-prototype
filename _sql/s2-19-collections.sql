-- ===========================================================================
--  TerraFront — saison 2 : les collections thématiques (Terra)
--  (décisions de Nataël, 11 octobre 2026)
--
--  5 collections : Fromages (32), Eaux minérales (51), Vins (71),
--  Préfectures (96), Plus beaux villages (185). Listes vérifiées le
--  11 octobre (document « Collections thématiques »).
--
--  - Chaque collection a son paquet : 5 communes de la collection QUE LE
--    JOUEUR N'A PAS ENCORE (jamais de doublon, donc rien à revendre).
--    Moins de 5 manquantes : il reçoit ce qui reste et paie au prorata.
--  - Ces paquets comptent dans la limite de 3 paquets de boutique par jour
--    et ne comptent pas pour les quêtes.
--  - Une carte de la liste Aurore garde sa chance d'1 sur 3.
--  - Collection complète : le joueur RÉCLAME sa récompense (points Terra +
--    dos de carte exclusif), une seule fois. Peu importe d'où viennent les
--    cartes (paquets, échanges, contrats, saison 1).
--  - Prix et récompenses : table collections, modifiables sans toucher au code.
--
--  Fonctions (joueur connecté) :
--   - collections_moi()                 : chaque collection et la progression du joueur
--   - collection_detail(id)             : les communes d'une collection, possédées ou non
--   - boutique_ouvrir_collection(id)    : paie et tire le paquet (même retour que
--                                         terra_ouvrir_paquet, colonne aurore comprise)
--   - collection_reclamer(id)           : verse la récompense d'une collection complète
--  Modifie boutique() pour lister aussi les dos gagnés (hors catalogue).
--
--  SANS EFFET EN SAISON 1 : tout refuse tant que terra_ouverte() est faux.
--  À passer APRÈS s2-15 (boutique) et s2-17 (Aurore). Rejouable.
--  Contrôle attendu à la fin : 5 | 435 | true | false | false
-- ===========================================================================

begin;

create table if not exists public.collections(
  id          text primary key,
  nom         text not null,
  emoji       text not null default '',
  description text not null default '',
  prix        integer not null check (prix >= 0),
  recompense  integer not null check (recompense >= 0),
  dos         text not null,
  ordre       integer not null default 0,
  active      boolean not null default true
);
alter table public.collections enable row level security;
revoke all on public.collections from public, anon, authenticated;

create table if not exists public.collection_communes(
  collection_id text not null references public.collections(id) on delete cascade,
  code          text not null references public.communes(code),
  primary key (collection_id, code)
);
create index if not exists collection_communes_code on public.collection_communes(code);
alter table public.collection_communes enable row level security;
revoke all on public.collection_communes from public, anon, authenticated;

create table if not exists public.collection_recompenses(
  joueur_id     uuid not null references public.joueurs(id) on delete cascade,
  collection_id text not null references public.collections(id),
  points        integer not null,
  le            timestamptz not null default now(),
  primary key (joueur_id, collection_id)
);
alter table public.collection_recompenses enable row level security;
revoke all on public.collection_recompenses from public, anon, authenticated;

-- rejouable : ne réécrit pas un prix modifié à la main
insert into public.collections (id, nom, emoji, description, prix, recompense, dos, ordre) values
  ('fromages', 'Fromages', '🧀', 'Les villages qui donnent leur nom à un fromage', 300, 1000, 'dos-fromages', 1),
  ('eaux', 'Eaux minérales', '💧', 'Les communes des sources d''eau minérale', 300, 1500, 'dos-source', 2),
  ('vins', 'Vins de France', '🍷', 'Les villages qui donnent leur nom à un vin', 300, 2000, 'dos-grand-cru', 3),
  ('prefectures', 'Préfectures', '🏛️', 'Le chef-lieu de chaque département', 600, 5000, 'dos-republique', 4),
  ('villages', 'Plus beaux villages', '🏘️', 'Les Plus Beaux Villages de France', 200, 3000, 'dos-village', 5)
on conflict (id) do nothing;

-- les dos de récompense : hors catalogue (actif = false), on ne peut que les gagner
insert into public.boutique_articles (id, type, nom, description, prix, actif, ordre) values
  ('dos-fromages', 'dos', 'Plateau de fromages', 'Dos de carte crème et croûte dorée', 0, false, 101),
  ('dos-source', 'dos', 'Source', 'Dos de carte bleu source, liseré argent', 0, false, 102),
  ('dos-grand-cru', 'dos', 'Grand cru', 'Dos de carte lie-de-vin, liseré or', 0, false, 103),
  ('dos-republique', 'dos', 'République', 'Dos de carte bleu nuit, liseré tricolore', 0, false, 104),
  ('dos-village', 'dos', 'Village', 'Dos de carte pierre de lavande', 0, false, 105)
on conflict (id) do nothing;

-- les paquets de collection : hors catalogue, servent au registre des achats
-- et à la limite de 3 paquets de boutique par jour
insert into public.boutique_articles (id, type, nom, description, prix, actif, ordre) values
  ('collection-fromages', 'paquet', 'Paquet Fromages', '5 communes de la collection qui te manquent', 300, false, 201),
  ('collection-eaux', 'paquet', 'Paquet Eaux minérales', '5 communes de la collection qui te manquent', 300, false, 202),
  ('collection-vins', 'paquet', 'Paquet Vins de France', '5 communes de la collection qui te manquent', 300, false, 203),
  ('collection-prefectures', 'paquet', 'Paquet Préfectures', '5 communes de la collection qui te manquent', 600, false, 204),
  ('collection-villages', 'paquet', 'Paquet Plus beaux villages', '5 communes de la collection qui te manquent', 200, false, 205)
on conflict (id) do nothing;

-- Fromages : 32 communes
insert into public.collection_communes (collection_id, code)
select 'fromages', v.code from (values
  ('01173'), ('04018'), ('10080'), ('12119'), ('12203'), ('13088'), ('14371'), ('14514'), ('15219'), ('21247'), ('36165'), ('36228'), ('37226'), ('38416'),
  ('38474'), ('39367'), ('41242'), ('42147'), ('46240'), ('52269'), ('59384'), ('61071'), ('63003'), ('63380'), ('68226'), ('69064'), ('73034'), ('74001'),
  ('76462'), ('77131'), ('77284'), ('77288')
) as v(code)
where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

-- Eaux minérales : 51 communes
insert into public.collection_communes (collection_id, code)
select 'eaux', v.code from (values
  ('03264'), ('03310'), ('04126'), ('07003'), ('07011'), ('07012'), ('07156'), ('07182'), ('07331'), ('09030'), ('19269'), ('22172'), ('26256'), ('2B256'),
  ('30344'), ('31042'), ('33009'), ('34008'), ('34293'), ('40088'), ('42194'), ('42198'), ('42222'), ('42285'), ('43191'), ('45069'), ('45290'), ('59398'),
  ('59457'), ('59526'), ('63017'), ('63035'), ('63052'), ('63100'), ('63102'), ('63335'), ('63378'), ('63470'), ('64421'), ('67324'), ('68318'), ('68359'),
  ('72007'), ('73128'), ('74119'), ('74281'), ('81062'), ('81124'), ('82155'), ('88114'), ('88516')
) as v(code)
where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

-- Vins de France : 71 communes
insert into public.collection_communes (collection_id, code)
select 'vins', v.code from (values
  ('07070'), ('11144'), ('11206'), ('13022'), ('18145'), ('18190'), ('18241'), ('21010'), ('21150'), ('21295'), ('21412'), ('21464'), ('21492'), ('21512'),
  ('21582'), ('21712'), ('21714'), ('24037'), ('24274'), ('26347'), ('30149'), ('30326'), ('33030'), ('33174'), ('33248'), ('33268'), ('33297'), ('33314'),
  ('33318'), ('33328'), ('33394'), ('33395'), ('33423'), ('33504'), ('36171'), ('37031'), ('37072'), ('37156'), ('37281'), ('39013'), ('39114'), ('46042'),
  ('49328'), ('49329'), ('51030'), ('51079'), ('51196'), ('51230'), ('51287'), ('58215'), ('64284'), ('65296'), ('66016'), ('66053'), ('69007'), ('69053'),
  ('69058'), ('69084'), ('69103'), ('69267'), ('71210'), ('71294'), ('71385'), ('81099'), ('83009'), ('84012'), ('84037'), ('84049'), ('84096'), ('84136'),
  ('89068')
) as v(code)
where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

-- Préfectures : 96 communes
insert into public.collection_communes (collection_id, code)
select 'prefectures', v.code from (values
  ('01053'), ('02408'), ('03190'), ('04070'), ('05061'), ('06088'), ('07186'), ('08105'), ('09122'), ('10387'), ('11069'), ('12202'), ('13055'), ('14118'),
  ('15014'), ('16015'), ('17300'), ('18033'), ('19272'), ('21231'), ('22278'), ('23096'), ('24322'), ('25056'), ('26362'), ('27229'), ('28085'), ('29232'),
  ('2A004'), ('2B033'), ('30189'), ('31555'), ('32013'), ('33063'), ('34172'), ('35238'), ('36044'), ('37261'), ('38185'), ('39300'), ('40192'), ('41018'),
  ('42218'), ('43157'), ('44109'), ('45234'), ('46042'), ('47001'), ('48095'), ('49007'), ('50502'), ('51108'), ('52121'), ('53130'), ('54395'), ('55029'),
  ('56260'), ('57463'), ('58194'), ('59350'), ('60057'), ('61001'), ('62041'), ('63113'), ('64445'), ('65440'), ('66136'), ('67482'), ('68066'), ('69123'),
  ('70550'), ('71270'), ('72181'), ('73065'), ('74010'), ('75056'), ('76540'), ('77288'), ('78646'), ('79191'), ('80021'), ('81004'), ('82121'), ('83137'),
  ('84007'), ('85191'), ('86194'), ('87085'), ('88160'), ('89024'), ('90010'), ('91228'), ('92050'), ('93008'), ('94028'), ('95127')
) as v(code)
where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

-- Plus beaux villages : 185 communes
insert into public.collection_communes (collection_id, code)
select 'villages', v.code from (values
  ('01290'), ('02586'), ('03062'), ('04061'), ('04076'), ('04135'), ('05082'), ('05157'), ('06043'), ('06068'), ('06113'), ('06132'), ('07023'), ('07348'),
  ('08226'), ('09074'), ('11185'), ('12024'), ('12038'), ('12072'), ('12082'), ('12098'), ('12167'), ('12216'), ('12218'), ('12219'), ('12262'), ('12301'),
  ('13011'), ('14070'), ('14077'), ('15117'), ('15219'), ('15238'), ('16020'), ('17019'), ('17161'), ('17219'), ('17247'), ('17437'), ('18007'), ('18241'),
  ('19019'), ('19057'), ('19067'), ('19239'), ('19254'), ('19273'), ('21152'), ('21271'), ('22153'), ('23045'), ('24035'), ('24040'), ('24086'), ('24152'),
  ('24240'), ('24280'), ('24355'), ('24364'), ('24425'), ('24443'), ('25339'), ('26086'), ('26138'), ('26146'), ('26185'), ('26193'), ('26243'), ('27052'),
  ('27377'), ('29134'), ('2A212'), ('2B296'), ('30005'), ('30151'), ('30175'), ('30222'), ('31472'), ('32133'), ('32194'), ('32204'), ('32290'), ('32345'),
  ('32416'), ('34158'), ('34187'), ('34261'), ('35314'), ('36081'), ('36182'), ('37042'), ('37090'), ('37157'), ('38359'), ('39041'), ('39114'), ('41113'),
  ('42140'), ('42210'), ('43008'), ('43033'), ('43117'), ('43118'), ('43152'), ('43154'), ('45348'), ('46011'), ('46055'), ('46057'), ('46058'), ('46177'),
  ('46185'), ('46240'), ('46256'), ('47175'), ('47203'), ('47215'), ('47312'), ('47324'), ('48090'), ('48119'), ('48146'), ('49140'), ('49219'), ('50030'),
  ('53255'), ('56196'), ('57588'), ('57623'), ('60271'), ('61372'), ('63241'), ('63439'), ('64014'), ('64289'), ('64416'), ('64485'), ('64504'), ('66044'),
  ('66074'), ('66125'), ('66150'), ('66223'), ('67213'), ('67295'), ('68028'), ('68078'), ('68147'), ('68277'), ('69024'), ('70408'), ('71510'), ('73047'),
  ('74315'), ('76735'), ('81064'), ('81069'), ('81139'), ('81170'), ('81217'), ('82008'), ('82026'), ('82094'), ('83010'), ('83019'), ('83035'), ('83046'),
  ('83065'), ('83124'), ('83139'), ('84002'), ('84050'), ('84068'), ('84073'), ('84102'), ('84126'), ('84143'), ('85305'), ('86004'), ('87101'), ('89267'),
  ('89279'), ('89446'), ('95523')
) as v(code)
where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;


-- ---------- lecture ----------
create or replace function public.collections_moi()
 returns table(id text, nom text, emoji text, description text, total integer, possedees integer,
               prix integer, recompense integer, dos text, dos_nom text, reclamee boolean)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  return query
  select c.id, c.nom, c.emoji, c.description,
         (select count(*) from collection_communes cc where cc.collection_id = c.id)::integer,
         (select count(*) from collection_communes cc
            join terra_collection t on t.commune_code = cc.code and t.joueur_id = v_uid
           where cc.collection_id = c.id)::integer,
         c.prix, c.recompense, c.dos,
         (select a.nom from boutique_articles a where a.id = c.dos),
         exists(select 1 from collection_recompenses r where r.joueur_id = v_uid and r.collection_id = c.id)
    from collections c
   where c.active
   order by c.ordre;
end;
$f$;

create or replace function public.collection_detail(p_collection text)
 returns table(code text, nom text, departement text, tier text, population integer,
               possedee boolean, aurore integer)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  return query
  select c.code::text, c.nom::text, c.departement::text, c.tier::text, c.population::integer,
         t.commune_code is not null, coalesce(t.aurore, 0)::integer
    from collection_communes cc
    join communes c on c.code = cc.code
    left join terra_collection t on t.commune_code = cc.code and t.joueur_id = v_uid
   where cc.collection_id = p_collection
   order by c.departement, c.nom;
end;
$f$;

-- ---------- le paquet de collection ----------
create or replace function public.boutique_ouvrir_collection(p_collection text)
 returns table(code text, nom text, departement text, tier text, population integer,
               nouvelle boolean, exemplaires integer, rang integer, palier_total integer,
               latitude double precision, longitude double precision, aurore boolean)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  col collections%rowtype;
  j joueurs%rowtype;
  v_manquantes integer;
  v_n integer;
  v_prix integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'La boutique ouvre avec la saison 2'; end if;
  select * into col from collections cl where cl.id = p_collection and cl.active;
  if not found then raise exception 'Collection introuvable'; end if;

  -- verrou : deux achats simultanés ne dépensent pas le même solde
  select * into j from joueurs jj where jj.id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;
  if boutique_paquets_du_jour(v_uid) >= 3 then
    raise exception 'Tu as deja achete 3 paquets en boutique aujourd''hui';
  end if;

  select count(*) into v_manquantes
    from collection_communes cc
   where cc.collection_id = col.id
     and not exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = cc.code);
  if v_manquantes = 0 then raise exception 'Tu as deja toute cette collection'; end if;
  v_n := least(5, v_manquantes);
  v_prix := ceil(col.prix * v_n / 5.0)::integer;
  if coalesce(j.solde, 0) < v_prix then raise exception 'Solde insuffisant'; end if;

  perform set_config('terrafront.motif', 'boutique', true);
  update joueurs jj set solde = jj.solde - v_prix where jj.id = v_uid;
  insert into boutique_achats(joueur_id, article_id, prix) values (v_uid, 'collection-' || col.id, v_prix);

  return query
  with tirage as (
    select t0.code, aurore_tirage(t0.code) as aur
      from (select cc.code from collection_communes cc
             where cc.collection_id = col.id
               and not exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = cc.code)
             order by random() limit v_n) t0
  ), ajout as (
    insert into terra_collection as tc (joueur_id, commune_code, exemplaires, aurore, origine)
    select v_uid, tirage.code, 1, tirage.aur::integer, 'collection' from tirage
    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + 1,
                                                        aurore = tc.aurore + excluded.aurore
    returning tc.commune_code, tc.exemplaires
  )
  select c.code::text, c.nom::text, c.departement::text, c.tier::text, c.population::integer,
         true, a2.exemplaires::integer, c.rang::integer, c.palier_total::integer,
         c.latitude::double precision, c.longitude::double precision, ti.aur
    from ajout a2
    join communes c on c.code = a2.commune_code
    join tirage ti on ti.code = a2.commune_code;
end;
$f$;

-- ---------- la récompense ----------
create or replace function public.collection_reclamer(p_collection text)
 returns table(points integer, dos text, dos_nom text, solde integer)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  col collections%rowtype;
  v_manquantes integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select * into col from collections cl where cl.id = p_collection;
  if not found then raise exception 'Collection introuvable'; end if;
  perform 1 from joueurs jj where jj.id = v_uid for update;
  if exists(select 1 from collection_recompenses r where r.joueur_id = v_uid and r.collection_id = col.id) then
    raise exception 'Recompense deja recue';
  end if;
  select count(*) into v_manquantes
    from collection_communes cc
   where cc.collection_id = col.id
     and not exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = cc.code);
  if v_manquantes > 0 then raise exception 'Il te manque encore % commune(s)', v_manquantes; end if;

  insert into collection_recompenses(joueur_id, collection_id, points) values (v_uid, col.id, col.recompense);
  perform set_config('terrafront.motif', 'collection', true);
  update joueurs jj set solde = coalesce(jj.solde, 0) + col.recompense where jj.id = v_uid;
  insert into boutique_inventaire(joueur_id, article_id) values (v_uid, col.dos) on conflict do nothing;
  return query select col.recompense, col.dos,
                      (select a.nom from boutique_articles a where a.id = col.dos),
                      (select jj.solde from joueurs jj where jj.id = v_uid);
end;
$f$;

-- ---------- boutique() : les dos gagnés apparaissent aussi ----------
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

do $do$
declare d text := pg_get_functiondef('public.boutique()'::regprocedure);
begin
  if d like '%dos gagnés%' then raise notice 'boutique() : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'from boutique_articles a where a.actif)',
         'from boutique_articles a where a.actif -- et les dos gagnés' || chr(10)
      || '           or (a.type = ''dos'' and exists(select 1 from boutique_inventaire i where i.joueur_id = v_uid and i.article_id = a.id)))',
       'catalogue');
  execute d;
  raise notice 'boutique() : dos gagnés ajoutés';
end $do$;

revoke all on function public.collections_moi()                    from public, anon;
revoke all on function public.collection_detail(text)              from public, anon;
revoke all on function public.boutique_ouvrir_collection(text)     from public, anon;
revoke all on function public.collection_reclamer(text)            from public, anon;
grant execute on function public.collections_moi()                 to authenticated;
grant execute on function public.collection_detail(text)           to authenticated;
grant execute on function public.boutique_ouvrir_collection(text)  to authenticated;
grant execute on function public.collection_reclamer(text)         to authenticated;

commit;

-- ---------- contrôle : 5 | 435 | true | false | false ----------
select (select count(*) from public.collections)                                                   as collections,
       (select count(*) from public.collection_communes)                                           as communes_435,
       position('dos gagnés' in pg_get_functiondef('public.boutique()'::regprocedure)) > 0          as boutique_ok,
       has_function_privilege('anon', 'public.boutique_ouvrir_collection(text)', 'execute')        as anon_doit_etre_false,
       public.terra_ouverte()                                                                      as terra_ouverte_doit_etre_false;
