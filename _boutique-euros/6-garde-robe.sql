-- ===========================================================================
--  TerraFront — boutique en euros : 6. garde-robe, testeurs, rétractation
--  25 octobre 2026. À passer APRÈS 1, 2, 4 et 5. Rejouable.
--
--  1. Boutique fermée tant que « boutique_ouverte » est faux, SAUF pour les
--     comptes testeurs (en mode test Stripe, une carte de test donnerait
--     sinon l'objet gratuitement à n'importe quel joueur).
--  2. Garde-robe : le dos de carte et l'habillage de paquet se règlent à part.
--     Un dos ou un habillage acheté en euros s'équipe comme un dos en points.
--     Le paquet Nacre est offert aux OG (il suit la possession du dos OG).
--  3. Rétractation : un joueur qui a choisi « dans 14 jours » peut changer
--     d'avis depuis « Mes achats ». L'objet n'est pas livré ; Nataël rembourse
--     dans Stripe, et le webhook passe la commande en « remboursee ».
--
--  Les fonctions existantes sont modifiées sur place (repères vérifiés :
--  si un repère manque, rien n'est modifié et le script s'arrête).
-- ===========================================================================
begin;

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

-- ---------- 1. testeurs ----------
insert into public.euros_reglages(cle, valeur) values ('boutique_ouverte', 'false')
on conflict (cle) do nothing;
insert into public.euros_reglages(cle, valeur)
select 'testeurs', coalesce(jsonb_agg(j.id::text), '[]'::jsonb)
  from public.joueurs j where j.pseudo = 'Nataël'
on conflict (cle) do nothing;

create or replace function public.euros_peut_acheter(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((euros_reglage('boutique_ouverte'))::boolean, false)
      or coalesce(euros_reglage('testeurs') ? p_uid::text, false)
$f$;

do $do$
declare d text := pg_get_functiondef('public.euros_preparer_commande(text,text,boolean,boolean,boolean,text,date)'::regprocedure);
begin
  if d like '%euros_peut_acheter%' then raise notice 'euros_preparer_commande : déjà fait'; return; end if;
  d := pg_temp.remplacer(d,
    'if not found then raise exception ''Article introuvable''; end if;',
    'if not found then raise exception ''Article introuvable''; end if;' || chr(10)
    || '  if not euros_peut_acheter(v_uid) then raise exception ''La boutique ouvre bientot''; end if;',
    'preparer');
  execute d;
end $do$;

do $do$
declare d text := pg_get_functiondef('public.euros_catalogue()'::regprocedure);
begin
  if d like '%euros_peut_acheter%' then raise notice 'euros_catalogue : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, '''og'', euros_est_og(v_uid),',
    '''og'', euros_est_og(v_uid),' || chr(10)
    || '    ''ouverte'', coalesce((euros_reglage(''boutique_ouverte''))::boolean, false),' || chr(10)
    || '    ''peut_acheter'', euros_peut_acheter(v_uid),', 'catalogue og');
  d := pg_temp.remplacer(d, 'from euros_articles a where a.actif)',
    'from euros_articles a where a.actif and euros_peut_acheter(v_uid))', 'catalogue articles');
  execute d;
end $do$;

-- ---------- 3. rétractation ----------
alter table public.euros_commandes add column if not exists retractation_le timestamptz;

do $do$
declare d text := pg_get_functiondef('public.euros_livrer_differees()'::regprocedure);
begin
  if d like '%retractation_le%' then raise notice 'euros_livrer_differees : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'where statut = ''payee'' and livrer_apres <= now()',
    'where statut = ''payee'' and livrer_apres <= now() and retractation_le is null', 'livrer');
  execute d;
end $do$;

do $do$
declare d text := pg_get_functiondef('public.euros_livrer(uuid)'::regprocedure);
begin
  if d like '%retractation_le%' then raise notice 'euros_livrer : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, 'if not found or c.statut <> ''payee'' then return; end if;',
    'if not found or c.statut <> ''payee'' or c.retractation_le is not null then return; end if;', 'livrer un');
  execute d;
end $do$;

do $do$
declare d text := pg_get_functiondef('public.euros_mes_commandes()'::regprocedure);
begin
  if d like '%retractation_le%' then raise notice 'euros_mes_commandes : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, '''livrer_apres'', c.livrer_apres,',
    '''livrer_apres'', c.livrer_apres, ''retractation_le'', c.retractation_le, ''article_id'', c.article_id,',
    'mes commandes');
  execute d;
end $do$;

create or replace function public.euros_demander_retractation(p_commande uuid)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  c euros_commandes%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into c from euros_commandes where id = p_commande and joueur_id = v_uid for update;
  if not found then raise exception 'Commande introuvable'; end if;
  if c.retractation_le is not null then return euros_mes_commandes(); end if;
  if c.statut <> 'payee' or c.livraison <> 'differee' or c.livrer_apres <= now() then
    raise exception 'Le delai de 14 jours est passe ou l''objet est deja livre';
  end if;
  update euros_commandes set retractation_le = now() where id = c.id;
  return euros_mes_commandes();
end;
$f$;

-- ---------- 2. garde-robe ----------
-- le dos équipé peut maintenant être un dos acheté en euros : on retire le
-- lien obligatoire vers boutique_articles (les contrôles sont dans les fonctions)
do $do$
declare n text;
begin
  select c.conname into n
    from pg_constraint c
   where c.conrelid = 'public.boutique_reglages'::regclass and c.contype = 'f'
     and c.conkey = array[(select a.attnum from pg_attribute a
                            where a.attrelid = 'public.boutique_reglages'::regclass and a.attname = 'dos')];
  if n is not null then execute format('alter table public.boutique_reglages drop constraint %I', n); end if;
end $do$;

do $do$
begin
  if not exists(select 1 from information_schema.columns
                 where table_schema = 'public' and table_name = 'boutique_reglages' and column_name = 'habillage') then
    alter table public.boutique_reglages add column habillage text;
    -- ce que voyaient les OG jusqu'ici : le paquet nacré suivait le dos OG
    update public.boutique_reglages set habillage = 'nacre' where dos = 'dos-og';
  end if;
end $do$;

create or replace function public.garde_robe_possede(p_uid uuid, p_rangee text, p_id text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select case
    when p_id is null then true
    when p_rangee = 'dos' then
         exists(select 1 from boutique_inventaire i join boutique_articles a on a.id = i.article_id
                 where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'dos')
      or exists(select 1 from euros_inventaire i join euros_articles a on a.id = i.article_id
                 where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'dos')
    when p_rangee = 'habillage' then
      case when p_id = 'nacre'
           then exists(select 1 from boutique_inventaire i where i.joueur_id = p_uid and i.article_id = 'dos-og')
           else exists(select 1 from euros_inventaire i join euros_articles a on a.id = i.article_id
                        where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'habillage') end
    else false end
$f$;

create or replace function public.garde_robe()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  r boutique_reglages%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into r from boutique_reglages where joueur_id = v_uid;
  return jsonb_build_object(
    -- un objet retiré (remboursé) n'est plus porté
    'dos', case when garde_robe_possede(v_uid, 'dos', r.dos) then r.dos end,
    'habillage', case when garde_robe_possede(v_uid, 'habillage', r.habillage) then r.habillage end,
    'dos_liste', jsonb_build_array(jsonb_build_object('id', null, 'nom', 'D''origine', 'source', 'base'))
      || coalesce((select jsonb_agg(jsonb_build_object('id', a.id, 'nom', a.nom,
                          'source', case when a.prix = 0 and not a.actif then 'offert' else 'points' end)
                          order by a.ordre)
                     from boutique_inventaire i join boutique_articles a on a.id = i.article_id
                    where i.joueur_id = v_uid and a.type = 'dos'), '[]'::jsonb)
      || coalesce((select jsonb_agg(jsonb_build_object('id', a.id, 'nom', a.nom, 'source', 'euros') order by a.ordre)
                     from euros_inventaire i join euros_articles a on a.id = i.article_id
                    where i.joueur_id = v_uid and a.type = 'dos'), '[]'::jsonb),
    'habillages', jsonb_build_array(jsonb_build_object('id', null, 'nom', 'Classique', 'source', 'base'))
      || case when exists(select 1 from boutique_inventaire i where i.joueur_id = v_uid and i.article_id = 'dos-og')
              then jsonb_build_array(jsonb_build_object('id', 'nacre', 'nom', 'Nacre · OG', 'source', 'offert'))
              else '[]'::jsonb end
      || coalesce((select jsonb_agg(jsonb_build_object('id', a.id, 'nom', a.nom, 'source', 'euros') order by a.ordre)
                     from euros_inventaire i join euros_articles a on a.id = i.article_id
                    where i.joueur_id = v_uid and a.type = 'habillage'), '[]'::jsonb));
end;
$f$;

create or replace function public.garde_robe_equiper(p_rangee text, p_id text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_rangee not in ('dos', 'habillage') then raise exception 'Choix invalide'; end if;
  if not garde_robe_possede(v_uid, p_rangee, nullif(p_id, '')) then raise exception 'Tu ne l''as pas encore'; end if;
  if p_rangee = 'dos' then
    insert into boutique_reglages(joueur_id, dos) values (v_uid, nullif(p_id, ''))
    on conflict (joueur_id) do update set dos = excluded.dos;
  else
    insert into boutique_reglages(joueur_id, habillage) values (v_uid, nullif(p_id, ''))
    on conflict (joueur_id) do update set habillage = excluded.habillage;
  end if;
  return garde_robe();
end;
$f$;

-- boutique() donne aussi l'habillage, pour l'appliquer dès l'ouverture du jeu
do $do$
declare d text := pg_get_functiondef('public.boutique()'::regprocedure);
begin
  if d like '%habillage%' then raise notice 'boutique() : déjà fait'; return; end if;
  d := pg_temp.remplacer(d, '''dos'', (select dos from boutique_reglages where joueur_id = v_uid),',
    '''dos'', (select dos from boutique_reglages where joueur_id = v_uid),' || chr(10)
    || '    ''habillage'', (select case when garde_robe_possede(v_uid, ''habillage'', habillage) then habillage end'
    || ' from boutique_reglages where joueur_id = v_uid),', 'boutique');
  execute d;
end $do$;

-- ---------- droits ----------
revoke all on function public.euros_peut_acheter(uuid)                from public, anon, authenticated;
revoke all on function public.garde_robe_possede(uuid, text, text)    from public, anon, authenticated;
revoke all on function public.euros_demander_retractation(uuid)       from public, anon;
revoke all on function public.garde_robe()                            from public, anon;
revoke all on function public.garde_robe_equiper(text, text)          from public, anon;
grant execute on function public.euros_demander_retractation(uuid)    to authenticated;
grant execute on function public.garde_robe()                         to authenticated;
grant execute on function public.garde_robe_equiper(text, text)       to authenticated;

commit;

-- ---------- contrôle : attendu  false | 1 | true | true | true ----------
select (select valeur from public.euros_reglages where cle = 'boutique_ouverte')            as boutique_ouverte,
       (select jsonb_array_length(valeur) from public.euros_reglages where cle = 'testeurs') as testeurs,
       (select count(*) = 0 from pg_constraint c
         where c.conrelid = 'public.boutique_reglages'::regclass and c.contype = 'f'
           and c.conkey = array[(select a.attnum from pg_attribute a
                                  where a.attrelid = 'public.boutique_reglages'::regclass and a.attname = 'dos')]) as dos_libre,
       pg_get_functiondef('public.euros_preparer_commande(text,text,boolean,boolean,boolean,text,date)'::regprocedure)
         like '%euros_peut_acheter%'                                                         as preparer_protege,
       not has_function_privilege('authenticated', 'public.euros_peut_acheter(uuid)', 'execute') as interne_ferme;
