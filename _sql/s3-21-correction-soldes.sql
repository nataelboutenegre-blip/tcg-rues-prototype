-- ===========================================================================
--  s3-21 (18/11/2026, LANCÉ) — faille du paquet du département (Paris / petite couronne)
--  Décision de Nataël (11 h 13) : « on descend tout le monde à 10 000 ». Appliqué aux
--  joueurs au-dessus de 10 000 TP qui ont acheté des paquets 75/92/93/94 (7 joueurs,
--  91 924 TP retirés). zintox (10 235, aucun paquet de ces départements) non touché.
--  Trace : table solde_corrections (avant / après) + mouvements_points motif
--  « correction_paquet_departement ». Retour arrière : update joueurs set solde = solde + (avant - apres).
-- ===========================================================================
create table if not exists public.solde_corrections (
  id bigserial primary key, joueur_id uuid not null references joueurs(id), avant integer not null, apres integer not null,
  motif text not null, le timestamptz not null default now());
alter table public.solde_corrections enable row level security;

select set_config('terrafront.motif', 'correction_paquet_departement', true);
with cibles as (
  select j.id, j.solde from joueurs j
   where j.solde > 10000
     and exists (select 1 from boutique_achats ba where ba.joueur_id = j.id and ba.article_id = 'paquet-departement' and ba.departement in ('75','92','93','94'))
   for update),
journal as (
  insert into solde_corrections (joueur_id, avant, apres, motif)
  select id, solde, 10000, 'paquet du département (Paris / petite couronne) : solde ramené à 10 000 (décision de Nataël, 18/11)' from cibles returning joueur_id),
maj as (update joueurs j set solde = 10000 from cibles c where j.id = c.id returning j.id)
select (select count(*) from maj) corriges, (select sum(c.solde - 10000) from cibles c) tp_retires;
