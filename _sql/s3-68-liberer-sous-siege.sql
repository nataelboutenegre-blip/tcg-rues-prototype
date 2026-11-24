-- s3-68 (24/11/2026, signalé par H34VEN) : on ne peut plus libérer, vendre au jeu ni mettre sous contrat
-- une commune assiégée au Front. commune_assiegee() ne regardait que l'ancienne table « sieges » (S2) :
-- en S3, libérer une commune en plein siège rendait de l'énergie au défenseur et faisait perdre la mise
-- de l'attaquant (6 cas du 22 au 24/11). Appelée par front_liberer, vendre_au_jeu, signer_contrat, contrat_candidates.
create or replace function public.commune_assiegee(p_code text)
 returns boolean language sql stable security definer set search_path to 'public'
as $function$
  select exists (select 1 from sieges s
                  where s.commune_code = p_code
                    and coalesce(s.victoires_consecutives, 0) > 0
                    and s.dernier_round > now() - interval '24 hours')
      or exists (select 1 from front_sieges f where f.commune_code = p_code and f.fini_le is null)   -- s3-68
$function$;
