# patch484 : « Passer le flambeau » (idée d'Arkhannou), avec s3-42. Aperçu validé le 22/11 à 10 h 46.
# Dans « Gérer » d'un membre : le chef lui donne son titre sans quitter le clan, après confirmation.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, C = 'app.js', 'style.css'

rep(A, """<p class="clan-note">Un bras droit peut inviter ; tu choisis ensuite s'il peut aussi exclure ou modifier le clan.</p>`}
      </div>`;
    };""", """<p class="clan-note">Un bras droit peut inviter ; tu choisis ensuite s'il peut aussi exclure ou modifier le clan.</p>`}
        ${(() => {   // patch484 : passer le flambeau
          const autres = (c.membres || []).filter(x => x.bras_droit && x.id !== m.id).length;
          return `<div class="flb-sep"></div><div class="clan-gere-l"><button type="button" class="bq-btn secondaire" data-clan-flambeau="${m.id}">🔥 Lui passer le flambeau</button></div>
            <p class="clan-note">${echapperTexte(m.pseudo)} devient chef du clan. Toi, tu restes dans le clan ${autres >= 2 ? 'comme simple membre (il y a déjà 2 bras droits)' : 'comme bras droit, avec tous les droits'}.</p>`;
        })()}
      </div>`;
    };""")

rep(A, """  if(b.dataset.clanGerer){ clanGere = clanGere === b.dataset.clanGerer ? null : b.dataset.clanGerer; renderClan(); return; }   // patch252""",
"""  if(b.dataset.clanGerer){ clanGere = clanGere === b.dataset.clanGerer ? null : b.dataset.clanGerer; renderClan(); return; }   // patch252
  if(b.dataset.clanFlambeau) return clanFlambeauConfirmer(b.dataset.clanFlambeau);   // patch484""")

rep(A, """async function actionClan(nom, args, succes){""", """// patch484 : la confirmation avant de passer le flambeau
function clanFlambeauConfirmer(id){
  const c = (clanCache.moi && clanCache.moi.clan) || {};
  const m = (c.membres || []).find(x => x.id === id);
  if(!m) return;
  const autres = (c.membres || []).filter(x => x.bras_droit && x.id !== id).length;
  const nom = echapperTexte(m.pseudo || 'ce membre');
  const fermer = ouvrirFenetre(`
    <div class="fenetre flb-f" role="dialog" aria-modal="true" aria-labelledby="flbT">
      <h2 id="flbT">🔥 Passer le flambeau à ${nom} ?</h2>
      <p><b>${nom}</b> devient le chef de <b>${echapperTexte(c.nom || 'ton clan')}</b>.</p>
      <ul>
        <li>${autres >= 2 ? 'Tu restes dans le clan comme <b>simple membre</b> : il y a déjà 2 bras droits.' : 'Tu restes dans le clan comme <b>bras droit</b>, avec tous les droits (inviter, exclure, modifier le clan).'}</li>
        <li>Seul ${nom} pourra te rendre le titre.</li>
        <li>Le clan est prévenu dans son tchat.</li>
      </ul>
      <div class="flb-act"><button type="button" class="flb-non" data-flb="non">Annuler</button><button type="button" class="flb-ok" data-flb="oui">Passer le flambeau</button></div>
    </div>`);
  const boite = document.querySelector('#fenetre .flb-f');
  if(!boite) return;
  boite.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-flb]');
    if(!b) return;
    if(b.dataset.flb === 'non'){ fermer(null); return; }
    b.disabled = true;
    const ok = await actionClan('clan_passer_flambeau', { p_joueur: id }, `${m.pseudo || 'Ce membre'} est le nouveau chef`);
    if(ok){ clanGere = null; fermer(true); renderClan(); } else b.disabled = false;
  });
}
async function actionClan(nom, args, succes){""")

rep(C, """/* patch483 : « Autour de… » dans Attaquer */""", """/* patch484 : passer le flambeau */
.flb-sep{ height: 1px; background: rgba(169,188,212,.15); margin: 10px 0; }
.fenetre.flb-f{ max-width: 460px; text-align: left; }
.fenetre.flb-f h2{ margin: 0 0 8px; font-size: 1.2rem; }
.fenetre.flb-f p{ margin: 0 0 10px; color: #A9BCD4; line-height: 1.45; } .fenetre.flb-f p b, .fenetre.flb-f li b{ color: #F1F5F9; }
.fenetre.flb-f ul{ margin: 0 0 16px; padding-left: 18px; color: #A9BCD4; line-height: 1.5; font-size: .93rem; }
.flb-act{ display: flex; gap: 8px; }
.flb-act button{ flex: 1; font: inherit; font-weight: 700; border-radius: 12px; padding: 12px; cursor: pointer; }
.flb-ok{ background: #F0B429; color: #1A1404; border: 0; }
.flb-ok:disabled{ opacity: .6; }
.flb-non{ background: transparent; color: #F1F5F9; border: 1px solid rgba(169,188,212,.35); }
/* patch483 : « Autour de… » dans Attaquer */""")
print('patch484 : fini')
