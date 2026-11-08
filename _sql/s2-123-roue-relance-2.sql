-- s2-123 (8/11/2026) : la case « Relance » de la roue du Front donne 2 tours gratuits (demande de Nataël).
--
-- Avant (s2-102) : la Relance rendait le jeton du tour (1 tour offert, qui ne compte pas dans la journée).
-- Maintenant : la valeur « relance » de la case dit combien de tours elle offre.
--   - relance = 1 : comme avant (le jeton est rendu) ;
--   - relance = 2 : le jeton est rendu ET un jeton de plus est ajouté (gardé même au-dessus de 3,
--     comme un cadeau). Le tour de la Relance ne compte pas dans la journée ; les tours joués
--     avec les jetons comptent normalement.
-- La réponse donne aussi « tours_offerts » pour le texte du jeu.

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

begin;

do $$
declare d text;
begin
  d := pg_get_functiondef('public.roue_front_tourner()'::regprocedure);
  d := pg_temp.remp(d, $a$  v_off    boolean;$a$, $a$  v_off    boolean;
  v_rel    integer := 0;   -- s2-123 : nombre de tours offerts par la case$a$, 1, 'déclaration');
  d := pg_temp.remp(d, $a$  v_off := coalesce((v_case->>'relance')::int, 0) = 1;              -- s2-102 : tour offert$a$,
$a$  v_rel := greatest(0, coalesce((v_case->>'relance')::int, 0));     -- s2-123 : 1 = le tour rendu, 2 = rendu + 1 de plus
  v_off := v_rel >= 1;                                              -- s2-102 : tour offert$a$, 1, 'relance');
  d := pg_temp.remp(d, $a$  if not v_off then   -- s2-102 : un tour offert rend son jeton
    update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;
  end if;$a$,
$a$  if not v_off then   -- s2-102 : un tour offert rend son jeton
    update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;
  elsif v_rel > 1 then   -- s2-123 : et la Relance en ajoute (gardés au-dessus de 3)
    update joueurs set jetons_gratuits = v_jet + (v_rel - 1), jetons_maj = now() where id = v_uid;
  end if;$a$, 1, 'jetons');
  d := pg_temp.remp(d, $a$    'relance',       v_off,$a$, $a$    'relance',       v_off,
    'tours_offerts', case when v_off then v_rel else 0 end,   -- s2-123$a$, 1, 'réponse');
  d := pg_temp.remp(d, $a$    'jetons',        round(v_jet - case when v_off then 0 else 1 end, 4),$a$,
$a$    'jetons',        round(v_jet + case when v_off then v_rel - 1 else -1 end, 4),   -- s2-123$a$, 1, 'réponse jetons');
  execute d;
end $$;

-- la case Relance offre 2 tours
update public.config_jeu
   set valeur = (select jsonb_set(c.valeur::jsonb, '{cases}',
                   (select jsonb_agg(case when e->>'id' = 'relance' then e || '{"relance": 2}'::jsonb else e end order by n)
                      from jsonb_array_elements(c.valeur::jsonb->'cases') with ordinality x(e, n)))::text
                   from public.config_jeu c where c.cle = 'roue_front')
 where cle = 'roue_front';

commit;

-- Contrôle : t | 2
select position('s2-123' in pg_get_functiondef('public.roue_front_tourner()'::regprocedure)) > 0 as fonction_ok,
       (select (e->>'relance')::int from public.config_jeu c, jsonb_array_elements(c.valeur::jsonb->'cases') e
         where c.cle = 'roue_front' and e->>'id' = 'relance') as relance;
