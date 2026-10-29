-- ===========================================================================
--  s2-64 — Couper l'atelier des cartes (patch270)
--  Plus rien ne s'affiche (ni l'atelier, ni les finitions et halos sur les
--  cartes), et les 4 objets ne sont plus en vente. Ce qui a été acheté reste
--  dans l'inventaire des joueurs, et chaque composition enregistrée revient
--  telle quelle si on relance s2-64-atelier.sql.
--  Contrôle attendu : 0 | 0
-- ===========================================================================
begin;

update public.config_jeu
   set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb)
 where cle = 'atelier';

update public.euros_articles set actif = false
 where id like 'atelier-%' and type = 'effet';

commit;

select coalesce((public.atelier_reglages() ->> 'ouvert')::int, 0)                       as ouvert,
       (select count(*) from public.euros_articles where id like 'atelier-%' and actif) as en_vente;
