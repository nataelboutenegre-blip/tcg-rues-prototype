-- s2-144 : pas de garnison dans une zone bombardée tant qu'elle est active (idée Oshannir, 13/11)
-- Réglage batiments.bombe_garnison_h (24 par défaut, 0 = coupé).

update config_jeu
   set valeur = (valeur::jsonb || '{"bombe_garnison_h": 24}'::jsonb)::text
 where cle = 'batiments' and not (valeur::jsonb ? 'bombe_garnison_h');

-- Fin du blocage pour une commune (null = pas bloquée)
create or replace function public.bombe_garnison_bloquee(p_code text)
returns timestamptz
language sql stable security definer set search_path to 'public'
as $function$
  select max(b.le + make_interval(hours => coalesce(batiment_reglage('bombe_garnison_h'), 24)::integer))
    from bombes b, communes k
   where k.code = p_code
     and coalesce(batiment_reglage('bombe_garnison_h'), 24) > 0
     and b.le > now() - make_interval(hours => coalesce(batiment_reglage('bombe_garnison_h'), 24)::integer)
     and k.latitude between b.lat - b.rayon_km / 110.0 and b.lat + b.rayon_km / 110.0
     and dist_km(k.latitude, k.longitude, b.lat, b.lon) <= b.rayon_km;
$function$;
revoke all on function public.bombe_garnison_bloquee(text) from public, anon;
grant execute on function public.bombe_garnison_bloquee(text) to authenticated, service_role;

CREATE OR REPLACE FUNCTION public.garnison_poser(p_code text, p_n integer)
 RETURNS TABLE(energie integer, garnisons integer, energie_joueur integer)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_uid uuid := auth.uid();
  v_actuelle integer;
  v_ajout integer;
  v_nb integer;
  v_bloque timestamptz;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then raise exception 'La garnison arrive avec la saison 2'; end if;
  if p_n is null or p_n < 1 then raise exception 'Nombre invalide'; end if;
  if not exists (select 1 from possessions p where p.commune_code = p_code and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  -- s2-144 : zone bombardée = pas de garnison tant qu'elle est active
  v_bloque := bombe_garnison_bloquee(p_code);
  if v_bloque is not null then
    raise exception 'Zone bombardée : pas de garnison ici avant % (%)',
      to_char(v_bloque at time zone 'Europe/Paris', 'FMHH24"h"MI'),
      case when (v_bloque at time zone 'Europe/Paris')::date > (now() at time zone 'Europe/Paris')::date then 'demain' else 'aujourd''hui' end;
  end if;
  -- une garnison laissee par un ancien proprietaire ne compte plus
  delete from front_garnisons g where g.commune_code = p_code and g.joueur_id <> v_uid;
  select g.energie into v_actuelle from front_garnisons g where g.commune_code = p_code for update;
  if v_actuelle is null then
    select count(*) into v_nb from front_garnisons g
      join possessions p on p.commune_code = g.commune_code and p.joueur_id = g.joueur_id
     where g.joueur_id = v_uid;
    if v_nb >= batiment_reglage('garnisons_max') then   -- s2-lot4 : le plafond vient du réglage
      raise exception 'Tu as déjà % garnisons : retires-en une avant', batiment_reglage('garnisons_max')::integer;
    end if;
    v_actuelle := 0;
  end if;
  v_ajout := least(p_n, 10 - v_actuelle);
  if v_ajout <= 0 then raise exception 'Cette garnison est pleine (10)'; end if;
  if not front_energie_depenser(v_uid, v_ajout) then
    raise exception 'Energie insuffisante (% requise)', v_ajout;
  end if;
  insert into front_garnisons as g (commune_code, joueur_id, energie)
  values (p_code, v_uid, v_ajout)
  on conflict (commune_code) do update set energie = g.energie + v_ajout;
  perform quete_noter(v_uid, 'garnison', 1);
  return query
    select (select g.energie from front_garnisons g where g.commune_code = p_code),
           (select count(*)::integer from front_garnisons g
              join possessions p on p.commune_code = g.commune_code and p.joueur_id = g.joueur_id
             where g.joueur_id = v_uid),
           (select floor(front_energie_lire(j.front_energie, j.front_energie_maj))::integer from joueurs j where j.id = v_uid);
end;
$function$;
