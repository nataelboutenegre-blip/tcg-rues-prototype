-- Supabase expose auth.uid(). Mon PostgreSQL local ne l'a pas : on le
-- reproduit avec le meme mecanisme, la claim « sub » de request.jwt.claims,
-- pour que les fonctions du jeu tournent ici sans etre modifiees.
create schema if not exists auth;
create or replace function auth.uid() returns uuid
language sql stable as $$
  select nullif(
    coalesce(current_setting('request.jwt.claims', true)::json ->> 'sub', ''),
    '')::uuid;
$$;
-- se faire passer pour un joueur
create or replace function devenir(p_id uuid) returns void
language sql as $$
  select set_config('request.jwt.claims',
                    json_build_object('sub', p_id)::text, false)::void;
$$;

-- points_rarete() existe en base, je ne l'ai pas sous les yeux. Les valeurs
-- ci-dessous sont plausibles mais arbitraires : ce banc verifie l'ORDRE du
-- palmares, pas le bareme. En production c'est la vraie fonction qui sert.
create or replace function public.points_rarete(p_tier text) returns integer
language sql immutable as $$
  select case p_tier when 'legendaire' then 1000 when 'rare' then 100
                     when 'peucommun' then 20 else 5 end;
$$;
