# patch459 : les lauriers du podium des clans (s3-29)
import sys, os
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(fichier, a, b, n=1):
    p = os.path.join(R, fichier); s = open(p, encoding='utf-8').read()
    assert s.count(a) == n, (fichier, a[:80], s.count(a)); s = s.replace(a, b); open(p, 'w', encoding='utf-8').write(s)
A = 'app.js'
rep(A, "    BLASONS = new Map((data || []).map(r => [r.tag, { blason: r.blason, libre: r.nom_libre_le ? new Date(r.nom_libre_le) : null }]));",
       "    BLASONS = new Map((data || []).map(r => [r.tag, { blason: r.blason, libre: r.nom_libre_le ? new Date(r.nom_libre_le) : null,\n      laurier: r.laurier_rang ? { rang: r.laurier_rang, saison: r.laurier_saison, masque: !!r.laurier_masque } : null }]));   // patch459")
rep(A, """  if(bl && bl.blason) return `<span class="blason blason-svg${petit ? ' petit' : ''}" title="${echapperTexte(tag)}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>`;
  return `<span class="blason${petit ? ' petit' : ''}" style="--clan:${couleur}">${echapperTexte(tag)}</span>`;""",
       """  const lr = (h) => typeof laurierAutour === 'function' ? laurierAutour(h, tag, petit) : h;   // patch459
  if(bl && bl.blason) return lr(`<span class="blason blason-svg${petit ? ' petit' : ''}" title="${echapperTexte(tag)}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>`);
  return lr(`<span class="blason${petit ? ' petit' : ''}" style="--clan:${couleur}">${echapperTexte(tag)}</span>`);""")
rep(A, """const trophesHtml = (liste, long) => (liste || []).map(t => long
  ? `<span class="rs2-trophee">🏆 Clan champion de la ${echapperTexte(nomSaison(t.saison).toLowerCase())}</span>`
  : `<span class="rs2-trophee-mini" title="Clan champion de la ${echapperTexte(nomSaison(t.saison).toLowerCase())}">🏆</span>`).join('');""",
       """const TROPHEE_ICONE = { 1: '🏆', 2: '🥈', 3: '🥉' }, TROPHEE_TXT = { 1: 'Clan champion', 2: '2e clan', 3: '3e clan' };   // patch459
const trophesHtml = (liste, long) => (liste || []).filter(t => TROPHEE_ICONE[t.rang || 1]).map(t => { const r = t.rang || 1, s = echapperTexte(nomSaison(t.saison).toLowerCase());
  return long ? `<span class="rs2-trophee r${r}">${TROPHEE_ICONE[r]} ${TROPHEE_TXT[r]} de la ${s}</span>`
              : `<span class="rs2-trophee-mini" title="${TROPHEE_TXT[r]} de la ${s}">${TROPHEE_ICONE[r]}</span>`; }).join('');""")
rep(A, """    <h2>Nom et sigle</h2>
    <div class="clan-form"><label>Nom du clan<input id="blNom\"""", """    ${typeof laurierEditionHtml === 'function' ? laurierEditionHtml(((clanCache && clanCache.moi && clanCache.moi.clan) || {}).tag) : ''}
    <h2>Nom et sigle</h2>
    <div class="clan-form"><label>Nom du clan<input id="blNom\"""")
s = open(os.path.join(R, A), encoding='utf-8').read().rstrip('\n') + '\n' + open(os.path.join(R, '_patchs', 'patch459.js'), encoding='utf-8').read()
open(os.path.join(R, A), 'w', encoding='utf-8').write(s)
c = open(os.path.join(R, 'style.css'), encoding='utf-8').read().rstrip('\n') + '\n' + open(os.path.join(R, '_patchs', 'patch459.css'), encoding='utf-8').read()
open(os.path.join(R, 'style.css'), 'w', encoding='utf-8').write(c)
print('patch459 : ok')
