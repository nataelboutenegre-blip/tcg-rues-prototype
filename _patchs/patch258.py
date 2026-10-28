# patch258 : le tchat du clan (avec s2-57) — temps réel Supabase, pastille sur l'onglet Clan
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

MOTEUR = r"""
// ---------- patch258 : le tchat du clan ----------
let tchat = { clan: null, msgs: [], canal: null, nonLus: 0, ouvert: false, envoi: false };
const TCHAT_MAX = 300;
function tchatHeure(d){
  const x = new Date(d), auj = new Date();
  const h = x.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  return x.toDateString() === auj.toDateString() ? h : x.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) + ' · ' + h;
}
function tchatHtml(c){
  const peutSuppr = c.chef || (c.droits || {}).exclure || (c.droits || {}).modifier;
  const role = (id) => { const m = (c.membres || []).find(x => x.id === id); return m ? (m.chef ? 'chef' : m.bras_droit ? 'bd' : '') : ''; };
  const lignes = tchat.msgs.map((m, i) => {
    const prec = tchat.msgs[i - 1];
    const suite = prec && prec.auteur === m.auteur && new Date(m.le) - new Date(prec.le) < 5 * 60000;
    const moi = m.auteur === window.__monId;
    return `<div class="tc-msg${moi ? ' moi' : ''}${suite ? ' suite' : ''}" data-tc-id="${m.id}">
      ${suite ? '' : `<div class="tc-tete"><b class="${role(m.auteur)}">${echapperTexte(m.pseudo || 'Joueur')}</b><span>${tchatHeure(m.le)}</span></div>`}
      <div class="tc-bulle">${m.supprime ? '<i>Message supprimé</i>' : echapperTexte(m.texte)}</div>
      ${m.supprime ? '' : `<div class="tc-actions">${!moi ? `<button type="button" data-tc-signaler="${m.id}">Signaler</button>` : ''}${moi || peutSuppr ? `<button type="button" data-tc-suppr="${m.id}">Supprimer</button>` : ''}</div>`}
    </div>`;
  }).join('');
  return `<div class="tc-bloc" style="--clan:${c.couleur}">
    <h2>Tchat du clan</h2>
    <div class="tc-liste" id="tcListe">${lignes || '<p class="tc-vide">Personne n’a encore écrit. Lance la discussion : cibles, échanges, départements à tenir…</p>'}</div>
    <form class="tc-saisie" id="tcForm"><input id="tcTexte" maxlength="300" autocomplete="off" placeholder="Écrire au clan…" aria-label="Message au clan"><button type="submit" class="bq-btn">Envoyer</button></form>
    <p class="tc-note">Visible seulement par les membres du clan. Les messages s’effacent au bout de 7 jours.</p>
  </div>`;
}
"""
s = rep(s, "let clanGere = null;", "let clanGere = null;" + MOTEUR)
s = rep(s, "      <h2>Membres</h2>${membres}", "      ${tchatHtml(c)}   <!-- patch258 -->\n      <h2>Membres</h2>${membres}")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch258 : le tchat du clan ---------- */
.tc-bloc{ margin:14px 0 6px; }
.tc-liste{ height:300px; overflow-y:auto; display:flex; flex-direction:column; gap:2px; padding:10px; border-radius:12px;
  background:var(--nuit); border:1px solid rgba(169,188,212,.14); scroll-behavior:smooth; }
.tc-vide{ margin:auto; text-align:center; color:var(--brume); font-size:.84rem; max-width:260px; line-height:1.5; }
.tc-msg{ max-width:82%; align-self:flex-start; margin-top:8px; position:relative; }
.tc-msg.suite{ margin-top:0; }
.tc-msg.moi{ align-self:flex-end; text-align:right; }
.tc-tete{ display:flex; gap:8px; align-items:baseline; font-size:.75rem; color:var(--brume); margin:0 4px 3px; }
.tc-msg.moi .tc-tete{ justify-content:flex-end; }
.tc-tete b{ color:#fff; font-weight:700; font-size:.8rem; }
.tc-tete b.chef::after{ content:' · Chef'; color:var(--clan); font-weight:600; }
.tc-tete b.bd::after{ content:' · Bras droit'; color:#F0B429; font-weight:600; }
.tc-bulle{ display:inline-block; text-align:left; padding:7px 11px; border-radius:14px; font-size:.88rem; line-height:1.4; word-break:break-word;
  background:var(--nuit-3); color:#fff; border-top-left-radius:5px; }
.tc-msg.moi .tc-bulle{ background:color-mix(in srgb, var(--clan) 34%, var(--nuit-2)); border-top-left-radius:14px; border-top-right-radius:5px; }
.tc-msg.suite .tc-bulle{ border-top-left-radius:14px; border-top-right-radius:14px; }
.tc-bulle i{ color:var(--brume); }
.tc-actions{ display:none; gap:8px; margin:3px 6px 0; font-size:.7rem; }
.tc-msg:hover .tc-actions, .tc-msg:focus-within .tc-actions{ display:flex; }
.tc-msg.moi .tc-actions{ justify-content:flex-end; }
.tc-actions button{ background:none; border:0; color:var(--brume); font:inherit; cursor:pointer; padding:0; text-decoration:underline; }
.tc-saisie{ display:flex; gap:8px; margin-top:8px; }
.tc-saisie input{ flex:1; min-width:0; background:var(--nuit); border:1px solid rgba(169,188,212,0.3); border-radius:9px; padding:9px 12px; color:#fff; font:inherit; }
.tc-note{ color:var(--brume); font-size:.74rem; margin:6px 2px 0; }
"""
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- le fonctionnement
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
LOGIQUE = r"""
function tchatVuCle(){ return 'tf-tchat-vu-' + tchat.clan; }
function tchatMajBadge(){
  const b = document.getElementById('clanBadge');
  if(!b) return;
  let vu = 0; try{ vu = Number(localStorage.getItem(tchatVuCle())) || 0; }catch(e){}
  const ongletOuvert = document.getElementById('panel-clan') && document.getElementById('panel-clan').classList.contains('active');
  if(ongletOuvert && tchat.msgs.length){ vu = tchat.msgs[tchat.msgs.length - 1].id; try{ localStorage.setItem(tchatVuCle(), String(vu)); }catch(e){} }
  const n = tchat.msgs.filter(m => m.id > vu && m.auteur !== window.__monId && !m.supprime).length;
  b.hidden = !n; b.textContent = n > 9 ? '9+' : String(n);
}
function tchatPseudo(id){
  const c = clanCache && clanCache.moi && clanCache.moi.clan;
  const m = c && (c.membres || []).find(x => x.id === id);
  return (m && m.pseudo) || tchat.pseudos.get(id) || 'Membre';
}
function tchatMajListe(){
  const l = document.getElementById('tcListe');
  const c = clanCache && clanCache.moi && clanCache.moi.clan;
  if(!l || !c) return;
  const enBas = l.scrollHeight - l.scrollTop - l.clientHeight < 60;
  const tmp = document.createElement('div'); tmp.innerHTML = tchatHtml(c);
  l.innerHTML = tmp.querySelector('#tcListe').innerHTML;
  if(enBas) l.scrollTop = l.scrollHeight;
}
function tchatRecevoir(m){
  if(!m || !m.id) return;
  const i = tchat.msgs.findIndex(x => x.id === m.id);
  if(i >= 0) tchat.msgs[i] = Object.assign(tchat.msgs[i], m);
  else { tchat.msgs.push(m); tchat.msgs.sort((a, b) => a.id - b.id); if(tchat.msgs.length > TCHAT_MAX) tchat.msgs.shift(); }
  if(m.pseudo) tchat.pseudos.set(m.auteur, m.pseudo);
  else m.pseudo = tchatPseudo(m.auteur);
  tchatMajListe(); tchatMajBadge();
}
async function tchatDemarrer(){
  try{
    const { data, error } = await sb.rpc('clan_tchat_lire');
    if(error || !data) return;
    const clan = data.clan_id || null;
    if(clan !== tchat.clan && tchat.canal){ try{ sb.removeChannel(tchat.canal); }catch(e){} tchat.canal = null; }
    tchat.clan = clan; tchat.msgs = data.messages || [];
    tchat.msgs.forEach(m => tchat.pseudos.set(m.auteur, m.pseudo));
    if(clan && !tchat.canal && typeof sb.channel === 'function'){
      tchat.canal = sb.channel('tchat-' + clan)
        .on('postgres_changes', { event: '*', schema: 'public', table: 'clan_messages', filter: 'clan_id=eq.' + clan }, (ev) => {
          const r = ev.new || {};
          if(ev.eventType === 'DELETE'){ tchat.msgs = tchat.msgs.filter(x => x.id !== (ev.old || {}).id); tchatMajListe(); tchatMajBadge(); return; }
          tchatRecevoir({ id: r.id, auteur: r.auteur, texte: r.texte, le: r.le, supprime: r.supprime });
        })
        .subscribe();
    }
    tchatMajListe(); tchatMajBadge();
  }catch(e){ console.error('Tchat :', e); }
}
function tchatApresRendu(){
  const l = document.getElementById('tcListe');
  if(l){ l.style.scrollBehavior = 'auto'; l.scrollTop = l.scrollHeight; l.style.scrollBehavior = ''; }
  tchatMajBadge();
}
document.addEventListener('submit', async (e) => {
  if(!e.target.closest('#tcForm')) return;
  e.preventDefault();
  const champ = document.getElementById('tcTexte');
  const t = (champ && champ.value || '').trim();
  if(!t || tchat.envoi) return;
  tchat.envoi = true;
  const { data, error } = await sb.rpc('clan_tchat_envoyer', { p_texte: t });
  tchat.envoi = false;
  if(error){ notifier({ type: 'erreur', titre: 'Message non envoyé', texte: messageLisible(error.message) }); return; }
  champ.value = '';
  tchatRecevoir(data);
  const l = document.getElementById('tcListe'); if(l) l.scrollTop = l.scrollHeight;
  champ.focus();
});
document.addEventListener('click', async (e) => {
  const sup = e.target.closest('[data-tc-suppr]'), sig = e.target.closest('[data-tc-signaler]');
  const b = sup || sig;
  if(!b) return;
  if(!b.classList.contains('confirmer')){ b.classList.add('confirmer'); b.textContent = sup ? 'Confirmer la suppression' : 'Confirmer le signalement';
    setTimeout(() => { if(b.isConnected){ b.classList.remove('confirmer'); b.textContent = sup ? 'Supprimer' : 'Signaler'; } }, 4000); return; }
  const id = Number(sup ? b.dataset.tcSuppr : b.dataset.tcSignaler);
  const { error } = await sb.rpc(sup ? 'clan_tchat_supprimer' : 'clan_tchat_signaler', { p_id: id });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
  if(sup) tchatRecevoir({ id, supprime: true, texte: '' });
  else notifier({ type: 'succes', titre: 'Message signalé', texte: 'Merci, il sera vérifié.' });
});
"""
s = rep(s, "function tchatHtml(c){", LOGIQUE + "\nfunction tchatHtml(c){")
s = rep(s, "let tchat = { clan: null, msgs: [], canal: null, nonLus: 0, ouvert: false, envoi: false };",
           "let tchat = { clan: null, msgs: [], canal: null, envoi: false, pseudos: new Map() };")
# démarrage : avec les clans de la carte (au lancement et après chaque action de clan)
s = rep(s, "    const [{ data, error }] = await Promise.all([sb.rpc('clans_carte'), chargerBlasons()]);   // patch253\n    if(error) return;",
           "    const [{ data, error }] = await Promise.all([sb.rpc('clans_carte'), chargerBlasons()]);   // patch253\n    tchatDemarrer();   // patch258\n    if(error) return;")
s = rep(s, "  zone.innerHTML = `<div class=\"clan-grille\">${gauche}${blocClassement}</div>`;",
           "  zone.innerHTML = `<div class=\"clan-grille\">${gauche}${blocClassement}</div>`;\n  tchatApresRendu();   // patch258")
s = rep(s, "    if(tab.dataset.tab === 'clan') loadClan();", "    if(tab.dataset.tab === 'clan'){ loadClan(); setTimeout(tchatMajBadge, 0); }")
# le texte du message : on n'affiche pas un message encore en cours de suppression
f.write_text(s, encoding='utf-8')

f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
s = rep(s, """        </div>
        Clan
      </div>""", """        </div>
        Clan
        <span class="tab-badge" id="clanBadge" hidden></span>
      </div>""")
f.write_text(s, encoding='utf-8')
print('patch258 ok')
