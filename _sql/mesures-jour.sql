-- ===========================================================================
--  TerraFront — Une photo par jour de ce qui vide le pot
--
--  POURQUOI
--    La mesure du 1er octobre a montré la limite d'un cumul : 9,6 cartes
--    tirées pour une conquête sur toute la vie du jeu, mais 74 conquêtes la
--    première semaine contre 926 la seconde. Le cumul décrit un jeu qui
--    n'existe plus. Et faute de compteur daté pour les paquets, impossible
--    de comparer les deux sources sur la même période.
--
--    Cette table règle ça une fois pour toutes : chaque jour garde ses
--    propres chiffres. Dans une semaine, la question « qu'est-ce qui vide le
--    pot » aura une réponse, et chaque réglage d'économie sera mesurable au
--    lieu d'être deviné.
--
--  CE QU'ELLE N'EST PAS
--    Pas une table de jeu. Rien ne la lit côté joueur, elle ne change aucune
--    règle, et la supprimer ne casserait rien.
--
--  COMMENT ELLE SE REMPLIT
--    Sans tâche planifiée : noter_journal() la rafraîchit au hasard, deux
--    fois sur cent, exactement comme elle purge déjà le journal. Avec
--    quelques centaines d'évènements par jour, ça fait plusieurs photos par
--    jour, et la dernière de la journée est la bonne. Elle ne se déclenche
--    que s'il y a de l'activité — ce qui est précisément quand elle sert.
--
--  LES COMPTES SONT JOURNALIERS, PAS CUMULÉS
--    Volontaire : le journal se purge au-delà de 30 jours, donc un cumul
--    deviendrait une fenêtre glissante sans prévenir. Un compte par jour
--    reste juste pour toujours.
-- ===========================================================================


create table if not exists public.mesures_jour (
  jour            date primary key,
  libres          integer,   -- communes encore dans le pot, au moment de la photo
  prises          integer,   -- communes détenues par un joueur
  conquetes       integer,   -- évènements du jour
  defenses        integer,
  echanges        integer,
  contrats        integer,
  achats          integer,
  tirages_remarquables integer, -- rares et légendaires tirés (le journal ne garde que ceux-là)
  joueurs_actifs  integer,   -- joueurs ayant agi dans la journée
  paquets_cumul   integer,   -- compteur de paquets, toutes époques : la différence entre
  cartes_cumul    integer,   -- deux jours donne le vrai chiffre du jour
  pris_le         timestamptz default now()
);

comment on table public.mesures_jour is
  'Photo quotidienne de l''économie du jeu. Aucun usage côté joueur.';

-- Personne d'autre que le serveur n'a à la lire.
revoke all on table public.mesures_jour from public, anon, authenticated;


-- ---------------------------------------------------------------------------
--  La photo elle-même. Idempotente : la rappeler le même jour met à jour.
-- ---------------------------------------------------------------------------
create or replace function public.prendre_mesure()
returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_prises integer;
  v_total  integer;
begin
  select count(*) into v_prises from possessions;
  select count(*) into v_total  from communes;

  insert into mesures_jour (
    jour, libres, prises, conquetes, defenses, echanges, contrats, achats,
    tirages_remarquables, joueurs_actifs, paquets_cumul, cartes_cumul, pris_le)
  select
    current_date,
    v_total - v_prises,
    v_prises,
    count(*) filter (where type = 'conquete'),
    count(*) filter (where type = 'defense'),
    count(*) filter (where type = 'echange'),
    count(*) filter (where type = 'contrat'),
    count(*) filter (where type = 'achat'),
    count(*) filter (where type = 'tirage'),
    count(distinct acteur),
    (select coalesce(sum(total_paquets), 0) from objectifs_compteurs),
    (select coalesce(sum(total_paquets), 0) * 5 from objectifs_compteurs),
    now()
  from journal
  where cree_le >= current_date
  on conflict (jour) do update set
    libres = excluded.libres,
    prises = excluded.prises,
    conquetes = excluded.conquetes,
    defenses = excluded.defenses,
    echanges = excluded.echanges,
    contrats = excluded.contrats,
    achats = excluded.achats,
    tirages_remarquables = excluded.tirages_remarquables,
    joueurs_actifs = excluded.joueurs_actifs,
    paquets_cumul = excluded.paquets_cumul,
    cartes_cumul = excluded.cartes_cumul,
    pris_le = excluded.pris_le;
end;
$function$;

revoke all on function public.prendre_mesure() from public, anon, authenticated;


-- ---------------------------------------------------------------------------
--  noter_journal() prend la photo en passant
--
--  Reproduction fidèle de la fonction existante. Deux lignes s'ajoutent, au
--  même endroit et avec le même procédé que la purge du journal qui s'y
--  trouve déjà. Rien d'autre ne change.
-- ---------------------------------------------------------------------------
create or replace function public.noter_journal(
  p_type text, p_acteur uuid, p_cible uuid, p_code text, p_tier text)
returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
declare v_nom text;
begin
  select nom into v_nom from communes where code = p_code;
  insert into journal (type, acteur, cible, commune_code, commune_nom, tier)
  values (p_type, p_acteur, p_cible, p_code, v_nom, p_tier);
  -- on ne garde que les evenements des 30 derniers jours
  if random() < 0.02 then
    delete from journal where cree_le < now() - interval '30 days';
  end if;
  -- la photo du jour, au meme rythme : quelques fois par jour, et seulement
  -- s'il se passe quelque chose
  if random() < 0.02 then
    perform prendre_mesure();
  end if;
end;
$function$;


-- Une première photo tout de suite, pour ne pas attendre demain.
select prendre_mesure();


-- ---------------------------------------------------------------------------
--  Vérification
-- ---------------------------------------------------------------------------
select 'A. table creee' as controle,
       coalesce((select 'oui, ' || count(*)::text || ' ligne(s)' from mesures_jour), 'NON') as valeur
union all
select 'B. droits sur la table',
       coalesce((select array_to_string(relacl, ' ') from pg_class
                  where relname = 'mesures_jour' and relnamespace = 'public'::regnamespace),
                'aucun droit accorde (attendu)')
union all
select 'C. noter_journal prend la photo',
       case when pg_get_functiondef(p.oid) like '%prendre_mesure()%' then 'oui' else 'NON' end
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'noter_journal'
union all
select 'D. photo du jour',
       coalesce((select 'libres ' || libres || ', conquetes ' || conquetes
                      || ', echanges ' || echanges || ', actifs ' || joueurs_actifs
                   from mesures_jour where jour = current_date), 'ABSENTE')
order by 1;
