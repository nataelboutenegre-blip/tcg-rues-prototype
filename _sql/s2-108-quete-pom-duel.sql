-- s2-108 (6/11/2026) : la quête « Plus ou moins : 7 sur 10 » compte aussi les duels classés.
-- Signalé par Oshannir : 8/10 en duel classé, quête pas validée. Seule la
-- partie du jour (pom_parties) comptait. Désormais : partie du jour OU duel
-- classé terminé aujourd'hui (pom_duels) avec 7 bonnes réponses ou plus.
-- Effet immédiat, y compris pour les duels déjà joués aujourd'hui.

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

do $$
declare d text := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
begin
  if position('s2-108' in d) > 0 then raise notice 'quetes_liste : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    '   where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini and pp.justes >= 7;',
    '   where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini and pp.justes >= 7;
  -- s2-108 : un duel classé terminé aujourd''hui compte aussi
  v_pom_perf := v_pom_perf + (select count(*) from pom_duels pd
    where pd.joueur_id = p_uid and pd.fini and pd.justes >= 7 and pd.fin_le >= v_minuit);',
    1, 'quetes_liste (duels)');
  d := pg_temp.remp(d,
    '''Plus ou moins : 7 sur 10'',       ''Le jeu du jour'',',
    '''Plus ou moins : 7 sur 10'',       ''Partie du jour ou duel classé'',',
    1, 'quetes_liste (texte)');
  execute d;
end $$;

-- Contrôle attendu : t | t
select position('s2-108' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as quete_ok,
       has_function_privilege('authenticated', 'public.quetes()', 'execute')                      as droits_ok;
