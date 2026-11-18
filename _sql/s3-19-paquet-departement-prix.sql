-- ===========================================================================
--  s3-19 (18/11/2026) — paquet du département : un prix par département
--  Faille signalée le 18/11 : le paquet coûte 800 TP partout et tire 5 communes du
--  département au hasard. Paris (17 légendaires, 3 épiques) rapportait ≈ 2 775 TP en
--  doublons revendus, le 92 ≈ 2 380, le 93 ≈ 2 350, le 94 ≈ 1 930, le 13 ≈ 1 110.
--  Maintenant : prix = le plus grand de 800 et de 130 % de la revente moyenne de
--  5 cartes du département, arrondi à la centaine au-dessus (75 → 3 700, 92 et 93
--  → 3 100, 94 → 2 600, 13 → 1 500 ; tous les autres restent à 800).
--  boutique() envoie « prix_dep » (seulement les départements au-dessus du prix de base).
--  Contrôle attendu (dernière ligne) : 3700 | 800 | true | true
-- ===========================================================================

-- les prix calculés une fois (36 000 communes : trop lent à chaque affichage de la boutique) ;
-- à relancer si les prix de revente ou les communes changent : select paquet_departement_prix_maj();
create table if not exists public.paquet_departement_prix_cache (
  departement text primary key,
  prix integer not null
);
alter table public.paquet_departement_prix_cache enable row level security;

create or replace function public.paquet_departement_prix_maj()
 returns integer language plpgsql security definer set search_path to 'public'
as $f$
declare v_base integer := coalesce((select ba.prix from boutique_articles ba where ba.id = 'paquet-departement'), 800);
  n integer;
begin
  delete from paquet_departement_prix_cache where true;
  insert into paquet_departement_prix_cache (departement, prix)
  select x.departement, x.prix from (
    select c.departement, (ceil(5 * avg(p.v) * 1.3 / 100) * 100)::integer prix
      from communes c
      join (select t, terra_prix_revente(t) v from unnest(array['commun','peucommun','rare','epique','legendaire']) t) p on p.t = c.tier
     group by c.departement) x
   where x.prix > v_base;
  get diagnostics n = row_count;
  return n;
end; $f$;
revoke all on function public.paquet_departement_prix_maj() from public, anon, authenticated;

create or replace function public.paquet_departement_prix(p_dep text)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select greatest(
    coalesce((select ba.prix from boutique_articles ba where ba.id = 'paquet-departement'), 800),
    coalesce((select pc.prix from paquet_departement_prix_cache pc where pc.departement = p_dep), 0));
$f$;
grant execute on function public.paquet_departement_prix(text) to authenticated;

select paquet_departement_prix_maj();

do $do$
declare d text; a text; b text;
  procedure_n integer;
begin
  -- 1. l'achat
  d := pg_get_functiondef('public.boutique_ouvrir_paquet(text,text)'::regprocedure);
  if position('s3-19' in d) = 0 then
    for a, b in values
      (E'  j joueurs%rowtype;\nbegin', E'  j joueurs%rowtype;\n  v_prix integer;   -- s3-19 : prix selon le département\nbegin'),
      (E'  select * into j from joueurs jj where jj.id = v_uid for update;',
       E'  v_prix := case when a.id = ''paquet-departement'' then paquet_departement_prix(p_departement) else a.prix end;   -- s3-19\n  select * into j from joueurs jj where jj.id = v_uid for update;'),
      ('if coalesce(j.solde, 0) < a.prix then', 'if coalesce(j.solde, 0) < v_prix then'),
      ('set solde = jj.solde - a.prix where', 'set solde = jj.solde - v_prix where'),
      ('values (v_uid, a.id, a.prix, case', 'values (v_uid, a.id, v_prix, case')
    loop
      procedure_n := (length(d) - length(replace(d, a, ''))) / length(a);
      if procedure_n <> 1 then raise exception 's3-19 : boutique_ouvrir_paquet a changé (% fois : %)', procedure_n, left(a, 50); end if;
      d := replace(d, a, b);
    end loop;
    execute d;
  end if;

  -- 2. la vitrine
  d := pg_get_functiondef('public.boutique()'::regprocedure);
  if position('s3-19' in d) = 0 then
    a := $a$'paquets_max', 3,$a$;
    b := $b$'paquets_max', 3,
    'prix_dep', (select coalesce(jsonb_object_agg(pc.departement, pc.prix), '{}'::jsonb) from paquet_departement_prix_cache pc),   -- s3-19$b$;
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-19 : boutique() a changé'; end if;
    execute replace(d, a, b);
  end if;
end $do$;

select paquet_departement_prix('75') paris, paquet_departement_prix('16') charente,
       position('s3-19' in pg_get_functiondef('public.boutique_ouvrir_paquet(text,text)'::regprocedure)) > 0 achat,
       position('s3-19' in pg_get_functiondef('public.boutique()'::regprocedure)) > 0 vitrine;
