-- ===========================================================================
--  TerraFront — s2-88 : échanges de clan, 3 par jour AVEC CHAQUE coéquipier
--  (3/11/2026, avec patch327). Idée d'Oshannir et Maroli, décision de Nataël :
--  « ça ajoute un réel intérêt au clan, sinon ça bride trop ; on check d'ici
--  quelques jours » (lecture-echanges-clan-limite.sql : 53 % des jours
--  d'échange finissaient à la limite de 3, toujours les mêmes 11 joueurs).
--
--  Avant (s2-50) : 3 échanges conclus par jour et par joueur, tous coéquipiers
--  confondus, et 3 propositions en attente au plus.
--  Maintenant : 3 échanges par jour pour chaque paire de coéquipiers, et
--  3 propositions en attente par coéquipier. Pas de plafond total.
--  clan_ech_etat() dit « par_membre » et, pour chaque coéquipier, combien
--  d'échanges vous avez déjà faits ensemble aujourd'hui (l'écran s'en sert).
--
--  Chaque fonction est modifiée à partir de sa définition EN BASE ; chaque
--  repère doit s'y trouver exactement une fois, sinon rien ne change.
--  Retour en arrière : relancer s2-50 ne suffit pas, demander à Claude.
--  Rejouable. Contrôle attendu : true | true | true | true
-- ===========================================================================

-- les échanges conclus aujourd'hui entre deux joueurs (jour de Paris)
create or replace function public.clan_ech_du_jour_avec(p_a uuid, p_b uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from clan_echanges e
   where e.etat = 'accepte'
     and ((e.proposant = p_a and e.destinataire = p_b) or (e.proposant = p_b and e.destinataire = p_a))
     and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris');
$f$;
revoke all on function public.clan_ech_du_jour_avec(uuid, uuid) from public, anon, authenticated;

do $do$
declare
  d text;
  f text;
  -- [fonction, avant, après]
  r text[][] := array[
    ['public.clan_ech_proposer(uuid, text, text)',
     'clan_ech_du_jour(v_uid) >= 3 then raise exception ''Tu as déjà fait tes 3 échanges du jour.''',
     'clan_ech_du_jour_avec(v_uid, p_cible) >= 3 then raise exception ''Tu as déjà fait tes 3 échanges du jour avec ce coéquipier.'''],
    ['public.clan_ech_proposer(uuid, text, text)',
     'where proposant = v_uid and etat = ''en_attente'' and expire_le > now()) >= 3 then',
     'where proposant = v_uid and destinataire = p_cible and etat = ''en_attente'' and expire_le > now()) >= 3 then'],
    ['public.clan_ech_proposer(uuid, text, text)',
     '''Tu as déjà 3 propositions en attente.''',
     '''Tu as déjà 3 propositions en attente avec ce coéquipier.'''],
    ['public.clan_ech_repondre(bigint, boolean)',
     'clan_ech_du_jour(v_uid) >= 3 then raise exception ''Tu as déjà fait tes 3 échanges du jour.''',
     'clan_ech_du_jour_avec(v_uid, e.proposant) >= 3 then raise exception ''Vous avez déjà fait vos 3 échanges du jour ensemble.'''],
    ['public.clan_ech_repondre(bigint, boolean)',
     'if clan_ech_du_jour(e.proposant) >= 3 then raise exception ''Ton coéquipier a déjà fait ses 3 échanges du jour.''; end if;',
     '-- s2-88 : la limite est par paire de coéquipiers (ligne au-dessus)'],
    ['public.clan_ech_etat()',
     '''faits'', clan_ech_du_jour(v_uid), ''max'', 3,',
     '''faits'', clan_ech_du_jour(v_uid), ''max'', 3, ''par_membre'', true,'],
    ['public.clan_ech_etat()',
     'jsonb_build_object(''id'', j.id, ''pseudo'', j.pseudo)',
     'jsonb_build_object(''id'', j.id, ''pseudo'', j.pseudo, ''faits'', clan_ech_du_jour_avec(v_uid, j.id))']
  ];
  i int;
  n int;
begin
  foreach f in array array['public.clan_ech_proposer(uuid, text, text)', 'public.clan_ech_repondre(bigint, boolean)', 'public.clan_ech_etat()'] loop
    d := pg_get_functiondef(f::regprocedure);
    if position('clan_ech_du_jour_avec' in d) > 0 then
      raise notice 's2-88 : % déjà modifiée', f;
      continue;
    end if;
    for i in 1 .. array_length(r, 1) loop
      if r[i][1] <> f then continue; end if;
      n := (length(d) - length(replace(d, r[i][2], ''))) / length(r[i][2]);
      if n <> 1 then
        raise exception 's2-88 : dans %, repère trouvé % fois (1 attendu) : %. Rien n''est changé.', f, n, r[i][2];
      end if;
      d := replace(d, r[i][2], r[i][3]);
    end loop;
    execute d;
  end loop;
end $do$;

-- Contrôle : true | true | true | true
select position('clan_ech_du_jour_avec(v_uid, p_cible)' in pg_get_functiondef('public.clan_ech_proposer(uuid, text, text)'::regprocedure)) > 0 as proposer_ok,
       position('destinataire = p_cible and etat' in pg_get_functiondef('public.clan_ech_proposer(uuid, text, text)'::regprocedure)) > 0      as attente_ok,
       position('clan_ech_du_jour_avec(v_uid, e.proposant)' in pg_get_functiondef('public.clan_ech_repondre(bigint, boolean)'::regprocedure)) > 0 as repondre_ok,
       position('par_membre' in pg_get_functiondef('public.clan_ech_etat()'::regprocedure)) > 0                                                 as etat_ok;
