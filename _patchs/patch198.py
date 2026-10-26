# -*- coding: utf-8 -*-
u"""
patch198 — suppression du compte : avant de supprimer, le jeu affiche la liste
des objets achetes en euros et demande de confirmer qu'on les perd
(CGV art. 4 : « Avant de supprimer, le jeu t'affiche la liste de tes objets
achetes et te demande de confirmer »). Un objet en attente de livraison
(14 jours) rappelle qu'on peut encore se retracter depuis « Mes achats ».
Sans achat : rien ne change. Aucun SQL (euros_mes_commandes existe deja).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'supprAchats' not in js, u'patch198 deja applique'
js = rempl(js, u"""        <li>Le journal et les classements passés gardent les parties jouées, sous « un joueur ».</li>
      </ul>""", u"""        <li>Le journal et les classements passés gardent les parties jouées, sous « un joueur ».</li>
      </ul>
      <div class="suppr-achats" id="supprAchats" hidden></div>""", 'bloc')
js = rempl(js, u"""  const pareil = () => champ.value.trim().toLowerCase() === pseudo.trim().toLowerCase() && pseudo !== '';
  champ.addEventListener('input', () => { ok.disabled = !pareil(); erreur.textContent = ''; });""",
u"""  // patch198 : les objets achetes en euros (CGV art. 4)
  let achatsAConfirmer = false;
  const casePerte = () => document.getElementById('supprPerte');
  const pareil = () => champ.value.trim().toLowerCase() === pseudo.trim().toLowerCase() && pseudo !== ''
    && (!achatsAConfirmer || (casePerte() && casePerte().checked));
  champ.addEventListener('input', () => { ok.disabled = !pareil(); erreur.textContent = ''; });
  (async () => {
    try{
      const { data, error } = await sb.rpc('euros_mes_commandes');
      const liste = error ? [] : (data || []).filter(c => c.statut === 'livree' || c.statut === 'payee');
      const zone = document.getElementById('supprAchats');
      if(!liste.length || !zone) return;
      const prix = (c) => (Number(c.prix_centimes || 0) / 100).toFixed(2).replace('.', ',') + ' €';
      zone.innerHTML = `<p class="suppr-achats-titre">Tu perds aussi ${liste.length > 1 ? `tes <b>${liste.length} objets achetés</b>` : 'ton <b>objet acheté</b>'}, sans remboursement :</p>
        <ul class="suppr-liste">${liste.map(c => `<li><b>${echapperTexte(c.article)}</b> · ${prix(c)}${c.statut === 'payee' ? ' · <i>pas encore livré : tu peux encore te rétracter depuis « Mes achats »</i>' : ''}</li>`).join('')}</ul>
        <label class="suppr-perte"><input type="checkbox" id="supprPerte"> <span>Je comprends que ces objets sont liés à mon compte et qu'ils disparaissent avec lui.</span></label>`;
      zone.hidden = false;
      achatsAConfirmer = true;
      ok.disabled = !pareil();
      casePerte().addEventListener('change', () => { ok.disabled = !pareil(); });
    }catch(err){ /* sans la boutique en euros : rien a afficher */ }
  })();""", 'confirmation')
ecrire('app.js', js)
css = lire('style.css')
assert 'patch198' not in css
css += u"""

/* ---------- patch198 : les objets achetes avant la suppression du compte ---------- */
.suppr-achats{ margin:0 0 16px; padding:12px 14px; border-radius:10px; background: rgba(229,72,77,.08); border:1px solid rgba(229,72,77,.35); }
.suppr-achats-titre{ margin:0 0 6px; color:#fff; font-size:.92rem; }
.suppr-achats .suppr-liste{ margin:0 0 10px; }
.suppr-achats i{ color: var(--brume); font-style:normal; font-size:.82rem; }
.suppr-perte{ display:flex; gap:8px; align-items:flex-start; font-size:.86rem; color:#fff; cursor:pointer; }
.suppr-perte input{ margin-top:3px; width:18px; height:18px; flex:none; }
"""
ecrire('style.css', css)
print(u'patch198 applique. Lancer : python3 maj-version.py')
