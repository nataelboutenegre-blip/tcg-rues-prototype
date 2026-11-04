-- ===========================================================================
--  TerraFront — s2-96 : les alertes d'attaque disaient faux (relevé le 4/11
--  en relisant les règles pour le récap des joueurs).
--
--  1. Après une défense RÉUSSIE qui fait passer l'attaquant de 2 victoires à
--     1, le défenseur recevait « X a gagné un round… » : l'alerte partait dès
--     que la série valait 1, qu'elle monte ou qu'elle descende (vérifié sur la
--     base de test avec les vraies fonctions). Maintenant elle ne part que
--     quand la série MONTE. Même garde pour l'alerte « en danger » (2 sur 3).
--  2. Les deux textes parlaient de victoires « d'affilée » (faux depuis que la
--     série est gardée) et de « poser un bouclier » (il n'y en a pas au Front).
--  3. La quête « Conquiers une commune » disait « Trois victoires d'affilée ».
--  Rien d'autre ne change. Indépendant du lot du 8/11 (aucun de ses fichiers
--  ne touche ces fonctions ni cette ligne) : peut passer tout de suite.
--  Modifiées en place à partir de leur définition en production : si un
--  texte attendu manque, rien ne change. Rejouable.
--  Contrôle attendu : true | true | true
-- ===========================================================================
begin;

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

-- 1. alerte « est attaquée » (1 victoire sur 3) ------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.notif_premiere_attaque()'::regprocedure);
  if position('s2-96' in d) > 0 then raise notice 'notif_premiere_attaque : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    'if new.victoires_consecutives = 1 and (tg_op = ''INSERT'' or old.victoires_consecutives is distinct from 1) then',
    'if new.victoires_consecutives = 1 and (tg_op = ''INSERT'' or coalesce(old.victoires_consecutives, 0) < 1) then   -- s2-96 : seulement quand la série monte',
    1, 'notif_premiere_attaque (condition)');
  d := pg_temp.remp(d,
    ''' a gagné un round. Encore 2 victoires d''''affilée et elle tombe : défends-la ou pose un bouclier.''',
    ''' a gagné un round contre toi : 1 victoire sur 3. Défends-la.''',
    1, 'notif_premiere_attaque (texte)');
  execute d;
end $$;

-- 2. alerte « est en danger » (2 victoires sur 3) ----------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.notif_danger_siege()'::regprocedure);
  if position('s2-96' in d) > 0 then raise notice 'notif_danger_siege : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    'if new.victoires_consecutives = 2 and (tg_op = ''INSERT'' or old.victoires_consecutives is distinct from 2) then',
    'if new.victoires_consecutives = 2 and (tg_op = ''INSERT'' or coalesce(old.victoires_consecutives, 0) < 2) then   -- s2-96 : seulement quand la série monte',
    1, 'notif_danger_siege (condition)');
  d := pg_temp.remp(d,
    ''' a gagné 2 rounds d''''affilée. Plus qu''''une victoire avant de la perdre : défends-la ou pose un bouclier.''',
    ''' a 2 victoires sur 3. Encore une et elle tombe : défends-la vite.''',
    1, 'notif_danger_siege (texte)');
  execute d;
end $$;

-- 3. la quête « Conquiers une commune » --------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  if position('pas forcément d''''affilée' in d) > 0 then raise notice 'quetes_liste : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    '''Trois victoires d''''affilée''',
    '''Trois victoires, pas forcément d''''affilée''',
    1, 'quetes_liste (conquête)');
  execute d;
end $$;

commit;

-- Contrôle : true | true | true
select position('s2-96' in pg_get_functiondef('public.notif_premiere_attaque()'::regprocedure)) > 0      as alerte_attaque_ok,
       position('s2-96' in pg_get_functiondef('public.notif_danger_siege()'::regprocedure)) > 0          as alerte_danger_ok,
       position('pas forcément d''''affilée' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0
       and has_function_privilege('authenticated', 'public.quetes()', 'execute')                         as quete_ok;
