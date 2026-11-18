-- Saison 3, jour J, l'après-midi (après le contrôle de l'ouverture) : on allume l'Artillerie, la Centrale de clan
-- et les ordres du chef (s3-27, lancé le 18/11, tout éteint). Une ligne par système : on peut n'en allumer qu'un.
-- Pour éteindre : la même ligne avec 0.
update public.config_jeu set valeur = ((valeur::jsonb) || '{"artilleries_ouvertes": 1}'::jsonb)::text where cle = 'batiments';
update public.config_jeu set valeur = ((valeur::jsonb) || '{"ouverts": 1}'::jsonb)::text where cle = 'ordres_chef';
update public.config_jeu set valeur = ((valeur::jsonb) || '{"ouverte": 1}'::jsonb)::text where cle = 'centrale_clan';
-- Contrôle : true | true | true
select artilleries_ouvertes() as artillerie, ordres_ouverts() as ordres, centrale_ouverte() as centrale;
