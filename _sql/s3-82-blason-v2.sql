-- s3-82 (Arkhannou, ASMFCB, H34VEN) : le blason de clan, version 2 (avec patch543).
--  - 8 partitions et 24 meubles de plus ;
--  - ornements : manteau (+ couleur), timbre (murale, heaume ; comtale = 1 semaine d'or, royale = 2), devise (nom ou sigle du clan, + couleur) ;
--  - calques : jusqu'à 8 meubles placés librement (m, c, x 0..100, y 0..120, s 25..220 %, r 0..355 par 5, f retourné).
-- Tout champ nouveau est facultatif : un blason v1 reste valide et ressort avec les valeurs par défaut.

create or replace function public.blason_propre(b jsonb) returns jsonb
language plpgsql immutable set search_path to 'public' as $$
declare
  emaux text[] := array['or','argent','gueules','azur','sinople','sable','pourpre','orange','ciel','rose','turquoise','brun'];
  parts text[] := array['plein','parti','coupe','tranche','taille','ecartele','chef','fasce','pal','bande','chevron','croix','sautoir',
                        'echiquete','fusele','gironne','tierce_pal','tierce_fasce','tierce_bande','pairle',
                        'fasce3','pale3','bande3','franc','chape','chausse','vetu','emanche'];
  meubles text[] := array['aucun','lys','etoile','croissant','tour','couronne','epee','cle','ancre','arbre','coeur','coquille','hermine','aigle','soleil','epis','chateau','trefle','cloche','epees','rose','aigle2','couronne2',
                          'etoile8','quadrilobe','eclair','flamme','feuille','gemme','fleche','engrenage','lion','lionrampant','griffon','dragon','sanglier','ours','loup','cerf','dauphin','coq','cygne','corbeau','licorne','salamandre','abeille','pegase'];
  cq jsonb := '[]'::jsonb; c jsonb; x numeric; y numeric; s numeric; r numeric;
begin
  if b is null or jsonb_typeof(b) <> 'object' then return null; end if;
  if not ((b->>'forme') = any(array['francais','ancien','banniere','rond'])
     and (b->>'partition') = any(parts)
     and (b->>'c1') = any(emaux) and (b->>'c2') = any(emaux) and coalesce(b->>'c3', 'gueules') = any(emaux) and (b->>'cm') = any(emaux)
     and (b->>'meuble') = any(meubles)
     and (b->>'nombre') in ('1', '3')
     and (b->>'bordure') = any(emaux || 'aucune'::text)
     and coalesce(b->>'manteau', 'aucun') in ('aucun', 'manteau')
     and coalesce(b->>'cmanteau', 'gueules') = any(emaux)
     and coalesce(b->>'timbre', 'aucun') in ('aucun', 'murale', 'heaume', 'comtale', 'royale')
     and coalesce(b->>'devise', 'aucune') in ('aucune', 'nom', 'sigle')
     and coalesce(b->>'cdevise', 'argent') = any(emaux)) then
    return null;
  end if;
  if b ? 'calques' and b->'calques' <> 'null'::jsonb then
    if jsonb_typeof(b->'calques') <> 'array' or jsonb_array_length(b->'calques') > 8 then return null; end if;
    for c in select v from jsonb_array_elements(b->'calques') v loop
      if jsonb_typeof(c) <> 'object' or not ((c->>'m') = any(meubles)) or (c->>'m') = 'aucun' or not ((c->>'c') = any(emaux))
         or jsonb_typeof(c->'x') <> 'number' or jsonb_typeof(c->'y') <> 'number' or jsonb_typeof(c->'s') <> 'number'
         or coalesce(jsonb_typeof(c->'r'), 'number') <> 'number' or coalesce(jsonb_typeof(c->'f'), 'boolean') <> 'boolean' then
        return null;
      end if;
      x := (c->>'x')::numeric; y := (c->>'y')::numeric; s := (c->>'s')::numeric; r := coalesce((c->>'r')::numeric, 0);
      if x < 0 or x > 100 or y < 0 or y > 120 or s < 25 or s > 220 or r < 0 or r > 355 then return null; end if;
      cq := cq || jsonb_build_array(jsonb_build_object('m', c->>'m', 'c', c->>'c', 'x', round(x)::int, 'y', round(y)::int, 's', round(s)::int,
                                                       'r', (round(r / 5) * 5)::int, 'f', coalesce((c->>'f')::boolean, false)));
    end loop;
  end if;
  return jsonb_build_object('forme', b->>'forme', 'partition', b->>'partition', 'c1', b->>'c1', 'c2', b->>'c2', 'c3', coalesce(b->>'c3', 'gueules'),
                            'meuble', b->>'meuble', 'cm', b->>'cm', 'nombre', (b->>'nombre')::int, 'bordure', b->>'bordure',
                            'manteau', coalesce(b->>'manteau', 'aucun'), 'cmanteau', coalesce(b->>'cmanteau', 'gueules'),
                            'timbre', coalesce(b->>'timbre', 'aucun'), 'devise', coalesce(b->>'devise', 'aucune'),
                            'cdevise', coalesce(b->>'cdevise', 'argent'), 'calques', cq);
end; $$;

do $do$
declare d text; avant text;
begin
  d := pg_get_functiondef('clan_modifier(text,text,text,jsonb)'::regprocedure); avant := d;
  d := replace(d, $a$      raise exception 'Ce meuble se gagne avec l''or de l''objectif de clan de la semaine';
    end if;$a$, $b$      raise exception 'Ce meuble se gagne avec l''or de l''objectif de clan de la semaine';
    end if;
    -- s3-82 : couronnes comtale (1 semaine d'or) et royale (2), meubles rares dans les calques
    if (case v_blason->>'timbre' when 'comtale' then 1 when 'royale' then 2 else 0 end) > clan_meubles_rares_n(v_clan.id)
       and (v_blason->>'timbre') is distinct from (v_clan.blason->>'timbre') then
      raise exception 'Cette couronne se gagne avec l''or de l''objectif de clan de la semaine';
    end if;
    if exists (select 1 from jsonb_array_elements(v_blason->'calques') q
                where array_position(array['rose','aigle2','couronne2'], q->>'m') > clan_meubles_rares_n(v_clan.id)
                  and (q->>'m') is distinct from (v_clan.blason->>'meuble')
                  and not exists (select 1 from jsonb_array_elements(case when jsonb_typeof(v_clan.blason->'calques') = 'array'
                                                                          then v_clan.blason->'calques' else '[]'::jsonb end) q2
                                   where q2->>'m' = q->>'m')) then
      raise exception 'Ce meuble se gagne avec l''or de l''objectif de clan de la semaine';
    end if;$b$);
  if d = avant then raise exception 's3-82 : clan_modifier non modifiée'; end if;
  execute d;
end $do$;
