-- s3-40 : à la clôture, les joueurs absents depuis 14 jours ou plus ne gardent aucune commune ★ (ok de Nataël, 21/11 16 h 22).
-- Sans ce réglage, la clôture complète les 5 ★ de tout le monde, absents compris.
-- Mesure de l'absence : jours_joues (un jour noté par jour de connexion, depuis le 23/10).
-- Réglage : config_jeu 'cloture' -> {"inactif_jours": 14} ; supprimer la ligne = comportement d'avant.
-- Leur collection Terra, leurs TP et leurs achats ne bougent pas. S'ils reviennent, ils repartent comme un nouveau joueur.
-- Rejouable. Contrôle : 14 · true · true · true

insert into public.config_jeu (cle, valeur) values ('cloture', '{"inactif_jours": 14}')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.cloture_inactif(p_joueur uuid) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select (c.valeur::jsonb ->> 'inactif_jours')::int from config_jeu c where c.cle = 'cloture'), 0) > 0
     and not exists (select 1 from jours_joues j
                      where j.joueur_id = p_joueur
                        and j.jour > (now() at time zone 'Europe/Paris')::date
                                     - (select (c.valeur::jsonb ->> 'inactif_jours')::int from config_jeu c where c.cle = 'cloture'));
$$;
revoke all on function public.cloture_inactif(uuid) from public, anon, authenticated;

do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.cloturer_saison(text,text,text,boolean,integer,text[],numeric)'::regprocedure);
  if position('s3-40' in d) > 0 then return; end if;
  n := d;
  -- les comptes de la simulation
  n := replace(n, E'    select joueur_id\n      from possessions\n     group by joueur_id\n    having count(*) filter (where gardee) < least(5, count(*))',
                  E'    select joueur_id\n      from possessions\n     where not cloture_inactif(joueur_id)   -- s3-40\n     group by joueur_id\n    having count(*) filter (where gardee) < least(5, count(*))');
  n := replace(n, E'select count(*) as n from possessions group by joueur_id',
                  E'select count(*) as n from possessions where not cloture_inactif(joueur_id) group by joueur_id');
  n := replace(n, E'      union all select ''joueurs a completer d''''office'', v_sans_favori::text',
                  E'      union all select ''absents sans aucune commune (s3-40)'', (select count(distinct joueur_id) || '' joueurs, '' || count(*) || '' communes'' from possessions where cloture_inactif(joueur_id))\n      union all select ''joueurs a completer d''''office'', v_sans_favori::text');
  -- l'écriture : les absents perdent leurs ★, et la complétion les ignore
  n := replace(n, E'  -- --- c) completer les favoris a 5 --------------------------------------\n',
                  E'  -- --- c) completer les favoris a 5 --------------------------------------\n  update possessions set gardee = false where gardee and cloture_inactif(joueur_id);   -- s3-40\n');
  n := replace(n, E'      from possessions p\n     group by p.joueur_id\n    having count(*) filter (where p.gardee) < 5',
                  E'      from possessions p\n     where not cloture_inactif(p.joueur_id)   -- s3-40\n     group by p.joueur_id\n    having count(*) filter (where p.gardee) < 5');
  if (length(n) - length(replace(n, 'cloture_inactif', ''))) / length('cloture_inactif') <> 5 then
    raise exception 's3-40 : cloturer_saison a changé (% remplacements sur 5), rien n''est fait',
      (length(n) - length(replace(n, 'cloture_inactif', ''))) / length('cloture_inactif');
  end if;
  execute n;
end $$;

select (select (valeur::jsonb ->> 'inactif_jours') from public.config_jeu where cle = 'cloture') jours,
       to_regprocedure('public.cloture_inactif(uuid)') is not null fonction,
       position('s3-40' in pg_get_functiondef('public.cloturer_saison(text,text,text,boolean,integer,text[],numeric)'::regprocedure)) > 0 cloture,
       position('s3-15' in pg_get_functiondef('public.cloturer_saison(text,text,text,boolean,integer,text[],numeric)'::regprocedure)) > 0 s3_15_garde;
