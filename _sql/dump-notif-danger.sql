-- ===========================================================================
--  TerraFront — LECTURE SEULE (27 octobre 2026)
--  Quand part la notification téléphone « X est en danger » ?
--  Ne modifie rien. Les lignes qui touchent au secret / à l'envoi sont
--  masquées : on ne lit que les conditions (if / when / victoires…).
-- ===========================================================================
with f as (
  select p.oid, p.proname, pg_get_functiondef(p.oid) as def
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and (p.proname ilike '%danger%' or pg_get_functiondef(p.oid) ilike '%''danger-%')
    and p.prokind = 'f'
), lignes as (
  select f.proname, l.n, l.txt
  from f, lateral unnest(string_to_array(f.def, E'\n')) with ordinality as l(txt, n)
)
select proname as fonction, n as ligne,
       case when txt ~* '(secret|x-terrafront|net\.http|bearer|authorization|apikey|https?://)' then '[masqué]' else txt end as texte
from lignes
where txt ~* '(create|returns|trigger|if |elsif|when|victoire|round|serie|série|danger|notifier_joueur|perform|then|insert|update|tg_|new\.|old\.)'
union all
select 'déclencheurs', 0, t.tgname || ' sur ' || t.tgrelid::regclass::text || ' → ' || t.tgfoid::regproc::text
from pg_trigger t
where not t.tgisinternal and t.tgfoid in (select oid from f)
order by 1, 2;
