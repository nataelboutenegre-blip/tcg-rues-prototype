-- ===========================================================================
--  TerraFront — le pot vide (23 octobre 2026)
--
--  Il reste ~1 600 communes libres et le pot devrait être vide samedi,
--  avant la saison 2. Sans ce fichier, un joueur paierait 200 points pour un
--  paquet acheté qui ne donne plus rien, et un paquet gratuit serait
--  consommé pour rien.
--
--  demarrer_paquet refuse maintenant, AVANT de prendre quoi que ce soit :
--    - un paquet ACHETÉ s'il reste moins de 5 communes libres
--      (les points et la limite du jour sont gardés) ;
--    - un paquet GRATUIT s'il ne reste aucune commune libre
--      (le paquet gratuit reste dans la réserve).
--  Les tirages déjà commencés ne changent pas.
--
--  La fonction de production est modifiée sur place (deux lignes insérées
--  avant « if p_type = 'gratuit' then ») : le reste de sa définition, y
--  compris le verrou de la saison 2, est gardé tel quel. Si ce texte n'est
--  pas trouvé exactement une fois, rien n'est modifié.
--  Rejouable. Finit par un contrôle (une ligne).
-- ===========================================================================

do $pot$
declare
  v_def text := pg_get_functiondef('public.demarrer_paquet(text)'::regprocedure);
  v_avant text := E'  if p_type = ''gratuit'' then';
  v_ajout text := E'  -- pot-vide (23 octobre) : refuser avant de prendre quoi que ce soit\n'
    || E'  if p_type = ''achete'' and (select count(*) from communes c where not exists (select 1 from possessions po where po.commune_code = c.code)) < 5 then\n'
    || E'    raise exception ''Plus assez de communes libres pour un paquet acheté : tes points sont gardés. La France est presque entièrement conquise !'';\n'
    || E'  end if;\n'
    || E'  if p_type = ''gratuit'' and not exists (select 1 from communes c where not exists (select 1 from possessions po where po.commune_code = c.code)) then\n'
    || E'    raise exception ''Plus aucune commune libre pour le moment : ton paquet gratuit est gardé. La France est entièrement conquise !'';\n'
    || E'  end if;\n\n';
  n integer;
begin
  if position('pot-vide' in v_def) > 0 then
    raise notice 'demarrer_paquet : déjà en place';
    return;
  end if;
  n := (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise exception 'demarrer_paquet : texte attendu présent % fois au lieu de 1. Rien n''a été modifié. Envoie-moi sa définition.', n;
  end if;
  execute replace(v_def, v_avant, v_ajout || v_avant);
  raise notice 'demarrer_paquet : modifiée';
end
$pot$;

-- Contrôle : en_place doit valoir true ; libres = communes encore libres
select position('pot-vide' in pg_get_functiondef('public.demarrer_paquet(text)'::regprocedure)) > 0 as en_place,
       (select count(*) from public.communes c
         where not exists (select 1 from public.possessions po where po.commune_code = c.code)) as libres;
