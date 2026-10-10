-- ===========================================================================
--  TerraFront — JOUR J : la nouvelle échelle des raretés (saison 2)
--  Préparé le 10 octobre 2026. NE PAS LANCER EN SAISON 1 AVEC p_confirmer.
--
--  Nouvelle échelle (décidée le 7-9 octobre), en habitants :
--    légendaire ≥ 30 000 · épique ≥ 8 000 · rare ≥ 2 300 · peu commune ≥ 450
--    · commune en dessous.
--  Mesuré sur data/communes.json : 302 / 1 015 / 3 406 / 12 841 / 17 183.
--  Uniquement des MONTÉES : la fonction refuse toute descente de palier.
--
--  La fonction recalcule aussi le numéro de chaque carte dans son palier
--  (communes.rang, « n° 2 / 302 ») et la taille du palier (palier_total).
--
--  Ce fichier crée la fonction puis lance une SIMULATION (rien n'est
--  modifié). Le jour J, après la clôture, lancer à la main :
--    select * from rebasculer_paliers_s2(p_confirmer => true);
--  Rejouable.
-- ===========================================================================

create or replace function public.rebasculer_paliers_s2(
    p_peucommun integer default 450, p_rare integer default 2300,
    p_epique integer default 8000, p_legendaire integer default 30000,
    p_confirmer boolean default false)
 returns table(section text, ligne text)
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_retro integer;
  v_montees integer;
begin
  if not (p_peucommun < p_rare and p_rare < p_epique and p_epique < p_legendaire) then
    raise exception 'Les seuils doivent aller en croissant';
  end if;
  if position('epique' in pg_get_constraintdef((select oid from pg_constraint where conname = 'communes_tier_check'))) = 0 then
    raise exception 'La contrainte communes_tier_check ne connaît pas « epique » : s2-1-socle.sql n''est pas passé';
  end if;
  if to_regclass('pg_temp.bascule2') is not null then drop table bascule2; end if;

  create temporary table bascule2 on commit drop as
  select c.code, c.population, c.tier as avant,
         case when c.population >= p_legendaire then 'legendaire'
              when c.population >= p_epique     then 'epique'
              when c.population >= p_rare       then 'rare'
              when c.population >= p_peucommun  then 'peucommun'
              else                                   'commun' end as apres
    from communes c;

  select count(*) into v_retro from bascule2 b
   where array_position(array['commun','peucommun','rare','epique','legendaire'], b.apres)
       < array_position(array['commun','peucommun','rare','epique','legendaire'], b.avant);
  if v_retro > 0 then
    raise exception 'Cette échelle ferait DESCENDRE % commune(s) de palier. Refusé.', v_retro;
  end if;
  select count(*) into v_montees from bascule2 b where b.avant <> b.apres;

  return query
  select '1. echelle'::text,
         (b.apres || ' : ' || count(*) || ' communes (avant '
          || (select count(*) from bascule2 x where x.avant = b.apres) || ')')::text
    from bascule2 b group by b.apres
   order by array_position(array['legendaire','epique','rare','peucommun','commun'], b.apres);

  return query
  select '2. mouvements'::text, (b.avant || ' -> ' || b.apres || ' : ' || count(*))::text
    from bascule2 b where b.avant <> b.apres group by b.avant, b.apres order by 2;

  return query
  select '3. detenues en Front qui montent'::text, (coalesce(j.pseudo, '?') || ' : ' || count(*))::text
    from bascule2 b join possessions p on p.commune_code = b.code
    left join joueurs j on j.id = p.joueur_id
   where b.avant <> b.apres group by coalesce(j.pseudo, '?') order by count(*) desc limit 15;

  if not p_confirmer then
    return query select '4. MODE BLANC'::text,
      ('Rien n''a été modifié. ' || v_montees || ' communes changeraient de palier. '
       || 'Relance avec p_confirmer => true pour appliquer.')::text;
    return;
  end if;

  update communes c set tier = b.apres
    from bascule2 b where b.code = c.code and b.avant <> b.apres;

  -- numéros des cartes dans leur palier, et taille des paliers
  with r as (
    select code,
           row_number() over (partition by tier order by population desc nulls last, code) as rg,
           count(*) over (partition by tier) as total
      from communes)
  update communes c set rang = r.rg, palier_total = r.total
    from r where r.code = c.code
     and (c.rang is distinct from r.rg or c.palier_total is distinct from r.total);

  return query select '4. APPLIQUÉ'::text,
    (v_montees || ' communes ont changé de palier ; numéros et totaux recalculés.')::text;
end;
$f$;

revoke all on function public.rebasculer_paliers_s2(integer, integer, integer, integer, boolean) from public, anon, authenticated;

-- Simulation (ne modifie rien) --------------------------------------------------------------
select * from rebasculer_paliers_s2();
