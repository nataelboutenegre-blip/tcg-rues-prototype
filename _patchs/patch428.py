# patch428 (13/11/2026) : les bâtiments des autres joueurs n'étaient lus qu'au chargement du jeu (Oshannir, Grigny-sur-Rhône).
# Une Fonderie construite après l'ouverture du jeu n'apparaissait ni sur la carte, ni dans l'écran de conquête
# (« Fonderie détruite : tu pilles… »), alors que le pillage avait bien lieu.
#  - relecture des bâtiments au retour dans le jeu (après 5 min) et toutes les 10 min quand le jeu est à l'écran ;
#  - après une conquête, si l'écran n'a pas annoncé de Fonderie, le Journal (fonderie_detruite) est vérifié et la ligne ajoutée.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch428' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """      if(SAISON2 && BATIMENTS) setTimeout(chargerBatiments, 800);
""", """      if(SAISON2 && BATIMENTS) setTimeout(chargerBatiments, 800);
      if(SAISON2 && !(BATIMENTS_CARTE.get(String(cible.code)) || {}).fonderie) fonderieDetruiteVerifier(cible.code, fen, d);   // patch428
""")

open(A, 'a', encoding='utf-8').write("""
// ---------- patch428 : les bâtiments des autres ne vieillissent plus (Oshannir, Grigny) ----------
VERIF_AU_RETOUR.push(() => { if(SAISON2 && BATIMENTS && Date.now() - batimentsLu > 5 * 60e3) chargerBatiments(); });
setInterval(siVisible(() => { if(SAISON2 && BATIMENTS && Date.now() - batimentsLu > 10 * 60e3) chargerBatiments(); }), 60e3);
async function fonderieDetruiteVerifier(code, fen, d){
  try{
    await new Promise(r => setTimeout(r, 600));
    const { data } = await sb.rpc('journal', { p_mode: 'moi', p_type: 'fonderie_detruite', p_limite: 3 });
    const e = (data || []).find(x => x.je_suis_acteur && String(x.commune_code) === String(code) && Date.now() - new Date(x.cree_le).getTime() < 5 * 60e3);
    if(!e || !d || !d.isConnected || d.querySelector('.as-bt-fonderie')) return;
    const s = document.createElement('span');
    s.className = 'as-mon as-bt as-bt-fonderie';
    s.innerHTML = `${ICONE_FONDERIE}Fonderie détruite : tu pilles la moitié de ses lingots`;
    const lg = d.querySelector('.as-lg');
    lg ? d.insertBefore(s, lg) : d.appendChild(s);
  }catch(err){}
}
""")
print('patch428 OK')
