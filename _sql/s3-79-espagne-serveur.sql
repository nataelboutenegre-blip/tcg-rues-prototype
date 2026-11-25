-- s3-79 : l'Espagne, l'Andorre et Monaco côté serveur, sans rien changer tant que leurs communes ne sont pas entrées.
-- Comme le Luxembourg (s3-34). Décisions de Nataël (25/11/2026) : Espagne « prochainement », Andorre et Monaco pour
-- boucher les trous de la carte ; Canaries sur la carte principale (encart), mêmes règles que la Corse et les Baléares ;
-- Terra : Andorre dans le paquet espagnol, Monaco dans le paquet français.
-- Provinces espagnoles = « départements » E01…E52 (01…52 sont pris par la France) ; Andorre = AND, Monaco = MCO.
-- Régions : les 17 communautés autonomes (noms français), Ceuta, Melilla, « Andorre », « Monaco ».
-- pays_de : E.. → ES, AND → ES (paquet espagnol), MCO → FR (paquet français). est_etranger reste vrai pour les trois :
-- ni paquets de département, ni contrats, ni Plus ou moins (France seulement).
-- Plus la réserve espagnole (comme luxembourg_communes_attente), remplie par Claude et photos-espagne.py.

begin;

create or replace function pg_temp.retoucher_tout(p_sig text, p_ancien text, p_nouveau text, p_n integer)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n = 0 and position(p_nouveau in d) > 0 then return; end if;   -- déjà fait
  if n <> p_n then raise exception 's3-79 : % : « % » trouvé % fois (attendu %)', p_sig, left(p_ancien, 70), n, p_n; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

create or replace function public.est_province_es(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- s3-79 : province espagnole (E + code INE de province : E01 Alava … E50 Saragosse, E51 Ceuta, E52 Melilla)
  select coalesce(p_dep ~ '^E(0[1-9]|[1-4][0-9]|5[0-2])$', false);
$$;
create or replace function public.est_micro_etat(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- s3-79 : Andorre (AND) et Monaco (MCO)
  select coalesce(p_dep in ('AND', 'MCO'), false);
$$;
create or replace function public.est_etranger(p_dep text)
returns boolean language sql immutable parallel safe as $$
  select est_canton(p_dep) or est_province_be(p_dep) or est_canton_lu(p_dep) or est_province_es(p_dep) or est_micro_etat(p_dep);
$$;
create or replace function public.pays_de(p_dep text)
returns text language sql immutable parallel safe as $$
  select case when est_canton(p_dep) then 'CH' when est_province_be(p_dep) then 'BE'
              when est_canton_lu(p_dep) then 'LU'
              when est_province_es(p_dep) or p_dep = 'AND' then 'ES'   -- s3-79 : l'Andorre dans le paquet espagnol
              else 'FR' end;   -- Monaco (MCO) : paquet français
$$;
create or replace function public.est_zone_front(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- là où se joue le Front « de la carte » : métropole, cantons suisses, provinces belges, cantons luxembourgeois,
  -- provinces espagnoles (Canaries comprises), Andorre, Monaco (pas l'outre-mer français)
  select est_metropole(p_dep) or est_canton(p_dep) or est_province_be(p_dep) or est_canton_lu(p_dep)
      or est_province_es(p_dep) or est_micro_etat(p_dep);
$$;

select pg_temp.retoucher_tout('public.cdj_region(text)',
  $a$    when est_canton_lu(p_dep) then 'Luxembourg'   -- s3-34$a$,
  $b$    when p_dep in ('E04','E11','E14','E18','E21','E23','E29','E41') then 'Andalousie'
    when p_dep in ('E22','E44','E50') then 'Aragon'
    when p_dep in ('E33') then 'Asturies'
    when p_dep in ('E35','E38') then 'Canaries'
    when p_dep in ('E39') then 'Cantabrie'
    when p_dep in ('E02','E13','E16','E19','E45') then 'Castille-La Manche'
    when p_dep in ('E05','E09','E24','E34','E37','E40','E42','E47','E49') then 'Castille-et-León'
    when p_dep in ('E08','E17','E25','E43') then 'Catalogne'
    when p_dep in ('E51') then 'Ceuta'
    when p_dep in ('E28') then 'Communauté de Madrid'
    when p_dep in ('E03','E12','E46') then 'Communauté valencienne'
    when p_dep in ('E06','E10') then 'Estrémadure'
    when p_dep in ('E15','E27','E32','E36') then 'Galice'
    when p_dep in ('E26') then 'La Rioja'
    when p_dep in ('E52') then 'Melilla'
    when p_dep in ('E31') then 'Navarre'
    when p_dep in ('E01','E20','E48') then 'Pays basque'
    when p_dep in ('E30') then 'Région de Murcie'
    when p_dep in ('E07') then 'Îles Baléares'
    when p_dep = 'AND' then 'Andorre'   -- s3-79
    when p_dep = 'MCO' then 'Monaco'
    when est_canton_lu(p_dep) then 'Luxembourg'   -- s3-34$b$, 1);

-- le paquet Terra : 'ES' comme 'LU' ; le paquet France prend les communes de pays « FR » (Monaco compris)
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$if v_pays not in ('FR', 'CH', 'BE', 'LU') then$a$, $b$if v_pays not in ('FR', 'CH', 'BE', 'LU', 'ES') then$b$, 1);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$when 'LU' then 'Le paquet luxembourgeois n''est pas encore ouvert'$a$,
  $b$when 'LU' then 'Le paquet luxembourgeois n''est pas encore ouvert' when 'ES' then 'Le paquet espagnol n''est pas encore ouvert'$b$, 1);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$and not est_etranger(c.departement) /* s3-3 */$a$, $b$and pays_de(c.departement) = 'FR' /* s3-3, s3-79 : Monaco */$b$, 1);

-- la réserve : 8 140 communes (Espagne 8 132, Andorre 7, Monaco 1)
create table if not exists public.espagne_communes_attente (
  code text primary key,
  nom text not null,
  departement text not null,
  population integer not null,
  latitude numeric not null,
  longitude numeric not null,
  tier text not null,
  rang_pays integer,
  nom_officiel text,
  wikidata text,
  photo text, photo_auteur text, photo_licence text, photo_source text);
alter table public.espagne_communes_attente enable row level security;
revoke all on public.espagne_communes_attente from anon, authenticated;

commit;

-- Contrôle : 0 commune espagnole · régions · pays · aucun changement pour les autres
select (select count(*) from communes where est_province_es(departement) or est_micro_etat(departement)) as communes_es,
       cdj_region('E28') as madrid, cdj_region('E35') as canaries, cdj_region('AND') as andorre, cdj_region('MCO') as monaco,
       cdj_region('LLU') as lux, cdj_region('59') as nord,
       pays_de('E08') || pays_de('AND') || pays_de('MCO') || pays_de('LLU') || pays_de('16') || pays_de('971') as pays,
       not est_province_es('01') and not est_province_es('E53') and est_province_es('E52') and not est_metropole('E28') as codes_ok,
       est_zone_front('971') as dom_hors_front,
       (select count(*) from communes where est_zone_front(departement)) =
         (select count(*) from communes where est_metropole(departement) or est_etranger(departement)) as meme_total,
       (select count(*) from communes where pays_de(departement) = 'FR') = (select count(*) from communes where not est_etranger(departement)) as paquet_fr_inchange,
       (select count(*) from espagne_communes_attente) as reserve;
