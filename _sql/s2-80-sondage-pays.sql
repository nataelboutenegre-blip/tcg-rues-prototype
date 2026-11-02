-- ===========================================================================
--  TerraFront — s2-80 : le sondage « d'autres pays ? » (2/11/2026)
--  Aperçu validé par Nataël le 2/11 (« Parfait la question »).
--
--  Une carte en haut du Tirage, pour les comptes de plus de 3 jours :
--  « Ajouter d'autres pays à TerraFront, ça te plairait ? »
--    meme  : Oui, sur la même carte que la France
--    apart : Oui, mais dans un mode à part
--    non   : Non, c'est la France qui me plaît
--    egal  : Ça m'est égal
--  Si oui : « Lequel en premier ? » (facultatif).
--  Une réponse par compte. « ✕ » cache la carte jusqu'au lendemain, une
--  seule relance, puis plus jamais. Pas de récompense, pas de pourcentages
--  montrés aux joueurs. Résultats : _sql/lecture-sondage-pays.sql.
--
--  Réglage : config_jeu 'sondage_pays' {ouvert 1/0, jours 3}. Pour arrêter
--  le sondage, passer ouvert à 0 (la carte disparaît pour tout le monde).
--  sondage_pays_etat()                    afficher la carte ?
--  sondage_pays_repondre(p_choix, p_pays) la réponse
--  sondage_pays_fermer()                  « ✕ »
--  Rejouable. Contrôle en une ligne.
-- ===========================================================================
begin;

insert into public.config_jeu (cle, valeur)
values ('sondage_pays', '{"ouvert": 1, "jours": 3}')
on conflict (cle) do nothing;

create table if not exists public.sondage_pays(
  joueur_id  uuid primary key references public.joueurs(id) on delete cascade,
  choix      text check (choix in ('meme', 'apart', 'non', 'egal')),
  pays       text check (pays in ('belgique', 'suisse', 'luxembourg', 'italie', 'espagne', 'allemagne',
                                  'royaume-uni', 'quebec', 'autre')),
  repondu_le timestamptz,
  fermetures integer not null default 0,
  ferme_le   timestamptz
);
alter table public.sondage_pays enable row level security;
revoke all on public.sondage_pays from public, anon, authenticated;

create or replace function public.sondage_pays_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  r jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'sondage_pays'), '{}'::jsonb);
  v_cree timestamptz;
  s sondage_pays%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce((r->>'ouvert')::int, 0) <> 1 then return jsonb_build_object('afficher', false); end if;
  select u.created_at into v_cree from auth.users u where u.id = v_uid;
  if v_cree is null or v_cree > now() - make_interval(days => coalesce((r->>'jours')::int, 3)) then
    return jsonb_build_object('afficher', false);
  end if;
  select * into s from sondage_pays where joueur_id = v_uid;
  if s.repondu_le is not null or coalesce(s.fermetures, 0) >= 2
     or (s.ferme_le is not null and s.ferme_le > now() - interval '20 hours') then
    return jsonb_build_object('afficher', false, 'repondu', s.repondu_le is not null);
  end if;
  return jsonb_build_object('afficher', true, 'relance', coalesce(s.fermetures, 0) = 1);
end; $f$;

create or replace function public.sondage_pays_repondre(p_choix text, p_pays text default null)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  v_pays text := nullif(trim(coalesce(p_pays, '')), '');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_choix is null or p_choix not in ('meme', 'apart', 'non', 'egal') then raise exception 'Réponse inconnue'; end if;
  if p_choix not in ('meme', 'apart') then v_pays := null; end if;
  if v_pays is not null and v_pays not in ('belgique', 'suisse', 'luxembourg', 'italie', 'espagne', 'allemagne',
                                            'royaume-uni', 'quebec', 'autre') then raise exception 'Pays inconnu'; end if;
  insert into sondage_pays as s (joueur_id, choix, pays, repondu_le)
  values (v_uid, p_choix, v_pays, now())
  on conflict (joueur_id) do update set choix = excluded.choix, pays = excluded.pays, repondu_le = excluded.repondu_le
   where s.repondu_le is null;   -- une seule réponse : la première compte
  return jsonb_build_object('ok', true);
end; $f$;

create or replace function public.sondage_pays_fermer()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  insert into sondage_pays as s (joueur_id, fermetures, ferme_le)
  values (v_uid, 1, now())
  on conflict (joueur_id) do update set fermetures = s.fermetures + 1, ferme_le = now();
  return jsonb_build_object('ok', true);
end; $f$;

revoke all on function public.sondage_pays_etat()                from public, anon;
revoke all on function public.sondage_pays_repondre(text, text)  from public, anon;
revoke all on function public.sondage_pays_fermer()              from public, anon;
grant execute on function public.sondage_pays_etat()               to authenticated;
grant execute on function public.sondage_pays_repondre(text, text) to authenticated;
grant execute on function public.sondage_pays_fermer()             to authenticated;

commit;

-- contrôle : true | 1 | nombre de comptes qui verront la carte (plus de 3 jours)
select to_regclass('public.sondage_pays') is not null as table_creee,
       (select (valeur::jsonb->>'ouvert') from public.config_jeu where cle = 'sondage_pays') as ouvert,
       (select count(*) from auth.users u join public.joueurs j on j.id = u.id
         where u.created_at <= now() - interval '3 days') as comptes_concernes;
