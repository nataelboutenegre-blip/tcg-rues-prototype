-- s2-143 (13/11/2026) : les merveilles plus justes (Oshannir : « le premier qui clique est premier »).
-- Constat : sur Notre-Dame, les 6 premiers avaient tous équipe et outils au maximum (12,8 h par heure) ;
-- leurs écarts ne venaient que de l'heure d'envoi. 8 joueurs sont au maximum.
-- Décisions de Nataël (13/11, « Ok parfait » 20 h 07 UTC) :
--  1. Fenêtre d'ouverture : une équipe envoyée dans les 12 premières heures d'une merveille compte depuis
--     l'ouverture (seulement la première fois qu'elle rejoint cette merveille).
--  2. Gravure par paliers : « Bâtisseur » à partir de 1 000 h données, tous gravés (au lieu des 10 premiers).
--     Les merveilles finies avant ce script gardent leurs 10 gravés (on n'efface aucun nom).
--  3. Savoir-faire : +2 % de rythme par monument restauré chez soi, +40 % au plus ; sur son chantier et sur la merveille.
-- Limite connue : pendant la fenêtre, le chantier perso a pu avancer en même temps (au plus 12 h comptées deux fois).

update config_jeu set valeur = (valeur::jsonb || jsonb_build_object(
    'ouverture_h', 12, 'batisseur', 1000, 'savoir_pct', 0.02, 'savoir_max', 0.40,
    'paliers_depuis', to_jsonb(now())))::text
 where cle = 'chantiers' and not (valeur::jsonb ? 'batisseur');

-- avant de changer les rythmes : arrêter les compteurs à l'ancien rythme
do $r$
declare u uuid;
begin
  for u in select distinct joueur_id from (select joueur_id from chantiers where not en_pause
                                           union select joueur_id from chantiers_mecenes where actif) x loop
    perform chantiers_regler(u);
  end loop;
end $r$;

-- le savoir-faire d'un joueur (0 à 0,40)
create or replace function public.chantiers_savoir(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select least(coalesce((chantiers_reglages() ->> 'savoir_max')::numeric, 0.40),
               coalesce((chantiers_reglages() ->> 'savoir_pct')::numeric, 0.02)
               * (select count(*) from chantiers_restaurations r where r.joueur_id = p_uid));
$f$;
-- le rythme d'une équipe, savoir-faire compris
create or replace function public.chantiers_rythme_j(p_uid uuid, p_ouvriers integer, p_outils integer)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$ select chantiers_rythme(p_ouvriers, p_outils) * (1 + chantiers_savoir(p_uid)); $f$;

-- les six fonctions qui calculaient le rythme passent par chantiers_rythme_j (réécrites depuis leur définition en base)
do $d$
declare f text; def text; n integer;
begin
  foreach f in array array['chantiers_regler', 'chantiers_rythme_appliquer', 'chantiers_finaliser', 'chantier_commencer', 'merveille_equipe', 'chantiers_etat_json'] loop
    select pg_get_functiondef(p.oid) into def from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = f;
    if def is null then raise exception 's2-143 : % introuvable', f; end if;
    n := (length(def) - length(replace(def, 'chantiers_rythme(e.ouvriers, e.outils)', ''))) / length('chantiers_rythme(e.ouvriers, e.outils)');
    if n < 1 then raise exception 's2-143 : appel introuvable dans %', f; end if;
    def := replace(def, 'chantiers_rythme(e.ouvriers, e.outils)',
                   case when f = 'chantiers_etat_json' then 'chantiers_rythme_j(p_uid, e.ouvriers, e.outils)'
                        else 'chantiers_rythme_j(e.joueur_id, e.ouvriers, e.outils)' end);
    -- 1. la fenêtre d'ouverture : la première arrivée sur la merveille compte depuis l'ouverture
    if f = 'merveille_equipe' then
      if position('values (m.commune_code, v_uid, 0, now(), true, v_r)' in def) = 0 then raise exception 's2-143 : envoi introuvable'; end if;
      def := replace(def, 'values (m.commune_code, v_uid, 0, now(), true, v_r)',
        'values (m.commune_code, v_uid, 0, case when now() < m.ouverte_le + make_interval(hours => coalesce((chantiers_reglages() ->> ''ouverture_h'')::int, 12)) then m.ouverte_le else now() end, true, v_r)   -- s2-143');
    end if;
    -- 3. une restauration de plus : le savoir-faire monte, la merveille suit
    if f = 'chantiers_finaliser' then
      if position('delete from chantiers where joueur_id = r.joueur_id;' in def) = 0 then raise exception 's2-143 : boucle des chantiers introuvable'; end if;
      def := replace(def, 'delete from chantiers where joueur_id = r.joueur_id;',
        'delete from chantiers where joueur_id = r.joueur_id;' || chr(10) || '    perform chantiers_rythme_appliquer(r.joueur_id);   -- s2-143 : le savoir-faire');
    end if;
    -- 2. les paliers : bâtisseurs gravés, et ce qu'il faut pour l'écran
    if f = 'chantiers_etat_json' then
      def := replace(def, $x$'mecene_tp', coalesce((g->>'mecene_tp')::int, 20), 'graves', v_graves),$x$,
        $x$'mecene_tp', coalesce((g->>'mecene_tp')::int, 20), 'graves', v_graves,
       'batisseur', coalesce((g->>'batisseur')::numeric, 1000), 'ouverture_h', coalesce((g->>'ouverture_h')::int, 12),
       'savoir_pct', coalesce((g->>'savoir_pct')::numeric, 0.02), 'savoir_max', coalesce((g->>'savoir_max')::numeric, 0.40)),   -- s2-143$x$);
      def := replace(def, $x$'equipe', jsonb_build_object('ouvriers', e.ouvriers, 'outils', e.outils, 'rythme', round(v_r, 4),$x$,
        $x$'equipe', jsonb_build_object('ouvriers', e.ouvriers, 'outils', e.outils, 'rythme', round(v_r, 4),
       'savoir', round(chantiers_savoir(p_uid), 4), 'restaures', (select count(*) from chantiers_restaurations r where r.joueur_id = p_uid),   -- s2-143$x$);
      def := replace(def, $x$'mecenes', (select count(*) from c where h >= v_mecene),$x$,
        $x$'mecenes', (select count(*) from c where h >= v_mecene),
             'batisseurs', (select count(*) from c where h >= coalesce((g->>'batisseur')::numeric, 1000)),   -- s2-143$x$);
      def := replace(def, $x$from chantiers_mecenes c left join joueurs j on j.id = c.joueur_id
                                                  where c.merveille = mv.commune_code and c.heures > 0
                                                  order by c.heures desc, c.joueur_id limit v_graves) z), '[]'::jsonb)$x$,
        $x$from chantiers_mecenes c left join joueurs j on j.id = c.joueur_id
                                                  where c.merveille = mv.commune_code and c.heures > 0
                                                    -- s2-143 : les bâtisseurs ; avant les paliers, les 10 premiers
                                                    and (c.heures >= coalesce((g->>'batisseur')::numeric, 1000)
                                                         or (mv.finie_le < coalesce((g->>'paliers_depuis')::timestamptz, 'infinity')
                                                             and (select count(*) from chantiers_mecenes c2 where c2.merveille = mv.commune_code
                                                                    and (c2.heures > c.heures or (c2.heures = c.heures and c2.joueur_id < c.joueur_id))) < v_graves))
                                                  order by c.heures desc, c.joueur_id) z), '[]'::jsonb)$x$);
      if position('s2-143 : les bâtisseurs' in def) = 0 or position('''batisseurs''' in def) = 0 or position('''savoir''' in def) = 0 then
        raise exception 's2-143 : chantiers_etat_json pas entièrement modifiée';
      end if;
    end if;
    execute def;
  end loop;
end $d$;

-- la cloche : une merveille vient d'ouvrir et mon équipe n'y est pas encore
create or replace function public.merveille_ouverture()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select case when auth.uid() is null or not chantiers_permis(auth.uid()) then null else (
    select jsonb_build_object('code', m.commune_code, 'nom', coalesce(mo.nom, co.nom), 'ouverte_le', m.ouverte_le,
             'fin_fenetre', m.ouverte_le + make_interval(hours => coalesce((chantiers_reglages() ->> 'ouverture_h')::int, 12)),
             'envoye', exists (select 1 from chantiers_mecenes c where c.merveille = m.commune_code and c.joueur_id = auth.uid()))
      from chantiers_merveilles m
      left join monuments mo on mo.commune_code = m.commune_code
      left join communes co on co.code = m.commune_code
     where m.finie_le is null
       and now() < m.ouverte_le + make_interval(hours => coalesce((chantiers_reglages() ->> 'ouverture_h')::int, 12))
     limit 1) end;
$f$;

revoke all on function public.chantiers_savoir(uuid), public.chantiers_rythme_j(uuid, integer, integer), public.merveille_ouverture() from public, anon, authenticated;
grant execute on function public.merveille_ouverture() to authenticated;

-- le savoir-faire s'applique tout de suite (les compteurs ont été arrêtés plus haut)
do $r$
declare u uuid;
begin
  for u in select distinct joueur_id from (select joueur_id from chantiers where not en_pause
                                           union select joueur_id from chantiers_mecenes where actif) x loop
    perform chantiers_rythme_appliquer(u);
  end loop;
end $r$;
notify pgrst, 'reload schema';
