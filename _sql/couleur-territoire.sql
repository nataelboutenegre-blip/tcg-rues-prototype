-- ===========================================================================
--  TerraFront — choisir la couleur de son territoire (25 octobre 2026)
--  Aperçu validé (« parfait comme ça ») : 24 couleurs, gratuit, se change
--  quand on veut. Sans choix (couleur vide), le jeu garde la couleur
--  attribuée automatiquement. Le doré n'est pas dans la liste.
--  Rejouable. Tout dans une transaction. Finit par un contrôle :
--  une ligne, attendu true / true / true / 24.
-- ===========================================================================
begin;

create or replace function public.palette_territoire()
 returns text[] language sql immutable as $f$
  select array['#E5484D','#8E7CF6','#2EC4B6','#F76B15','#E93D82','#3DD68C','#5EB1EF','#FF977D',
               '#9EB1FF','#12A594','#D6409F','#C2A383','#B42318','#6E56CF','#0090A8','#A4D63A',
               '#F2E8D5','#7A4B2A','#00C2FF','#C77DFF','#8A9A5B','#FF5C8A','#4C6EF5','#B07A54']::text[]
$f$;

alter table public.joueurs add column if not exists couleur text;
do $$ begin
  alter table public.joueurs add constraint joueurs_couleur_ok
    check (couleur is null or couleur = any (public.palette_territoire()));
exception when duplicate_object then null; end $$;

-- choisir (ou revenir à l'automatique avec null)
create or replace function public.choisir_couleur(p_couleur text)
 returns text language plpgsql security definer set search_path to 'public' as $f$
declare v text := nullif(upper(trim(coalesce(p_couleur, ''))), '');
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if v is not null and not (v = any (palette_territoire())) then
    raise exception 'Couleur inconnue';
  end if;
  update joueurs set couleur = v where id = auth.uid();
  return v;
end; $f$;

-- les couleurs choisies (une cinquantaine de lignes au plus aujourd'hui)
create or replace function public.couleurs_territoire()
 returns table(joueur_id uuid, couleur text) language sql stable security definer
 set search_path to 'public' as $f$
  select j.id, j.couleur from joueurs j where j.couleur is not null
$f$;

revoke all on function public.choisir_couleur(text)   from public, anon;
revoke all on function public.couleurs_territoire()   from public, anon;
grant execute on function public.choisir_couleur(text) to authenticated;
grant execute on function public.couleurs_territoire() to authenticated;

commit;

select exists (select 1 from information_schema.columns
                where table_schema = 'public' and table_name = 'joueurs' and column_name = 'couleur') as colonne_ok,
       to_regprocedure('public.choisir_couleur(text)') is not null  as choisir_ok,
       to_regprocedure('public.couleurs_territoire()') is not null  as lire_ok,
       array_length(public.palette_territoire(), 1)                  as couleurs;
