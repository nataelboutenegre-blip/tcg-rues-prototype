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
