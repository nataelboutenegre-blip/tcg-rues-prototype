-- s2-17 — Cartes Aurore (saison 2, dès le premier jour)
--
-- Ce que fait ce fichier :
--   1. la liste des 233 communes Aurore (aurore_communes) ;
--   2. aurore_tirage(code) : 1 chance sur 3 qu'une commune de la liste sorte
--      en Aurore quand elle est tirée ;
--   3. terra_ouvrir_paquet et boutique_ouvrir_paquet : ajoutent l'Aurore au
--      tirage et renvoient une colonne de plus, « aurore » (vrai si CETTE
--      carte du paquet est sortie en Aurore). Changer les colonnes renvoyées
--      oblige à supprimer puis recréer la fonction : on part de la définition
--      EN PRODUCTION, on remplace quelques lignes repérées, on recrée et on
--      redonne le droit d'exécution aux joueurs connectés ;
--   4. terra_vendre et terra_vendre_doublons : gardent leurs exemplaires
--      Aurore (comme le Contrat, la Bourse et l'échange le font déjà).
--      Sans ça, vendre les doublons d'une carte Aurore échouait sur la
--      contrainte « aurore <= exemplaires ».
--
-- Rejouable : chaque étape vérifie si elle est déjà faite. S'il manque un
-- repère, le fichier s'arrête AVANT de toucher la fonction et dit lequel.
-- Contrôle attendu à la fin : 233 | true | true | true | true

begin;

-- ---------- 1. la liste ----------
create table if not exists public.aurore_communes (
  code text primary key references public.communes(code)
);
alter table public.aurore_communes enable row level security;
revoke all on public.aurore_communes from public, anon, authenticated;

-- seules les communes présentes dans le jeu sont prises : le contrôle final
-- doit afficher 233, sinon il en manque (le dire à Claude)
insert into public.aurore_communes (code)
select v.code from (values
  ('01160'), ('01173'), ('01354'), ('01419'), ('01427'), ('02095'), ('06108'), ('06155'), ('08081'), ('08409'), ('10297'), ('10343'),
  ('12089'), ('13073'), ('13074'), ('13080'), ('13113'), ('14098'), ('14167'), ('14228'), ('14726'), ('14762'), ('15187'), ('17219'),
  ('17291'), ('25539'), ('26108'), ('26116'), ('26235'), ('27213'), ('28015'), ('29024'), ('29042'), ('29160'), ('29241'), ('30062'),
  ('30133'), ('30155'), ('30156'), ('30243'), ('31033'), ('31113'), ('31351'), ('31395'), ('31424'), ('31433'), ('31547'), ('31582'),
  ('32160'), ('33090'), ('33122'), ('33229'), ('33312'), ('33422'), ('33527'), ('34022'), ('34031'), ('34095'), ('34113'), ('34114'),
  ('34192'), ('34255'), ('34259'), ('34270'), ('34299'), ('35024'), ('35093'), ('35206'), ('37018'), ('37122'), ('37261'), ('38140'),
  ('38317'), ('38397'), ('41018'), ('41194'), ('42005'), ('42127'), ('42237'), ('42275'), ('42304'), ('44029'), ('44064'), ('44066'),
  ('44073'), ('44098'), ('44151'), ('44158'), ('44182'), ('44186'), ('45155'), ('45191'), ('45234'), ('47157'), ('49015'), ('49080'),
  ('49092'), ('49228'), ('50099'), ('50129'), ('51030'), ('52448'), ('54115'), ('54159'), ('54257'), ('54263'), ('54274'), ('54280'),
  ('54483'), ('54498'), ('54528'), ('56008'), ('56176'), ('56240'), ('57012'), ('57097'), ('57206'), ('57207'), ('57283'), ('57447'),
  ('57480'), ('57660'), ('57666'), ('57751'), ('59008'), ('59009'), ('59011'), ('59032'), ('59112'), ('59122'), ('59165'), ('59212'),
  ('59268'), ('59299'), ('59339'), ('59343'), ('59410'), ('59447'), ('59457'), ('59526'), ('59553'), ('59569'), ('59586'), ('59636'),
  ('59650'), ('60282'), ('60471'), ('60509'), ('60581'), ('62004'), ('62014'), ('62035'), ('62250'), ('62427'), ('62516'), ('62628'),
  ('62757'), ('62758'), ('63430'), ('64256'), ('64284'), ('64545'), ('65047'), ('66021'), ('66037'), ('67137'), ('67152'), ('67372'),
  ('67471'), ('68256'), ('69043'), ('69089'), ('69191'), ('69194'), ('69199'), ('69202'), ('69244'), ('71153'), ('71486'), ('74133'),
  ('74282'), ('74288'), ('76103'), ('76165'), ('76384'), ('76447'), ('76451'), ('76681'), ('78089'), ('78481'), ('79081'), ('79195'),
  ('80016'), ('80021'), ('80561'), ('82037'), ('82134'), ('83004'), ('83070'), ('83073'), ('83090'), ('83115'), ('83130'), ('83137'),
  ('83148'), ('84016'), ('84031'), ('84056'), ('84088'), ('85109'), ('85128'), ('85302'), ('86070'), ('86158'), ('86214'), ('87001'),
  ('87048'), ('87050'), ('91174'), ('92009'), ('92019'), ('92036'), ('92050'), ('93007'), ('93045'), ('93050'), ('93062'), ('93063'),
  ('93064'), ('93072'), ('94034'), ('94043'), ('95019')) as v(code)
where exists (select 1 from public.communes c where c.code = v.code)
on conflict (code) do nothing;

-- ---------- 2. le tirage ----------
create or replace function public.aurore_chance() returns numeric
language sql immutable as $$ select 1.0 / 3 $$;

create or replace function public.aurore_tirage(p_code text) returns boolean
language sql volatile security definer set search_path = public as $$
  select exists (select 1 from aurore_communes a where a.code = p_code)
         and random() < aurore_chance()
$$;
revoke all on function public.aurore_chance() from public, anon, authenticated;
revoke all on function public.aurore_tirage(text) from public, anon, authenticated;

-- outil du fichier : remplace un passage qui doit apparaître exactement une fois
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

-- ---------- 3a. terra_ouvrir_paquet ----------
do $do$
declare d text := pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure);
begin
  if d like '%aurore_tirage%' then raise notice 'terra_ouvrir_paquet : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'latitude double precision, longitude double precision)',
                            'latitude double precision, longitude double precision, aurore boolean)', 'colonnes');
  d := pg_temp.remplacer(d, E'    select c.code from communes c order by random() limit 5\n',
                            E'    select t0.code, aurore_tirage(t0.code) as aur\n'
                         || E'      from (select c.code from communes c order by random() limit 5) t0\n', 'tirage');
  d := pg_temp.remplacer(d, E'(joueur_id, commune_code, exemplaires, origine)\n    select v_uid, tirage.code, 1, ''paquet'' from tirage\n'
                         || E'    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + 1\n',
                            E'(joueur_id, commune_code, exemplaires, aurore, origine)\n    select v_uid, tirage.code, 1, tirage.aur::integer, ''paquet'' from tirage\n'
                         || E'    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + 1,\n'
                         || E'                                                        aurore = tc.aurore + excluded.aurore\n', 'ajout');
  d := pg_temp.remplacer(d, E'c.longitude::double precision\n    from ajout a\n    join communes c on c.code = a.commune_code\n',
                            E'c.longitude::double precision, ti.aur\n    from ajout a\n    join communes c on c.code = a.commune_code\n'
                         || E'    join tirage ti on ti.code = a.commune_code\n', 'resultat');
  execute 'drop function public.terra_ouvrir_paquet(boolean)';
  execute d;
  execute 'revoke all on function public.terra_ouvrir_paquet(boolean) from public, anon';
  execute 'grant execute on function public.terra_ouvrir_paquet(boolean) to authenticated';
  raise notice 'terra_ouvrir_paquet : Aurore ajoutée';
end $do$;

-- ---------- 3b. boutique_ouvrir_paquet ----------
do $do$
declare d text := pg_get_functiondef('public.boutique_ouvrir_paquet(text, text)'::regprocedure);
begin
  if d like '%aurore_tirage%' then raise notice 'boutique_ouvrir_paquet : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'latitude double precision, longitude double precision)',
                            'latitude double precision, longitude double precision, aurore boolean)', 'colonnes');
  d := pg_temp.remplacer(d, E'    select tirage.code, count(*)::integer n from tirage group by tirage.code\n',
                            E'    select tirage.code, count(*)::integer n,\n'
                         || E'           (count(*) filter (where aurore_tirage(tirage.code)))::integer naur\n'
                         || E'      from tirage group by tirage.code\n', 'compte');
  d := pg_temp.remplacer(d, E'(joueur_id, commune_code, exemplaires, origine)\n    select v_uid, compte.code, compte.n, ''boutique'' from compte\n'
                         || E'    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + excluded.exemplaires\n',
                            E'(joueur_id, commune_code, exemplaires, aurore, origine)\n    select v_uid, compte.code, compte.n, compte.naur, ''boutique'' from compte\n'
                         || E'    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + excluded.exemplaires,\n'
                         || E'                                                        aurore = tc.aurore + excluded.aurore\n', 'ajout');
  d := pg_temp.remplacer(d, E'c.longitude::double precision\n    from ajout a2\n    join communes c on c.code = a2.commune_code\n',
                            E'c.longitude::double precision, co.naur > 0\n    from ajout a2\n    join communes c on c.code = a2.commune_code\n'
                         || E'    join compte co on co.code = a2.commune_code\n', 'resultat');
  execute 'drop function public.boutique_ouvrir_paquet(text, text)';
  execute d;
  execute 'revoke all on function public.boutique_ouvrir_paquet(text, text) from public, anon';
  execute 'grant execute on function public.boutique_ouvrir_paquet(text, text) to authenticated';
  raise notice 'boutique_ouvrir_paquet : Aurore ajoutée';
end $do$;

-- ---------- 4a. terra_vendre : garde les exemplaires Aurore ----------
do $do$
declare d text := pg_get_functiondef('public.terra_vendre(text, integer)'::regprocedure);
begin
  if d like '%v_garde%' then raise notice 'terra_vendre : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, E'  v_ex integer;\n', E'  v_ex integer;\n  v_garde integer;\n', 'declare');
  d := pg_temp.remplacer(d, 'select t.exemplaires into v_ex from terra_collection t',
                            'select t.exemplaires, greatest(1, t.aurore) into v_ex, v_garde from terra_collection t', 'lecture');
  d := pg_temp.remplacer(d, E'if v_ex - p_n < 1 then raise exception ''Tu ne peux vendre que tes doublons (% en trop)'', v_ex - 1; end if;',
                            E'if v_ex - p_n < v_garde then raise exception ''Tu ne peux vendre que tes doublons (% en trop)'', v_ex - v_garde; end if;', 'garde');
  execute d;   -- mêmes paramètres, mêmes colonnes : create or replace suffit, les droits restent
  raise notice 'terra_vendre : exemplaires Aurore protégés';
end $do$;

-- ---------- 4b. terra_vendre_doublons ----------
do $do$
declare d text := pg_get_functiondef('public.terra_vendre_doublons(text[])'::regprocedure);
begin
  if d like '%greatest(1, t.aurore)%' then raise notice 'terra_vendre_doublons : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 't.exemplaires - 1 as en_trop', 't.exemplaires - greatest(1, t.aurore) as en_trop', 'en_trop');
  d := pg_temp.remplacer(d, 't.exemplaires > 1 and c.tier = any(p_tiers)',
                            't.exemplaires > greatest(1, t.aurore) and c.tier = any(p_tiers)', 'filtre');
  d := pg_temp.remplacer(d, 'update terra_collection tc set exemplaires = 1',
                            'update terra_collection tc set exemplaires = tc.exemplaires - cibles.en_trop', 'maj');
  execute d;
  raise notice 'terra_vendre_doublons : exemplaires Aurore protégés';
end $do$;

commit;

-- ---------- contrôle : 233 | true | true | true | true ----------
select (select count(*) from public.aurore_communes)                                                  as communes_aurore,
       pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure) like '%aurore_tirage%'       as paquet,
       pg_get_functiondef('public.boutique_ouvrir_paquet(text, text)'::regprocedure) like '%aurore_tirage%' as boutique,
       pg_get_functiondef('public.terra_vendre(text, integer)'::regprocedure) like '%v_garde%'              as vendre,
       pg_get_functiondef('public.terra_vendre_doublons(text[])'::regprocedure) like '%greatest(1, t.aurore)%' as doublons;
