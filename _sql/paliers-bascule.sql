-- ===========================================================================
--  TerraFront — nouvelle echelle de rarete
--
--  De   2 000 / 10 000 / 100 000   (29 318 / 4 392 /   981 /  48)
--  vers 1 000 /  5 000 /  50 000   (24 799 / 7 748 / 2 046 / 146)
--
--  POURQUOI : aujourd'hui 84 % des communes sont communes, donc 0,844^5 =
--  43 % des paquets sortent entierement gris. Avec la nouvelle echelle,
--  71 % de communes, soit 19 % de paquets gris. Un paquet sur deux sans
--  rien a regarder devient un paquet sur cinq.
--
--  L'ecart de 14x entre rare et legendaire est VOULU : c'est lui qui fait
--  qu'une legendaire reste une legendaire. Ce n'est pas un defaut a
--  corriger.
--
--  SURETE : les trois seuils ne font que BAISSER, donc aucune commune ne
--  peut descendre de palier. Personne ne perd de points. La fonction
--  refuse de s'executer si elle trouve une seule retrogradation — l'argu-
--  ment de surete est dans le code, pas dans une note.
--
--  Le classement peut malgre tout se reordonner : une promotion ajoute
--  des points a celui qui detient la commune. Le mode blanc montre ce
--  reordonnancement avant que quoi que ce soit ne change.
--
--  USAGE
--    select * from rebasculer_paliers();              -- mode blanc
--    select * from rebasculer_paliers(p_confirmer => true);
-- ===========================================================================

drop function if exists public.rebasculer_paliers(integer, integer, integer, boolean);

create function public.rebasculer_paliers(
  p_peucommun  integer default 1000,
  p_rare       integer default 5000,
  p_legendaire integer default 50000,
  p_confirmer  boolean default false)
returns table(section text, ligne text)
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_retro integer;
  v_montees integer;
begin
  if not (p_peucommun < p_rare and p_rare < p_legendaire) then
    raise exception 'Les trois seuils doivent aller en croissant : % < % < %',
      p_peucommun, p_rare, p_legendaire;
  end if;

  -- Les tables temporaires sont detruites a la fin de la transaction, mais
  -- deux appels DANS LA MEME transaction se marcheraient dessus : l'editeur
  -- SQL de Supabase peut enchainer deux requetes sans commit entre les deux.
  -- to_regclass plutot que « drop if exists » : celui-ci emet un NOTICE
  -- bruyant a chaque appel dans l'editeur SQL.
  if to_regclass('pg_temp.bascule') is not null then drop table bascule; end if;
  if to_regclass('pg_temp.rangs')   is not null then drop table rangs;   end if;

  -- Le palier vise pour chaque commune, calcule une seule fois.
  create temporary table bascule on commit drop as
  select c.code, c.population, c.tier as avant,
         case when c.population >= p_legendaire then 'legendaire'
              when c.population >= p_rare       then 'rare'
              when c.population >= p_peucommun  then 'peucommun'
              else                                   'commun' end as apres
    from communes c;

  -- Le rang d'un palier, pour savoir si un mouvement monte ou descend.
  -- 4 = commun, 1 = legendaire.
  create temporary table rangs on commit drop as
  select * from (values ('legendaire', 1), ('rare', 2),
                        ('peucommun', 3), ('commun', 4)) as t(tier, rg);

  select count(*) into v_retro
    from bascule b
    join rangs ra on ra.tier = b.avant
    join rangs rp on rp.tier = b.apres
   where rp.rg > ra.rg;

  if v_retro > 0 then
    raise exception 'Cette echelle ferait DESCENDRE % commune(s) de palier. Les joueurs qui les detiennent perdraient des points. Refuse.', v_retro;
  end if;

  select count(*) into v_montees from bascule b where b.avant <> b.apres;

  -- --- ce que ca change dans la carte ------------------------------------
  return query
  select '1. echelle'::text,
         (b.apres || ' : ' || count(*) || ' communes'
          || ' (avant ' || (select count(*) from bascule x where x.avant = b.apres) || ')')::text
    from bascule b group by b.apres
    order by 2;

  return query
  select '2. mouvements'::text,
         (b.avant || ' -> ' || b.apres || ' : ' || count(*) || ' communes')::text
    from bascule b where b.avant <> b.apres
   group by b.avant, b.apres order by 2;

  -- --- ce que ca change chez les joueurs ---------------------------------
  -- Les communes DETENUES qui changent de palier, et par qui.
  return query
  select '3. detenues qui montent'::text,
         (coalesce(j.pseudo, '?') || ' : ' || count(*) || ' commune(s)')::text
    from bascule b
    join possessions p on p.commune_code = b.code
    left join joueurs j on j.id = p.joueur_id
   where b.avant <> b.apres
   group by coalesce(j.pseudo, '?')
   order by 2;

  -- --- le classement, avant et apres -------------------------------------
  return query
  with avant as (
    select p.joueur_id, coalesce(j.pseudo, '?') as pseudo,
           sum(points_rarete(b.avant))::integer as score,
           count(*)::integer as communes,
           sum(coalesce(c.population, 0))::bigint as habitants
      from possessions p
      join bascule b on b.code = p.commune_code
      join communes c on c.code = p.commune_code
      left join joueurs j on j.id = p.joueur_id
     group by p.joueur_id, coalesce(j.pseudo, '?')
  ), apres as (
    select p.joueur_id,
           sum(points_rarete(b.apres))::integer as score
      from possessions p
      join bascule b on b.code = p.commune_code
     group by p.joueur_id
  ), rangs_av as (
    select a.*, row_number() over (order by a.score desc, a.communes desc,
                                   a.habitants desc, a.pseudo) as rg
      from avant a
  ), rangs_ap as (
    select a.joueur_id, ap.score as score_ap,
           row_number() over (order by ap.score desc, a.communes desc,
                              a.habitants desc, a.pseudo) as rg_ap
      from avant a join apres ap on ap.joueur_id = a.joueur_id
  )
  select '4. classement'::text,
         (lpad(v.rg::text, 2) || ' -> ' || lpad(w.rg_ap::text, 2)
          || case when v.rg = w.rg_ap then '  = ' else ' !! ' end
          || rpad(v.pseudo, 14)
          || lpad(v.score::text, 7) || ' -> ' || lpad(w.score_ap::text, 7)
          || '  (+' || (w.score_ap - v.score) || ')')::text
    from rangs_av v join rangs_ap w on w.joueur_id = v.joueur_id
   order by v.rg;

  -- --- l'effet sur les paquets -------------------------------------------
  return query
  select '5. paquets gris'::text,
         ('avant ' || round(100 * power(
             (select count(*)::numeric from bascule where avant = 'commun')
             / (select count(*) from bascule), 5), 1) || ' %'
          || '  ->  apres ' || round(100 * power(
             (select count(*)::numeric from bascule where apres = 'commun')
             / (select count(*) from bascule), 5), 1) || ' %'
          || '   (5 cartes toutes communes, pot plein)')::text;

  -- --- on ecrit, ou pas ---------------------------------------------------
  if not p_confirmer then
    return query select '6. MODE BLANC'::text,
      ('Rien n''a ete modifie. ' || v_montees || ' communes changeraient de palier. '
       || 'Relance avec p_confirmer => true pour appliquer.')::text;
    return;
  end if;

  update communes c
     set tier = b.apres
    from bascule b
   where b.code = c.code and b.avant <> b.apres;

  return query select '6. APPLIQUE'::text,
    (v_montees || ' communes ont change de palier. Pense a mettre a jour le '
     || 'bloc des raretes de la page d''accueil (index.html), qui est en dur.')::text;
end;
$function$;

revoke all on function public.rebasculer_paliers(integer, integer, integer, boolean)
  from public, anon, authenticated;


-- ---------------------------------------------------------------------------
--  Les comptes du tableau des Regles viennent de la base
--
--  Ils etaient ecrits en dur dans index.html. Deux sources pour un meme
--  chiffre finissent toujours par diverger — c'est ce qui a mis la barre
--  du bas sur deux lignes ce matin. Le client lira cette fonction.
-- ---------------------------------------------------------------------------
create or replace function public.totaux_paliers()
returns table(tier text, total integer, pop_min integer, pop_max integer)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select c.tier::text, count(*)::integer,
         min(c.population)::integer, max(c.population)::integer
    from communes c
   group by c.tier;
$function$;

revoke all on function public.totaux_paliers() from public;
grant execute on function public.totaux_paliers() to anon, authenticated;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. fonctions' as controle,
       string_agg(p.proname, ', ' order by p.proname) as valeur
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('rebasculer_paliers', 'totaux_paliers')
union all
select 'B. droits',
       coalesce(string_agg(p.proname || ' -> ' ||
                coalesce(array_to_string(p.proacl, ' '), 'defaut'),
                chr(10) order by p.proname), 'aucune')
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('rebasculer_paliers', 'totaux_paliers')
order by 1;
