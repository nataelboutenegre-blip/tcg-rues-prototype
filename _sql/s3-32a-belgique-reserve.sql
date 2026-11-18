-- s3-32a : la réserve belge (565 communes), comme suisse_communes_attente pour la Suisse.
-- Aucun joueur ne voit rien : les communes n'entrent dans « communes » qu'à l'ouverture (s3-32, plus tard).
-- Source : Statbel (secteurs statistiques et population au 1/1/2025, CC BY 4.0), regroupés par commune ;
-- rareté aux proportions de la France (décision du 18/11) ; noms selon la règle des grandes villes.
-- Les lignes et les photos sont posées par _donnees/belgique/photos-belgique.py (sur le Mac de Nataël, clé service_role chez lui).
begin;
create table if not exists public.belgique_communes_attente (
  code text primary key,
  nom text not null,
  departement text not null,
  population integer not null,
  latitude numeric not null,
  longitude numeric not null,
  tier text not null,
  rang_pays integer not null,
  nom_officiel text,
  wikidata text,
  photo text, photo_auteur text, photo_licence text, photo_source text);
alter table public.belgique_communes_attente enable row level security;
revoke all on public.belgique_communes_attente from anon, authenticated;
-- les 565 lignes sont posées par _donnees/belgique/photos-belgique.py (depuis jeu/communes-belgique.csv), avant les photos
commit;
-- Contrôle : 565 · 11 provinces · 5 / 16 / 56 / 209 / 279 · 11825551
select count(*) as communes, count(distinct departement) as provinces,
       (select string_agg(n::text, ' / ' order by o) from (select count(*) n, array_position(array['legendaire','epique','rare','peucommun','commun'], tier) o
          from belgique_communes_attente group by tier) t) as raretes,
       sum(population) as population
  from belgique_communes_attente;
