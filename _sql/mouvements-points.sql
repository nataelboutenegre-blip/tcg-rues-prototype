-- ===========================================================================
--  TerraFront — Le registre des points
--
--  POURQUOI CE FICHIER EXISTE
--    Boule2Pain demande « les points utilisés depuis le début, en attaque,
--    en défense, en achat, bref partout ». L'inventaire de la base du
--    2 octobre dit que c'est impossible : aucune table ne porte le montant
--    d'une dépense. Le journal n'a jamais eu de colonne montant — il stocke
--    type, acteur, cible, commune, tier, et rien d'autre. `historique` dit
--    qui a eu quoi et quand, jamais à quel prix. `annonces` ne garde les
--    prix que des ventes en cours. `joueurs.solde` n'est qu'un solde actuel.
--
--    Ce n'est donc pas « incomplet » : la dépense n'a jamais été écrite
--    nulle part. Rien ne permet de la reconstituer, même approximativement
--    (une attaque ratée coûte des points et ne laisse aucune trace).
--
--    La statistique dira donc « depuis le 3 octobre ». C'est la vérité, et
--    c'est mieux qu'un chiffre inventé.
--
--  CE QUE CE FICHIER FAIT
--    Il pose un registre, et un déclencheur qui l'alimente à chaque fois
--    que le solde d'un joueur change — quelle que soit la fonction qui l'a
--    changé, y compris celles dont je n'ai pas le code sous les yeux.
--
--    C'est volontairement un déclencheur et non une modification des
--    fonctions : `acheter` et `demarrer_paquet` ne sont dans aucun fichier
--    du dépôt. Les modifier à l'aveugle serait la seule manière de casser
--    quelque chose ce soir. Le déclencheur les attrape sans les toucher.
--
--  CE QU'IL NE FAIT PAS ENCORE
--    Le motif (attaque, défense, bouclier, paquet, bourse, commission) est
--    une colonne que les fonctions remplissent elles-mêmes, une par une.
--    Tant qu'elles ne le font pas, le motif reste nul : le total est juste,
--    la ventilation viendra après. Un chiffre vrai sans détail vaut mieux
--    qu'un détail faux.
--
--  AUCUNE DONNÉE EXISTANTE N'EST TOUCHÉE. Rien n'est supprimé, rien n'est
--  recalculé. Le registre démarre vide, et se remplit à partir de
--  maintenant.
-- ===========================================================================

begin;

-- ---------------------------------------------------------------------------
--  1. Le registre
--     montant négatif = dépense, positif = gain. Une seule colonne signée
--     plutôt que deux : impossible d'oublier laquelle remplir.
-- ---------------------------------------------------------------------------
create table if not exists public.mouvements_points (
  id        bigserial primary key,
  joueur_id uuid        not null references public.joueurs(id) on delete cascade,
  montant   integer     not null,
  motif     text,
  cree_le   timestamptz not null default now()
);

create index if not exists mouvements_points_joueur_idx
  on public.mouvements_points (joueur_id, cree_le desc);
create index if not exists mouvements_points_date_idx
  on public.mouvements_points (cree_le desc);

-- Un joueur lit ses propres mouvements, et rien d'autre. Personne n'écrit
-- depuis le client : seul le déclencheur, qui est security definer, insère.
alter table public.mouvements_points enable row level security;

drop policy if exists mouvements_points_lecture on public.mouvements_points;
create policy mouvements_points_lecture on public.mouvements_points
  for select to authenticated
  using (joueur_id = auth.uid());

revoke all on public.mouvements_points from public, anon;
grant select on public.mouvements_points to authenticated;
revoke all on sequence public.mouvements_points_id_seq from public, anon, authenticated;


-- ---------------------------------------------------------------------------
--  2. Le déclencheur
--
--     Il se déclenche sur toute modification du solde, d'où qu'elle vienne.
--     C'est ce qui le rend fiable : une fonction ajoutée demain et oubliée
--     sera comptée quand même.
--
--     Le motif se lit dans un réglage de transaction. Les fonctions qui
--     veulent l'étiqueter feront « perform set_config('terrafront.motif',
--     'attaque', true) » — le `true` final veut dire LOCAL, donc limité à
--     la transaction en cours. Sans ce `true`, le réglage survivrait dans
--     la connexion mutualisée de Supabase et étiquetterait de travers le
--     mouvement d'un autre joueur.
-- ---------------------------------------------------------------------------
create or replace function public.tracer_solde()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $$
begin
  if new.solde is distinct from old.solde then
    insert into public.mouvements_points (joueur_id, montant, motif)
    values (new.id,
            new.solde - old.solde,
            nullif(current_setting('terrafront.motif', true), ''));
  end if;
  return new;
end;
$$;

revoke all on function public.tracer_solde() from public, anon, authenticated;

drop trigger if exists joueurs_solde_trace on public.joueurs;
create trigger joueurs_solde_trace
  after update of solde on public.joueurs
  for each row execute function public.tracer_solde();


-- ---------------------------------------------------------------------------
--  3. Les deux statistiques demandées
--
--     mes_statistiques() renvoie une ligne. `points_depuis` dit à partir de
--     quelle date le compteur des points est valable : l'interface doit
--     l'afficher, sinon le chiffre ment par omission.
-- ---------------------------------------------------------------------------
create or replace function public.mes_statistiques()
returns table(
  echanges_realises integer,
  points_depenses   integer,
  points_gagnes     integer,
  points_depuis     timestamptz)
language sql
stable
security definer
set search_path to 'public'
as $$
  select
    (select count(*)::integer from echanges e
      where e.etat = 'accepte'
        and (e.proposant = auth.uid() or e.destinataire = auth.uid())),
    (select coalesce(-sum(m.montant), 0)::integer from mouvements_points m
      where m.joueur_id = auth.uid() and m.montant < 0),
    (select coalesce(sum(m.montant), 0)::integer from mouvements_points m
      where m.joueur_id = auth.uid() and m.montant > 0),
    (select min(m.cree_le) from mouvements_points m where m.joueur_id = auth.uid());
$$;

revoke all on function public.mes_statistiques() from public, anon;
grant execute on function public.mes_statistiques() to authenticated;

commit;


-- ---------------------------------------------------------------------------
--  Contrôle — une seule requête, c'est la dernière que l'éditeur affichera
-- ---------------------------------------------------------------------------
select 'echanges acceptes depuis le debut' as quoi,
       (select count(*) from public.echanges where etat = 'accepte')::text as valeur
union all
select 'echanges proposes (toutes issues)',
       (select count(*) from public.echanges)::text
union all
select 'registre des points installe',
       case when exists (select 1 from pg_trigger
                          where tgname = 'joueurs_solde_trace' and not tgisinternal)
            then 'oui, il se remplit a partir de maintenant' else 'NON' end
union all
select 'mouvements deja enregistres',
       (select count(*) from public.mouvements_points)::text;
