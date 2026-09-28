-- ---------------------------------------------------------------------------
--  classement-etat.sql — lecture seule
--
--  cloturer_saison() archive le palmares dans cet ordre : nombre de
--  communes, puis legendaires, puis rares. C'est une supposition. Si le
--  classement affiche dans le jeu range autrement, un joueur verra son
--  rang changer entre la veille de la cloture et le palmares definitif,
--  et il aura raison de le signaler.
--
--  On lit la fonction pour aligner les deux.
-- ---------------------------------------------------------------------------
select 'definition de ' || p.proname
       || '(' || pg_get_function_identity_arguments(p.oid) || ')' as quoi,
       pg_get_functiondef(p.oid) as detail
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname = 'classement'
order by 1;
