-- s3-55 (22/11/2026, décision de Nataël 22 h 08) : le centre de notifications passe à la saison 3.
-- 1. Deux réglages « Téléphone » de plus : « Mes sièges » (tel.defense : on t'a défendu, il manque de l'énergie)
--    et « Clan » (tel.clan : ordres du chef, appels à l'aide, flambeau). Ces notifications partaient déjà
--    sur le téléphone sans qu'on puisse les couper. Par défaut : allumées (rien ne change pour personne).
-- 2. « Avant toi » (la course à la commune) lit aussi les sièges de la saison 3 (front_sieges, prise_par_autre),
--    avec la jauge en % au lieu des « x / 3 » de la saison 2 (colonne pct).
-- Retour arrière : rien à défaire côté joueurs (les clés en plus sont ignorées par l'ancien jeu).

create or replace function public.notif_defaut() returns jsonb
language sql immutable set search_path to 'public' as $$
  select '{"jeu": {"attaque": true, "perdue": true, "defense": true, "echange": true, "alerte": true,
                   "quete": true, "recolte": true, "clan": true, "paquet": false},
           "tel": {"attaque": true, "paquet": true, "defense": true, "clan": true},
           "seuil": "commun",
           "sourdine": []}'::jsonb;
$$;

create or replace function public.regler_notif(p_canal text, p_type text, p_actif boolean)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_actif is null
     or not ((p_canal = 'jeu' and p_type in ('attaque','perdue','defense','echange','alerte','quete','recolte','clan','paquet'))
          or (p_canal = 'tel' and p_type in ('attaque','paquet','defense','clan'))) then   -- s3-55 : defense, clan
    raise exception 'Réglage inconnu';
  end if;
  insert into notif_preferences(joueur_id) values (v_uid) on conflict do nothing;
  update notif_preferences
     set prefs = jsonb_set(prefs, array[p_canal], coalesce(prefs -> p_canal, '{}'::jsonb) || jsonb_build_object(p_type, p_actif)),
         maj = now()
   where joueur_id = v_uid;
  return notif_prefs_de(v_uid);
end;
$$;

create or replace function public.notif_coupee(p_joueur uuid, p_tag text)
returns boolean language plpgsql stable security definer set search_path to 'public' as $$
declare v_p jsonb; v_code text; v_tier text; v_dep text;
  v_ordre text[] := array['commun','peucommun','rare','epique','legendaire'];
begin
  if not exists (select 1 from notif_preferences np where np.joueur_id = p_joueur) then return false; end if;
  v_p := notif_prefs_de(p_joueur);
  if p_tag = 'paquet' then return not coalesce((v_p #>> '{tel,paquet}')::boolean, true); end if;
  -- s3-55 : mes sièges (côté attaquant) et le clan
  if p_tag like 'defendu-%' or p_tag like 'manque-%' then return not coalesce((v_p #>> '{tel,defense}')::boolean, true); end if;
  if p_tag like 'ordre-%' or p_tag like 'aide-%' or p_tag like 'flambeau-%' then return not coalesce((v_p #>> '{tel,clan}')::boolean, true); end if;
  if p_tag like 'danger-%' then
    if not coalesce((v_p #>> '{tel,attaque}')::boolean, true) then return true; end if;
    v_code := substr(p_tag, 8);
    if (v_p -> 'sourdine') ? v_code then return true; end if;
    select c.tier, c.departement into v_tier, v_dep from communes c where c.code = v_code;
    if (v_p -> 'sourdine_dep') ? v_dep then return true; end if;
    if (v_p -> 'alerte_dep') ? v_dep then return false; end if;   -- s2-39 : le seuil ne s'applique pas
    if v_tier is not null and array_position(v_ordre, v_tier) < array_position(v_ordre, coalesce(v_p ->> 'seuil', 'commun')) then
      return true;
    end if;
  end if;
  return false;
end;
$$;

drop function if exists public.mes_sieges_effaces();
create function public.mes_sieges_effaces()
returns table(commune_code text, commune_nom text, par_pseudo text, victoires integer, le timestamptz, pct integer)
language sql stable security definer set search_path to 'public' as $$
  select * from (
    select e.commune_code, c.nom::text, j.pseudo::text, e.victoires, e.le, null::integer
      from sieges_effaces e
      left join communes c on c.code = e.commune_code
      left join joueurs j on j.id = e.par
     where auth.uid() is not null and e.attaquant_id = auth.uid()
       and e.le > now() - interval '7 days'
    union all
    -- s3-55 : la saison 3, un autre a pris la commune pendant mon siège
    select s.commune_code, c.nom::text,
           (select jj.pseudo::text from front_sieges g join joueurs jj on jj.id = g.attaquant
             where g.commune_code = s.commune_code and g.resultat = 'conquise' and g.id <> s.id
               and g.fini_le between s.fini_le - interval '2 minutes' and s.fini_le + interval '2 minutes'
             order by abs(extract(epoch from g.fini_le - s.fini_le)) limit 1),
           0, s.fini_le,
           least(100, round(100 * s.degats / greatest(1, siege_resistance(s.commune_code, s.attaquant))))::integer
      from front_sieges s
      left join communes c on c.code = s.commune_code
     where auth.uid() is not null and s.attaquant = auth.uid()
       and s.resultat = 'prise_par_autre' and s.fini_le > now() - interval '7 days'
  ) x order by 5 desc limit 30;
$$;
revoke all on function public.mes_sieges_effaces() from public, anon;
grant execute on function public.mes_sieges_effaces() to authenticated;
