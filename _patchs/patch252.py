# patch252 : les bras droits du clan (avec s2-51)
#  - le chef nomme jusqu'à 2 bras droits et coche leurs droits (inviter, exclure)
#  - un bras droit voit le champ « Inviter » / le bouton « Exclure » selon ses droits
#  - badge « Bras droit » dans la liste des membres (mon clan et clans dépliés)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

# 1. la ligne d'un membre : rôle, bouton Gérer (chef) ou Exclure (bras droit autorisé), panneau du chef
s = rep(s, """    const membres = (c.membres || []).map(m => `<div class="clan-membre"><span class="av" style="--clan:${c.couleur}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
        <div><b>${echapperTexte(m.pseudo)}</b><small>${m.chef ? 'Chef' : 'Membre'}${m.moi ? ' · toi' : ''}</small></div>
        <span class="clan-nb">${nbClan(m.communes)} communes</span>
        ${c.chef && !m.moi ? `<button class="bq-btn secondaire" data-clan-exclure="${m.id}">Exclure</button>` : '<span></span>'}
        ${act ? activiteClanHtml(act.get(m.id)) : ''}</div>`).join('');""",
"""    // patch252 : les bras droits
    const droits = c.droits || {};
    const nbBras = (c.membres || []).filter(m => m.bras_droit).length;
    const role = (m) => m.chef ? 'Chef' : m.bras_droit ? '<span class="clan-bd">Bras droit</span>' : 'Membre';
    const bouton = (m) => m.moi ? '<span></span>'
      : c.chef ? `<button class="bq-btn secondaire" data-clan-gerer="${m.id}" aria-expanded="${clanGere === m.id}">Gérer</button>`
      : (droits.exclure && !m.chef && !m.bras_droit) ? `<button class="bq-btn secondaire" data-clan-exclure="${m.id}">Exclure</button>` : '<span></span>';
    const gerer = (m) => {
      if(!c.chef || m.moi || clanGere !== m.id) return '';
      const d = m.droits || {};
      const exclure = `<button class="bq-btn secondaire danger" data-clan-exclure="${m.id}">Exclure du clan</button>`;
      const bascule = (cle, txt) => `<button type="button" class="filter-pill${d[cle] ? ' active' : ''}" aria-pressed="${!!d[cle]}" data-clan-droit="${cle}" data-clan-qui="${m.id}">${d[cle] ? '✓ ' : ''}${txt}</button>`;
      return `<div class="clan-gere">
        ${m.bras_droit
          ? `<div class="clan-gere-l"><span>Ses droits</span>${bascule('inviter', 'Inviter')}${bascule('exclure', 'Exclure des membres')}</div>
             <div class="clan-gere-l"><button type="button" class="bq-btn secondaire" data-clan-bras="${m.id}" data-actif="0">Retirer le rôle</button>${exclure}</div>`
          : nbBras >= 2 ? `<p class="clan-note">Tu as déjà 2 bras droits : retire le rôle à l'un d'eux pour nommer ce membre.</p><div class="clan-gere-l">${exclure}</div>`
          : `<div class="clan-gere-l"><button type="button" class="bq-btn" data-clan-bras="${m.id}" data-actif="1">Nommer bras droit</button>${exclure}</div><p class="clan-note">Un bras droit peut inviter ; tu choisis ensuite s'il peut aussi exclure.</p>`}
      </div>`;
    };
    const membres = (c.membres || []).map(m => `<div class="clan-membre"><span class="av" style="--clan:${c.couleur}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
        <div><b>${echapperTexte(m.pseudo)}</b><small>${role(m)}${m.moi ? ' · toi' : ''}</small></div>
        <span class="clan-nb">${nbClan(m.communes)} communes</span>
        ${bouton(m)}
        ${act ? activiteClanHtml(act.get(m.id)) : ''}${gerer(m)}</div>`).join('');""")

# 2. le champ « Inviter » : le chef, ou un bras droit qui en a le droit
s = rep(s, "${c.chef && n < 8 ? `<div class=\"clan-inviter\">", "${(c.chef || droits.inviter) && n < 8 ? `<div class=\"clan-inviter\">")

# 3. la règle
s = rep(s, "<li>Après avoir quitté un clan, il faut attendre 48 h avant d'en rejoindre un autre.</li>",
           "<li>Le chef peut nommer 2 bras droits et choisir leurs droits (inviter, exclure). Si le chef quitte le clan, un bras droit prend sa place.</li><li>Après avoir quitté un clan, il faut attendre 48 h avant d'en rejoindre un autre.</li>")

# 4. les clans dépliés (classement) : le badge aussi
s = rep(s, "${m.chef ? ' · <span class=\"cl-mb-chef\">Chef</span>' : ''}",
           "${m.chef ? ' · <span class=\"cl-mb-chef\">Chef</span>' : m.bras_droit ? ' · <span class=\"cl-mb-chef bd\">Bras droit</span>' : ''}")

# 5. l'état et les clics
s = rep(s, "let clanCache = null;\n", "let clanCache = null;\nlet clanGere = null;   // patch252 : le membre dont le chef ouvre la gestion\n")
s = rep(s, """  if(b.dataset.clanExclure){""",
"""  if(b.dataset.clanGerer){ clanGere = clanGere === b.dataset.clanGerer ? null : b.dataset.clanGerer; renderClan(); return; }   // patch252
  if(b.dataset.clanBras) return actionClan('clan_role', { p_joueur: b.dataset.clanBras, p_bras_droit: b.dataset.actif === '1', p_inviter: true, p_exclure: false },
                                           b.dataset.actif === '1' ? 'Bras droit nommé' : 'Rôle retiré');
  if(b.dataset.clanDroit){
    const m = ((clanCache.moi.clan || {}).membres || []).find(x => x.id === b.dataset.clanQui);
    const d = Object.assign({ inviter: true, exclure: false }, (m && m.droits) || {});
    d[b.dataset.clanDroit] = !d[b.dataset.clanDroit];
    return actionClan('clan_role', { p_joueur: b.dataset.clanQui, p_bras_droit: true, p_inviter: d.inviter, p_exclure: d.exclure }, 'Droits mis à jour');
  }
  if(b.dataset.clanExclure){""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch252 : bras droits du clan ---------- */
.clan-bd, .cl-mb-chef.bd{ color: var(--clan, #F0B429); font-weight:700; }
.clan-membre .clan-bd{ color:#F0B429; }
.clan-gere{ grid-column: 2 / -1; display:flex; flex-direction:column; gap:8px; padding:10px 12px; margin-top:2px;
  background: rgba(169,188,212,.06); border:1px solid rgba(169,188,212,.16); border-radius:10px; }
.clan-gere-l{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.clan-gere-l > span:first-child{ font-size:.8rem; color: var(--brume); margin-right:2px; }
.clan-gere .clan-note{ margin:0; }
.clan-gere .danger{ color:#F2A0A0; border-color:rgba(242,120,120,.4); }
"""
f.write_text(s, encoding='utf-8')
print('patch252 ok')
