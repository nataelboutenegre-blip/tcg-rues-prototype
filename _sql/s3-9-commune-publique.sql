-- s3-9 (11/11/2026) : « Qui possède ta commune ? », la fiche publique d'une commune (sans connexion)
-- Décidé le 7/11 (« ok on part sur ça ») et le 10/11 (version simple pour le 22/11).
--
-- Fonctions ouvertes à anon (visiteurs sans compte) :
--  - commune_publique(ref) : ref = code INSEE (« 16102 »), code suisse (« CH6621 ») ou adresse lisible (« cognac-16 ») ;
--    renvoie la commune (nom, département, population, rareté, rang, photo et son crédit, position), son propriétaire
--    (pseudo, couleur choisie ou empreinte de couleur, clan), depuis quand il la tient, combien de fois elle a été prise
--    cette saison, et ses voisines à moins de 12 km (code + couleur du propriétaire, ou libre) pour la petite carte ;
--  - communes_publiques_chercher(texte) : 8 communes au plus, les plus peuplées d'abord (nom, département, adresse).
-- Rien d'autre sur le joueur : pas d'identifiant ; l'empreinte `h` (hachage du joueur) sert seulement à retrouver la même
-- couleur que dans le jeu (colorForPlayer).
--
-- Contrôle attendu : true | true | true | true | true (communes_recherche aussi grande que communes)

create or replace function public.cp_empreinte(p text) returns bigint
language plpgsql immutable set search_path to 'public' as $$
declare h bigint := 0; i integer;
begin
  -- même calcul que colorForPlayer() dans app.js
  for i in 1..length(p) loop h := (h * 31 + ascii(substr(p, i, 1))) % 4294967296; end loop;
  return h;
end $$;

create or replace function public.cp_adresse(p_nom text, p_dep text) returns text
language sql stable set search_path to 'public', 'extensions' as $$
  select trim(both '-' from regexp_replace(lower(unaccent(p_nom)), '[^a-z0-9]+', '-', 'g')) || '-' || lower(p_dep);
$$;

create or replace function public.cp_trouver(p_ref text) returns text
language plpgsql stable security definer set search_path to 'public', 'extensions' as $$
declare v_ref text := lower(btrim(coalesce(p_ref, ''))); v_code text; v_dep text; v_nom text;
begin
  if v_ref = '' or length(v_ref) > 120 then return null; end if;
  select c.code into v_code from communes c where c.code = upper(v_ref);
  if v_code is not null then return v_code; end if;
  v_dep := substring(v_ref from '-([0-9a-z]{2,3})$');
  if v_dep is null then return null; end if;
  v_nom := left(v_ref, length(v_ref) - length(v_dep) - 1);
  select c.code into v_code from communes c
   where lower(c.departement) = v_dep
     and trim(both '-' from regexp_replace(lower(unaccent(c.nom)), '[^a-z0-9]+', '-', 'g')) = v_nom
   order by c.population desc limit 1;
  return v_code;
end $$;

create or replace function public.commune_publique(p_ref text) returns jsonb
language plpgsql stable security definer set search_path to 'public', 'extensions' as $$
declare v_code text := cp_trouver(p_ref); c communes; po possessions; v_debut timestamptz; v_proprio jsonb; v_voisines jsonb;
begin
  if v_code is null then return null; end if;
  select * into c from communes where code = v_code;
  select * into po from possessions where commune_code = v_code;
  select s.debut into v_debut from saisons s where s.etat <> 'terminee' order by s.debut desc limit 1;
  if po.joueur_id is not null then
    select jsonb_build_object('pseudo', j.pseudo, 'couleur', j.couleur, 'h', cp_empreinte(j.id::text),
                              'clan', k.tag, 'clan_nom', k.nom, 'clan_couleur', k.couleur)
      into v_proprio
      from joueurs j left join clan_membres m on m.joueur_id = j.id left join clans k on k.id = m.clan_id
     where j.id = po.joueur_id;
  end if;
  select coalesce(jsonb_agg(jsonb_build_object('c', v.code, 'd', v.departement, 'couleur', j.couleur,
                                               'h', case when vp.joueur_id is not null then cp_empreinte(vp.joueur_id::text) end)), '[]'::jsonb)
    into v_voisines
    from communes v
    left join possessions vp on vp.commune_code = v.code
    left join joueurs j on j.id = vp.joueur_id
   where v.code <> v_code
     and v.latitude between c.latitude - 0.12 and c.latitude + 0.12
     and v.longitude between c.longitude - 0.17 and c.longitude + 0.17
     and dist_km(c.latitude, c.longitude, v.latitude, v.longitude) <= 12;
  return jsonb_build_object(
    'code', c.code, 'nom', c.nom, 'dept', c.departement, 'population', c.population, 'tier', c.tier,
    'rang', c.rang, 'palier_total', c.palier_total,
    'photo', c.photo, 'photo_auteur', c.photo_auteur, 'photo_licence', c.photo_licence, 'photo_source', c.photo_source,
    'lat', c.latitude, 'lon', c.longitude, 'adresse', cp_adresse(c.nom, c.departement),
    'proprio', v_proprio,
    'depuis', po.acquired_at,
    'prises', (select count(*) from historique h where h.commune_code = v_code and v_debut is not null and h.acquired_at >= v_debut),
    'voisines', v_voisines);
end $$;

-- le nom simplifié de chaque commune (« l-isle-adam »), calculé une fois : la recherche ne refait pas unaccent 37 000 fois
create table if not exists public.communes_recherche(
  code text primary key references public.communes(code) on delete cascade,
  s text not null);
alter table public.communes_recherche enable row level security;
revoke all on public.communes_recherche from anon, authenticated;
insert into public.communes_recherche(code, s)
select c.code, trim(both '-' from regexp_replace(lower(unaccent(c.nom)), '[^a-z0-9]+', '-', 'g')) from public.communes c
on conflict (code) do update set s = excluded.s;

create or replace function public.cp_recherche_maj() returns trigger
language plpgsql security definer set search_path to 'public', 'extensions' as $$
begin
  insert into communes_recherche(code, s)
  values (new.code, trim(both '-' from regexp_replace(lower(unaccent(new.nom)), '[^a-z0-9]+', '-', 'g')))
  on conflict (code) do update set s = excluded.s;
  return null;
end $$;
drop trigger if exists trg_cp_recherche on public.communes;
create trigger trg_cp_recherche after insert or update of nom on public.communes
  for each row execute function public.cp_recherche_maj();

create or replace function public.communes_publiques_chercher(p_texte text) returns jsonb
language sql stable security definer set search_path to 'public', 'extensions' as $$
  with q as (select trim(both '-' from regexp_replace(lower(unaccent(coalesce(p_texte, ''))), '[^a-z0-9]+', '-', 'g')) as m),
  x as (select c.code, c.nom, c.departement as dept, c.population, c.tier, r.s || '-' || lower(c.departement) as adresse,
               case when r.s = q.m then 0 when r.s like q.m || '%' then 1 else 2 end as ordre
          from communes_recherche r join communes c on c.code = r.code, q
         where length(q.m) >= 2 and length(q.m) <= 60 and position(q.m in r.s) > 0
         order by 7, c.population desc
         limit 8)
  select coalesce(jsonb_agg(to_jsonb(x) - 'ordre' order by x.ordre, x.population desc), '[]'::jsonb) from x;
$$;

revoke all on function public.cp_empreinte(text), public.cp_adresse(text, text), public.cp_trouver(text), public.cp_recherche_maj() from public, anon, authenticated;
revoke all on function public.commune_publique(text), public.communes_publiques_chercher(text) from public;
grant execute on function public.commune_publique(text), public.communes_publiques_chercher(text) to anon, authenticated;
notify pgrst, 'reload schema';

select has_function_privilege('anon', 'public.commune_publique(text)', 'execute') as anon_fiche,
       has_function_privilege('anon', 'public.communes_publiques_chercher(text)', 'execute') as anon_recherche,
       not has_function_privilege('anon', 'public.cp_trouver(text)', 'execute') as interne_ferme,
       public.cp_trouver('cognac-16') = '16102' as adresse_ok,
       (select count(*) from public.communes_recherche) = (select count(*) from public.communes) as recherche_complete;
