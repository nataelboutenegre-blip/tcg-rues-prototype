-- ===========================================================================
--  Modération : lire les tchats de tous les clans (incognito)
--  À lancer dans l'éditeur SQL de Supabase. Lecture seule : rien n'est
--  écrit, rien ne se voit dans le jeu (pas de présence, pas de « vu »).
--  Réglages : la période (48 h) et le clan (null = tous, sinon son sigle).
--  Une ligne par message, du plus récent au plus ancien ; « signale » = nombre
--  de signalements reçus par le message.
-- ===========================================================================
with reglages as (select interval '48 hours' as periode, null::text as sigle)
select k.tag                                                    as clan,
       to_char(m.le at time zone 'Europe/Paris', 'DD/MM HH24:MI') as le,
       j.pseudo                                                 as auteur,
       case when m.supprime then '(supprimé)' else m.texte end  as message,
       (select count(*) from public.clan_signalements s where s.message_id = m.id) as signale,
       m.id
  from public.clan_messages m
  join public.clans k on k.id = m.clan_id
  join public.joueurs j on j.id = m.auteur
  cross join reglages r
 where m.le > now() - r.periode
   and (r.sigle is null or upper(k.tag) = upper(r.sigle))
 order by m.le desc
 limit 500;
