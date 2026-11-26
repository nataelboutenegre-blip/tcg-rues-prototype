-- s3-84 (26/11) : tous les packs de formes du motif de territoire deviennent gratuits pour tout le monde.
-- Personne ne les avait achetés (aucune ligne 'motifs-%' dans euros_inventaire) ; les articles étaient déjà inactifs.
create or replace function public.motif_packs(p_joueur uuid)
 returns text[] language sql stable security definer set search_path to 'public'
as $function$
  -- s3-84 : tous les packs de formes sont gratuits pour tout le monde (avant : achetés via euros_inventaire 'motifs-*')
  select coalesce(array_agg(distinct m.pack), '{}') from motif_formes m where m.pack is not null;
$function$;
