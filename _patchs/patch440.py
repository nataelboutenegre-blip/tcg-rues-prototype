#!/usr/bin/env python3
# patch440 : la fiche d'une commune dit ce qu'une bombe y a fait (Arkhannou, 16/11).
# Une bombe détruit les garnisons et les Forteresses, pas les autres bâtiments : la fiche l'explique
# quand la commune est dans une zone bombardée, et dit si sa garnison a sauté (bombe_touchees).
import io, sys
A = 'app.js'; S = 'style.css'
a = io.open(A, encoding='utf-8').read(); s = io.open(S, encoding='utf-8').read()
if 'patch440' in a: sys.exit('patch440 déjà appliqué')
def rempl(t, avant, apres, n=1):
    assert t.count(avant) == n, (t.count(avant), avant[:70]); return t.replace(avant, apres)

a = rempl(a, "function ouvrirPanneau(code, xCss, yCss){", r"""// ---------- patch440 : ce qu'une bombe a fait à une commune, dans sa fiche (Arkhannou) ----------
const BOMBE_TOUCHEES = new Map();   // id de zone -> Set des communes dont la garnison a sauté (ou la promesse en cours)
function bombeZonesDe(c){
  if(!c || c.lat == null || c.lon == null) return [];
  const t = Date.now();
  return (BOMBES_ZONES || []).filter(z => z.lat != null && new Date(z.fin).getTime() > t
    && distanceKm(Number(c.lat), Number(c.lon), Number(z.lat), Number(z.lon)) <= Number(z.rayon_km));
}
function bombeGarnisonTexte(code, zones, mienne){
  const touchee = zones.some(z => { const s = BOMBE_TOUCHEES.get(z.id); return s instanceof Set && s.has(String(code)); });
  return touchee ? (mienne ? ' Ta garnison ici a été détruite.' : ' Sa garnison a été détruite.') : '';
}
function bombeNoteFiche(code, c, mienne){
  if(!SAISON2 || !BATIMENTS) return '';
  const zones = bombeZonesDe(c);
  if(!zones.length) return '';
  const fin = new Date(Math.max(...zones.map(z => new Date(z.fin).getTime())));
  const demain = fin.toDateString() !== new Date().toDateString();
  const heure = fin.getHours() + 'h' + String(fin.getMinutes()).padStart(2, '0') + (demain ? ' demain' : '');
  const bonus = Number(btReglage('bombe_bonus', 15));
  const gain = SIEGE ? `dégâts × ${(1 + bonus / 100).toLocaleString('fr-FR')}` : `+${bonus} %`;
  // les garnisons soufflées : on les demande une fois par zone, la ligne se complète à l'arrivée
  for(const z of zones){
    if(BOMBE_TOUCHEES.has(z.id)) continue;
    BOMBE_TOUCHEES.set(z.id, sb.rpc('bombe_touchees', { p_id: z.id }).then(({ data, error }) => {
      BOMBE_TOUCHEES.set(z.id, new Set(!error && Array.isArray(data) ? data.map(x => String(x.c)) : []));
      const el = document.getElementById('pcBombeGarnison');
      if(el && el.dataset.code === String(code)) el.textContent = bombeGarnisonTexte(code, bombeZonesDe(c), mienne);
    }).catch(() => { BOMBE_TOUCHEES.delete(z.id); }));
  }
  const bt = BATIMENTS_CARTE.get(String(code)) || {};
  const debout = [['fonderie', 'la Fonderie'], ['centre', 'le Centre de recherche'], ['radar', 'le Radar'], ['banque', 'la Banque']].filter(([k]) => bt[k]).map(([, n]) => n);
  const liste = debout.length > 1 ? debout.slice(0, -1).join(', ') + ' et ' + debout[debout.length - 1] : debout[0];
  const batiments = debout.length
    ? `<span class="pc-bombe-l">${liste.charAt(0).toUpperCase() + liste.slice(1)} ${debout.length > 1 ? 'restent' : 'reste'} debout : une bombe ne détruit que les garnisons et les Forteresses. ${mienne ? `Tu ${debout.length > 1 ? 'les' : debout[0].startsWith('la') ? 'la' : 'le'} perds si la commune est prise` : `Pour ${debout.length > 1 ? 'les' : debout[0].startsWith('la') ? 'la' : 'le'} faire tomber, il faut prendre la commune`}.</span>`
    : '';
  const pose = Number(btReglage('bombe_garnison_h', 24)) > 0 ? ' Aucune garnison ne peut y être posée d’ici là.' : '';
  return `<p class="pc-bombe"><span class="pc-bombe-l"><b>💥 Zone bombardée</b> jusqu’à ${heure} : ${mienne ? `les attaquants y ont ${gain}` : `${gain} pour tes attaques`}.<span id="pcBombeGarnison" data-code="${echapperHtml(String(code))}">${bombeGarnisonTexte(code, zones, mienne)}</span>${pose}</span>${batiments}</p>`;
}
function ouvrirPanneau(code, xCss, yCss){""")
a = rempl(a, """    <div class="pc-lignes">${lignes.map(([a, b]) => `<div class="pc-ligne"><span>${a}</span><b>${b}</b></div>`).join('')}</div>
    ${echClan}""", """    <div class="pc-lignes">${lignes.map(([a, b]) => `<div class="pc-ligne"><span>${a}</span><b>${b}</b></div>`).join('')}</div>
    ${bombeNoteFiche(code, c, !!mienne)}
    ${echClan}""")
s = s.rstrip('\n') + """

/* patch440 : ce qu'une bombe a fait à cette commune */
.pc-bombe{ margin:10px 0 0; padding:9px 11px; border-radius:10px; display:flex; flex-direction:column; gap:6px;
  font-size:.78rem; line-height:1.45; color:#FFD9D6; background:rgba(229,72,77,.13); border:1px solid rgba(229,72,77,.45); }
.pc-bombe b{ color:#fff; font-weight:700; }
.pc-bombe-l + .pc-bombe-l{ padding-top:6px; border-top:1px solid rgba(229,72,77,.3); color:#F1D9D7; }
"""
io.open(A, 'w', encoding='utf-8').write(a); io.open(S, 'w', encoding='utf-8').write(s)
print('patch440 appliqué')
