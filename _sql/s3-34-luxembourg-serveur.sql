-- s3-34 : le Luxembourg côté serveur, sans rien changer tant que les communes luxembourgeoises ne sont pas entrées.
-- Comme la Belgique (s3-31). Décision de Nataël (19/11/2026, 11 h 32) : le Luxembourg ouvre le 22/11 avec la S3.
-- Cantons luxembourgeois = « départements » à trois lettres (LCA, LCL, LDI, LEC, LES, LGR, LLU, LME, LRE, LRM, LVI, LWI) :
-- les codes officiels à deux lettres (CA, LU, VD, GR…) sont déjà des cantons suisses. Région « Luxembourg ».
-- Toutes les fonctions retouchées par s3-31 passent par est_etranger / pays_de / est_zone_front : il suffit de les étendre.
-- Seuls cdj_region (le nom de la région) et terra_ouvrir_paquet (la liste des pays) citent la Belgique en dur.
-- Plus la réserve luxembourgeoise (comme belgique_communes_attente), vide : les lignes et les photos viennent du Mac.

begin;

create or replace function pg_temp.retoucher_tout(p_sig text, p_ancien text, p_nouveau text, p_n integer)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n = 0 and position(p_nouveau in d) > 0 then return; end if;   -- déjà fait
  if n <> p_n then raise exception 's3-34 : % : « % » trouvé % fois (attendu %)', p_sig, left(p_ancien, 70), n, p_n; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

create or replace function public.est_canton_lu(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- s3-34 : canton luxembourgeois (L + deux lettres)
  select coalesce(p_dep ~ '^L(CA|CL|DI|EC|ES|GR|LU|ME|RE|RM|VI|WI)$', false);
$$;
create or replace function public.est_etranger(p_dep text)
returns boolean language sql immutable parallel safe as $$
  select est_canton(p_dep) or est_province_be(p_dep) or est_canton_lu(p_dep);
$$;
create or replace function public.pays_de(p_dep text)
returns text language sql immutable parallel safe as $$
  select case when est_canton(p_dep) then 'CH' when est_province_be(p_dep) then 'BE'
              when est_canton_lu(p_dep) then 'LU' else 'FR' end;
$$;
create or replace function public.est_zone_front(p_dep text)
returns boolean language sql immutable parallel safe as $$
  -- là où se joue le Front « de la carte » : métropole, cantons suisses, provinces belges, cantons luxembourgeois (pas l'outre-mer)
  select est_metropole(p_dep) or est_canton(p_dep) or est_province_be(p_dep) or est_canton_lu(p_dep);
$$;

select pg_temp.retoucher_tout('public.cdj_region(text)',
  $a$    when est_province_be(p_dep) then 'Belgique'   -- s3-31$a$,
  $b$    when est_canton_lu(p_dep) then 'Luxembourg'   -- s3-34
    when est_province_be(p_dep) then 'Belgique'   -- s3-31$b$, 1);

-- le paquet Terra par pays : 'LU' comme 'BE'
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$if v_pays not in ('FR', 'CH', 'BE') then$a$, $b$if v_pays not in ('FR', 'CH', 'BE', 'LU') then$b$, 1);
select pg_temp.retoucher_tout('public.terra_ouvrir_paquet(boolean, text)',
  $a$case v_pays when 'BE' then 'Le paquet belge n''est pas encore ouvert'$a$,
  $b$case v_pays when 'BE' then 'Le paquet belge n''est pas encore ouvert' when 'LU' then 'Le paquet luxembourgeois n''est pas encore ouvert'$b$, 1);

-- la réserve : 100 communes, posées par _donnees/luxembourg/photos-luxembourg.py (Mac de Nataël, clé service_role chez lui)
create table if not exists public.luxembourg_communes_attente (
  code text primary key,
  nom text not null,
  departement text not null,
  population integer not null,
  latitude numeric not null,
  longitude numeric not null,
  tier text not null,
  rang_pays integer not null,
  nom_officiel text,
  wikidata text,
  photo text, photo_auteur text, photo_licence text, photo_source text);
alter table public.luxembourg_communes_attente enable row level security;
revoke all on public.luxembourg_communes_attente from anon, authenticated;

commit;

-- Contrôle : 0 commune luxembourgeoise · régions · pays · aucun changement pour la France, la Suisse et la Belgique
select (select count(*) from communes where est_canton_lu(departement)) as communes_lux,
       cdj_region('LLU') as lux, cdj_region('WLG') as liege, cdj_region('GE') as geneve, cdj_region('59') as nord,
       zone_depart_zone('LES') as zone_esch,
       pays_de('LLU') || pays_de('VAN') || pays_de('ZH') || pays_de('16') || pays_de('971') as pays,
       est_canton('LU') and not est_canton_lu('LU') and est_canton_lu('LLU') and not est_canton('LLU') and not est_province_be('LLU') as codes_ok,
       est_zone_front('971') as dom_hors_front,
       (select count(*) from communes where est_zone_front(departement)) =
         (select count(*) from communes where est_metropole(departement) or est_canton(departement) or est_province_be(departement)) as meme_total,
       (select count(*) from luxembourg_communes_attente) as reserve;
