-- s3-31 : la Belgique côté serveur, sans rien changer tant que les communes belges ne sont pas entrées.
-- Provinces belges = « départements » à trois lettres (VAN, VBR, WBR, VWV, VOV, WHT, WLG, VLI, WLX, WNA, BRU),
-- région « Belgique » (décisions de Nataël, 18/11/2026). Les communes arrivent plus tard (s3-32, le jour de l'ouverture).
-- Avant : les fonctions du Front filtraient « length(departement) = 2 » (métropole + cantons) ; une province belge
-- (3 lettres) aurait été prise pour l'outre-mer dans draw_commune. Après : est_zone_front() = métropole, cantons, provinces.
-- Les paquets et contrats français excluaient « est_canton » : ils excluent maintenant est_etranger() (cantons + provinces).
-- Le paquet Terra par pays accepte 'BE' (même règle que 'CH' : chances d'un paquet France, puis une commune du pays).

begin;

create or replace function pg_temp.retoucher_tout(p_sig text, p_ancien text, p_nouveau text, p_n integer)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n = 0 and position(p_nouveau in d) > 0 then return; end if;   -- déjà fait
  if n <> p_n then raise exception 's3-31 : % : « % » trouvé % fois (attendu %)', p_sig, left(p_ancien, 70), n, p_n; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

create or replace function public.est_province_be(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- s3-31 : province belge (ISO 3166-2:BE sans « BE- ») ; Bruxelles-Capitale = BRU
  select coalesce(p_dep ~ '^(VAN|VBR|WBR|VWV|VOV|WHT|WLG|VLI|WLX|WNA|BRU)$', false);
$$;
create or replace function public.est_etranger(p_dep text)
returns boolean language sql immutable parallel safe as $$
  select est_canton(p_dep) or est_province_be(p_dep);
$$;
create or replace function public.pays_de(p_dep text)
returns text language sql immutable parallel safe as $$
  select case when est_canton(p_dep) then 'CH' when est_province_be(p_dep) then 'BE' else 'FR' end;
$$;
create or replace function public.est_zone_front(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- là où se joue le Front « de la carte » : métropole, cantons suisses, provinces belges (pas l'outre-mer)
  select est_metropole(p_dep) or est_canton(p_dep) or est_province_be(p_dep);
$$;

-- la région
select pg_temp.retoucher_tout('public.cdj_region(text)',
  $a$    when est_canton(p_dep) then 'Suisse'   -- s3-1$a$,
  $b$    when est_province_be(p_dep) then 'Belgique'   -- s3-31
    when est_canton(p_dep) then 'Suisse'   -- s3-1$b$, 1);
select pg_temp.retoucher_tout('public.zone_depart_zone(text)', 'or est_canton(p_dep)', 'or est_etranger(p_dep)', 1);

-- le Front : tirage, pot, taux, territoires
select pg_temp.retoucher_tout('public.draw_commune(text)',
  'where length(c.departement) <> 2 and p.commune_code is null', $b$where c.departement ~ '^9[78]' /* s3-31 */ and p.commune_code is null$b$, 1);
select pg_temp.retoucher_tout('public.draw_commune(text)',
  'and length(c.departement) = 2 and (v_zone_deps', 'and est_zone_front(c.departement) and (v_zone_deps', 1);
select pg_temp.retoucher_tout('public.poids_tirage()', 'length(c.departement) = 2', 'est_zone_front(c.departement)', 1);
select pg_temp.retoucher_tout('public.taux_actuels()', 'length(c.departement) = 2', 'est_zone_front(c.departement)', 1);
select pg_temp.retoucher_tout('public.prendre_mesure()', 'where length(departement) = 2', 'where est_zone_front(departement)', 1);
select pg_temp.retoucher_tout('public.saison_courante()', 'length(c.departement) = 2', 'est_zone_front(c.departement)', 1);
select pg_temp.retoucher_tout('public.front_territoires()', 'length(c.departement) = 2', 'est_zone_front(c.departement)', 2);
select pg_temp.retoucher_tout('public.mon_score_detail()', 'length(c.departement) = 2', 'est_zone_front(c.departement)', 2);

-- France seulement (paquets du département, paquet garanti, Boutique tournante, contrats, Plus ou moins, Terra France)
select pg_temp.retoucher_tout('public.boutique_ouvrir_paquet(text, text)', 'est_canton(', 'est_etranger(', 3);
select pg_temp.retoucher_tout('public.pass_ouvrir_paquet(integer, text)', 'est_canton(', 'est_etranger(', 3);
select pg_temp.retoucher_tout('public.bt_tirer(uuid, text)', 'not est_canton(', 'not est_etranger(', 1);
select pg_temp.retoucher_tout('public.contrat_defile(text, integer)', 'not est_canton(', 'not est_etranger(', 1);
select pg_temp.retoucher_tout('public.signer_contrat(text[], text)', 'not est_canton(', 'not est_etranger(', 1);
select pg_temp.retoucher_tout('public.pom_generer()', 'not est_canton(', 'not est_etranger(', 5);

-- le paquet Terra par pays : 'BE' comme 'CH'
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)', 'not est_canton(', 'not est_etranger(', 2);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$if v_pays not in ('FR', 'CH') then$a$, $b$if v_pays not in ('FR', 'CH', 'BE') then$b$, 1);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$  if v_pays = 'CH' and not exists (select 1 from communes c where est_canton(c.departement)) then
    raise exception 'Le paquet suisse arrive avec la saison 3';$a$,
  $b$  if v_pays <> 'FR' and not exists (select 1 from communes c where pays_de(c.departement) = v_pays) then   -- s3-31
    raise exception '%', case v_pays when 'BE' then 'Le paquet belge n''est pas encore ouvert' else 'Le paquet suisse arrive avec la saison 3' end;$b$, 1);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)', $a$  if v_pays = 'CH' then$a$, $b$  if v_pays <> 'FR' then$b$, 1);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  'where est_canton(c.departement) and c.', 'where pays_de(c.departement) = v_pays and c.', 2);

-- les coefficients de population (s3-30) : les provinces belges quand elles seront entrées (relancer score_pop_calculer())
select pg_temp.retoucher_tout('public.score_pop_calculer()',
  'where est_metropole(c.departement) or est_canton(c.departement)', 'where est_zone_front(c.departement)', 1);

commit;

-- Contrôle : 0 commune belge · régions · zone · aucun changement pour la France et la Suisse
select (select count(*) from communes where est_province_be(departement)) as communes_belges,
       cdj_region('WLG') as liege, cdj_region('GE') as geneve, cdj_region('59') as nord, zone_depart_zone('BRU') as zone_bru,
       pays_de('VAN') || pays_de('ZH') || pays_de('16') || pays_de('971') as pays,
       est_zone_front('971') as dom_hors_front,
       (select count(*) from communes where est_zone_front(departement)) = (select count(*) from communes where length(departement) = 2) as meme_total;
