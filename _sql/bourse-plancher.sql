-- ===========================================================================
--  TerraFront — Un prix plancher sur la Bourse
--
--  CE QUI S'EST PASSÉ
--    Oshannir a mis une légendaire en vente à 1 point, son partenaire a fait
--    pareil, ils se sont achetés mutuellement. Coût : 2 points, contre
--    400 (200 chacun) par l'onglet Échange. Il te l'a dit lui-même.
--
--    Côté serveur, mettre_en_vente ne vérifiait qu'une chose : « le prix
--    doit être positif ». Un point suffisait.
--
--  CE QUE CE FICHIER FAIT
--    Il ajoute UNE condition à mettre_en_vente : le prix ne peut pas être
--    inférieur à ce que le jeu lui-même paie pour cette carte, c'est-à-dire
--    prix_rachat(tier) — 5 / 20 / 100 / 1 000.
--
--    En dessous de ce seuil, vendre sur la Bourse n'avait aucun sens pour
--    un vendeur de bonne foi : il avait toujours mieux à faire en vendant
--    au jeu. Le plancher ne retire donc aucun usage légitime.
--
--  CE QUE CE FICHIER NE FAIT PAS, ET C'EST UN CHOIX ASSUMÉ
--    Il ne referme pas le trou. Deux complices qui s'achètent mutuellement
--    à 1 000 sont toujours à zéro net. Le plancher leur impose d'avoir
--    1 000 points disponibles — une vraie friction pour un petit joueur,
--    aucune pour un gros — et il supprime au passage le seul vrai
--    dissuasif actuel : le risque de se faire rafler sa carte par un tiers
--    qui surveille la liste. À 1 000 points, personne n'a intérêt à la
--    rafler, puisque c'est son prix juste.
--
--    Ce qui refermerait le trou, c'est une ponction sur la transaction,
--    au barème de commission_echange(). Décision reportée.
--
--  LES ANNONCES EN COURS NE SONT PAS TOUCHÉES. Celles qui sont en dessous
--  du plancher restent en vente à leur prix jusqu'à ce que leur
--  propriétaire les retire ou les reprice — et un nouveau prix, lui, devra
--  respecter le plancher.
--
--  LE RESTE DE LA FONCTION EST IDENTIQUE AU MOT PRÈS. Je l'ai reprise de
--  pg_get_functiondef, pas de mémoire : search_path, SECURITY DEFINER et
--  le on conflict sont ceux qui tournent aujourd'hui en production.
-- ===========================================================================

create or replace function public.mettre_en_vente(p_commune_code text, p_prix integer)
 returns void
 language plpgsql
 security definer
 set search_path to 'public', 'extensions'
as $function$
declare
  v_joueur_id uuid := auth.uid();
  v_tier      text;
  v_plancher  integer;
begin
  if v_joueur_id is null then raise exception 'Non connecte'; end if;
  if p_prix <= 0 then raise exception 'Le prix doit etre positif'; end if;

  if not exists (select 1 from possessions where commune_code = p_commune_code and joueur_id = v_joueur_id) then
    raise exception 'Tu ne possedes pas cette commune';
  end if;

  -- Le plancher : on ne peut pas brader en dessous de ce que le jeu paie.
  select c.tier into v_tier from communes c where c.code = p_commune_code;
  if v_tier is null then raise exception 'Commune inconnue'; end if;
  v_plancher := prix_rachat(v_tier);
  if p_prix < v_plancher then
    raise exception 'Prix minimum pour cette rarete : % points. Le jeu te la rachete a ce prix.', v_plancher;
  end if;

  insert into annonces (commune_code, joueur_id, prix)
  values (p_commune_code, v_joueur_id, p_prix)
  on conflict (commune_code) do update set prix = excluded.prix, joueur_id = excluded.joueur_id, created_at = now();
end;
$function$;


-- ---------------------------------------------------------------------------
--  Contrôle — une seule requête, c'est la dernière que l'éditeur affichera.
--  Les annonces en cours, avec leur plancher, pour voir lesquelles sont en
--  dessous. Aucune n'est modifiée.
-- ---------------------------------------------------------------------------
select c.tier                                   as rarete,
       count(*)                                 as annonces,
       min(a.prix)                              as prix_le_plus_bas,
       public.prix_rachat(c.tier)               as plancher_desormais,
       count(*) filter (where a.prix < public.prix_rachat(c.tier))
                                                as sous_le_plancher
  from public.annonces a
  join public.communes c on c.code = a.commune_code
 group by c.tier
 order by public.prix_rachat(c.tier) desc;
