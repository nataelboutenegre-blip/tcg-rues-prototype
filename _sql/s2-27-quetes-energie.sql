-- ===========================================================================
--  TerraFront — saison 2 : plus d'énergie par les quêtes (25 octobre 2026)
--  Décision de Nataël : plus de quêtes Front, plafond relevé, à revoir avec
--  les chiffres le 1er novembre.
--
--  1. Plafond de l'énergie des quêtes : 20 → 35 par jour (reclamer_quete).
--     Le réservoir reste plafonné à 60 comme avant.
--  2. Trois quêtes Front de plus (+5 énergie chacune), lues dans des données
--     qui existent déjà (aucune fonction de combat n'est touchée) :
--       f_conq3   Conquiers 3 communes            (compteur « conquete »)
--       f_depts   Conquiers dans 2 départements   (front_victoires du jour)
--       f_tenir   Garde une commune prise hier    (front_victoires d'hier
--                                                  + toujours dans possessions)
--  Les deux fonctions sont modifiées à partir de leur définition en base :
--  si un texte attendu manque (ou est en double), tout s'annule.
--  À passer AVANT de pousser patch185 (qui affiche « / 35 »).
--  Rejouable. Contrôle attendu : true | true | 11
-- ===========================================================================
begin;

-- 1. quetes_liste : trois quêtes Front ---------------------------------------
do $$
declare
  d text := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  r record;
begin
  if position('f_conq3' in d) > 0 then raise notice 'quetes_liste : déjà fait'; return; end if;
  for r in select * from (values
    ($a$v_radar int; v_rafale int; v_pom int;$a$,
     $a$v_radar int; v_rafale int; v_pom int; v_depts int; v_tenue int;$a$),
    ($a$  select count(*) into v_pom from pom_parties pp where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini;$a$,
     $a$  select count(*) into v_pom from pom_parties pp where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini;
  select count(distinct c.departement) into v_depts
    from front_victoires fv join communes c on c.code = fv.commune_code
   where fv.joueur_id = p_uid and fv.type = 'conquete' and fv.le >= v_minuit;
  select count(*) into v_tenue
    from front_victoires fv
    join possessions p on p.commune_code = fv.commune_code and p.joueur_id = p_uid
   where fv.joueur_id = p_uid and fv.type = 'conquete'
     and fv.le >= v_minuit - interval '24 hours' and fv.le < v_minuit;$a$),
    ($a$c_conquete, 1,    50, 3),$a$,
     $a$c_conquete, 1,    50, 3),
    ('f_conq3',     'front', 'jour',   'Conquiers 3 communes',           'Trois prises dans la journée',           c_conquete, 3,    0, 5),
    ('f_depts',     'front', 'jour',   'Conquiers dans 2 départements',  'Deux départements différents',           v_depts,    2,    0, 5),
    ('f_tenir',     'front', 'jour',   'Garde une commune prise hier',   'Toujours à toi aujourd''hui',            v_tenue,    1,    0, 5),$a$)
  ) as t(avant, apres) loop
    if (length(d) - length(replace(d, r.avant, ''))) / length(r.avant) <> 1 then
      raise exception 'quetes_liste : texte attendu introuvable (ou en double) : %', left(r.avant, 60);
    end if;
    d := replace(d, r.avant, r.apres);
  end loop;
  execute d;
  raise notice 'quetes_liste : 3 quêtes Front ajoutées';
end $$;

-- 2. reclamer_quete : plafond 35 ---------------------------------------------
do $$
declare
  d text := pg_get_functiondef('public.reclamer_quete(text)'::regprocedure);
  r record;
begin
  if position('35 - v_deja' in d) > 0 then raise notice 'reclamer_quete : déjà fait'; return; end if;
  for r in select * from (values
    ($a$greatest(0, 20 - v_deja)$a$, $a$greatest(0, 35 - v_deja)$a$),
    ($a$(20 / 20)$a$,               $a$(35 / 35)$a$)
  ) as t(avant, apres) loop
    if (length(d) - length(replace(d, r.avant, ''))) / length(r.avant) <> 1 then
      raise exception 'reclamer_quete : texte attendu introuvable (ou en double) : %', left(r.avant, 60);
    end if;
    d := replace(d, r.avant, r.apres);
  end loop;
  execute d;
  raise notice 'reclamer_quete : plafond 35';
end $$;

commit;

-- contrôle : nouvelles quêtes | plafond 35 | quêtes Front du jour (11 attendu)
select position('f_tenir' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0   as quetes_ok,
       position('35 - v_deja' in pg_get_functiondef('public.reclamer_quete(text)'::regprocedure)) > 0 as plafond_ok,
       (select count(*) from public.quetes_liste('00000000-0000-0000-0000-000000000000'::uuid)
         where mode = 'front' and categorie = 'jour')                                               as quetes_front;
