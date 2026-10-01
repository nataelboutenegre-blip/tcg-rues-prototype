-- ===========================================================================
--  TerraFront — Le journal rend aussi le code de la commune
--
--  POURQUOI
--    Le journal dit « Maroli a conquis Millau sur toi ». Avec les monuments,
--    il devrait dire que le viaduc a changé de mains dans la foulée — c'est
--    la ligne qui donne envie d'aller le reprendre.
--
--    Le navigateur connaît déjà la liste des monuments, mais elle est rangée
--    par code INSEE, et le journal ne renvoie que le NOM de la commune.
--    Rapprocher les deux par le nom serait faux : il y a seize Saint-Martin,
--    et on attribuerait le viaduc au mauvais village.
--
--  CE QUE CHANGE CE FICHIER
--    Une colonne de plus dans ce que renvoie la fonction : commune_code.
--    Rien d'autre. Mêmes filtres, même tri, mêmes droits.
--
--    PostgreSQL refuse de changer les colonnes renvoyées par une fonction
--    avec « create or replace » : il faut la supprimer puis la recréer. Le
--    drop emporte les droits, donc on les repose juste après, dans la même
--    transaction — à aucun moment la fonction n'existe sans ses droits.
--
--  SI TU NE LE PASSES PAS
--    Le jeu continue exactement comme avant : le navigateur ne trouve pas la
--    colonne, n'affiche pas le nom du monument sur les lignes du journal, et
--    tout le reste est inchangé.
-- ===========================================================================

begin;

drop function if exists public.journal(text, text, text, timestamptz, bigint, integer);

create function public.journal(
  p_mode      text        default 'tous',
  p_type      text        default null,
  p_recherche text        default null,
  p_avant     timestamptz default null,
  p_avant_id  bigint      default null,
  p_limite    integer     default 30)
returns table(id bigint, type text, commune_nom text, commune_code text, tier text,
              cree_le timestamptz, acteur_pseudo text, cible_pseudo text,
              je_suis_acteur boolean, je_suis_cible boolean)
language sql
stable
security definer
set search_path to 'public', 'extensions'
as $function$
  with motif as (
    -- moins de deux caracteres : on considere qu'il n'y a pas de recherche,
    -- sinon la premiere lettre tapee balaie la table pour rien
    select case when length(btrim(coalesce(p_recherche, ''))) >= 2
                then unaccent(lower(btrim(p_recherche)))
           end as m
  )
  select e.id, e.type::text, e.commune_nom::text, e.commune_code::text,
         e.tier::text, e.cree_le,
         coalesce(ja.pseudo, 'Un joueur')::text,
         jc.pseudo::text,
         (e.acteur = auth.uid()) as je_suis_acteur,
         (e.cible  = auth.uid()) as je_suis_cible
    from journal e
    cross join motif
    left join joueurs ja on ja.id = e.acteur
    left join joueurs jc on jc.id = e.cible
   where auth.uid() is not null
     and (p_mode <> 'moi' or e.acteur = auth.uid() or e.cible = auth.uid())
     and (p_type is null or e.type = p_type)
     and (p_avant is null or p_avant_id is null
          or (e.cree_le, e.id) < (p_avant, p_avant_id))
     and (motif.m is null
          or position(motif.m in unaccent(lower(coalesce(e.commune_nom, '')))) > 0
          or position(motif.m in unaccent(lower(coalesce(ja.pseudo, '')))) > 0
          or position(motif.m in unaccent(lower(coalesce(jc.pseudo, '')))) > 0
          or position(motif.m in lower(coalesce(e.commune_code, ''))) > 0)
   order by e.cree_le desc, e.id desc
   limit least(greatest(p_limite, 1), 100);
$function$;

-- Le drop a emporté les droits : on les repose, et plus serrés que le défaut
-- de PostgreSQL, qui accorde execute à PUBLIC.
revoke all on function
  public.journal(text, text, text, timestamptz, bigint, integer)
  from public, anon;
grant execute on function
  public.journal(text, text, text, timestamptz, bigint, integer)
  to authenticated;

commit;


-- ---------------------------------------------------------------------------
--  Contrôle
-- ---------------------------------------------------------------------------
select 'A. colonnes renvoyées' as controle,
       string_agg(a.attname, ', ' order by a.attnum) as valeur
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  join unnest(p.proallargtypes, p.proargmodes, p.proargnames)
       with ordinality as a(typ, mode, attname, attnum) on true
 where n.nspname = 'public' and p.proname = 'journal' and a.mode = 't'
union all
select 'B. droits',
       array_to_string(p.proacl, ' ')
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'journal'
union all
select 'C. le journal répond',
       (select count(*)::text || ' ligne(s) lisibles dans la table'
          from journal where cree_le > now() - interval '30 days')
order by 1;
