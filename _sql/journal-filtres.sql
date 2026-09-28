-- ---------------------------------------------------------------------------
--  journal-filtres.sql — le journal se filtre et se cherche en base
--
--  Jusqu'ici journal(p_mode, p_limite) renvoyait les 30 dernieres lignes,
--  sans autre tri que la date. Filtrer par type ou chercher un pseudo dans
--  le navigateur n'aurait filtre que ces 30 lignes : chercher « Abolah »
--  n'aurait rien trouve s'il n'avait rien fait dans les 30 dernieres
--  actions. Le filtre doit donc etre la ou sont les donnees.
--
--  Quatre parametres nouveaux, tous avec une valeur par defaut :
--
--    p_type       null = tous les types, sinon conquete/defense/achat/
--                 tirage/echange
--    p_recherche  texte libre, compare sans accents ni casse au nom de la
--                 commune, au code INSEE, et aux pseudos des deux joueurs
--    p_avant      \ curseur : « la ligne suivant celle-ci »
--    p_avant_id   /
--
--  Pourquoi un curseur et pas un offset : l'ordre est (cree_le desc,
--  id desc), et une action qui arrive pendant qu'un joueur lit decalerait
--  toute la suite d'un cran. Avec un offset il sauterait une ligne. Le
--  couple (date, id) ne bouge pas.
--
--  Pourquoi le couple et pas la date seule : l'echange du 27/09 a ecrit
--  deux lignes a 12:15:13.007902, a la microseconde pres. Un curseur sur
--  la date seule aurait perdu la seconde ou l'aurait repetee.
--
--  Pourquoi position() et pas like : si un joueur tape « % », le motif
--  '%' || q || '%' matche toute la table. position() n'a aucun joker.
--
--  Pourquoi drop puis create : create or replace ne sait pas changer une
--  signature. Les nouveaux parametres ayant tous une valeur par defaut,
--  l'app en production, qui appelle journal(p_mode, p_limite), continue de
--  fonctionner entre ce script et le deploiement du nouveau app.js.
--
--  Pourquoi search_path = public, extensions : unaccent vit dans le schema
--  extensions chez Supabase. Le chemin reste fige, comme il doit l'etre
--  pour une fonction SECURITY DEFINER, mais il inclut ce qu'elle utilise.
--  Si unaccent etait introuvable, le create echouerait ici meme, pas en
--  production : PostgreSQL valide le corps d'une fonction SQL a sa
--  creation.
--
--  Aucun index ajoute. 1 454 lignes, et journal_date (cree_le DESC) sert
--  deja le tri. A revoir si la table passe la centaine de milliers.
-- ---------------------------------------------------------------------------

begin;

drop function if exists public.journal(text, integer);

create function public.journal(
  p_mode      text        default 'tous',
  p_type      text        default null,
  p_recherche text        default null,
  p_avant     timestamptz default null,
  p_avant_id  bigint      default null,
  p_limite    integer     default 30)
returns table(id bigint, type text, commune_nom text, tier text,
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
  select e.id, e.type::text, e.commune_nom::text, e.tier::text, e.cree_le,
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

-- Le drop a emporte les droits : on les repose, et plus serres que le
-- defaut de PostgreSQL, qui accorde execute a PUBLIC.
revoke all on function
  public.journal(text, text, text, timestamptz, bigint, integer)
  from public, anon;
grant execute on function
  public.journal(text, text, text, timestamptz, bigint, integer)
  to authenticated;

commit;


-- ---------------------------------------------------------------------------
--  Verification — on se fait passer pour le joueur le plus actif, on
--  exerce chaque filtre, et on annule tout a la fin. Rien n'est ecrit.
-- ---------------------------------------------------------------------------
begin;

select set_config(
  'request.jwt.claims',
  json_build_object('sub', (select acteur from journal
                             where acteur is not null
                             group by acteur order by count(*) desc limit 1))::text,
  true);

with accentuee as (
  -- une commune reellement accentuee, prise dans le journal : on la
  -- cherchera SANS accent, ce qui ne peut marcher que si unaccent est
  -- bien resolu depuis l'interieur de la fonction
  select commune_nom,
         unaccent(lower(commune_nom)) as sans_accent
    from journal
   where commune_nom ~ '[àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]'
   order by id desc
   limit 1
),
p1 as (select * from public.journal(p_limite => 5)),
cur as (select cree_le, id from p1 order by cree_le, id limit 1)
select 'A. page 1 (5 demandees)' as controle,
       count(*)::text as resultat from p1
union all
select 'B. page 2 via le curseur',
       (select count(*)::text from public.journal(
          p_avant    => (select cree_le from cur),
          p_avant_id => (select id from cur),
          p_limite   => 5))
union all
select 'C. chevauchement des deux pages (doit etre 0)',
       (select count(*)::text
          from p1 join public.journal(
                 p_avant    => (select cree_le from cur),
                 p_avant_id => (select id from cur),
                 p_limite   => 5) p2 using (id))
union all
select 'D. p_type=conquete : que des conquetes ?',
       (select coalesce(bool_and(type = 'conquete'), true)::text
          from public.journal(p_type => 'conquete', p_limite => 50))
union all
select 'E. recherche sans accent de « '
       || coalesce((select commune_nom from accentuee), 'aucune commune accentuee')
       || ' » (doit etre > 0)',
       coalesce((select count(*)::text from public.journal(
          p_recherche => (select sans_accent from accentuee), p_limite => 50)), 'n/a')
union all
select 'F. recherche d''une seule lettre, ignoree (doit valoir 5)',
       (select count(*)::text from public.journal(p_recherche => 'a', p_limite => 5))
union all
select 'G. le motif %a% pris au pied de la lettre (doit etre 0)',
       (select count(*)::text from public.journal(p_recherche => '%a%', p_limite => 50))
union all
select 'H. ancien appel, comme le fait l''app en production',
       (select count(*)::text from public.journal(p_mode => 'tous', p_limite => 30))
order by 1;

rollback;
