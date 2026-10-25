-- ===========================================================================
--  TerraFront — annuler « les Aurore du Front gardent leur éclat en Terra »
--  (25 octobre 2026, au soir — décision de Nataël)
--
--  Le matin, aurore-saison-1.sql avait donné une Aurore en Terra à chaque
--  commune de la liste Aurore versée depuis le Front S1 (colonne aurore_s1).
--  Retour en arrière : seules restent les Aurore tombées dans les paquets.
--
--  - On retire UN exemplaire Aurore à chaque carte marquée aurore_s1 (et pas
--    « remettre à 0 ») : si le joueur a tiré la même commune en Aurore dans
--    un paquet depuis ce matin, cette Aurore-là reste.
--  - Avant de toucher à quoi que ce soit, la liste est copiée dans
--    aurore_s1_annulees : on peut revenir en arrière si besoin.
--  - L'étiquette « Front S1 » disparaît d'elle-même (terra_aurores_s1 ne
--    renvoie plus rien). Le Front n'est pas touché.
--  Rejouable. Contrôle attendu : 0 | N | N (N = cartes concernées ce matin).
-- ===========================================================================
begin;

create table if not exists public.aurore_s1_annulees (
  joueur_id    uuid not null,
  commune_code text not null,
  aurore_avant integer not null,
  annulee_le   timestamptz not null default now(),
  primary key (joueur_id, commune_code)
);
alter table public.aurore_s1_annulees enable row level security;
revoke all on public.aurore_s1_annulees from public, anon, authenticated;

insert into public.aurore_s1_annulees (joueur_id, commune_code, aurore_avant)
select t.joueur_id, t.commune_code, t.aurore
  from public.terra_collection t
 where t.aurore_s1
on conflict (joueur_id, commune_code) do nothing;

update public.terra_collection t
   set aurore = greatest(t.aurore - 1, 0), aurore_s1 = false
 where t.aurore_s1;

commit;

-- contrôle : encore marquées S1 | copiées dans la sauvegarde | joueurs touchés
select (select count(*) from public.terra_collection where aurore_s1)               as encore_s1,
       (select count(*) from public.aurore_s1_annulees)                              as sauvegardees,
       (select count(distinct joueur_id) from public.aurore_s1_annulees)             as joueurs;
