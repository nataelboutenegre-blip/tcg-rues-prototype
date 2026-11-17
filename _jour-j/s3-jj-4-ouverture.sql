-- ===========================================================================
--  Saison 3, jour J — étape 4 : OUVERTURE (après la clôture et l'entrée de la Suisse)
--  Allume le siège, la zone de départ et le Mess ; coupe la réserve d'accueil
--  (décision du 16/11 : sinon les comptes de plus de 7 jours n'ont aucun paquet
--  du Front) ; ouvre le pass (l'XP compte ; la VENTE reste à part).
--  Réversible : remettre les valeurs (siège 0, zone 0, mess 0, réserve 1).
--  Contrôle attendu : 1 | 1 | 1 | 0 | <date> | true
-- ===========================================================================
begin;
do $$ begin
  if (select etat from saisons where id = 'saison-2') <> 'terminee'
     or not exists (select 1 from saisons where id = 'saison-3') then
    raise exception 'La clôture n''est pas passée : rien n''a changé';
  end if;
end $$;
update public.config_jeu set valeur = (valeur::jsonb || '{"actif": 1}'::jsonb)::text  where cle = 'siege';
update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 1}'::jsonb)::text where cle = 'zone_depart';
update public.config_jeu set valeur = (valeur::jsonb || '{"actif": 1}'::jsonb)::text  where cle = 'mess';
update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb)::text where cle = 'reserve_accueil';
update public.pass_saisons set debut = coalesce(debut, now()) where saison = 'saison-3';
commit;

select (select (valeur::jsonb->>'actif')::int  from config_jeu where cle = 'siege')           as siege,
       (select (valeur::jsonb->>'ouvert')::int from config_jeu where cle = 'zone_depart')     as zone,
       (select (valeur::jsonb->>'actif')::int  from config_jeu where cle = 'mess')            as mess,
       (select (valeur::jsonb->>'ouvert')::int from config_jeu where cle = 'reserve_accueil') as reserve_accueil,
       (select debut at time zone 'Europe/Paris' from pass_saisons where saison = 'saison-3') as pass_ouvert_le,
       exists (select 1 from public.pass_en_cours())                                          as pass_en_cours;

-- La VENTE du pass, seulement après un achat test réussi :
-- update public.euros_articles set actif = true where id = 'pass-s3';
