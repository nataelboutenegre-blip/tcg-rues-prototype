-- ===========================================================================
--  s2-62 — Halloween : l'interrupteur de patch265 (aperçus validés le 29/10 :
--  « C'est parfait ! »)
--
--  À LANCER AU MOMENT DE L'ANNONCE, comme s2-60 et s2-61 : le code est déjà
--  en ligne mais reste caché tant que cette fonction n'existe pas.
--
--  Ce que ça allume, du vendredi 30/10 au dimanche 1/11 inclus (fin le 2/11
--  à minuit, heure de Paris, toute seule). Les joueurs déjà connectés le
--  voient au plus tard 10 min après, les autres à l'ouverture du jeu :
--    - le décor « la nuit tombe » : nuit, brume, braises, titre TerreurFront,
--      paquet hanté (les habillages achetés ne changent pas) ;
--    - une question, une fois par appareil : screamers oui ou non
--      (modifiable ensuite dans Profil) ;
--    - pour ceux qui ont dit oui : à l'ouverture d'un paquet GRATUIT, environ
--      1 fois sur 5, au plus 1 toutes les 30 min et 3 par jour. Jamais pendant
--      un achat, un combat ou la mallette.
--
--  Réglages (config_jeu 'halloween') : ouvert (1/0), debut, fin, screamers
--  (1/0), proba, delai_min, max_jour. Pour couper vite : s2-62-halloween-couper.sql
--  Rejouable. Contrôle attendu : true | true | true | true
--  (en_cours vaut false si on le lance avant le 30/10 : c'est normal.)
-- ===========================================================================
begin;

insert into public.config_jeu (cle, valeur)
values ('halloween', '{"ouvert": 1, "debut": "2026-10-30T00:00:00+01:00", "fin": "2026-11-02T00:00:00+01:00", "screamers": 1, "proba": 0.2, "delai_min": 30, "max_jour": 3}')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.halloween_options()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select case when coalesce((h.v ->> 'ouvert')::int, 0) = 1
               and now() >= (h.v ->> 'debut')::timestamptz
               and now() <  (h.v ->> 'fin')::timestamptz
         then jsonb_build_object('actif', 1,
                'fin', h.v ->> 'fin',
                'screamers', coalesce((h.v ->> 'screamers')::int, 0),
                'proba', coalesce((h.v ->> 'proba')::numeric, 0.2),
                'delai_min', coalesce((h.v ->> 'delai_min')::int, 30),
                'max_jour', coalesce((h.v ->> 'max_jour')::int, 3))
         else jsonb_build_object('actif', 0) end
    from (select (select c.valeur::jsonb from config_jeu c where c.cle = 'halloween') as v) h
$f$;

revoke all on function public.halloween_options() from public, anon;
grant execute on function public.halloween_options() to authenticated;

commit;

select (public.halloween_options() ->> 'actif') is not null                                         as fonction_ok,
       (select (c.valeur::jsonb ->> 'fin')::timestamptz = timestamptz '2026-11-02 00:00:00+01'
          from public.config_jeu c where c.cle = 'halloween')                                       as dates_ok,
       has_function_privilege('authenticated', 'public.halloween_options()', 'execute')
         and not has_function_privilege('anon', 'public.halloween_options()', 'execute')            as droits_ok,
       (public.halloween_options() ->> 'actif')::int = 1                                            as en_cours;
