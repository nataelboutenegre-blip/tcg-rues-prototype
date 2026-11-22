# patch489 : après un duel classé (Plus ou moins, Rafale, Radar), le jeu dit combien de tickets du Mess on vient
# de gagner et met le compteur à jour tout de suite. Avant, le serveur donnait bien les tickets, mais rien ne le
# disait et le compteur du Mess restait sur l'ancien chiffre tant qu'on ne rouvrait pas l'Arcade
# (retour de Nataël, 22/11 12 h 20 : « je n'ai pas eu de ticket »). Jeu seul.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'

rep(A, """    const { data, error } = await sb.rpc('mess_etat');
    MESS = !error && data ? data : null;
  }catch(e){ MESS = null; }""", """    const { data, error } = await sb.rpc('mess_etat');
    MESS = !error && data ? data : null;
  }catch(e){ MESS = null; }
  messTicketsGagnes();   // patch489""")
rep(A, """async function messCharger(){""", """// patch489 : les tickets gagnés aujourd'hui (mess_etat().jour) ont monté depuis la dernière lecture : on le dit.
// Le dernier chiffre vu est gardé sur l'appareil, pour un duel réglé plus tard (l'adversaire joue après moi).
function messTicketsGagnes(){
  if(!MESS || !messVisible()) return;
  const jour = new Date().toLocaleDateString('fr-CA'), n = Number(MESS.jour) || 0;
  let vu = null;
  try{ const s = (localStorage.getItem('tf-mess-jour') || '').split('|'); if(s[0] === jour) vu = Number(s[1]) || 0; }catch(e){}
  try{ localStorage.setItem('tf-mess-jour', jour + '|' + n); }catch(e){}
  if(vu === null){ if(!messDuelFini) return; vu = 0; }   // première lecture du jour : on ne dit rien, sauf juste après un duel
  messDuelFini = false;
  if(n <= vu) return;
  const g = n - vu, max = Number(MESS.regles && MESS.regles.par_jour) || 30;
  notifier({ type: 'succes', titre: `🎟 +${g} ticket${g > 1 ? 's' : ''} pour le Mess`,
    texte: `Tu en as ${Number(MESS.tickets) || 0}${n >= max ? ` · maximum du jour atteint (${max})` : ` · ${n} / ${max} gagnés aujourd’hui`}. Touche ici pour aller au Mess.`,
    aller: () => { const t = document.querySelector('.tab[data-tab="qg"]'); if(t) t.click(); setTimeout(() => { const c = document.getElementById('qgMess'); if(c && c.scrollIntoView) c.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 300); } });
}
var messDuelFini = false;
// un duel classé vient de finir : on relit le Mess (le serveur donne les tickets au moment où le duel se règle)
function messApresDuel(){
  if(!SAISON2) return;
  messDuelFini = true;
  setTimeout(() => { try{ messCharger(); }catch(e){} }, 600);
}
async function messCharger(){""")
# les trois fins de duel classé
rep(A, """  if(d.gain) loadPackStatus();
  chargerPomDuelEtat();
}""", """  if(d.gain) loadPackStatus();
  chargerPomDuelEtat();
  if(d.resultat) messApresDuel();   // patch489
}""")
rep(A, """  rafaleAfficherFin(data, true);
}""", """  rafaleAfficherFin(data, true);
  messApresDuel();   // patch489
}""")
rep(A, """  radarMontrer('rdFin');
  const rejouerDuel = !!fin && !p.entr && !p.amical && !p.cible;   // patch381 : un duel classé qui vient de finir""",
"""  radarMontrer('rdFin');
  const rejouerDuel = !!fin && !p.entr && !p.amical && !p.cible;   // patch381 : un duel classé qui vient de finir
  if(fin && !p.entr) messApresDuel();   // patch489""")
print('patch489 : fini')
