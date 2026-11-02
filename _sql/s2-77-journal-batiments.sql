-- ===========================================================================
--  TerraFront — s2-77 : les bâtiments dans le journal (2/11/2026)
--  Décidé avec Nataël le 2/11 (aperçu « Les bâtiments dans le journal » :
--  « parfait »). Va avec patch310.
--
--  - Construction d'une Fonderie ou d'une Forteresse → ligne 'fonderie' ou
--    'forteresse' (acteur = le constructeur).
--  - Fonderie détruite parce que sa commune change de main → ligne
--    'fonderie_detruite' (acteur = le nouveau propriétaire, cible = l'ancien).
--  - Construction annulée (s2-73) → sa ligne est retirée du journal.
--  - Jamais le Centre de recherche (secret). Rien pour une Forteresse
--    détruite par une bombe (les bombes ont leurs alertes).
--
--  Le journal ne peut JAMAIS bloquer une construction, une annulation ou une
--  conquête : en cas d'erreur, rien n'est noté et le reste se fait.
--  Rejouable. Contrôle en une ligne.
-- ===========================================================================
begin;

create or replace function public.batiments_journal()
 returns trigger language plpgsql security definer set search_path to 'public' as $f$
declare
  v_tier text;
  v_proprio uuid;
begin
  if tg_op = 'INSERT' then
    if new.type in ('fonderie', 'forteresse') then
      select c.tier into v_tier from communes c where c.code = new.commune_code;
      perform noter_journal(new.type, new.joueur_id, null, new.commune_code, v_tier);
    end if;
    return null;
  end if;

  -- DELETE
  select p.joueur_id into v_proprio from possessions p where p.commune_code = old.commune_code;
  if old.type = 'fonderie' and v_proprio is not null and v_proprio <> old.joueur_id then
    -- la commune vient de changer de main : la Fonderie est détruite
    select c.tier into v_tier from communes c where c.code = old.commune_code;
    perform noter_journal('fonderie_detruite', v_proprio, old.joueur_id, old.commune_code, v_tier);
  elsif old.type in ('fonderie', 'forteresse') and v_proprio = old.joueur_id and old.pret_le > now() then
    -- construction annulée pendant ses 6 h : on retire sa ligne
    delete from journal j
     where j.type = old.type and j.acteur = old.joueur_id and j.commune_code = old.commune_code
       and j.cree_le >= old.cree_le - interval '1 minute';
  end if;
  return null;
exception when others then
  raise warning 'batiments_journal : %', sqlerrm;
  return null;
end; $f$;
revoke all on function public.batiments_journal() from public, anon, authenticated;

drop trigger if exists trg_batiments_journal on public.batiments;
create trigger trg_batiments_journal after insert or delete on public.batiments
  for each row execute function public.batiments_journal();

commit;

-- Contrôle : true | (contraintes sur journal.type : doit être vide) | (bâtiments en cours)
select exists (select 1 from pg_trigger where tgname = 'trg_batiments_journal' and not tgisinternal) as declencheur_ok,
       coalesce((select string_agg(pg_get_constraintdef(c.oid), ' ; ') from pg_constraint c
                  where c.conrelid = 'public.journal'::regclass and c.contype = 'c'
                    and pg_get_constraintdef(c.oid) ilike '%type%'), '')          as contrainte_type,
       (select count(*) from public.batiments where pret_le > now())               as chantiers_en_cours;
