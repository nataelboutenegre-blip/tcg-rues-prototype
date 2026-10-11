-- ===========================================================================
--  siege-vente-bloquee.sql — une commune assiégée ne peut plus quitter son
--  propriétaire autrement que par le combat (signalé par Akan, 11 octobre).
--
--  L'abus : à 2 victoires sur 3, le défenseur vendait sa commune au jeu
--  (ou la passait à un ami par la bourse ou un échange) : il touchait le
--  rachat, l'attaquant avait payé ses attaques pour rien.
--
--  Une commune est « assiégée » tant qu'un attaquant a au moins 1 victoire
--  sur elle ET qu'il l'a attaquée dans les dernières 24 h (un siège
--  abandonné ne bloque pas la commune pour toujours).
--
--  Bloqué pendant un siège : vendre au jeu, mettre en vente à la bourse,
--  acheter à la bourse, proposer ou accepter un échange.
--  La défense reste possible, évidemment.
--
--  Chaque fonction est modifiée à partir de sa définition EN PRODUCTION
--  (lue le 11 octobre) ; s'il manque un repère, rien n'est touché.
--  Rejouable. Contrôle attendu à la fin : true | 5 | puis le texte de
--  signer_contrat (à m'envoyer : les contrats sont la dernière porte).
-- ===========================================================================

begin;

create or replace function public.commune_assiegee(p_code text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select exists (select 1 from sieges s
                  where s.commune_code = p_code
                    and coalesce(s.victoires_consecutives, 0) > 0
                    and s.dernier_round > now() - interval '24 hours')
$f$;
revoke all on function public.commune_assiegee(text) from public, anon, authenticated;

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

do $do$
declare d text;
begin
  -- 1. vendre au jeu
  d := pg_get_functiondef('public.vendre_au_jeu(text)'::regprocedure);
  if d not like '%commune_assiegee%' then
    d := pg_temp.remplacer(d, E'  v_prix := prix_rachat(v_tier);\n',
      E'  if commune_assiegee(p_commune_code) then\n'
   || E'    raise exception ''Cette commune est assiegee : tu ne peux pas la vendre tant que le siege dure'';\n'
   || E'  end if;\n\n  v_prix := prix_rachat(v_tier);\n', 'vendre_au_jeu');
    execute d;
  end if;

  -- 2. mettre en vente à la bourse
  d := pg_get_functiondef('public.mettre_en_vente(text, integer)'::regprocedure);
  if d not like '%commune_assiegee%' then
    d := pg_temp.remplacer(d, E'  -- Le plancher : on ne peut pas brader',
      E'  if commune_assiegee(p_commune_code) then\n'
   || E'    raise exception ''Cette commune est assiegee : tu ne peux pas la mettre en vente tant que le siege dure'';\n'
   || E'  end if;\n\n  -- Le plancher : on ne peut pas brader', 'mettre_en_vente');
    execute d;
  end if;

  -- 3. acheter à la bourse (une annonce posée avant le siège)
  d := pg_get_functiondef('public.acheter(text, text)'::regprocedure);
  if d not like '%commune_assiegee%' then
    d := pg_temp.remplacer(d, E'  select solde into v_solde from joueurs where id = v_acheteur for update;',
      E'  if commune_assiegee(p_commune_code) then\n'
   || E'    raise exception ''Cette commune est assiegee : elle ne peut pas changer de main tant que le siege dure'';\n'
   || E'  end if;\n\n  select solde into v_solde from joueurs where id = v_acheteur for update;', 'acheter');
    execute d;
  end if;

  -- 4. proposer un échange
  d := pg_get_functiondef('public.proposer_echange(text, text, text)'::regprocedure);
  if d not like '%commune_assiegee%' then
    d := pg_temp.remplacer(d, E'  -- pas de bouclier en cours',
      E'  if commune_assiegee(p_ma_commune) or commune_assiegee(p_sa_commune) then\n'
   || E'    raise exception ''Une des deux communes est assiegee : pas d''''echange tant que le siege dure.'';\n'
   || E'  end if;\n\n  -- pas de bouclier en cours', 'proposer_echange');
    execute d;
  end if;

  -- 5. accepter un échange (proposé avant le siège)
  d := pg_get_functiondef('public.accepter_echange(bigint)'::regprocedure);
  if d not like '%commune_assiegee%' then
    d := pg_temp.remplacer(d, E'  select c.tier, c.nom into v_tier, v_nom_p from communes c where c.code = e.commune_proposant;',
      E'  if commune_assiegee(e.commune_proposant) or commune_assiegee(e.commune_destinataire) then\n'
   || E'    raise exception ''Une des deux communes est assiegee : pas d''''echange tant que le siege dure.'';\n'
   || E'  end if;\n\n  select c.tier, c.nom into v_tier, v_nom_p from communes c where c.code = e.commune_proposant;', 'accepter_echange');
    execute d;
  end if;
end $do$;

commit;

-- contrôle : true | 5 | texte de signer_contrat
select to_regprocedure('public.commune_assiegee(text)') is not null as garde_creee,
       (select count(*) from pg_proc p where p.pronamespace = 'public'::regnamespace
          and p.proname in ('vendre_au_jeu','mettre_en_vente','acheter','proposer_echange','accepter_echange')
          and pg_get_functiondef(p.oid) like '%commune_assiegee%') as fonctions_protegees_5,
       (select string_agg(pg_get_functiondef(p.oid), E'\n\n') from pg_proc p
         where p.pronamespace = 'public'::regnamespace and p.proname = 'signer_contrat') as signer_contrat_a_envoyer;
