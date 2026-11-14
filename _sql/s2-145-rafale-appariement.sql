-- s2-145 (15/11/2026) : Rafale, plus de duel très déséquilibré quand il n'y a pas le choix (Maroli).
-- Une partie en attente n'est donnée que si l'écart d'Elo est <= ecart_max ET qu'on n'a pas affronté
-- ce joueur depuis 24 h ; sinon on joue « en attente » (comme quand il n'y a personne).
-- Une partie qui attend depuis plus de attente_h heures est donnée à n'importe qui (chacun finit par avoir son résultat).

insert into config_jeu(cle, valeur) values ('rafale_appariement', '{"ecart_max": 200, "attente_h": 12}')
on conflict (cle) do nothing;

CREATE OR REPLACE FUNCTION public.rafale_lancer()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_uid uuid := auth.uid();
  v_id bigint;
  v_elo int;
  s rafale_parties;
  v_lettre text;
  v_cfg jsonb := coalesce((select valeur::jsonb from config_jeu where cle = 'rafale_appariement'), '{}'::jsonb);   -- s2-145
  v_ecart int := coalesce((v_cfg ->> 'ecart_max')::int, 200);
  v_attente int := coalesce((v_cfg ->> 'attente_h')::int, 12);
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('rafale' || v_uid::text, 7));

  select id into v_id from rafale_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_id is not null then
    perform rafale_rattraper(v_id);
    if not (select fini from rafale_parties where id = v_id) then return rafale_vue(v_id); end if;
  end if;

  insert into rafale_joueurs(joueur_id) values (v_uid) on conflict do nothing;
  select elo into v_elo from rafale_joueurs where joueur_id = v_uid;

  -- un adversaire : partie classée finie, pas encore affrontée, d'un autre
  -- joueur ; de préférence pas affronté depuis 24 h, puis Elo proche, puis
  -- la plus ancienne
  -- s2-145 : Elo trop loin ou déjà affronté depuis 24 h = refusé, sauf partie en attente depuis plus de attente_h
  select p.* into s
    from rafale_parties p
    left join rafale_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee
     and p.joueur_id <> v_uid and p.cible_id is null and not p.amical
     and (p.fin_le < now() - make_interval(hours => v_attente)
          or (abs(coalesce(r.elo, 1000) - v_elo) <= v_ecart
              and not exists (select 1 from rafale_parties m
                                join rafale_parties ms on ms.id = m.source_id
                               where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id
                                 and m.cree_le > now() - interval '24 hours')))
   order by exists (select 1 from rafale_parties m
                      join rafale_parties ms on ms.id = m.source_id
                     where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id
                       and m.cree_le > now() - interval '24 hours'),
            abs(coalesce(r.elo, 1000) - v_elo), p.fin_le
   limit 1
   for update of p skip locked;

  if s.id is not null then
    update rafale_parties set utilisee = true where id = s.id;
    v_lettre := s.lettre;
  else
    v_lettre := substr(rafale_lettres(), 1 + floor(random() * length(rafale_lettres()))::int, 1);
  end if;

  insert into rafale_parties(joueur_id, lettre, source_id) values (v_uid, v_lettre, s.id)
  returning id into v_id;
  return rafale_vue(v_id);
end;
$function$;
