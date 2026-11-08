# patch381 : « Rejouer » à la fin d'un duel classé du Radar et de Rafale (idée de Cairnan217, 8/11)
# L'entraînement et Plus ou moins l'avaient déjà ; le duel classé n'avait que « Retour au QG ».
# Seulement juste après une partie (fin = true), pas en relisant l'historique ni pour un défi amical.
# Rejouer = le même bouton que « Lancer un duel » (qgLancer pour le Radar, rfLancer pour Rafale).
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# ---- Radar
s = rep(s, """          : `<button type="button" class="qg-btn plein" id="rdRetour">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rdCopier">Copier pour Discord</button>' : ''}`}</div></div>
    </div>`;""", """          : `${rejouerDuel ? '<button type="button" class="qg-btn plein" id="rdRejouerDuel">Rejouer</button>' : ''}<button type="button" class="qg-btn${rejouerDuel ? '' : ' plein'}" id="rdRetour">${rejouerDuel ? 'QG' : 'Retour au QG'}</button>${partage ? '<button type="button" class="qg-btn" id="rdCopier">Copier pour Discord</button>' : ''}`}</div></div>
    </div>`;
  const rdRej = document.getElementById('rdRejouerDuel');   // patch381
  if(rdRej) rdRej.onclick = () => { const b = document.getElementById('qgLancer'); if(b && !b.disabled) b.click(); else { const t = document.querySelector('.tab[data-tab="qg"]'); if(t) t.click(); } };""")
s = rep(s, """function radarAfficherResume(p, fin){
  radarMontrer('rdFin');""", """function radarAfficherResume(p, fin){
  radarMontrer('rdFin');
  const rejouerDuel = !!fin && !p.entr && !p.amical && !p.cible;   // patch381 : un duel classé qui vient de finir""")

# ---- Rafale
s = rep(s, """        : `<button type="button" class="qg-btn plein" id="rfRetourBas">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rfCopier">Copier pour Discord</button>' : ''}`}</div></div>`;""", """        : `${rejouerDuel ? '<button type="button" class="qg-btn plein" id="rfRejouerDuel">Rejouer</button>' : ''}<button type="button" class="qg-btn${rejouerDuel ? '' : ' plein'}" id="rfRetourBas">${rejouerDuel ? 'QG' : 'Retour au QG'}</button>${partage ? '<button type="button" class="qg-btn" id="rfCopier">Copier pour Discord</button>' : ''}`}</div></div>`;
  const rfRej = document.getElementById('rfRejouerDuel');   // patch381
  if(rfRej) rfRej.onclick = () => { const b = document.getElementById('rfLancer'); if(b) b.click(); };""")
s = rep(s, """function rafaleAfficherFin(p, fin){
  clearInterval(rafaleChrono);""", """function rafaleAfficherFin(p, fin){
  const rejouerDuel = !!fin && !p.entr && !p.amical && !p.cible;   // patch381 : un duel classé qui vient de finir
  clearInterval(rafaleChrono);""")

F.write_text(s, encoding='utf-8')
print('patch381 ok')
