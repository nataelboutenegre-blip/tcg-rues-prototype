# patch359 (6/11/2026) : « Tes dés au Front » dans le Profil (idée d'Arkhannou).
#
# Un bloc de plus dans Profil (seulement le sien) : rounds d'attaque, défenses
# et garnisons de la saison, et pour l'attaque et la défense, le pourcentage
# réussi aux dés comparé à celui qui était attendu (chances affichées au
# moment du lancer, enregistrées depuis le 4/11), avec un verdict :
# pile dans la moyenne / un peu de (mal)chance / beaucoup de (mal)chance.
# Sans s2-106 (ou en Terra seul), le bloc n'apparaît pas.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch359' not in s, 'patch359 déjà appliqué'

s = rep(s, "function blocsProfil(p){",
"""// patch359 : « Tes dés au Front » (s2-106), seulement dans son propre Profil
async function chargerMesDes(){
  if(!SAISON2) return null;
  try{ const { data, error } = await sb.rpc('mes_stats_combat'); return error ? null : (data || null); }
  catch(e){ return null; }
}
function desVerdict(x){
  const n = Number(x.mesures || 0);
  if(n < 10) return { cls: 'neutre', txt: 'Pas encore assez de lancers pour juger' };
  const ecart = Number(x.des_gagnes || 0) - Number(x.attendu || 0);
  const z = ecart / Math.sqrt(Math.max(Number(x.variance || 0), 0.25));
  if(Math.abs(z) < 1) return { cls: 'neutre', txt: 'Pile dans la moyenne' };
  if(z >= 2) return { cls: 'chance', txt: 'Beaucoup de chance' };
  if(z > 0) return { cls: 'chance', txt: 'Un peu de chance' };
  if(z <= -2) return { cls: 'malchance', txt: 'Vraiment pas de chance' };
  return { cls: 'malchance', txt: 'Un peu de malchance' };
}
function blocDes(st){
  if(!st || !st.attaque) return '';
  const a = st.attaque, d = st.defense || {}, g = st.garnison || {};
  if(!Number(a.total) && !Number(d.total) && !Number(g.total)) return '';
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const pc = (x, n) => Number(n) > 0 ? Math.round(100 * Number(x) / Number(n)) : 0;
  const ligne = (titre, x, unite, gagnesTxt, perdusTxt, gagnes, total) => {
    if(!Number(total)) return '';
    const v = desVerdict(x);
    const reel = pc(x.des_gagnes, x.mesures), attendu = pc(x.attendu, x.mesures);
    return `<div class="des-l">
      <div class="des-h"><b>${titre}</b><span>${nb(total)} ${unite}${Number(total) > 1 ? 's' : ''} · <i class="ok">${nb(gagnes)} ${gagnesTxt}</i> · <i class="ko">${nb(Number(total) - Number(gagnes))} ${perdusTxt}</i></span></div>
      ${Number(x.mesures) > 0 ? `<div class="des-barre" title="Réussi aux dés : ${reel} % · attendu : ${attendu} %">
        <i style="width:${reel}%"></i><u style="left:${attendu}%"></u>
      </div>
      <div class="des-c"><span>Aux dés : <b>${reel} %</b> réussis, <b>${attendu} %</b> attendus</span><em class="${v.cls}">${v.txt}</em></div>` : ''}
    </div>`;
  };
  const garn = Number(a.garnison) > 0 ? `<p class="des-n">Dont ${nb(a.garnison)} perdu${Number(a.garnison) > 1 ? 's' : ''} à cause d’une garnison alors que tu avais gagné aux dés.</p>` : '';
  return `<div class="pf-bloc pf-des">
    <h3>Tes dés au Front</h3>
    <p class="des-sous">Cette saison. Le trait blanc marque ce que tes chances affichées promettaient.</p>
    ${ligne('Attaque', a, 'assaut', 'gagnés', 'perdus', a.gagnes, a.total)}
    ${garn}
    ${ligne('Défense', d, 'tentative', 'réussies', 'ratées', d.reussies, d.total)}
    ${Number(g.total) ? `<div class="des-l"><div class="des-h"><b>Garnisons</b><span>${nb(g.total)} assaut${Number(g.total) > 1 ? 's' : ''} · <i class="ok">${nb(g.reussies)} repoussé${Number(g.reussies) > 1 ? 's' : ''}</i> (1 chance sur 2)</span></div></div>` : ''}
  </div>`;
}

function blocsProfil(p){""")

s = rep(s, "    [profilPanneau.vitrine, profilPanneau.badges, profilPanneau.echanges, profilPanneau.titres, profilPanneau.parrainage] =\n      await Promise.all([chargerVitrine(id), chargerBadges(id), chargerStatEchanges(id), chargerMesTitres(), chargerParrainage()]);",
           "    [profilPanneau.vitrine, profilPanneau.badges, profilPanneau.echanges, profilPanneau.titres, profilPanneau.parrainage, profilPanneau.des] =\n      await Promise.all([chargerVitrine(id), chargerBadges(id), chargerStatEchanges(id), chargerMesTitres(), chargerParrainage(), chargerMesDes()]);   // patch359")

s = rep(s, "    ${blocsProfil(p)}\n    <div class=\"pf-boutons\">",
           "    ${blocsProfil(p)}\n    ${blocDes(p.des)}\n    <div class=\"pf-boutons\">")

F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch359' not in c
c += """
/* patch359 : Tes dés au Front (Profil) */
.pf-des{ margin-top:14px; }
.pf-des .des-sous{ margin:-4px 0 10px; font-size:.82rem; color: var(--brume); }
.des-l{ padding:10px 0; border-top:1px solid rgba(169,188,212,.14); }
.des-l:first-of-type{ border-top:0; }
.des-h{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap; }
.des-h b{ font-size:.98rem; }
.des-h span{ font-size:.84rem; color: var(--brume); }
.des-h i{ font-style:normal; font-weight:600; }
.des-h i.ok{ color:#7FE3B4; } .des-h i.ko{ color:#FF9A94; }
.des-barre{ position:relative; height:10px; margin:9px 0 6px; border-radius:6px; background:rgba(169,188,212,.16); overflow:visible; }
.des-barre i{ display:block; height:100%; border-radius:6px; background:linear-gradient(90deg,#F0B429,#FFD36B); }
.des-barre u{ position:absolute; top:-4px; bottom:-4px; width:3px; margin-left:-1.5px; border-radius:2px; background:#fff; box-shadow:0 0 0 2px rgba(15,31,56,.85); }
.des-c{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; font-size:.84rem; color: var(--brume); }
.des-c b{ color:#fff; }
.des-c em{ font-style:normal; font-weight:700; font-size:.8rem; padding:3px 9px; border-radius:20px; }
.des-c em.neutre{ background:rgba(169,188,212,.14); color:#DCE6F2; }
.des-c em.chance{ background:rgba(127,227,180,.16); color:#7FE3B4; }
.des-c em.malchance{ background:rgba(255,154,148,.15); color:#FF9A94; }
.des-n{ margin:-4px 0 4px; font-size:.8rem; color: var(--brume); }
"""
C.write_text(c, encoding='utf-8')
print('patch359 appliqué')
