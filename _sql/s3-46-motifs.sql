-- s3-46 : le motif de territoire (Boutique › Atelier › Mon territoire)
-- Chaque joueur compose un motif (8 calques au plus) qui se répète sur son territoire, par-dessus sa couleur.
-- Tout le monde le voit sur la carte, de près. De loin il s'efface.
-- Retour arrière : update config_jeu set valeur = (valeur::jsonb || '{"motifs":0}')::text where cle = 'interface';  (plus aucun motif affiché)

create table if not exists public.motif_formes (
  id text primary key,
  pack text            -- null = gratuit ; sinon l'article « motifs-<pack> »
);
alter table public.motif_formes enable row level security;

insert into public.motif_formes(id, pack) values
  ('cercle', null), ('anneau', null), ('carre', null), ('carrearrondi', null), ('losange', null), ('triangle', null),
  ('hexagone', null), ('octogone', null), ('etoile5', null), ('etoile8', null), ('etincelle', null), ('demicercle', null),
  ('ecaille', null), ('quadrilobe', null), ('croix', null), ('goutte', null), ('bande', null), ('bandefine', null),
  ('double', null), ('rayures', null), ('chevron', null), ('vague', null), ('vaguefine', null), ('zigzag', null),
  ('creneaux', null), ('grecque', null), ('pointilles', null), ('diagonale', null), ('croisillons', null), ('grille', null),
  ('damier', null), ('piedpoule', 'tissus'), ('arete', 'tissus'), ('losanges', null), ('eclair', null), ('coeur', null),
  ('flamme', null), ('feuille', null), ('cible', null), ('gemme', null), ('fleche', null), ('engrenage', null),
  ('lys', 'heraldique'), ('couronne', 'heraldique'), ('tour', 'heraldique'), ('epee', 'heraldique'), ('ecusson', 'heraldique'), ('hermine', 'heraldique'),
  ('cle', 'heraldique'), ('trefle', 'heraldique'), ('sapin', 'nature'), ('arbre', 'nature'), ('soleil', 'nature'), ('lune', 'nature'),
  ('flocon', 'nature'), ('epi', 'nature'), ('montagne', 'nature'), ('fleur', 'nature'), ('nuage', 'nature'), ('epingle', 'cartographe'),
  ('rose', 'cartographe'), ('courbes', 'cartographe'), ('ancre', 'cartographe'), ('phare', 'cartographe')
on conflict (id) do update set pack = excluded.pack;

create table if not exists public.joueur_motifs (
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  motif jsonb,
  maj timestamptz not null default now(),
  bloque_jusqu timestamptz,       -- après un retrait par la modération
  retire_par uuid,
  retire_le timestamptz
);
alter table public.joueur_motifs enable row level security;

create table if not exists public.motif_signalements (
  id bigint generated always as identity primary key,
  cible uuid not null references public.joueurs(id) on delete cascade,
  par uuid not null references public.joueurs(id) on delete cascade,
  le timestamptz not null default now(),
  motif jsonb,
  traite boolean not null default false
);
create unique index if not exists motif_signalements_un on public.motif_signalements(cible, par) where not traite;
alter table public.motif_signalements enable row level security;

-- les 4 packs de formes, 1,99 € pièce (éteints tant que l'éditeur n'est pas en ligne)
insert into public.euros_articles(id, type, nom, description, prix_centimes, actif, ordre) values
  ('motifs-heraldique', 'motif', 'Formes Héraldique', '8 formes pour ton motif de territoire : lys, couronne, tour, épée, écusson, hermine, clé, trèfle.', 199, false, 610),
  ('motifs-nature', 'motif', 'Formes Nature', '9 formes pour ton motif de territoire : sapin, arbre, soleil, lune, flocon, épi, montagne, fleur, nuage.', 199, false, 611),
  ('motifs-cartographe', 'motif', 'Formes Cartographe', '5 formes pour ton motif de territoire : épingle, rose des vents, courbes de niveau, ancre, phare.', 199, false, 612),
  ('motifs-tissus', 'motif', 'Trames Tissus', '2 trames pour ton motif de territoire : pied-de-poule et arête de poisson.', 199, false, 613)
on conflict (id) do nothing;

create or replace function public.motifs_ouverts() returns boolean
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select (valeur::jsonb->>'motifs')::int from config_jeu where cle = 'interface'), 1) = 1;
$$;

create or replace function public.motif_packs(p_joueur uuid) returns text[]
language sql stable security definer set search_path to 'public' as $$
  select coalesce(array_agg(substr(i.article_id, 8)), '{}')
    from euros_inventaire i where i.joueur_id = p_joueur and i.article_id like 'motifs-%';
$$;

-- Vérifie un motif et le rend propre (seules les clés connues, valeurs bornées). Lève une erreur lisible sinon.
create or replace function public.motif_net(p jsonb, p_joueur uuid) returns jsonb
language plpgsql stable security definer set search_path to 'public' as $$
declare
  c jsonb; sortie jsonb := '[]'::jsonb; packs text[] := motif_packs(p_joueur);
  f text; pk text; trouve boolean; lettres text := ''; l text; coul text; e text;
  num constant text := '^-?[0-9]+(\.[0-9]+)?$';
  n int := 0;
begin
  if p is null or jsonb_typeof(p) <> 'object' or jsonb_typeof(p->'calques') <> 'array' then
    raise exception 'Motif illisible';
  end if;
  if jsonb_array_length(p->'calques') > 8 then raise exception '8 calques au plus'; end if;
  for c in select * from jsonb_array_elements(p->'calques') loop
    n := n + 1;
    if jsonb_typeof(c) <> 'object' then raise exception 'Motif illisible'; end if;
    f := c->>'forme';
    l := null;
    if f = 'lettre' then
      l := upper(coalesce(c->>'lettre', ''));
      if l !~ '^[A-Z0-9]$' then raise exception 'Lettre inconnue'; end if;
      lettres := lettres || l;
    else
      select true, m.pack into trouve, pk from motif_formes m where m.id = f;
      if trouve is not true then raise exception 'Forme inconnue'; end if;
      if pk is not null and not (pk = any (packs)) then raise exception 'Cette forme fait partie d''un pack que tu n''as pas'; end if;
    end if;
    coul := upper(coalesce(c->>'couleur', ''));
    if coul !~ '^#[0-9A-F]{6}$' then raise exception 'Couleur inconnue'; end if;
    e := coalesce(c->>'e', 'aucun');
    if e not in ('aucun', 'ombre', 'relief', 'contour') then e := 'aucun'; end if;
    if coalesce(c->>'x', '') !~ num or coalesce(c->>'y', '') !~ num or coalesce(c->>'t', '') !~ num
       or coalesce(c->>'r', '0') !~ num or coalesce(c->>'a', '1') !~ num then raise exception 'Motif illisible'; end if;
    sortie := sortie || jsonb_build_array(jsonb_strip_nulls(jsonb_build_object(
      'forme', f, 'lettre', l, 'couleur', coul,
      'x', round(least(100, greatest(0, (c->>'x')::numeric)), 1),
      'y', round(least(100, greatest(0, (c->>'y')::numeric)), 1),
      't', round(least(300, greatest(4, (c->>'t')::numeric)), 1),
      'r', round(least(360, greatest(0, coalesce(c->>'r', '0')::numeric))),
      'a', round(least(1, greatest(0.05, coalesce(c->>'a', '1')::numeric)), 2),
      'fx', coalesce(c->>'fx', '') = 'true', 'fy', coalesce(c->>'fy', '') = 'true', 'e', e)));
  end loop;
  if length(lettres) > 3 then raise exception '3 lettres au plus par motif'; end if;
  -- les lettres dans l'ordre alphabétique : quelques combinaisons refusées, où qu'elles soient posées
  if length(lettres) >= 2 and (select string_agg(x, '' order by x) from regexp_split_to_table(lettres, '') x)
       = any (coalesce((select array(select jsonb_array_elements_text(valeur::jsonb->'motifs_lettres_refusees')) from config_jeu where cle = 'interface'), '{}')
              || array['DFP', 'DP', 'SS', 'KKK', 'MNT', 'CNU', 'HIL']) then
    raise exception 'Cette combinaison de lettres n''est pas acceptée';
  end if;
  return jsonb_build_object('v', 1,
    'densite', least(90, greatest(18, case when coalesce(p->>'densite', '') ~ num then round((p->>'densite')::numeric)::int else 42 end)),
    'intensite', least(100, greatest(15, case when coalesce(p->>'intensite', '') ~ num then round((p->>'intensite')::numeric)::int else 80 end)),
    'quinconce', coalesce(p->>'quinconce', '') = 'true',
    'calques', sortie);
end; $$;

create or replace function public.mon_motif() returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select jsonb_build_object(
    'ouvert', motifs_ouverts(),
    'motif', (select m.motif from joueur_motifs m where m.joueur_id = auth.uid()),
    'bloque_jusqu', (select m.bloque_jusqu from joueur_motifs m where m.joueur_id = auth.uid() and m.bloque_jusqu > now()),
    'packs', to_jsonb(motif_packs(auth.uid())),
    'moderateur', discussion_est_moderateur(auth.uid()),
    'signalements', case when discussion_est_moderateur(auth.uid())
      then (select count(distinct s.cible) from motif_signalements s where not s.traite) else 0 end);
$$;

-- Enregistre mon motif. Aucun calque = je retire mon motif.
create or replace function public.motif_enregistrer(p_motif jsonb) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare moi uuid := auth.uid(); net jsonb; jusqu timestamptz;
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if not motifs_ouverts() then raise exception 'Les motifs ne sont pas ouverts pour le moment'; end if;
  select m.bloque_jusqu into jusqu from joueur_motifs m where m.joueur_id = moi;
  if jusqu is not null and jusqu > now() then
    raise exception 'Ton motif a été retiré par la modération. Tu pourras en refaire un le %', to_char(jusqu at time zone 'Europe/Paris', 'DD/MM à HH24:MI');
  end if;
  net := motif_net(p_motif, moi);
  if jsonb_array_length(net->'calques') = 0 then net := null; end if;
  insert into joueur_motifs(joueur_id, motif, maj) values (moi, net, now())
  on conflict (joueur_id) do update set motif = excluded.motif, maj = now();
  -- un motif changé repart de zéro côté signalements
  update motif_signalements set traite = true where cible = moi and not traite;
  return jsonb_build_object('ok', true, 'motif', net);
end; $$;

-- Les motifs de tous les joueurs, pour la carte (comme couleurs_territoire).
create or replace function public.motifs_territoire() returns table(joueur_id uuid, motif jsonb)
language sql stable security definer set search_path to 'public' as $$
  select m.joueur_id, m.motif from joueur_motifs m where m.motif is not null and motifs_ouverts();
$$;

create or replace function public.motif_signaler(p_joueur uuid) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare moi uuid := auth.uid(); mo jsonb; ps text; nb int; r record;
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if p_joueur = moi then raise exception 'C''est ton propre motif'; end if;
  select m.motif into mo from joueur_motifs m where m.joueur_id = p_joueur;
  if mo is null then raise exception 'Ce joueur n''a pas de motif'; end if;
  if (select count(*) from motif_signalements s where s.par = moi and s.le > now() - interval '1 day') >= 5 then
    raise exception 'Tu as déjà signalé 5 motifs aujourd''hui';
  end if;
  insert into motif_signalements(cible, par, motif) values (p_joueur, moi, mo) on conflict do nothing;
  get diagnostics nb = row_count;
  if nb = 1 and (select count(*) from motif_signalements s where s.cible = p_joueur and not s.traite) = 1 then
    select j.pseudo into ps from joueurs j where j.id = p_joueur;
    for r in select d.joueur_id from discussion_moderateurs d loop
      begin
        perform notifier_joueur(r.joueur_id, 'Motif signalé', 'Le motif de ' || coalesce(ps, 'un joueur') || ' a été signalé.', '/', 'motif-signale');
      exception when others then null; end;
    end loop;
  end if;
  return jsonb_build_object('ok', true, 'deja', nb = 0);
end; $$;

-- Modération : la liste des motifs signalés, puis retirer (bloque 3 jours) ou classer.
create or replace function public.motifs_signales() returns jsonb
language plpgsql stable security definer set search_path to 'public' as $$
begin
  if not discussion_est_moderateur(auth.uid()) then raise exception 'Réservé à la modération'; end if;
  return coalesce((select jsonb_agg(x order by x.nb desc, x.le desc) from (
    select s.cible as joueur_id, j.pseudo, j.couleur, count(*) as nb, max(s.le) as le, m.motif
      from motif_signalements s join joueurs j on j.id = s.cible left join joueur_motifs m on m.joueur_id = s.cible
     where not s.traite group by s.cible, j.pseudo, j.couleur, m.motif) x), '[]'::jsonb);
end; $$;

create or replace function public.motif_moderer(p_joueur uuid, p_retirer boolean, p_jours int default 3) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare moi uuid := auth.uid();
begin
  if not discussion_est_moderateur(moi) then raise exception 'Réservé à la modération'; end if;
  if p_retirer then
    insert into joueur_motifs(joueur_id, motif, maj, bloque_jusqu, retire_par, retire_le)
    values (p_joueur, null, now(), now() + make_interval(days => least(30, greatest(0, coalesce(p_jours, 3)))), moi, now())
    on conflict (joueur_id) do update set motif = null, maj = now(), bloque_jusqu = excluded.bloque_jusqu, retire_par = moi, retire_le = now();
    begin
      perform notifier_joueur(p_joueur, 'Motif retiré', 'Ton motif de territoire a été retiré par la modération.', '/', 'motif-retire');
    exception when others then null; end;
  end if;
  update motif_signalements set traite = true where cible = p_joueur and not traite;
  return jsonb_build_object('ok', true);
end; $$;

revoke all on function public.motif_net(jsonb, uuid), public.motif_packs(uuid) from public, anon, authenticated;
revoke all on function public.motifs_territoire(), public.motifs_ouverts(), public.mon_motif(), public.motif_enregistrer(jsonb), public.motif_signaler(uuid), public.motifs_signales(), public.motif_moderer(uuid, boolean, int) from public, anon;
grant execute on function public.mon_motif(), public.motif_enregistrer(jsonb), public.motif_signaler(uuid), public.motifs_signales(), public.motif_moderer(uuid, boolean, int), public.motifs_territoire(), public.motifs_ouverts() to authenticated;
