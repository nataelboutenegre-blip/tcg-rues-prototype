-- s3-48 (22/11/2026) : échanges de clan, 6 par jour avec chaque coéquipier au lieu de 3 (idée de H34VEN sur Discord,
-- « ok » de Nataël 15 h 02 : « met 6 et on vérifiera »). Mesure avant : 70 % des paires qui échangeaient un jour
-- allaient jusqu'à 3. Le nombre devient un réglage : config_jeu 'clans_s3'.echanges_jour (3 si absent).
-- Il vaut aussi pour les propositions en attente par coéquipier.
-- Retour arrière : update config_jeu set valeur = (valeur::jsonb || '{"echanges_jour":3}')::text where cle = 'clans_s3';

update config_jeu set valeur = (valeur::jsonb || '{"echanges_jour": 6}')::text where cle = 'clans_s3';

create or replace function public.clan_ech_max() returns integer
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select (valeur::jsonb->>'echanges_jour')::int from config_jeu where cle = 'clans_s3'), 3);
$$;
grant execute on function public.clan_ech_max() to authenticated;

do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.clan_ech_proposer(uuid,text,text)'::regprocedure);
  n := replace(d, $a$if clan_ech_du_jour_avec(v_uid, p_cible) >= 3 then raise exception 'Tu as déjà fait tes 3 échanges du jour avec ce coéquipier.'; end if;$a$,
                  $a$if clan_ech_du_jour_avec(v_uid, p_cible) >= clan_ech_max() then raise exception 'Tu as déjà fait tes % échanges du jour avec ce coéquipier.', clan_ech_max(); end if;   -- s3-48$a$);
  n := replace(n, $a$and etat = 'en_attente' and expire_le > now()) >= 3 then
    raise exception 'Tu as déjà 3 propositions en attente avec ce coéquipier.';$a$,
                  $a$and etat = 'en_attente' and expire_le > now()) >= clan_ech_max() then
    raise exception 'Tu as déjà % propositions en attente avec ce coéquipier.', clan_ech_max();   -- s3-48$a$);
  if n = d or position('>= 3' in n) > 0 then raise exception 's3-48 : clan_ech_proposer inchangée'; end if;
  execute n;

  d := pg_get_functiondef('public.clan_ech_repondre(bigint,boolean)'::regprocedure);
  n := replace(d, $a$if not e.inter and clan_ech_du_jour_avec(v_uid, e.proposant) >= 3 then raise exception 'Vous avez déjà fait vos 3 échanges du jour ensemble.'; end if;$a$,
                  $a$if not e.inter and clan_ech_du_jour_avec(v_uid, e.proposant) >= clan_ech_max() then raise exception 'Vous avez déjà fait vos % échanges du jour ensemble.', clan_ech_max(); end if;   -- s3-48$a$);
  if n = d then raise exception 's3-48 : clan_ech_repondre inchangée'; end if;
  execute n;

  d := pg_get_functiondef('public.clan_ech_etat()'::regprocedure);
  n := replace(d, $a$'max', 3,$a$, $a$'max', clan_ech_max(),$a$);
  if n = d then raise exception 's3-48 : clan_ech_etat inchangée'; end if;
  execute n;
end $$;

select clan_ech_max() as max,
       position('clan_ech_max()' in pg_get_functiondef('public.clan_ech_proposer(uuid,text,text)'::regprocedure)) > 0 as proposer,
       position('clan_ech_max()' in pg_get_functiondef('public.clan_ech_repondre(bigint,boolean)'::regprocedure)) > 0 as repondre,
       position('clan_ech_max()' in pg_get_functiondef('public.clan_ech_etat()'::regprocedure)) > 0 as etat;
