# patch319 : la course au nom gravé (grands chantiers) — avec s2-83
#  Sur chaque monument du choix : combien d'autres joueurs le restaurent, dans combien de
#  temps le plus avancé finit, et si on peut encore passer devant avec son équipe.
#  Sur son propre chantier : en tête ou pas, et de combien. Jamais de pseudo.
#  Sans s2-83 (champs absents), rien ne change à l'écran.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch319' not in s

s = rep(s, """// les dessins : chargés une fois, à la demande
function chMoteur(){""", """// patch319 : la course au nom gravé (les autres chantiers sur ce monument, jamais de pseudo)
function chCourse(m){
  const n = Number(m && m.autres) || 0;
  const fin = m && m.autres_fin ? new Date(m.autres_fin).getTime() : null;
  return { n, reste: fin == null ? null : Math.max(0, fin - chMaintenant()) / 3600e3 };   // en heures
}
function chJoueurs(n){ return chNb(n) + ' joueur' + (n > 1 ? 's' : ''); }
function chCourseChoix(m, monDuree){
  if(m.graveur) return `<span class="ch-mon-grave">★ Gravé : ${echapperTexte(m.graveur)}</span>`;
  const k = chCourse(m);
  if(!k.n || !('autres' in m)) return '<span class="ch-mon-grave">Personne ne l’a encore restauré</span>';
  const tete = k.reste == null ? `${chJoueurs(k.n)} en chantier, en pause` : `${chJoueurs(k.n)} en chantier · le plus avancé finit dans ${chDuree(k.reste)}`;
  const devant = k.reste == null || monDuree < k.reste;
  return `<span class="ch-mon-grave">⚒ ${tete}</span><span class="ch-mon-course ${devant ? 'ok' : 'ko'}">${devant ? 'Tu peux encore passer devant' : 'Il finira avant toi, sauf renfort'}</span>`;
}
function chCourseLigne(mon, c){
  if(!mon || mon.graveur || !('autres' in mon)) return '';
  const k = chCourse(mon);
  if(!k.n) return '<p class="ch-course">Personne d’autre ne restaure ce monument en ce moment : le premier qui le finit y grave son nom.</p>';
  const qui = `${chJoueurs(k.n)} ${k.n > 1 ? 'le restaurent' : 'le restaure'} aussi`;
  if(c.en_pause || !c.fin_prevue) return `<p class="ch-course">Course au nom gravé : ${qui}.${k.reste != null ? ` Le plus avancé finit dans ${chDuree(k.reste)}.` : ''} Ton chantier est en pause.</p>`;
  const moi = Math.max(0, new Date(c.fin_prevue).getTime() - chMaintenant()) / 3600e3;
  if(k.reste == null || moi <= k.reste) return `<p class="ch-course ok">Course au nom gravé : ${qui}. <b>Tu es en tête</b>${k.reste != null ? ` : le suivant finit ${chDuree(k.reste - moi)} après toi` : ''}.</p>`;
  return `<p class="ch-course ko">Course au nom gravé : ${qui}. Le plus avancé finit dans ${chDuree(k.reste)}, <b>${chDuree(moi - k.reste)} avant toi</b>. Des ouvriers ou de meilleurs outils peuvent te faire passer devant.</p>`;
}

// les dessins : chargés une fois, à la demande
function chMoteur(){""")

s = rep(s, """      h += chSegs('chSegs') + `<div class="ch-lignes"><p id="chLigneFin"></p><p id="chLigneRythme"></p></div>
""", """      h += chSegs('chSegs') + `<div class="ch-lignes"><p id="chLigneFin"></p><p id="chLigneRythme"></p></div>${chCourseLigne(mon, c)}
""")

s = rep(s, """          <span class="ch-mon-grave">${m.graveur ? '★ Gravé : ' + echapperTexte(m.graveur) : 'Personne ne l’a encore restauré'}</span>
""", """          ${chCourseChoix(m, (Number(T[m.taille]) || 0) / r)}
""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s = rep(s, """.ch-mon-grave{ font-size:0.72rem; color:#FFD56B; }
""", """.ch-mon-grave{ font-size:0.72rem; color:#FFD56B; }
/* patch319 : la course au nom gravé */
.ch-mon-course{ font-size:0.7rem; font-weight:600; }
.ch-mon-course.ok{ color:#7EE2B0; } .ch-mon-course.ko{ color:#FF8F92; }
.ch-course{ margin:0; font-size:0.82rem; line-height:1.35; color:#C9D6E6; padding:7px 10px; border-radius:10px; background:#162C4B; border-left:3px solid #FFD56B; }
.ch-course.ok{ border-left-color:#7EE2B0; } .ch-course.ko{ border-left-color:#FF8F92; }
.ch-course b{ color:#fff; }
""")
f.write_text(s, encoding='utf-8')
print('patch319 ok')
