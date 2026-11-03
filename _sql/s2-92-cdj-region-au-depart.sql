-- ===========================================================================
--  TerraFront — s2-92 : Commune du jour, la région dès le départ
--  (3/11/2026, idée de Nataël : « le premier essai, c'est un peu du hasard »).
--
--  Avant : rien au départ que la silhouette ; population après 1 essai, région
--  après 2, anecdote après 3, département après 4, habitants après 5.
--  Après : la région tout de suite ; puis population après 1 essai, anecdote
--  après 2, département après 3, habitants après 4.
--  Chaque indice dit aussi après combien d'essais il s'ouvre (« apres ») : le
--  jeu l'affiche (patch333). Un jeu pas encore mis à jour garde son ancien
--  libellé (« après n + 1 essais ») le temps de recharger la page.
--
--  Redéfinition complète de cdj_indices (petite fonction, même signature,
--  mêmes droits) : la partie normale et la partie invitée l'utilisent toutes
--  les deux (cdj-3-invite.sql). Les gains en TP ne changent pas.
--  Rejouable. Finit par une ligne de contrôle.
-- ===========================================================================

create or replace function public.cdj_indices(p_code text, p_ouverts int)
returns jsonb
language plpgsql stable security definer
set search_path to 'public'
as $$
declare
  c communes;
  v_fait text;
  v_rang int;
begin
  select * into c from communes where code = p_code;

  -- l'anecdote : le meilleur fait qui ne donne pas le nom, sinon le rang
  -- de population dans le département
  if p_ouverts >= 2 then   -- s2-92
    select f->>'t' into v_fait
      from jsonb_array_elements(coalesce(c.faits, '[]'::jsonb)) f
     where (f->>'t') !~ '«|lettres|caractères'
     order by (f->>'r')::int
     limit 1;
    if v_fait is null then
      select count(*) + 1 into v_rang from communes
       where departement = c.departement and population > c.population;
      v_fait := case when v_rang = 1 then 'La commune la plus peuplée de son département.'
                     else 'La ' || v_rang || 'e commune la plus peuplée de son département.' end;
    end if;
  end if;

  -- s2-92 : la région dès le départ, les autres décalées d'un cran
  return jsonb_build_array(
    jsonb_build_object('cle', 'region',      'apres', 0, 'valeur', cdj_region(c.departement)),
    jsonb_build_object('cle', 'population',  'apres', 1, 'valeur', case when p_ouverts >= 1 then
      case when c.population < 10000 then 'entre 5 000 et 10 000 habitants'
           when c.population < 20000 then 'entre 10 000 et 20 000 habitants'
           when c.population < 50000 then 'entre 20 000 et 50 000 habitants'
           when c.population < 100000 then 'entre 50 000 et 100 000 habitants'
           else 'plus de 100 000 habitants' end end),
    jsonb_build_object('cle', 'anecdote',    'apres', 2, 'valeur', case when p_ouverts >= 2 then v_fait end),
    jsonb_build_object('cle', 'departement', 'apres', 3, 'valeur', case when p_ouverts >= 3 then c.departement end),
    -- le nom des habitants donnait presque le nom de la commune : en dernier (6 octobre)
    jsonb_build_object('cle', 'gentile',     'apres', 4, 'valeur', case when p_ouverts >= 4 then c.gentile end));
end;
$$;

revoke all on function public.cdj_indices(text, int) from public, anon, authenticated;

-- contrôle : « region, population, anecdote, departement, gentile » | true | true
select (select string_agg(x->>'cle', ', ') from jsonb_array_elements(i) x) as ordre_indices,
       (i->0->>'valeur') is not null as region_au_depart,
       (i->1->>'valeur') is null as population_apres_un_essai
  from (select cdj_indices((select commune_code from cdj_jours order by jour desc limit 1), 0) as i) t;
