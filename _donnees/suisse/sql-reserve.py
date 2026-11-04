#!/usr/bin/env python3
"""
TerraFront — saison 3 : écrit les fichiers SQL de la réserve suisse.

Lit _donnees/suisse/jeu/communes-suisse.csv (2 110 communes) et écrit
_sql/s3-4a … s3-4d-suisse-reserve.sql : les communes, rangées canton par
canton dans une table d'attente (suisse_communes_attente), invisible pour
les joueurs. Rien n'entre dans le jeu : c'est s3-5 qui les y fait entrer,
le jour J, en une seule fois.

À relancer seulement si communes-suisse.csv change (population corrigée,
nom…), depuis la racine du dépôt :
    python3 _donnees/suisse/sql-reserve.py
"""
import csv
import pathlib

RACINE = pathlib.Path(__file__).resolve().parents[2]
CSV = RACINE / '_donnees/suisse/jeu/communes-suisse.csv'
SORTIE = RACINE / '_sql'
PARTIES = 4

# ordre officiel des cantons (numéros OFS 1 à 26)
CANTONS = ['ZH', 'BE', 'LU', 'UR', 'SZ', 'OW', 'NW', 'GL', 'ZG', 'FR', 'SO', 'BS', 'BL',
           'SH', 'AR', 'AI', 'SG', 'GR', 'AG', 'TG', 'TI', 'VD', 'VS', 'NE', 'GE', 'JU']
RARETES = ['legendaire', 'epique', 'rare', 'peucommun', 'commun']
SEUILS = [(30000, 'legendaire'), (8000, 'epique'), (2300, 'rare'), (450, 'peucommun')]


def rarete(pop):
    for seuil, nom in SEUILS:
        if pop >= seuil:
            return nom
    return 'commun'


def sql_txt(s):
    return "'" + s.replace("'", "''") + "'"


lignes = list(csv.DictReader(CSV.open(encoding='utf-8')))
assert len(lignes) == 2110, len(lignes)
assert len({r['code'] for r in lignes}) == 2110
for r in lignes:
    assert r['code'].startswith('CH') and r['code'][2:].isdigit(), r['code']
    assert r['departement'] in CANTONS, r['departement']
    assert r['nom'].strip() == r['nom'] and r['nom'], r['code']
    assert r['tier'] == rarete(int(r['population'])), r['code']
    assert 45.8 < float(r['latitude']) < 47.9 and 5.9 < float(r['longitude']) < 10.6, r['code']

par_canton = {c: sorted((r for r in lignes if r['departement'] == c), key=lambda r: int(r['code'][2:]))
              for c in CANTONS}

# découpe en parties de taille voisine, sans couper un canton
groupes, cumul, cible = [[]], 0, len(lignes) / PARTIES
for c in CANTONS:
    n = len(par_canton[c])
    k = len(groupes)
    if groupes[-1] and k < PARTIES and abs(cumul + n - cible * k) > abs(cumul - cible * k):
        groupes.append([])
    groupes[-1].append(c)
    cumul += n
assert len(groupes) == PARTIES and sum(len(par_canton[c]) for g in groupes for c in g) == 2110

TABLE = """\
-- La table d'attente : invisible pour les joueurs (RLS sans règle de lecture)
create table if not exists public.suisse_communes_attente (
  code        text primary key check (code ~ '^CH[0-9]+$'),
  nom         text not null check (nom <> ''),
  departement text not null check (departement ~ '^[A-Z]{2}$'),
  population  integer not null check (population >= 0),
  latitude    numeric not null check (latitude between 45.8 and 47.9),
  longitude   numeric not null check (longitude between 5.9 and 10.6),
  tier        text not null check (tier in ('legendaire', 'epique', 'rare', 'peucommun', 'commun'))
);
alter table public.suisse_communes_attente enable row level security;
revoke all on table public.suisse_communes_attente from anon, authenticated;
"""

for i, g in enumerate(groupes):
    lettre = 'abcd'[i]
    n = sum(len(par_canton[c]) for c in g)
    detail = ', '.join(f'{c} {len(par_canton[c])}' for c in g)
    rangs = []
    for c in g:
        for r in par_canton[c]:
            rangs.append(f"  ({sql_txt(r['code'])}, {sql_txt(r['nom'])}, '{c}', {int(r['population'])}, "
                         f"{float(r['latitude'])}, {float(r['longitude'])}, '{r['tier']}')")
    cantons_sql = ', '.join(f"'{c}'" for c in g)
    texte = f"""\
-- ===========================================================================
--  TerraFront — s3-4{lettre} : la réserve suisse, partie {i + 1} sur {PARTIES}
--  {n} communes : {detail}
--
--  Range les communes dans une table d'attente (suisse_communes_attente).
--  RIEN N'ENTRE DANS LE JEU : ni tirage, ni carte, ni pot. C'est s3-5 qui les
--  fait entrer, le jour J, après la clôture de la saison 2.
--  Les 4 parties se lancent quand on veut, dans n'importe quel ordre.
--  Rejouable (une commune déjà rangée est mise à jour).
--  Fichier écrit par _donnees/suisse/sql-reserve.py (ne pas modifier à la main).
--  Contrôle attendu : {n} | (total rangé jusqu'ici, 2110 après les 4 parties)
-- ===========================================================================
begin;

{TABLE}
insert into public.suisse_communes_attente (code, nom, departement, population, latitude, longitude, tier)
values
{(',' + chr(10)).join(rangs)}
on conflict (code) do update
   set nom = excluded.nom, departement = excluded.departement, population = excluded.population,
       latitude = excluded.latitude, longitude = excluded.longitude, tier = excluded.tier;

commit;

-- Contrôle : {n} | total rangé (2110 quand les 4 parties sont passées)
select count(*) filter (where departement in ({cantons_sql}))::integer as cette_partie,
       count(*)::integer                                              as total_range
  from public.suisse_communes_attente;
"""
    (SORTIE / f's3-4{lettre}-suisse-reserve.sql').write_text(texte, encoding='utf-8')
    print(f's3-4{lettre} : {n} communes ({detail}), {len(texte.encode()) // 1024} Ko')
