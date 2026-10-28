-- ===========================================================================
--  s2-50 — Échanges de clan : 3 par jour et 3 propositions en attente
--  (28/10, décision de Nataël : « synchroniser le nombre d'échanges avec les
--  propositions » ; avant : 2 échanges conclus par jour, 5 propositions)
--  Touche seulement les nombres dans clan_ech_etat, clan_ech_proposer et
--  clan_ech_repondre (s2-29). Chaque remplacement vérifie qu'il trouve
--  exactement le texte attendu ; sinon rien ne change.
--  Rejouable. Contrôle attendu : true | true | true
-- ===========================================================================
do $do$
declare
  d text;
begin
  -- clan_ech_etat : le maximum affiché dans le jeu
  d := pg_get_functiondef('public.clan_ech_etat()'::regprocedure);
  if position('''max'', 3,' in d) = 0 then
    if (length(d) - length(replace(d, '''max'', 2,', ''))) / length('''max'', 2,') <> 1 then
      raise exception 'clan_ech_etat ne ressemble pas à la version attendue : rien n''a changé';
    end if;
    execute replace(d, '''max'', 2,', '''max'', 3,');
  end if;

  -- clan_ech_proposer : 3 échanges, 3 propositions en attente
  d := pg_get_functiondef('public.clan_ech_proposer(uuid, text, text)'::regprocedure);
  if position('Tu as déjà 3 propositions' in d) = 0 then
    if position('clan_ech_du_jour(v_uid) >= 2 then raise exception ''Tu as déjà fait tes 2 échanges du jour.''' in d) = 0
       or position('>= 5 then' in d) = 0 or position('Tu as déjà 5 propositions en attente.' in d) = 0 then
      raise exception 'clan_ech_proposer ne ressemble pas à la version attendue : rien n''a changé';
    end if;
    d := replace(d, 'clan_ech_du_jour(v_uid) >= 2 then raise exception ''Tu as déjà fait tes 2 échanges du jour.''',
                    'clan_ech_du_jour(v_uid) >= 3 then raise exception ''Tu as déjà fait tes 3 échanges du jour.''');
    d := replace(d, '>= 5 then', '>= 3 then');
    d := replace(d, 'Tu as déjà 5 propositions en attente.', 'Tu as déjà 3 propositions en attente.');
    execute d;
  end if;

  -- clan_ech_repondre : 3 échanges pour les deux joueurs
  d := pg_get_functiondef('public.clan_ech_repondre(bigint, boolean)'::regprocedure);
  if position('fait tes 3 échanges' in d) = 0 then
    if position('clan_ech_du_jour(v_uid) >= 2 then raise exception ''Tu as déjà fait tes 2 échanges du jour.''' in d) = 0
       or position('clan_ech_du_jour(e.proposant) >= 2 then raise exception ''Ton coéquipier a déjà fait ses 2 échanges du jour.''' in d) = 0 then
      raise exception 'clan_ech_repondre ne ressemble pas à la version attendue : rien n''a changé';
    end if;
    d := replace(d, 'clan_ech_du_jour(v_uid) >= 2 then raise exception ''Tu as déjà fait tes 2 échanges du jour.''',
                    'clan_ech_du_jour(v_uid) >= 3 then raise exception ''Tu as déjà fait tes 3 échanges du jour.''');
    d := replace(d, 'clan_ech_du_jour(e.proposant) >= 2 then raise exception ''Ton coéquipier a déjà fait ses 2 échanges du jour.''',
                    'clan_ech_du_jour(e.proposant) >= 3 then raise exception ''Ton coéquipier a déjà fait ses 3 échanges du jour.''');
    execute d;
  end if;
end $do$;

select position('''max'', 3,' in pg_get_functiondef('public.clan_ech_etat()'::regprocedure)) > 0                        as etat_3,
       position('3 propositions en attente' in pg_get_functiondef('public.clan_ech_proposer(uuid, text, text)'::regprocedure)) > 0 as proposer_3,
       position('fait ses 3 échanges' in pg_get_functiondef('public.clan_ech_repondre(bigint, boolean)'::regprocedure)) > 0  as repondre_3;
