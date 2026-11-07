-- s2-112 (7/11/2026) : les bâtiments en pixel art (aperçu validé « c'est parfait »,
-- feu vert de Nataël à 12 h 21).
--   - chaque bâtiment a un style, choisi à la construction (2 ou 3 gratuits par
--     type, purement décoratifs) ; les bâtiments déjà construits prennent le
--     premier style de leur type ;
--   - batiment_construire_style(code, type, style) : la construction habituelle
--     (mêmes règles, même prix), puis le style ;
--   - mes_batiments() donne le style de chaque bâtiment et la liste des styles ;
--   - batiments_autres(...) : les bâtiments des autres joueurs, comme sur la
--     carte (batiments_visibles) : JAMAIS une Banque, un Centre seulement une
--     fois dévoilé. Filtres : type, départements (la région, côté jeu),
--     recherche (commune ou joueur), tri ; 50 lignes au plus par appel.
-- Réglage : config_jeu 'batiments_styles' (les styles de chaque type, le
-- premier est celui par défaut).
-- Testé sur la prod dans un bloc annulé.

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

begin;

alter table public.batiments add column if not exists style text;

insert into public.config_jeu (cle, valeur)
values ('batiments_styles', '{"fonderie": ["brique", "acier"], "forteresse": ["chateau", "bastion", "tour"], "banque": ["classique", "coffre"], "centre": ["labo", "bunker"]}')
on conflict (cle) do nothing;

create or replace function public.batiment_styles()
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'batiments_styles'), '{}'::jsonb);
$f$;

-- construire avec un style : les règles et le prix de batiment_construire, puis le style
create or replace function public.batiment_construire_style(p_code text, p_type text, p_style text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-112
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_style is not null and not coalesce((batiment_styles() -> p_type) ? p_style, false) then
    raise exception 'Style inconnu pour ce bâtiment';
  end if;
  perform batiment_construire(p_code, p_type);
  if p_style is not null then
    update batiments set style = p_style
     where joueur_id = v_uid and commune_code = p_code and type = p_type;
  end if;
  return mes_batiments();
end;
$f$;

-- les bâtiments des autres, comme sur la carte
create or replace function public.batiments_autres(p_type text default null, p_depts text[] default null,
  p_recherche text default null, p_tri text default 'recents', p_limite integer default 30, p_decalage integer default 0)
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
-- s2-112 : jamais une Banque, un Centre seulement une fois dévoilé (comme batiments_visibles)
declare
  v_uid uuid := auth.uid();
  v_q text := nullif(btrim(left(coalesce(p_recherche, ''), 40)), '');
  v_lim integer := greatest(1, least(coalesce(p_limite, 30), 50));
  v_dec integer := greatest(0, least(coalesce(p_decalage, 0), 5000));
  v_styles jsonb := batiment_styles();
  r jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not batiments_ouverts() then return jsonb_build_object('total', 0, 'lignes', '[]'::jsonb); end if;
  if coalesce(array_length(p_depts, 1), 0) > 120 then raise exception 'Trop de départements d''un coup'; end if;
  if v_q is not null then v_q := replace(replace(replace(v_q, '\', '\\'), '%', '\%'), '_', '\_'); end if;
  with base as (
    select b.id, b.type, coalesce(b.style, v_styles -> b.type ->> 0) as style,
           b.commune_code as code, c.nom, c.departement as dept, c.tier,
           j.pseudo, b.cree_le, b.pret_le <= now() as pret,
           case when b.type = 'centre' then
             case when exists (select 1 from bombes_preparations p where p.joueur_id = b.joueur_id and p.etat = 'en_cours')
                  then 'preparation' else 'lancee' end end as centre
      from batiments b
      join communes c on c.code = b.commune_code
      left join joueurs j on j.id = b.joueur_id
     where b.joueur_id <> v_uid
       and b.type <> 'banque'
       and (b.type <> 'centre' or centre_devoile(b.joueur_id, b.commune_code))
       and (p_type is null or b.type = p_type)
       and (p_depts is null or c.departement = any(p_depts))
       and (v_q is null or c.nom ilike '%' || v_q || '%' or j.pseudo ilike '%' || v_q || '%')
  ), page as (
    select base.*, row_number() over (order by
             case when p_tri = 'nom' then nom end,
             case when p_tri = 'joueur' then lower(pseudo) end,
             cree_le desc, id desc) as rn
      from base
  )
  select jsonb_build_object(
           'total', (select count(*) from base),
           'lignes', coalesce((select jsonb_agg(to_jsonb(x) - 'rn' order by x.rn)
                                 from (select * from page where rn > v_dec order by rn limit v_lim) x), '[]'::jsonb))
    into r;
  return r;
end;
$f$;

revoke execute on function public.batiment_styles() from public, anon, authenticated;
revoke execute on function public.batiment_construire_style(text, text, text) from public, anon;
grant execute on function public.batiment_construire_style(text, text, text) to authenticated;
revoke execute on function public.batiments_autres(text, text[], text, text, integer, integer) from public, anon;
grant execute on function public.batiments_autres(text, text[], text, text, integer, integer) to authenticated;

-- ce que le jeu affiche : le style de chaque bâtiment, et les styles possibles
do $$
declare d text := pg_get_functiondef('public.mes_batiments()'::regprocedure);
begin
  if position('s2-112' in d) > 0 then raise notice 'mes_batiments : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'''pret'', b.pret_le <= now()',
'''pret'', b.pret_le <= now(), ''style'', coalesce(b.style, batiment_styles() -> b.type ->> 0)', 5, 'styles des bâtiments');
  d := pg_temp.remp(d,
'    ''ouverts'', batiments_ouverts(),',
'    ''ouverts'', batiments_ouverts(),
    ''styles'', batiment_styles(),   -- s2-112', 1, 'liste des styles');
  execute d;
end $$;

commit;

-- Contrôle attendu : t | t | t | t | t
select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'batiments' and column_name = 'style') as colonne_ok,
       position('s2-112' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0                        as mes_batiments_ok,
       has_function_privilege('authenticated', 'public.batiment_construire_style(text, text, text)', 'execute')
       and has_function_privilege('authenticated', 'public.batiments_autres(text, text[], text, text, integer, integer)', 'execute') as droits_ok,
       not has_function_privilege('anon', 'public.batiments_autres(text, text[], text, text, integer, integer)', 'execute')        as anonymes_exclus,
       exists (select 1 from public.config_jeu where cle = 'batiments_styles')                                    as reglages_ok;
