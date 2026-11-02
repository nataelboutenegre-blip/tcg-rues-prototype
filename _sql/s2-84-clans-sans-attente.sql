-- ===========================================================================
--  TerraFront — s2-84 : plus d'attente pour rejoindre un clan (2/11/2026)
--  Décidé par Nataël le 2/11 au soir : l'attente de 48 h après avoir quitté
--  (ou été exclu d') un clan passe à 0. Les échanges sont déjà protégés :
--  ils ne s'ouvrent que 48 h après l'arrivée dans un clan (s2-29), et ça ne
--  change pas.
--
--  L'attente devient un réglage, en heures : config_jeu 'clan_attente_h'.
--  0 = aucune attente. Pour la remettre, mettre par exemple '48' (dernière
--  ligne commentée). Si le réglage disparaît, on revient à 48 h comme avant.
--  Toutes les fonctions qui vérifiaient l'attente passent par clan_attente()
--  (créer un clan, accepter une invitation, postuler, accepter un candidat,
--  mon_clan) : rien d'autre à modifier.
--  Rejouable. Contrôle en une ligne : 0 | true | 0
-- ===========================================================================

insert into public.config_jeu (cle, valeur) values ('clan_attente_h', '0')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.clan_attente(p_uid uuid)
 returns timestamptz language sql stable security definer set search_path to 'public'
as $f$
  -- s2-84 : attente réglable (config_jeu 'clan_attente_h', en heures ; 0 = aucune). Null si le joueur est libre.
  select d.le + make_interval(hours => h.n)
    from clan_departs d,
         (select coalesce((select nullif(trim(both '"' from c.valeur::text), '')::int
                             from config_jeu c where c.cle = 'clan_attente_h'), 48) as n) h
   where d.joueur_id = p_uid and h.n > 0 and d.le + make_interval(hours => h.n) > now()
   order by d.le desc
   limit 1;
$f$;

-- Contrôle : 0 | true | 0  (réglage, fonction en place, joueurs encore bloqués)
select (select valeur::text from public.config_jeu where cle = 'clan_attente_h')                          as attente_h,
       position('s2-84' in pg_get_functiondef('public.clan_attente(uuid)'::regprocedure)) > 0         as fonction_ok,
       (select count(*) from public.clan_departs d where public.clan_attente(d.joueur_id) is not null) as encore_bloques;

-- Pour remettre une attente (en heures) :
-- update public.config_jeu set valeur = '48' where cle = 'clan_attente_h';
