-- ===========================================================================
--  TerraFront — saison 2, Terra : Bourse et Échange sur les doublons
--  (9 octobre 2026)
--
--  SANS EFFET EN SAISON 1 : toutes les fonctions refusent tant que
--  terra_ouverte() est faux. La Bourse et l'Échange de la saison 1
--  (annonces, echanges, possessions) ne sont pas touchés.
--  À lancer APRÈS s2-8-terra-contrat.sql.
--
--  Règle commune (décidée le 9 octobre) : on ne vend et on n'échange que
--  des DOUBLONS. On garde toujours un exemplaire de chaque commune ; les
--  exemplaires Aurore ne partent jamais.
--
--  Bourse :
--   - mettre en vente = l'exemplaire quitte la collection et attend dans
--     l'annonce (personne ne peut le vendre deux fois) ; retirer le rend ;
--   - une annonce par commune et par vendeur ; prix minimum = prix de
--     revente au jeu (5 / 20 / 100 / 300 / 600) ;
--   - acheter : le prix passe de l'acheteur au vendeur, l'exemplaire
--     rejoint la collection de l'acheteur.
--  Échange :
--   - un doublon contre un doublon d'un autre joueur, même rareté ;
--   - commission_echange() payée par chacun, comme en saison 1 ;
--   - rien n'est bloqué à l'envoi : tout est revérifié à l'acceptation ;
--   - 48 h pour répondre ; 20 propositions envoyées en attente au plus ;
--     une même commune donnée ne peut pas être promise plus de fois
--     qu'elle n'a de doublons.
--
--  Fonctions pour le jeu (authenticated) :
--    terra_marche()                         annonces en cours
--    terra_mettre_en_vente(code, prix)
--    terra_retirer_de_la_vente(code)
--    terra_acheter(id)
--    terra_cibles_echange(tier, recherche)  doublons des autres joueurs
--    terra_proposer_echange(ma, sa, autre, message)
--    terra_mes_echanges()
--    terra_accepter_echange(id) / terra_refuser_echange(id)
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

create table if not exists public.terra_annonces(
  id           bigserial primary key,
  vendeur      uuid not null references public.joueurs(id) on delete cascade,
  commune_code text not null references public.communes(code),
  prix         integer not null check (prix > 0),
  cree_le      timestamptz not null default now(),
  unique (vendeur, commune_code)
);
create index if not exists terra_annonces_commune on public.terra_annonces(commune_code);

create table if not exists public.terra_echanges(
  id                   bigserial primary key,
  proposant            uuid not null references public.joueurs(id) on delete cascade,
  destinataire         uuid not null references public.joueurs(id) on delete cascade,
  commune_proposant    text not null references public.communes(code),
  commune_destinataire text not null references public.communes(code),
  message              text,
  etat                 text not null default 'en_attente'
                       check (etat in ('en_attente', 'accepte', 'refuse', 'annule', 'expire')),
  cree_le              timestamptz not null default now(),
  expire_le            timestamptz not null default now() + interval '48 hours',
  repondu_le           timestamptz
);
create index if not exists terra_echanges_proposant on public.terra_echanges(proposant, etat);
create index if not exists terra_echanges_destinataire on public.terra_echanges(destinataire, etat);

alter table public.terra_annonces enable row level security;
alter table public.terra_echanges enable row level security;
revoke all on public.terra_annonces, public.terra_echanges from public, anon, authenticated;
revoke all on sequence public.terra_annonces_id_seq, public.terra_echanges_id_seq from public, anon, authenticated;

-- Le nombre de doublons utilisables d'un joueur pour une commune (0 si aucun).
create or replace function public.terra_doublons(p_joueur uuid, p_code text)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select greatest(0, t.exemplaires - greatest(1, t.aurore))
                     from terra_collection t
                    where t.joueur_id = p_joueur and t.commune_code = p_code), 0);
$f$;

-- Ajoute un exemplaire ; renvoie vrai si la commune est nouvelle pour lui.
create or replace function public.terra_ajouter(p_joueur uuid, p_code text, p_origine text)
 returns boolean language plpgsql security definer set search_path to 'public'
as $f$
declare v_ex integer;
begin
  insert into terra_collection as tc (joueur_id, commune_code, exemplaires, origine)
  values (p_joueur, p_code, 1, p_origine)
  on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + 1
  returning tc.exemplaires into v_ex;
  return v_ex = 1;
end;
$f$;

-- ---------------------------------------------------------------------------
--  Bourse
-- ---------------------------------------------------------------------------
create or replace function public.terra_marche()
 returns table(id bigint, commune_code text, nom text, departement text, tier text, population integer,
               prix integer, vendeur uuid, pseudo text, mienne boolean, je_l_ai boolean)
 language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  return query
  select a.id, a.commune_code::text, c.nom::text, c.departement::text, c.tier::text, c.population,
         a.prix, a.vendeur, j.pseudo::text, a.vendeur = auth.uid(),
         exists (select 1 from terra_collection t
                  where t.joueur_id = auth.uid() and t.commune_code = a.commune_code and t.exemplaires > 0)
    from terra_annonces a
    join communes c on c.code = a.commune_code
    join joueurs j on j.id = a.vendeur
   order by a.cree_le desc
   limit 400;
end;
$f$;

create or replace function public.terra_mettre_en_vente(p_code text, p_prix integer)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_tier text;
  v_min integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select c.tier into v_tier from communes c where c.code = p_code;
  if v_tier is null then raise exception 'Commune inconnue'; end if;
  v_min := terra_prix_revente(v_tier);
  if p_prix is null or p_prix < v_min then
    raise exception 'Prix minimum pour cette rarete : % points. Le jeu te la rachete a ce prix.', v_min;
  end if;
  if p_prix > 1000000 then raise exception 'Prix trop eleve'; end if;
  perform 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = p_code for update;
  if exists (select 1 from terra_annonces a where a.vendeur = v_uid and a.commune_code = p_code) then
    raise exception 'Cette commune est deja en vente';
  end if;
  if terra_doublons(v_uid, p_code) < 1 then
    raise exception 'Tu ne peux vendre que tes doublons';
  end if;
  update terra_collection set exemplaires = exemplaires - 1
   where joueur_id = v_uid and commune_code = p_code;
  insert into terra_annonces (vendeur, commune_code, prix) values (v_uid, p_code, p_prix);
end;
$f$;

create or replace function public.terra_retirer_de_la_vente(p_code text)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_id bigint;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  delete from terra_annonces a where a.vendeur = v_uid and a.commune_code = p_code returning a.id into v_id;
  if v_id is null then raise exception 'Pas d''annonce sur cette commune'; end if;
  perform terra_ajouter(v_uid, p_code, 'bourse');
end;
$f$;

create or replace function public.terra_acheter(p_id bigint)
 returns table(nom text, nouvelle boolean, prix integer, solde integer)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  a terra_annonces%rowtype;
  v_solde integer;
  v_nouvelle boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select * into a from terra_annonces t where t.id = p_id for update;
  if a.id is null then raise exception 'Cette annonce n''existe plus'; end if;
  if a.vendeur = v_uid then raise exception 'C''est ton annonce'; end if;
  -- les deux soldes, toujours dans le meme ordre pour eviter les interblocages
  perform 1 from joueurs j where j.id in (v_uid, a.vendeur) order by j.id for update;
  select coalesce(j.solde, 0) into v_solde from joueurs j where j.id = v_uid;
  if v_solde < a.prix then raise exception 'Il te manque % pts', a.prix - v_solde; end if;
  delete from terra_annonces t where t.id = p_id;
  perform set_config('terrafront.motif', 'terra_bourse', true);
  update joueurs set solde = coalesce(joueurs.solde, 0) - a.prix where id = v_uid;
  update joueurs set solde = coalesce(joueurs.solde, 0) + a.prix where id = a.vendeur;
  v_nouvelle := terra_ajouter(v_uid, a.commune_code, 'bourse');
  return query select (select c.nom::text from communes c where c.code = a.commune_code), v_nouvelle, a.prix,
                      (select j.solde from joueurs j where j.id = v_uid);
end;
$f$;

-- ---------------------------------------------------------------------------
--  Échange
-- ---------------------------------------------------------------------------
create or replace function public.terra_cibles_echange(p_tier text, p_recherche text default '')
 returns table(commune_code text, nom text, departement text, tier text, proprietaire uuid, pseudo text,
               nouvelle boolean)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_r text := btrim(coalesce(p_recherche, ''));
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  return query
  select t.commune_code::text, c.nom::text, c.departement::text, c.tier::text, t.joueur_id, j.pseudo::text,
         not exists (select 1 from terra_collection m
                      where m.joueur_id = auth.uid() and m.commune_code = t.commune_code and m.exemplaires > 0)
    from terra_collection t
    join communes c on c.code = t.commune_code
    join joueurs j on j.id = t.joueur_id
   where t.joueur_id <> auth.uid()
     and c.tier = p_tier
     and t.exemplaires - greatest(1, t.aurore) > 0
     and (v_r = '' or c.nom ilike '%' || v_r || '%' or c.departement ilike v_r || '%')
   -- d'abord celles qui manquent a ma collection
   order by 7 desc, c.nom, j.pseudo
   limit 80;
end;
$f$;

create or replace function public.terra_proposer_echange(p_ma_commune text, p_sa_commune text, p_autre uuid,
                                                         p_message text default null)
 returns table(id bigint, message text)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_tier_a text;
  v_tier_b text;
  v_nom_b text;
  v_mot text;
  v_id bigint;
begin
  if v_uid is null then raise exception 'Connecte-toi pour proposer un echange.'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  if p_autre is null or p_autre = v_uid then raise exception 'Choisis un autre joueur.'; end if;
  if p_ma_commune = p_sa_commune then raise exception 'Choisis deux communes differentes.'; end if;

  update terra_echanges e set etat = 'expire', repondu_le = now()
   where e.etat = 'en_attente' and e.expire_le <= now() and e.proposant = v_uid;

  select c.tier into v_tier_a from communes c where c.code = p_ma_commune;
  select c.tier, c.nom into v_tier_b, v_nom_b from communes c where c.code = p_sa_commune;
  if v_tier_a is null or v_tier_b is null then raise exception 'Commune inconnue.'; end if;
  if v_tier_a <> v_tier_b then raise exception 'Les deux communes doivent etre de la meme rarete.'; end if;

  if terra_doublons(v_uid, p_ma_commune) < 1 then
    raise exception 'Tu ne peux echanger que tes doublons.';
  end if;
  if terra_doublons(p_autre, p_sa_commune) < 1 then
    raise exception 'Ce joueur n''a plus de doublon de cette commune.';
  end if;
  if (select count(*) from terra_echanges e
       where e.proposant = v_uid and e.etat = 'en_attente' and e.commune_proposant = p_ma_commune)
     >= terra_doublons(v_uid, p_ma_commune) then
    raise exception 'Tous tes doublons de cette commune sont deja promis dans d''autres propositions.';
  end if;
  if exists (select 1 from terra_echanges e
              where e.proposant = v_uid and e.destinataire = p_autre and e.etat = 'en_attente'
                and e.commune_proposant = p_ma_commune and e.commune_destinataire = p_sa_commune) then
    raise exception 'Tu as deja fait cette proposition.';
  end if;
  if (select count(*) from terra_echanges e where e.proposant = v_uid and e.etat = 'en_attente') >= 20 then
    raise exception 'Tu as deja 20 propositions en attente : attends des reponses ou annules-en.';
  end if;

  v_mot := nullif(btrim(regexp_replace(
             regexp_replace(coalesce(p_message, ''), '[[:cntrl:]]+', ' ', 'g'),
             '\s+', ' ', 'g')), '');
  if v_mot is not null and length(v_mot) > 200 then v_mot := substr(v_mot, 1, 200); end if;
  if v_mot is not null and to_regclass('public.amis') is not null then
    if exists (select 1 from amis a
                where a.joueur_id = p_autre and a.ami_id = v_uid and a.etat = 'bloque') then
      v_mot := null;
    end if;
  end if;

  insert into terra_echanges (proposant, destinataire, commune_proposant, commune_destinataire, message)
  values (v_uid, p_autre, p_ma_commune, p_sa_commune, v_mot)
  returning terra_echanges.id into v_id;

  return query select v_id, ('Proposition envoyee pour ' || v_nom_b)::text;
end;
$f$;

create or replace function public.terra_mes_echanges()
 returns table(id bigint, sens text, autre_pseudo text, autre_id uuid,
               je_donne_code text, je_donne_nom text, je_donne_dept text,
               je_recois_code text, je_recois_nom text, je_recois_dept text,
               tier text, commission integer, expire_le timestamptz, mot text, nouvelle boolean)
 language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;

  update terra_echanges e set etat = 'expire', repondu_le = now()
   where e.etat = 'en_attente' and e.expire_le <= now()
     and (e.proposant = v_uid or e.destinataire = v_uid);
  -- un doublon vendu, echange ou revendu entre-temps : la proposition tombe
  update terra_echanges e set etat = 'annule', repondu_le = now()
   where e.etat = 'en_attente'
     and (e.proposant = v_uid or e.destinataire = v_uid)
     and (terra_doublons(e.proposant, e.commune_proposant) < 1
       or terra_doublons(e.destinataire, e.commune_destinataire) < 1);

  return query
  select e.id,
         case when e.proposant = v_uid then 'envoye' else 'recu' end,
         j.pseudo::text, j.id,
         cd.code::text, cd.nom::text, cd.departement::text,
         cr.code::text, cr.nom::text, cr.departement::text,
         cd.tier::text, commission_echange(cd.tier), e.expire_le, e.message,
         not exists (select 1 from terra_collection m
                      where m.joueur_id = v_uid and m.commune_code = cr.code and m.exemplaires > 0)
    from terra_echanges e
    join joueurs j on j.id = case when e.proposant = v_uid then e.destinataire else e.proposant end
    join communes cd on cd.code = case when e.proposant = v_uid then e.commune_proposant else e.commune_destinataire end
    join communes cr on cr.code = case when e.proposant = v_uid then e.commune_destinataire else e.commune_proposant end
   where e.etat = 'en_attente'
     and (e.proposant = v_uid or e.destinataire = v_uid)
   order by e.cree_le desc;
end;
$f$;

create or replace function public.terra_accepter_echange(p_id bigint)
 returns table(message text, commission integer, nouvelle boolean)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  e terra_echanges%rowtype;
  v_tier text;
  v_comm integer;
  v_nom_p text;
  v_nom_d text;
  v_sp integer;
  v_sd integer;
  v_nouvelle boolean;
begin
  if v_uid is null then raise exception 'Connecte-toi pour accepter cet echange.'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select * into e from terra_echanges t where t.id = p_id for update;
  if e.id is null then raise exception 'Cette proposition n''existe plus.'; end if;
  if e.destinataire <> v_uid then raise exception 'Cette proposition ne t''est pas adressee.'; end if;
  if e.etat <> 'en_attente' then raise exception 'Cette proposition a deja ete traitee.'; end if;
  if e.expire_le <= now() then
    update terra_echanges set etat = 'expire', repondu_le = now() where id = p_id;
    raise exception 'Cette proposition a expire.';
  end if;

  perform 1 from terra_collection t
   where (t.joueur_id, t.commune_code) in ((e.proposant, e.commune_proposant), (v_uid, e.commune_destinataire))
   order by t.joueur_id, t.commune_code for update;
  if terra_doublons(e.proposant, e.commune_proposant) < 1 then
    update terra_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'L''autre joueur n''a plus de doublon de cette commune.';
  end if;
  if terra_doublons(v_uid, e.commune_destinataire) < 1 then
    update terra_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Tu n''as plus de doublon de cette commune.';
  end if;

  select c.tier, c.nom into v_tier, v_nom_p from communes c where c.code = e.commune_proposant;
  select c.nom into v_nom_d from communes c where c.code = e.commune_destinataire;
  v_comm := commission_echange(v_tier);

  perform 1 from joueurs j where j.id in (e.proposant, v_uid) order by j.id for update;
  select coalesce(j.solde, 0) into v_sp from joueurs j where j.id = e.proposant;
  select coalesce(j.solde, 0) into v_sd from joueurs j where j.id = v_uid;
  if v_sd < v_comm then raise exception 'Il te manque % pts pour la commission.', v_comm - v_sd; end if;
  if v_sp < v_comm then raise exception 'L''autre joueur n''a plus de quoi payer la commission.'; end if;

  update terra_collection set exemplaires = exemplaires - 1
   where joueur_id = e.proposant and commune_code = e.commune_proposant;
  update terra_collection set exemplaires = exemplaires - 1
   where joueur_id = v_uid and commune_code = e.commune_destinataire;
  v_nouvelle := terra_ajouter(v_uid, e.commune_proposant, 'echange');
  perform terra_ajouter(e.proposant, e.commune_destinataire, 'echange');

  perform set_config('terrafront.motif', 'terra_echange', true);
  update joueurs set solde = coalesce(joueurs.solde, 0) - v_comm where id in (e.proposant, v_uid);
  update terra_echanges set etat = 'accepte', repondu_le = now() where id = p_id;

  return query select ('Echange conclu : ' || v_nom_p || ' contre ' || v_nom_d)::text, v_comm, v_nouvelle;
end;
$f$;

create or replace function public.terra_refuser_echange(p_id bigint)
 returns table(message text)
 language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); e terra_echanges%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select * into e from terra_echanges t where t.id = p_id for update;
  if e.id is null or e.etat <> 'en_attente' then raise exception 'Cette proposition n''est plus en attente.'; end if;
  if e.destinataire = v_uid then
    update terra_echanges set etat = 'refuse', repondu_le = now() where id = p_id;
    return query select 'Proposition refusee'::text;
  elsif e.proposant = v_uid then
    update terra_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    return query select 'Proposition annulee'::text;
  else
    raise exception 'Cette proposition ne te concerne pas.';
  end if;
end;
$f$;

-- Droits ----------------------------------------------------------------------------------
revoke all on function public.terra_doublons(uuid, text) from public, anon, authenticated;
revoke all on function public.terra_ajouter(uuid, text, text) from public, anon, authenticated;
revoke all on function public.terra_marche() from public, anon;
revoke all on function public.terra_mettre_en_vente(text, integer) from public, anon;
revoke all on function public.terra_retirer_de_la_vente(text) from public, anon;
revoke all on function public.terra_acheter(bigint) from public, anon;
revoke all on function public.terra_cibles_echange(text, text) from public, anon;
revoke all on function public.terra_proposer_echange(text, text, uuid, text) from public, anon;
revoke all on function public.terra_mes_echanges() from public, anon;
revoke all on function public.terra_accepter_echange(bigint) from public, anon;
revoke all on function public.terra_refuser_echange(bigint) from public, anon;
grant execute on function public.terra_marche() to authenticated;
grant execute on function public.terra_mettre_en_vente(text, integer) to authenticated;
grant execute on function public.terra_retirer_de_la_vente(text) to authenticated;
grant execute on function public.terra_acheter(bigint) to authenticated;
grant execute on function public.terra_cibles_echange(text, text) to authenticated;
grant execute on function public.terra_proposer_echange(text, text, uuid, text) to authenticated;
grant execute on function public.terra_mes_echanges() to authenticated;
grant execute on function public.terra_accepter_echange(bigint) to authenticated;
grant execute on function public.terra_refuser_echange(bigint) to authenticated;

-- Contrôle ---------------------------------------------------------------------------------
select terra_ouverte() as terra_ouverte_doit_etre_false,
       (select count(*) from pg_proc where proname in ('terra_doublons', 'terra_ajouter', 'terra_marche',
          'terra_mettre_en_vente', 'terra_retirer_de_la_vente', 'terra_acheter', 'terra_cibles_echange',
          'terra_proposer_echange', 'terra_mes_echanges', 'terra_accepter_echange', 'terra_refuser_echange')) as fonctions_doit_etre_11,
       has_function_privilege('authenticated', 'public.terra_ajouter(uuid,text,text)', 'execute') as ajouter_ouvert_doit_etre_false;
