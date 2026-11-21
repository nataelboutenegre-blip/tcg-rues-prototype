-- s3-39 : la finition Or de l'atelier devient la dernière récompense du pass complet de la saison 3 (niveau 20).
-- Ok de Nataël le 21/11 (10 h 19). Le skin Vendanges passe du niveau 20 au 18, à la place du titre
-- « Légende de la saison 3 ». Le pass sait maintenant donner un élément de l'atelier (type 'atelier').
-- À lancer AVANT l'ouverture du pass (s3-13b). Rejouable. Contrôle : atelier | atelier-or | skin | 1
begin;
-- l'objet (jamais en vente : seulement par le pass)
insert into public.euros_articles (id, type, nom, description, prix_centimes, reserve_og, saison, actif, ordre)
values ('atelier-or', 'effet', 'Finition Or', 'La feuille d''or de l''atelier, sur toutes tes cartes Terra', 399, false, null, false, 450)
on conflict (id) do nothing;

alter table public.pass_recompenses drop constraint if exists pass_recompenses_type_check;
alter table public.pass_recompenses add constraint pass_recompenses_type_check
  check (type = any (array['tp','energie','titre','dos','habillage','skin','paquet','lingots','atelier']));

update public.pass_recompenses set type = 'skin', valeur = 'pass-s2-skin-vendanges', quantite = 0, nom = 'Skin Vendanges'
 where saison = 'saison-3' and niveau = 18 and payant;
update public.pass_recompenses set type = 'atelier', valeur = 'atelier-or', quantite = 0, nom = 'Finition Or'
 where saison = 'saison-3' and niveau = 20 and payant;

-- pass_reclamer : un élément de l'atelier se range dans l'inventaire comme un dos ou un skin
do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.pass_reclamer(integer)'::regprocedure);
  n := replace(d, 'elsif r.type in (''dos'', ''habillage'', ''skin'') then',
                  'elsif r.type in (''dos'', ''habillage'', ''skin'', ''atelier'') then   -- s3-39');
  if n = d then
    if position('''atelier'') then' in d) > 0 then return; end if;
    raise exception 's3-39 : pass_reclamer a changé, rien n''est fait';
  end if;
  execute n;
end $$;
commit;

select (select type from public.pass_recompenses where saison = 'saison-3' and niveau = 20) t20,
       (select valeur from public.pass_recompenses where saison = 'saison-3' and niveau = 20) v20,
       (select type from public.pass_recompenses where saison = 'saison-3' and niveau = 18) t18,
       (select count(*) from public.euros_articles where id = 'atelier-or' and not actif) objet;
