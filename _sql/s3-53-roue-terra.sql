-- s3-53 (22/11/2026, idée de Maroli et ASMFCB, décision de Nataël 20 h 17 : « +10 % et on check ») :
-- la roue des paquets Terra. À côté du choix du pays, « Au hasard » : même prix (un jeton ou 200 TP),
-- un pays tiré au sort selon les poids du réglage, et une fois sur 10 un paquet gratuit en plus (+1 jeton).
-- Réglage : config_jeu 'terra_roue' { ouverte, poids {FR, CH, BE, LU}, bonus_pct }. Journal : terra_roue_tours.
-- Retour arrière : update config_jeu set valeur = (valeur::jsonb || '{"ouverte":0}')::text where cle = 'terra_roue';

insert into config_jeu(cle, valeur) values ('terra_roue', '{"ouverte": 1, "poids": {"FR": 55, "CH": 25, "BE": 13, "LU": 7}, "bonus_pct": 10}')
on conflict (cle) do nothing;

create table if not exists public.terra_roue_tours (
  id bigint generated always as identity primary key,
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  pays text not null,
  paye boolean not null default false,
  bonus boolean not null default false,
  le timestamptz not null default now()
);
create index if not exists terra_roue_tours_le on public.terra_roue_tours(le);
alter table public.terra_roue_tours enable row level security;

create or replace function public.terra_roue_reglages() returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select valeur::jsonb from config_jeu where cle = 'terra_roue'), '{"ouverte": 0}'::jsonb);
$$;

create or replace function public.terra_roue(p_paye boolean default false) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare
  v_uid uuid := auth.uid(); cfg jsonb := terra_roue_reglages(); v_pays text; v_total numeric := 0; v_x numeric; r record;
  v_bonus boolean; v_cartes jsonb; j joueurs%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce((cfg->>'ouverte')::int, 0) <> 1 then raise exception 'La roue n''est pas ouverte'; end if;
  -- les pays ouverts (leurs communes sont entrées) et leur poids
  for r in select k as pays, greatest(0, (cfg->'poids'->>k)::numeric) as w from jsonb_object_keys(cfg->'poids') k
            where k = 'FR' or exists (select 1 from communes c where pays_de(c.departement) = k) loop
    v_total := v_total + r.w;
  end loop;
  if v_total <= 0 then v_pays := 'FR';
  else
    v_x := random() * v_total;
    for r in select k as pays, greatest(0, (cfg->'poids'->>k)::numeric) as w from jsonb_object_keys(cfg->'poids') k
              where k = 'FR' or exists (select 1 from communes c where pays_de(c.departement) = k) order by k loop
      v_pays := r.pays;
      exit when v_x < r.w;
      v_x := v_x - r.w;
    end loop;
  end if;
  -- le paquet, payé comme les autres (jeton ou 200 TP), avec ses brillantes
  v_cartes := terra_ouvrir_paquet_b(p_paye, v_pays);
  -- le bonus : un paquet gratuit de plus, même au-dessus de 3 jetons
  v_bonus := random() * 100 < coalesce((cfg->>'bonus_pct')::numeric, 0);
  if v_bonus then
    select * into j from joueurs where id = v_uid for update;
    update joueurs set terra_jetons = terra_jetons_lire(j.terra_jetons, j.terra_jetons_maj) + 1, terra_jetons_maj = now() where id = v_uid;
  end if;
  insert into terra_roue_tours(joueur_id, pays, paye, bonus) values (v_uid, v_pays, coalesce(p_paye, false), v_bonus);
  return jsonb_build_object('pays', v_pays, 'bonus', v_bonus, 'cartes', v_cartes);
end; $$;

revoke all on function public.terra_roue(boolean), public.terra_roue_reglages() from public, anon;
grant execute on function public.terra_roue(boolean), public.terra_roue_reglages() to authenticated;
