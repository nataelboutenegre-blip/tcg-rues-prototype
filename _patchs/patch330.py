# patch330 (3/11/2026) : saison 3, la Suisse — les fondations, éteintes.
# Rien ne change pour les joueurs tant que SUISSE_OUVERTE vaut false.
# ?suisse=test les allume dans cet onglet (essai privé, comme ?brillantes=test).
# - les 26 cantons : noms (bulles, badges), nombre de communes, région « Suisse » ;
# - un seul test de zone de la carte (métropole, plus les cantons quand la
#   Suisse est ouverte) à la place des 5 filtres METRO_DEPT_RE : sans lui, les
#   communes suisses n'apparaîtraient pas sur la carte du Front ;
# - le département d'une commune suisse se lit dans ses données et plus dans les
#   deux premiers caractères du code (« CH6621 » donnerait « CH ») ;
# - Plus ou moins : l'est des Grisons (> 10 °E) n'est plus pris pour l'outre-mer.
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

# 1. l'interrupteur, les cantons, le test de zone
rep("""const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;
""", """const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;
// patch330 : la Suisse (saison 3). Éteinte tant que SUISSE_OUVERTE vaut false ;
// ?suisse=test l'allume dans cet onglet pour essayer. Les cantons tiennent le
// rôle des départements (code à deux lettres, région « Suisse »).
const SUISSE_OUVERTE = false;
const SUISSE = SUISSE_OUVERTE || (() => {
  try {
    if(/[?&]suisse=test\\b/.test(location.search)) sessionStorage.setItem('tf-suisse-test', '1');
    return sessionStorage.getItem('tf-suisse-test') === '1';
  } catch(e){ return /[?&]suisse=test\\b/.test(location.search); }
})();
const CANTONS = {"AG":"Argovie","AI":"Appenzell Rhodes-Intérieures","AR":"Appenzell Rhodes-Extérieures","BE":"Berne","BL":"Bâle-Campagne","BS":"Bâle-Ville","FR":"Fribourg","GE":"Genève","GL":"Glaris","GR":"Grisons","JU":"Jura","LU":"Lucerne","NE":"Neuchâtel","NW":"Nidwald","OW":"Obwald","SG":"Saint-Gall","SH":"Schaffhouse","SO":"Soleure","SZ":"Schwytz","TG":"Thurgovie","TI":"Tessin","UR":"Uri","VD":"Vaud","VS":"Valais","ZG":"Zoug","ZH":"Zurich"};
const CANTON_RE = /^(AG|AI|AR|BE|BL|BS|FR|GE|GL|GR|JU|LU|NE|NW|OW|SG|SH|SO|SZ|TG|TI|UR|VD|VS|ZG|ZH)$/;
const estCanton = (dep) => CANTON_RE.test(String(dep || ''));
// la zone dessinée sur la carte de France (outre-mer à part, dans son encart)
const estZoneCarte = (dep) => METRO_DEPT_RE.test(dep) || (SUISSE && estCanton(dep));
if(SUISSE) Object.assign(DEPT_NAMES, CANTONS);
""")

# 2. les filtres de la carte et de la légende
rep("""    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
""", """    if(!estZoneCarte(e.dept) || e.lat == null) continue;   // patch330
""", 4)
rep("""    if(!METRO_DEPT_RE.test(e.dept)) return;
""", """    if(!estZoneCarte(e.dept)) return;   // patch330
""")

# 3. le département d'une commune suisse se lit dans ses données
rep("""const depDuCode = (cc) => { cc = String(cc || ''); return cc.startsWith('97') ? cc.slice(0, 3) : cc.slice(0, 2); };""",
    """const depDuCode = (cc) => {
  cc = String(cc || '');
  if(/^CH\\d/.test(cc)){   // patch330 : « CH6621 » -> le canton, lu dans les données
    const r = CARTE.cat && CARTE.cat.get(cc);
    const e = collectionMap.get(cc) || othersMap.get(cc);
    return (r && r[2]) || (e && e.dept) || '';
  }
  return cc.startsWith('97') ? cc.slice(0, 3) : cc.slice(0, 2);
};""")
rep("""${badgeDept(cc.startsWith('97') ? cc.slice(0, 3) : cc.slice(0, 2))}""", """${badgeDept(depDuCode(cc))}""")
rep("""      const dep = code.startsWith('97') ? code.slice(0, 3) : code.slice(0, 2);   // patch267""",
    """      const dep = depDuCode(code);   // patch267, patch330""")

# 4. la région « Suisse » (titres, frontières de région, bulles)
rep("""  '83':"Provence-Alpes-Côte d'Azur",'84':"Provence-Alpes-Côte d'Azur",
};
""", """  '83':"Provence-Alpes-Côte d'Azur",'84':"Provence-Alpes-Côte d'Azur",
};
if(SUISSE) for(const c in CANTONS) DEP_REGION[c] = 'Suisse';   // patch330
""")

# 5. le nombre de communes de chaque canton (parts de la carte, Ma France)
rep("""  .split(',').map(x => { const [d, n] = x.split(':'); return [d, Number(n)]; }));
""", """  .split(',').map(x => { const [d, n] = x.split(':'); return [d, Number(n)]; }));
// patch330 : les cantons (swissBOUNDARIES3D 2026)
if(SUISSE) 'AG:196,AI:5,AR:20,BE:334,BL:86,BS:3,FR:119,GE:45,GL:3,GR:100,JU:51,LU:79,NE:24,NW:11,OW:7,SG:75,SH:26,SO:104,SZ:30,TG:80,TI:100,UR:19,VD:300,VS:122,ZG:11,ZH:160'
  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });
""")

# 6. Plus ou moins : la Suisse va jusqu'à 10,5 °E, l'outre-mer est bien plus loin
rep("""+c.lon < -5.6 || +c.lon > 10; }""", """+c.lon < -5.6 || +c.lon > 10.6; }   // patch330 : les Grisons""")

F.write_text(s, encoding='utf-8')
print('patch330 appliqué')
