# patch423 (12/11/2026) : dans la discussion générale aussi, le pseudo cité (@pseudo) et le pseudo de l'auteur
# ouvrent le profil (suite de patch422, demande d'Oshannir). Un @ qui ne correspond à aucun joueur connu reste en doré, comme avant.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch423' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
# le texte d'un message : les @ reconnus deviennent des liens (même règle que le tchat du clan)
rep(A, """function dgTexteHtml(t){ return echapperTexte(t || '').replace(/(^|\\s)(@[^\\s@]{2,20})/g, '$1<span class="dg-at">$2</span>'); }""",
"""function dgTexteBrut(t){ return echapperTexte(t || '').replace(/(^|\\s)(@[^\\s@]{2,20})/g, '$1<span class="dg-at">$2</span>'); }
function dgTexteHtml(t){ return tchatTexteHtml(t, dgIndex(), { cls: 'dg-at dg-at-lien', repli: dgTexteBrut }).html; }   // patch423""")
rep(A, """function tchatTexteHtml(texte, idx){
  const t = String(texte || '');
  if(!t.includes('@') || !idx.liste.length) return { html: echapperTexte(t), moi: false };""",
"""function tchatTexteHtml(texte, idx, o){
  const t = String(texte || ''), esc = (o && o.repli) || echapperTexte, cls = (o && o.cls) || 'tc-mention';   // patch423
  if(!t.includes('@') || !idx.liste.length) return { html: esc(t), moi: false };""")
rep(A, """    html += echapperTexte(t.slice(i, at)) + `<button type="button" class="tc-mention${estMoi ? ' moi' : ''}" data-tc-profil="${echapperTexte(trouve.id)}">@${echapperTexte(trouve.pseudo)}</button>`;
    i = at + 1 + trouve.pseudo.length;
  }
  return { html: html + echapperTexte(t.slice(i)), moi };""",
"""    html += esc(t.slice(i, at)) + `<button type="button" class="${cls}${estMoi ? ' moi' : ''}" data-tc-profil="${echapperTexte(trouve.id)}">@${echapperTexte(trouve.pseudo)}</button>`;
    i = at + 1 + trouve.pseudo.length;
  }
  return { html: html + esc(t.slice(i)), moi };""")
# le pseudo de l'auteur (messages des autres)
rep(A, """  const h = groupe ? '' : `<div class="dg-h"><b style="color:${c}">${echapperTexte(m.pseudo || 'Joueur')}</b>""",
"""  const h = groupe ? '' : `<div class="dg-h"><button type="button" class="dg-qui" data-tc-profil="${echapperTexte(m.auteur || '')}" style="color:${c}">${echapperTexte(m.pseudo || 'Joueur')}</button>""")
# toucher un pseudo n'ouvre pas la feuille du message
rep(A, """  const msg = e.target.closest('#dgFil .dg-m');
  if(msg){""", """  if(e.target.closest('#dgFil [data-tc-profil]')) return;   // patch423 : le profil s'ouvre (patch422)
  const msg = e.target.closest('#dgFil .dg-m');
  if(msg){""")
open(A, 'a', encoding='utf-8').write("""
// ---------- patch423 : la discussion générale reconnaît aussi ses auteurs ----------
let dgIdx = { cle: '', map: null, liste: [] };
function dgIndex(){
  const base = tchatIndex(), der = DG.msgs.length ? DG.msgs[DG.msgs.length - 1].id : 0;
  const cle = base.cle + '|' + DG.msgs.length + '|' + der;
  if(dgIdx.cle === cle) return dgIdx;
  const map = new Map(base.map);
  for(const m of DG.msgs){ if(m && m.auteur && m.pseudo && !m.retire){ const k = normPseudo(m.pseudo); if(!map.has(k)) map.set(k, { id: m.auteur, pseudo: m.pseudo, clan: false }); } }
  dgIdx = { cle, map, liste: [...map.entries()].sort((a, b) => b[0].length - a[0].length) };
  return dgIdx;
}
""")
open(C, 'a', encoding='utf-8').write("""
/* patch423 : pseudos cliquables dans la discussion générale */
.dg-at-lien{ display:inline; font:inherit; font-weight:700; color:#FFD35A; background:rgba(255,211,90,.12); border:0; border-radius:5px; padding:0 3px; margin:0; cursor:pointer; }
.dg-at-lien:hover{ text-decoration:underline; text-underline-offset:3px; }
.dg-qui{ background:none; border:0; padding:0; margin:0; font:inherit; font-weight:800; font-size:.8rem; cursor:pointer; }
.dg-qui:hover{ text-decoration:underline; text-underline-offset:3px; }
""")
print('patch423 OK')
