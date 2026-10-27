-- ===========================================================================
--  s2-44 — Énergie du Front : réserve 45 (au lieu de 40), +1 toutes les
--  8 minutes (au lieu de 10). Décision de Nataël, 27 octobre 2026.
--  Mesure du jour : les 5 plus gros conquérants dépensaient 160 à 195
--  énergie par jour, presque tout ce qu'ils pouvaient recevoir.
--
--  1. front_energie_lire : la recharge (480 s, plafond 45). Le plafond des
--     bonus (quêtes, récolte, garnison, parrainage) reste 60.
--  2. front_energie() : renvoie 45 comme maximum et le bon délai. Modifiée à
--     partir de sa définition en production (textes attendus vérifiés, sinon
--     rien ne change).
--  Effet de bord assumé : au passage, un joueur qui n'a pas touché à son
--  énergie depuis un moment récupère sa recharge au nouveau rythme, et ceux
--  qui étaient à 40 montent à 45. Petit cadeau, une seule fois.
--  Rejouable. Contrôle attendu : true | true | true.
-- ===========================================================================
begin;

create or replace function public.front_energie_lire(p_val numeric, p_maj timestamptz)
 returns numeric
 language sql
 stable
 set search_path to 'public'
as $f$
  select case when p_val >= 45 then p_val
              else least(45, p_val + extract(epoch from (now() - p_maj)) / 480.0) end;
$f$;

do $$
declare d text; n int;
begin
  d := pg_get_functiondef('public.front_energie()'::regprocedure);
  if position('480' in d) > 0 then raise notice 'front_energie : déjà à jour'; return; end if;
  -- les trois endroits attendus : le maximum renvoyé, la réserve pleine, le délai
  n := (length(d) - length(replace(d, 'floor(v)::integer, 40,', ''))) / length('floor(v)::integer, 40,');
  if n <> 1 then raise exception 'front_energie : maximum attendu introuvable (%), rien n''a changé', n; end if;
  n := (length(d) - length(replace(d, 'when v >= 40 then null', ''))) / length('when v >= 40 then null');
  if n <> 1 then raise exception 'front_energie : réserve pleine attendue introuvable (%), rien n''a changé', n; end if;
  n := (length(d) - length(replace(d, '* 600)', ''))) / length('* 600)');
  if n <> 1 then raise exception 'front_energie : délai attendu introuvable (%), rien n''a changé', n; end if;
  d := replace(d, 'floor(v)::integer, 40,', 'floor(v)::integer, 45,');
  d := replace(d, 'when v >= 40 then null', 'when v >= 45 then null');
  d := replace(d, '* 600)', '* 480)');
  execute d;
end $$;

commit;

select pg_get_functiondef('public.front_energie_lire(numeric, timestamptz)'::regprocedure) ~ '480\.0' as recharge_8_min,
       pg_get_functiondef('public.front_energie()'::regprocedure) ~ 'integer, 45,' as maximum_45,
       pg_get_functiondef('public.front_energie()'::regprocedure) ~ '\* 480\)' as delai_8_min;
