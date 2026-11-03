# patch325 (3/11/2026) : d'où viennent les nouveaux (idée validée par Nataël)
# Au premier passage sur le site, le jeu retient la source dans la mémoire
# locale : ?src=… (ou ?utm_source=…), sinon « parrain » si ?ref=…, sinon le
# site d'où l'on vient (document.referrer), sinon « direct ». À l'arrivée
# dans le jeu d'un compte de moins de 14 jours, elle part avec l'étape
# « arrive » de la mesure de l'accueil (s2-86, colonne detail). Pas de SQL.
# Lien à mettre dans un post : https://terrafront.fr/?src=reddit
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

rep("""function onbAppareil(){""", """// patch325 : la source, retenue une fois, au tout premier passage (avant que l'adresse soit nettoyée)
(function onbSource(){
  try{
    if(localStorage.getItem('tf-src')) return;
    const q = new URLSearchParams(location.search);
    let src = q.get('src') || q.get('utm_source') || '';
    if(!src && q.get('ref')) src = 'parrain';
    if(!src && document.referrer){
      try{ const h = new URL(document.referrer).hostname.replace(/^www\\./, ''); if(h && h !== location.hostname) src = h; }catch(e){}
    }
    src = String(src || 'direct').toLowerCase().replace(/[^a-z0-9._-]/g, '').slice(0, 40) || 'direct';
    localStorage.setItem('tf-src', src);
  }catch(e){}
})();
function onbSourceLue(){ try{ return localStorage.getItem('tf-src') || 'inconnue'; }catch(e){ return 'inconnue'; } }
function onbAppareil(){""")

rep("""  onbDemarrer(session_); onbMarque('arrive');   // patch324""",
    """  onbDemarrer(session_); onbMarque('arrive', onbSourceLue());   // patch324, patch325 : la source""")

F.write_text(s, encoding='utf-8')
print('patch325 appliqué')
