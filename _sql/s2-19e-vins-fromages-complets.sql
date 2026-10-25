-- ===========================================================================
--  TerraFront — collections Vins et Fromages complétées (25 octobre 2026)
--  Remarque de Boule2Pain et Maroli sur Discord : il manquait des vins
--  (Tonnerrois, Riceys, Alsace…) et des fromages.
--  Règle inchangée : une commune qui donne son nom à un vin ou à un fromage.
--
--  Vins : +108 communes (de 78 à 186) :
--   - Alsace : les 10 communes des dénominations complémentaires (Bergheim,
--     Blienschwiller, Ottrott, Rodern, Saint-Hippolyte, Scherwiller, Wolxheim,
--     Klevener de Heiligenstein, Côte de Rouffach, Côtes de Barr) ;
--   - Bourgogne : Beaune, Auxey-Duresses, Chorey, Ladoix, Monthelie, Pernand,
--     Saint-Aubin, Saint-Romain, Savigny, Chambolle, Fixin, Marsannay, Morey,
--     Vougeot, Bouzeron, Givry, Montagny, Rully, Saint-Véran (Saint-Vérand) ;
--   - Yonne : Irancy, Saint-Bris, Vézelay, Chitry, Coulanges-la-Vineuse,
--     Épineuil, Tonnerre ; Aube : Les Riceys (rosé des Riceys) ;
--   - Loire, Sud-Ouest, Bordeaux, Languedoc-Roussillon, Rhône, Provence,
--     Savoie, Jura, Corse, Lorraine, Beaujolais (voir la liste ci-dessous).
--   Condrieu et Valençay étaient déjà dans les Fromages : ils sont aussi Vins.
--  Fromages : +19 communes (de 32 à 51) : Soumaintrain, Saint-Florentin,
--   Bergues, Avesnes-sur-Helpe (boulette d'Avesnes), Rollot, Murol, Olivet,
--   Dreux (feuille de Dreux), Nangis, Montereau, Fontainebleau, Pithiviers,
--   Échourgnac, Saint-Félicien, Laruns, Bethmale, Tignes (persillé),
--   La Mothe-Saint-Héray (mothais), Sancerre (crottin de Chavignol).
--
--  Récompenses revues (la collection est plus longue) : Vins 2 000 -> 5 000,
--  Fromages 1 000 -> 1 500. Un joueur qui avait déjà réclamé une collection
--  garde ce qu'il a reçu (la récompense ne se réclame qu'une fois).
--  Rejouable. Contrôle attendu : 186 | 51 | 5000 | 1500
-- ===========================================================================
begin;

insert into public.collection_communes (collection_id, code)
select 'vins', v.code from (values
  ('68028'), ('67051'), ('67368'), ('68280'), ('68296'), ('67445'), ('67554'), ('67189'), ('68287'), ('67021'), ('21054'), ('21037'), ('21173'), ('21606'),
  ('21428'), ('21480'), ('21541'), ('21569'), ('21590'), ('21133'), ('21265'), ('21390'), ('21442'), ('21716'), ('71051'), ('71221'), ('71302'), ('71378'),
  ('71487'), ('89202'), ('89337'), ('89446'), ('89108'), ('89118'), ('89153'), ('89418'), ('10317'), ('37228'), ('41050'), ('41067'), ('03254'), ('18057'),
  ('37003'), ('37014'), ('37070'), ('41137'), ('41166'), ('31202'), ('12138'), ('64274'), ('47043'), ('47086'), ('24523'), ('32398'), ('12098'), ('12094'),
  ('33253'), ('33081'), ('33120'), ('33392'), ('33058'), ('33067'), ('33222'), ('33290'), ('33261'), ('33342'), ('33108'), ('33402'), ('34096'), ('34245'),
  ('34108'), ('34159'), ('34145'), ('66107'), ('66164'), ('34203'), ('34269'), ('30034'), ('26377'), ('84028'), ('26113'), ('26086'), ('26110'), ('07281'),
  ('69064'), ('36228'), ('13011'), ('74269'), ('73017'), ('73018'), ('74024'), ('73084'), ('73096'), ('73140'), ('73171'), ('73247'), ('73249'), ('74131'),
  ('74166'), ('39217'), ('2B205'), ('2A004'), ('2B050'), ('2A272'), ('2A114'), ('2A247'), ('54528'), ('69165')
) as v(code)
 where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

insert into public.collection_communes (collection_id, code)
select 'fromages', v.code from (values
  ('89402'), ('89345'), ('59067'), ('59036'), ('80678'), ('63247'), ('45232'), ('28134'), ('77327'), ('77305'), ('77186'), ('45252'), ('24159'), ('07236'),
  ('64320'), ('09055'), ('73296'), ('79184'), ('18241')
) as v(code)
 where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

update public.collections set recompense = 5000 where id = 'vins' and recompense = 2000;
update public.collections set recompense = 1500 where id = 'fromages' and recompense = 1000;

commit;

select (select count(*) from public.collection_communes where collection_id = 'vins')     as vins_186,
       (select count(*) from public.collection_communes where collection_id = 'fromages') as fromages_51,
       (select recompense from public.collections where id = 'vins')                      as recompense_vins,
       (select recompense from public.collections where id = 'fromages')                  as recompense_fromages;
