# patch469 : les cinq thèmes de la saison 3 se vendent en collection (skin + dos assorti), plus à l'unité.
# Décision de Nataël (19/11/2026). Avant le 22, sur l'appareil où ?topo=test est posé, la boutique montrait les
# cinq skins en aperçu : elle montre maintenant les cinq collections (en tête, aperçu seul, pas d'achat).
# Les articles existent en base depuis _sql/s3-36 (non visibles) ; mise en vente : _jour-j/s3-jj-4b-skins.sql.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'app.js'); t = open(p, encoding='utf-8').read()
if 'COLLECTIONS_S3_APERCU' in t: print('app.js : déjà fait'); raise SystemExit
a0 = t.index("// patch454 : les cinq skins de la saison 3 arrivent en boutique le 22/11")
a1 = t.index("function renderBoutiqueEuros(){")
assert 0 < a0 < a1 and a1 - a0 < 2500, (a0, a1)
neuf = """// patch454, patch469 : les cinq thèmes de la saison 3 arrivent en boutique le 22/11, en collections (le skin et son dos
// assorti, lignes euros_articles du jour J). Avant, sur l'appareil où ?topo=test est posé, la boutique les montre déjà,
// en aperçu seul (pas d'achat).
const COLLECTIONS_S3_APERCU = [
  { id: 'pack-topo', nom: 'Collection Topo', description: 'Le dos et le skin Topo', prix_centimes: 649, contenu: ['dos-topo', 'skin-topo'] },
  { id: 'pack-givre', nom: 'Collection Givre', description: 'Le dos et le skin Givre', prix_centimes: 599, contenu: ['dos-givre', 'skin-givre'] },
  { id: 'pack-kintsugi', nom: 'Collection Kintsugi', description: 'Le dos et le skin Kintsugi', prix_centimes: 699, contenu: ['dos-kintsugi', 'skin-kintsugi'] },
  { id: 'pack-vitrail', nom: 'Collection Vitrail', description: 'Le dos et le skin Vitrail', prix_centimes: 649, contenu: ['dos-vitrail', 'skin-vitrail'] },
  { id: 'pack-aquarelle', nom: 'Collection Aquarelle', description: 'Le dos et le skin Aquarelle', prix_centimes: 599, contenu: ['dos-aquarelle', 'skin-aquarelle'] }];
function bqeApercusS3(cat){
  let test = false; try{ test = localStorage.getItem('tf-topo') === '1'; }catch(e){}
  if(!test || !cat || !Array.isArray(cat.articles)) return;
  const manque = COLLECTIONS_S3_APERCU.filter(a => !cat.articles.some(x => x.id === a.id));
  cat.articles.unshift(...manque.map(a => ({ ...a, type: 'collection', prix_moi: a.prix_centimes, actif: true, reserve_og: false, apercu: true })));
}
"""
open(p, 'w', encoding='utf-8').write(t[:a0] + neuf + t[a1:]); print('app.js : ok')
