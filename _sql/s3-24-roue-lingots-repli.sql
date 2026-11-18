-- ===========================================================================
--  s3-24 (18/11/2026) — roue du Front : réserve de lingots pleine → des TP
--  Constat (15-17/11) : 38 % des cases « lingots » de la roue (329 sur 877) ne
--  donnaient rien, le porte-monnaie du joueur étant plein. Décision de Nataël
--  (18/11, 15 h 53) : les lingots qui n'entrent pas deviennent des TerraPoints,
--  à 5 TP par lingot (≈ 1 200 TP par jour en tout ; 15 TP comme le Mess aurait
--  ajouté ≈ 3 650 TP par jour). Les lingots seulement : l'énergie ne change pas.
--
--  Réglage : config_jeu 'roue_front'.tp_par_lingot (5 ; 0 = pas de repli).
--  Les TP passent au solde avec le motif « roue » ; la colonne tp de
--  roue_front_tours compte le repli. Le résultat renvoie tp_repli et
--  lingots_changes (patch452 l'affiche).
--  Contrôle attendu (dernière ligne) : 5 | true
-- ===========================================================================

update public.config_jeu
   set valeur = (valeur::jsonb || '{"tp_par_lingot": 5}'::jsonb)::text
 where cle = 'roue_front';

CREATE OR REPLACE FUNCTION public.roue_front_tourner()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_uid    uuid := auth.uid();
  cfg      jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'roue_front'), '{}'::jsonb);
  v_jour   date := (now() at time zone 'Europe/Paris')::date;
  v_par    integer := coalesce((cfg->>'par_jour')::int, 15);
  j        record;
  v_jet    numeric;
  v_n      integer;
  v_total  numeric;
  v_tir    numeric;
  v_acc    numeric := 0;
  r        record;
  v_case   jsonb;
  v_e      numeric;  v_e_reel integer := 0;
  v_l      numeric;  v_l_reel integer := 0;
  v_t      integer;
  v        numeric;
  v_nouv   numeric;
  v_tp     integer;
  v_off    boolean;
  v_rel    integer := 0;        -- s2-123 : nombre de tours offerts par la case
  v_soir_n integer := 0;        -- s2-125 : tours du soir restants avant ce tour
  v_offr   integer := 0;        -- s2-126 : tours offerts en réserve avant ce tour
  v_mode   text := 'jeton';     -- s2-126 : 'soir', 'offert' ou 'jeton'
  v_offr2  integer;
  v_l_chg  integer := 0;        -- s3-24 : lingots qui n'entrent pas
  v_repli  integer := 0;        -- s3-24 : leurs TerraPoints
begin
  /* s2-98 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not roue_front_ouverte(v_uid) then
    raise exception 'La roue du Front n''est pas pour toi en ce moment : tes paquets gratuits t''attendent !';
  end if;

  /* un seul tour à la fois par joueur : le compte du jour et les jetons restent justes */
  select case when roue_cfg_int('jetons_propres') = 1 then jj.roue_jetons else jj.jetons_gratuits end as jetons_gratuits,   -- s3-18
           case when roue_cfg_int('jetons_propres') = 1 then jj.roue_jetons_maj else jj.jetons_maj end as jetons_maj,
           jj.front_energie, jj.front_energie_maj,
         jj.roue_soir_jour, jj.roue_soir_restants, jj.roue_offerts
    into j from joueurs jj where jj.id = v_uid for update;
  if not found then raise exception 'Joueur introuvable'; end if;

  /* s2-125 : la soirée de la roue */
  if roue_soir_ouverte() then
    v_soir_n := case when j.roue_soir_jour is distinct from v_jour
                     then coalesce((cfg->'soir'->>'tours')::int, 0)
                     else coalesce(j.roue_soir_restants, 0) end;
  end if;
  v_offr := greatest(0, coalesce(j.roue_offerts, 0));
  v_mode := case when v_soir_n >= 1 then 'soir' when v_offr >= 1 then 'offert' else 'jeton' end;

  select count(*) into v_n from roue_front_tours t where t.joueur_id = v_uid and t.jour = v_jour
     and not t.offert;   -- s2-102 : un tour offert ne compte pas
  if v_n >= v_par and v_mode = 'jeton' then
    raise exception 'Tu as fait tes % tours du jour : la roue revient demain !', v_par;
  end if;

  v_jet := coalesce(j.jetons_gratuits, 0);
  if v_jet < 3 then v_jet := least(3, v_jet + extract(epoch from (now() - coalesce(j.jetons_maj, now()))) / 1200.0); end if;
  if v_jet < 1 and v_mode = 'jeton' then
    raise exception 'Pas de tour disponible pour le moment : un tour revient toutes les 20 minutes.';
  end if;

  /* le tirage : chaque case a sa chance (poids) */
  select sum(greatest(0, coalesce((e->>'poids')::numeric, 0))) into v_total from jsonb_array_elements(coalesce(cfg->'cases', '[]'::jsonb)) e;
  if coalesce(v_total, 0) <= 0 then raise exception 'La roue n''est pas réglée'; end if;
  v_tir := random() * v_total;
  for r in select e, n from jsonb_array_elements(cfg->'cases') with ordinality as x(e, n) order by n loop
    v_acc := v_acc + greatest(0, coalesce((r.e->>'poids')::numeric, 0));
    v_case := r.e;
    exit when v_tir < v_acc;
  end loop;

  v_e := greatest(0, coalesce((v_case->>'energie')::numeric, 0));
  v_l := greatest(0, coalesce((v_case->>'lingots')::numeric, 0));
  v_t := greatest(0, coalesce((v_case->>'terra')::int, 0));
  v_tp := greatest(0, coalesce((v_case->>'tp')::int, 0));           -- s2-102 : TerraPoints
  v_rel := greatest(0, coalesce((v_case->>'relance')::int, 0));     -- s2-123 : 1 = le tour rendu, 2 = rendu + 1 offert
  v_off := v_rel >= 1;                                              -- s2-102 : le tour est rendu

  /* s2-126 : ce que le tour consomme, et les tours offerts gagnés */
  if v_mode = 'soir' and not v_off then
    update joueurs set roue_soir_jour = v_jour, roue_soir_restants = v_soir_n - 1 where id = v_uid;
  elsif v_mode = 'soir' then
    update joueurs set roue_soir_jour = v_jour, roue_soir_restants = v_soir_n where id = v_uid;
  elsif v_mode = 'jeton' and not v_off then
    if roue_cfg_int('jetons_propres') = 1 then   -- s3-18 : les jetons de la roue
      update joueurs set roue_jetons = v_jet - 1, roue_jetons_maj = now() where id = v_uid;
    else
      update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;
    end if;
  end if;
  v_offr2 := v_offr - case when v_mode = 'offert' and not v_off then 1 else 0 end
                    + case when v_off then v_rel - 1 else 0 end;
  if v_offr2 <> v_offr then
    update joueurs set roue_offerts = v_offr2 where id = v_uid;
  end if;

  /* énergie : jusqu'au plafond des bonus, jamais en dessous de ce qu'on avait */
  if v_e > 0 then
    v := front_energie_lire(j.front_energie, j.front_energie_maj);
    v_nouv := greatest(v, least(front_energie_reglage('plafond'), v + v_e));
    v_e_reel := greatest(0, floor(v_nouv) - floor(v))::integer;
    update joueurs set front_energie = v_nouv, front_energie_maj = now() where id = v_uid;
  end if;

  /* lingots : figer la réserve (production comprise), puis ajouter sans dépasser son maximum */
  if v_l > 0 then
    v := lingots_figer(v_uid);
    v_nouv := greatest(v, least(lingots_max(v_uid), v + v_l));
    v_l_reel := greatest(0, floor(v_nouv) - floor(v))::integer;
    update joueurs set lingots = v_nouv where id = v_uid;
    /* s3-24 : ce qui n'entre pas devient des TerraPoints */
    v_l_chg := greatest(0, v_l::integer - v_l_reel);
    v_repli := v_l_chg * greatest(0, coalesce((cfg->>'tp_par_lingot')::int, 5));
    if v_repli = 0 then v_l_chg := 0; end if;
  end if;

  /* paquet Terra : un jeton de plus (gardé même au-dessus de 3, comme un cadeau) */
  if v_t > 0 then
    update joueurs set terra_jetons = terra_jetons_lire(terra_jetons, terra_jetons_maj) + v_t, terra_jetons_maj = now()
     where id = v_uid;
  end if;

  /* s2-102 : TerraPoints, au solde de Terra (tracé avec le motif « roue ») ; s3-24 : repli compris */
  if v_tp + v_repli > 0 then
    perform set_config('terrafront.motif', 'roue', true);
    update joueurs set solde = coalesce(solde, 0) + v_tp + v_repli where id = v_uid;
  end if;

  insert into roue_front_tours (joueur_id, jour, case_id, energie, lingots, terra, tp, offert, soir)
  values (v_uid, v_jour, coalesce(v_case->>'id', '?'), v_e_reel, v_l_reel, v_t, v_tp + v_repli, v_off or v_mode <> 'jeton', v_mode = 'soir');

  return jsonb_build_object(
    'case',          v_case->>'id',
    'energie',       v_e_reel,
    'energie_prevue', v_e::integer,
    'lingots',       v_l_reel,
    'lingots_prevus', v_l::integer,
    'lingots_changes', v_l_chg,                                                                -- s3-24
    'tp_repli',      v_repli,                                                                   -- s3-24
    'terra',         v_t,
    'tp',            v_tp,
    'relance',       v_off,
    'tours_offerts', case when v_off then v_rel else 0 end,   -- s2-123
    'solde',         (select coalesce(jj.solde, 0) from joueurs jj where jj.id = v_uid),
    'energie_totale', (select floor(front_energie_lire(jj.front_energie, jj.front_energie_maj))::integer from joueurs jj where jj.id = v_uid),
    'lingots_total', floor(coalesce(lingots_lire(v_uid), 0))::integer,
    'jetons',        round(v_jet - case when v_mode = 'jeton' and not v_off then 1 else 0 end, 4),
    'tours_jour',    v_n + case when v_mode = 'jeton' and not v_off then 1 else 0 end,
    'par_jour',      v_par,
    'soir',          roue_soir_ouverte(),                                                       -- s2-125
    'tour_du_soir',  v_mode = 'soir',
    'soir_restants', case when v_mode = 'soir' then v_soir_n - case when v_off then 0 else 1 end else v_soir_n end,
    'offerts',       v_offr2,                                                                   -- s2-126
    'mode',          v_mode);
end; $function$;

-- Contrôle
select (select (valeur::jsonb ->> 'tp_par_lingot')::int from config_jeu where cle = 'roue_front') as tp_par_lingot,
       position('v_repli' in pg_get_functiondef('public.roue_front_tourner'::regproc)) > 0 as fonction_a_jour;
