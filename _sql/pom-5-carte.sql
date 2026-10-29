-- ===========================================================================
--  pom-5 — Plus ou moins : la mini-carte (aperçu validé le 29/10 : « c'est
--  bien comme ça »). Idée née de la remarque de H34VEN (« la photo n'aide
--  pas »).
--
--  À LANCER AU MOMENT DE L'ANNONCE : le jeu (patch263) est déjà prêt mais
--  n'affiche la carte que si le serveur envoie la position des communes.
--  Sans ce fichier, le duel reste comme avant (« ou » entre les photos).
--
--  pom_carte() envoie en plus la latitude et la longitude de chaque commune
--  (partie du jour, entraînement, duels classés). La population reste cachée
--  tant que le duel n'est pas joué.
--  Rejouable. Contrôle attendu : true | true | 0
-- ===========================================================================
begin;

create or replace function public.pom_carte(p_code text, p_reveler boolean)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object('code', c.code, 'nom', c.nom, 'departement', c.departement,
           'photo', c.photo, 'auteur', c.photo_auteur, 'licence', c.photo_licence, 'source', c.photo_source,
           'lat', c.latitude, 'lon', c.longitude,
           'population', case when p_reveler then c.population end)
    from communes c where c.code = p_code
$f$;

revoke all on function public.pom_carte(text, boolean) from public, anon, authenticated;

commit;

select (public.pom_carte(c.code, false) ->> 'lat') is not null                 as position_envoyee,
       (public.pom_carte(c.code, false) ->> 'population') is null              as population_cachee,
       (select count(*) from public.communes x
         where x.photo is not null and x.population >= 500 and x.latitude is null) as communes_sans_position
  from public.communes c
 where c.photo is not null and c.latitude is not null
 limit 1;
