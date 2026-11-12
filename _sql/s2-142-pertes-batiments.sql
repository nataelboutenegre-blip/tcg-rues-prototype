-- s2-142 (12/11/2026) : quand on te prend une commune, le jeu dit ce que tu perds avec.
-- Question de Nataël après ASMFCB (sa capacité de 45 lingots retombée à 30 sans explication) :
-- jusqu'ici seule la Fonderie laissait une trace (journal « fonderie_detruite », sans les lingots) ;
-- Banque, Forteresse, Centre (et la bombe en préparation), pillage et plafond : rien.
--
-- 1. journal.infos (jsonb, vide pour les lignes existantes).
-- 2. batiments_changement_proprio : sur une CONQUÊTE, une ligne « pertes » (acteur = le conquérant,
--    cible = l'ancien propriétaire) avec la liste des bâtiments perdus :
--      {"b":[{"t":"fonderie","pille":12,"max_avant":45,"max_apres":30,"ecrete":3},
--            {"t":"banque","contenu":34,"pille":17},{"t":"forteresse"},{"t":"centre","bombe":true}]}
--    Le reste de la fonction est inchangé. L'écriture du journal a son propre bloc d'exception :
--    si elle échoue, la prise et le pillage se font quand même (sinon le « exception when others »
--    de la fonction annulerait tout, bâtiments compris).
-- 3. journal() : nouvelle colonne infos, donnée seulement à la cible ; les lignes « pertes »
--    ne sont visibles que par la cible (le Centre est un bâtiment caché, la Banque aussi).
--    direct_fil ne lit que conquete/defense/fonderie/forteresse : rien ne fuit sur la carte en direct.

alter table public.journal add column if not exists infos jsonb;

create or replace function public.batiments_changement_proprio()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  b record;
  v numeric;
  v_nf integer;
  v_pille integer;
  v_conquete boolean;
  v_banque numeric;
  v_max_avant numeric;
  v_max_apres numeric;
  v_bombe boolean;
  v_pertes jsonb := '[]'::jsonb;   -- s2-142
  v_ancien uuid;
begin
  if tg_op = 'UPDATE' and new.joueur_id is not distinct from old.joueur_id then return null; end if;
  v_conquete := tg_op = 'UPDATE' and new.joueur_id is not null
                and new.conquise_le is distinct from old.conquise_le and new.conquise_le is not null;
  for b in select * from batiments where commune_code = old.commune_code loop
    v_ancien := coalesce(v_ancien, b.joueur_id);
    if b.type = 'fonderie' then
      v := lingots_figer(b.joueur_id);
      v_max_avant := lingots_max(b.joueur_id);
      select count(*) into v_nf from batiments f where f.joueur_id = b.joueur_id and f.type = 'fonderie';
      delete from batiments where id = b.id;
      v_pille := 0;
      if v_conquete and v > 0 then
        v_pille := floor(least(v, lingots_max_fonderies(b.joueur_id)) * batiment_reglage('pillage') / greatest(v_nf, 1))::integer;   -- s2-104 : la Banque est à l'abri
        update joueurs set lingots = lingots - v_pille where id = b.joueur_id;
        perform lingots_figer(new.joueur_id);
        update joueurs set lingots = lingots + v_pille where id = new.joueur_id;
      end if;
      v_max_apres := lingots_max(b.joueur_id);
      update joueurs set lingots = least(lingots, lingots_max(b.joueur_id)) where id = b.joueur_id;
      v_pertes := v_pertes || jsonb_build_array(jsonb_build_object('t', 'fonderie', 'pille', v_pille,
                    'max_avant', floor(v_max_avant)::integer, 'max_apres', floor(v_max_apres)::integer,
                    'ecrete', greatest(0, floor(coalesce(v, 0) - v_pille - v_max_apres))::integer));
    elsif b.type = 'banque' then   -- s2-104, s2-110 : le contenu déposé
      v_banque := floor(coalesce(b.contenu, 0));
      delete from batiments where id = b.id;
      v_pille := 0;
      if v_banque > 0 then
        if v_conquete then
          v_pille := floor(v_banque * coalesce(batiment_reglage('banque_pillage'), 0.5))::integer;
          perform lingots_figer(new.joueur_id);
          update joueurs set lingots = lingots + v_pille where id = new.joueur_id;
        end if;
      end if;
      v_pertes := v_pertes || jsonb_build_array(jsonb_build_object('t', 'banque', 'contenu', v_banque::integer, 'pille', v_pille));
    elsif b.type = 'centre' then
      delete from batiments where id = b.id;
      select exists (select 1 from bombes_preparations p where p.joueur_id = b.joueur_id and p.etat = 'en_cours') into v_bombe;
      update bombes_preparations set etat = 'perdue', fini_le = now()
       where joueur_id = b.joueur_id and etat = 'en_cours';
      v_pertes := v_pertes || jsonb_build_array(jsonb_build_object('t', 'centre', 'bombe', v_bombe));
    else
      delete from batiments where id = b.id;
      v_pertes := v_pertes || jsonb_build_array(jsonb_build_object('t', b.type));
    end if;
  end loop;
  -- s2-142 : la ligne « pertes » du journal, pour l'ancien propriétaire
  if v_conquete and jsonb_array_length(v_pertes) > 0 and v_ancien is not null then
    begin
      insert into journal (type, acteur, cible, commune_code, commune_nom, tier, infos)
      select 'pertes', new.joueur_id, v_ancien, c.code, c.nom, c.tier, jsonb_build_object('b', v_pertes)
        from communes c where c.code = old.commune_code;
    exception when others then
      raise warning 'batiments_changement_proprio (journal pertes) : %', sqlerrm;
    end;
  end if;
  return null;
exception when others then
  raise warning 'batiments_changement_proprio : %', sqlerrm;
  return null;
end;
$function$;

-- journal() : la colonne infos en plus (le type de retour change : drop puis create)
drop function if exists public.journal(text, text, text, timestamptz, bigint, integer);
create function public.journal(p_mode text default 'tous'::text, p_type text default null::text, p_recherche text default null::text,
                               p_avant timestamptz default null::timestamptz, p_avant_id bigint default null::bigint, p_limite integer default 30)
 returns table(id bigint, type text, commune_nom text, commune_code text, tier text, cree_le timestamptz, acteur_pseudo text, cible_pseudo text,
               je_suis_acteur boolean, je_suis_cible boolean, infos jsonb)
 language sql
 stable security definer
 set search_path to 'public', 'extensions'
as $function$
  with motif as (
    select case when length(btrim(coalesce(p_recherche, ''))) >= 2
                then unaccent(lower(btrim(p_recherche)))
           end as m
  )
  select e.id, e.type::text, e.commune_nom::text, e.commune_code::text,
         e.tier::text, e.cree_le,
         coalesce(ja.pseudo, 'Un joueur')::text,
         jc.pseudo::text,
         (e.acteur = auth.uid()) as je_suis_acteur,
         (e.cible  = auth.uid()) as je_suis_cible,
         case when e.cible = auth.uid() then e.infos end
    from journal e
    cross join motif
    left join joueurs ja on ja.id = e.acteur
    left join joueurs jc on jc.id = e.cible
   where auth.uid() is not null
     and (e.type <> 'pertes' or e.cible = auth.uid())   -- s2-142 : seulement pour celui qui perd
     and (p_mode <> 'moi' or e.acteur = auth.uid() or e.cible = auth.uid())
     and (p_type is null or e.type = p_type)
     and (p_avant is null or p_avant_id is null
          or (e.cree_le, e.id) < (p_avant, p_avant_id))
     and (motif.m is null
          or position(motif.m in unaccent(lower(coalesce(e.commune_nom, '')))) > 0
          or position(motif.m in unaccent(lower(coalesce(ja.pseudo, '')))) > 0
          or position(motif.m in unaccent(lower(coalesce(jc.pseudo, '')))) > 0
          or position(motif.m in lower(coalesce(e.commune_code, ''))) > 0)
   order by e.cree_le desc, e.id desc
   limit least(greatest(p_limite, 1), 100);
$function$;
revoke all on function public.journal(text, text, text, timestamptz, bigint, integer) from public;
grant execute on function public.journal(text, text, text, timestamptz, bigint, integer) to authenticated, service_role;
revoke execute on function public.journal(text, text, text, timestamptz, bigint, integer) from anon;   -- les droits par défaut le donnent à anon
notify pgrst, 'reload schema';
