# patch528 (idée d'Arkhannou) : un siège dont l'énergie en attente suffit se voit (s3-67 : 'suffit', 'attente').
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# 1. les aides
rep('app.js', "function sgEstPourquoi(v){\n  const m = ",
"""function sgSuffit(v){ return !!(v && v.en_cours && v.suffit); }   // patch528
function sgSuffitMaj(art, v){   // patch528 : la carte, le bouton et la ligne d'explication suivent
  if(!art) return;
  const ok = sgSuffit(v);
  art.classList.toggle('ca-ok', ok);
  const lib = art.querySelector('.ca-att[data-action="assieger"] .ca-lib');
  if(lib) lib.textContent = ok ? 'Énergie suffisante' : (v && v.en_cours ? 'Continuer' : 'Assiéger');
}
function sgEstPourquoi(v){
  if(sgSuffit(v)) return `<span class="p">${Number(v.attente) || 0} ⚡ en attente : ça devrait suffire</span>`;   // patch528
  const m = """)

# 2. la carte construite
rep('app.js', """bouton = `<button class="cible-attaquer ca-att" data-action="assieger" data-code="${c.commune_code}">${vrai && vrai.en_cours ? 'Continuer' : 'Assiéger'} <span class="ca-pastille\"""",
"""bouton = `<button class="cible-attaquer ca-att" data-action="assieger" data-code="${c.commune_code}"><span class="ca-lib">${sgSuffit(vrai) ? 'Énergie suffisante' : vrai && vrai.en_cours ? 'Continuer' : 'Assiéger'}</span> <span class="ca-pastille\"""")
rep('app.js', """    return `<article class="ca-cible">${carte}""",
"""    const okSg = SIEGE && etatClasse === 'pret' && sgSuffit(sgEstLu(c.commune_code));   // patch528
    return `<article class="ca-cible${okSg ? ' ca-ok' : ''}">${SIEGE ? '<span class="ca-ok-b">✓ ça suffit</span>' : ''}${carte}""")

# 3. quand l'estimation arrive
rep('app.js', """      grid.querySelectorAll(`[data-sg-pq="${CSS.escape(k)}"]`).forEach(e => { e.innerHTML = sgEstPourquoi(v); });
    }""",
"""      grid.querySelectorAll(`[data-sg-pq="${CSS.escape(k)}"]`).forEach(e => { e.innerHTML = sgEstPourquoi(v); sgSuffitMaj(e.closest('.ca-cible'), v); });   // patch528
    }""")

# 4. tri « moins d'énergie » : rien à faire → après les vraies cibles
rep('app.js', "return v && v.e < 9999 ? -v.e : -1e6; }", "return v && v.e < 9999 ? (sgSuffit(v) ? -5000 : -v.e) : -1e6; }")

# 5. le style
rep('style.css', ".ca-est .m{ color:#FF8A8F; } .ca-est .p{ color:#3DD68C; }",
""".ca-est .m{ color:#FF8A8F; } .ca-est .p{ color:#3DD68C; }
/* patch528 : l'énergie en attente suffit */
.ca-cible{ position:relative; }
.ca-ok-b{ display:none; }
.ca-cible.ca-ok .ca-ok-b{ display:block; position:absolute; z-index:3; top:8px; left:50%; transform:translateX(-50%); background:#3DD68C; color:#0B2A1A;
  font-family:var(--texte); font-size:.66rem; font-weight:700; padding:2px 8px; border-radius:999px; white-space:nowrap; pointer-events:none; }
.ca-cible.ca-ok > .mini{ box-shadow:0 0 0 2px #3DD68C; }
.ca-cible.ca-ok .cible-attaquer.ca-att{ background:transparent; color:#7FE0AE; box-shadow:inset 0 0 0 1.5px #3DD68C; font-family:var(--texte); font-size:.78rem; font-weight:700; letter-spacing:0; white-space:nowrap; }
.ca-cible.ca-ok .ca-att .ca-pastille{ display:none; }""")

p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-24'
l = "✅ Front : quand l'énergie déjà en attente suffit pour prendre la commune, la carte passe en vert « Énergie suffisante ». Plus besoin de relancer pour rien (merci Arkhannou)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
