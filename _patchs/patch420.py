# patch420 (11/11/2026) : les dos de carte du podium de la saison 2
# Piste A « Lauriers » choisie par Nataël, un métal par place : or au 1er, argent au 2e, bronze au 3e.
# Trois shaders (DOS_GLSL, comme les dos premium) + CSS (fond de secours, chiffre et « SAISON 2 » dans l'emblème).
# Les trois dos sont montrés dans la fiche des récompenses ; le joueur du podium est prévenu une fois (comme le dos OG).
# Les articles sont créés par s2-138 (jamais en vente) ; l'attribution se fait à la clôture.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch420' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# 1. les shaders, avant dosGl (qui lit la liste des dos premium à son démarrage)
rep(A, "\nconst DOS_GLSL_FIN = `", "\n" + open('_patchs/patch420-dos.js', encoding='utf-8').read() + "const DOS_GLSL_FIN = `")

# 2. le joueur du podium est prévenu une fois
rep(A, """                 texte: 'Ton dos de carte OG t\\'attend dans la Boutique : touche « Équiper ».' });
    }
  }catch(e){}
}""", """                 texte: 'Ton dos de carte OG t\\'attend dans la Boutique : touche « Équiper ».' });
    }
  }catch(e){}
  // patch420 : le dos du podium de la saison 2
  try{
    const pod = (data.articles || []).find(a => /^dos-podium-s2-/.test(a.id) && a.possede);
    if(pod && data.dos !== pod.id && localStorage.getItem('tf-dos-podium-s2-vu') !== '1'){
      localStorage.setItem('tf-dos-podium-s2-vu', '1');
      notifier({ type: 'succes', titre: 'Bravo pour ton podium de la saison 2 !',
                 texte: 'Ton dos de carte « ' + pod.nom + ' » t\\'attend dans la Boutique : touche « Équiper ».' });
    }
  }catch(e){}
}""")

# 3. la fiche des récompenses montre les trois dos
rep(A, """        <p class="rs2-note">Le dos de carte du podium ne s’obtiendra pas autrement.</p>""",
"""        <div class="rs2-dos">
          <div>${dosApercuHtml('dos-podium-s2-or')}<small>1er</small></div>
          <div>${dosApercuHtml('dos-podium-s2-argent')}<small>2e</small></div>
          <div>${dosApercuHtml('dos-podium-s2-bronze')}<small>3e</small></div>
        </div>
        <p class="rs2-note">Le dos de carte du podium : en or, en argent ou en bronze selon la place, un seul exemplaire de chaque. Il ne s’obtiendra pas autrement.</p>""")

open(C, 'a', encoding='utf-8').write(open('_patchs/patch420-dos.css', encoding='utf-8').read())
print('patch420 OK')
