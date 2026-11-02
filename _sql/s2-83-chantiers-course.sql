-- ===========================================================================
--  TerraFront — s2-83 : la course au nom gravé (2/11/2026), avec patch319
--
--  Chaque monument de l'état des chantiers (chantiers_etat_json) dit en plus :
--    autres     : combien d'AUTRES joueurs ont un chantier en cours dessus ;
--    autres_fin : l'heure de fin du plus avancé d'entre eux (chantiers pas en
--                 pause), ou rien.
--  Jamais de pseudo ni d'identifiant : seulement un nombre et une heure.
--  Ajoute deux lignes à la fonction en production ; si le repère n'est pas
--  trouvé une seule fois, rien n'est modifié. Rejouable.
--  Contrôle attendu : true | true
-- ===========================================================================
begin;

do $g$
declare
  d text;
  n integer;
  v_avant text := '''a_moi'', exists (select 1 from terra_collection t where t.joueur_id = p_uid';
begin
  d := pg_get_functiondef('public.chantiers_etat_json(uuid)'::regprocedure);
  if position('s2-83' in d) > 0 then
    raise notice 'chantiers_etat_json : déjà à jour';
    return;
  end if;
  n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
  if n <> 1 then raise exception 'chantiers_etat_json : repère attendu une fois, trouvé % fois : rien n''a changé', n; end if;
  execute replace(d, v_avant,
    '''autres'', (select count(*) from chantiers o where o.commune_code = cm.commune_code and o.joueur_id <> p_uid),   -- s2-83
                     ''autres_fin'', (select min(o.fin_prevue) from chantiers o
                                     where o.commune_code = cm.commune_code and o.joueur_id <> p_uid and not o.en_pause),
                     ' || v_avant);
end
$g$;

commit;

-- contrôle : la fonction est à jour, et elle tourne
select position('s2-83' in pg_get_functiondef('public.chantiers_etat_json(uuid)'::regprocedure)) > 0 as course_ajoutee,
       jsonb_typeof(public.chantiers_etat_json('00000000-0000-0000-0000-000000000000'::uuid) -> 'monuments') = 'array' as etat_ok;
