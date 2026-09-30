# -*- coding: utf-8 -*-
u"""
patch45 — Les photos reelles sur les cartes.

CE QUI CHANGE
  Quand une commune a une photo dans Supabase Storage, la carte l'affiche
  par-dessus le dessin de courbes de niveau. Sinon, le dessin reste seul :
  il n'y a jamais de trou, et les 33 000 cartes sans photo ne bougent pas
  d'un pixel.

  Deux endroits : la vignette de la Collection et la grande carte de la
  fiche. Pas la carte de Combat, qui n'a pas les colonnes photo dans sa
  requete — ce sera un second passage si tu le veux.

QUATRE PRECAUTIONS QUI NE SONT PAS OPTIONNELLES

  1. CHARGEMENT DIFFERE. Les vignettes pesent 65 Ko en moyenne, pas les
     30 Ko que j'avais estimes. Une Collection de 930 communes ferait
     60 Mo sans loading="lazy". Avec, le navigateur ne charge que ce qui
     approche de l'ecran.

  2. REPLI SUR ERREUR. Si une image manque ou ne se charge pas, onerror
     retire l'image ET son voile, et le dessin qui est deja dessous
     reapparait. Une carte cassee est pire qu'une carte sans photo.

  3. VOILE SEULEMENT SUR PHOTO. Le degrade du bas sert a garder le numero
     de departement lisible sur une photo claire. Il est emis par le JS
     avec l'image, pas pose en CSS sur toutes les cartes : sinon les
     cartes sans photo changeraient d'aspect pour rien.

  4. ATTRIBUTION. 778 des 1 007 premieres photos sont en CC BY-SA :
     citer l'auteur, la licence et la source est une obligation legale.
     Elle est affichee en bas de la fiche, avec un lien vers la page
     Commons de l'image.

REPLI SI LE SQL N'EST PAS PASSE
  Les colonnes photo* sont demandees dans une variante de requete
  supplementaire. Si elles n'existent pas encore, le client retombe sur
  la requete actuelle et tout fonctionne comme avant.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- 1. l'URL d'une photo, et l'art d'une carte ----------------------------
js = rempl(js,
u"""function miniArtSvg(code, tierId){""",
u"""// Le bucket « communes » est public : l'adresse se compose a partir de
// celle du projet, que le client connait deja.
const urlPhoto = (fichier) => fichier
  ? SUPABASE_URL + '/storage/v1/object/public/communes/' + fichier
  : null;

// L'art d'une carte : la photo si on l'a, le dessin sinon. Le dessin reste
// EN DESSOUS de l'image, pas a la place : si le chargement echoue, onerror
// retire l'image et son voile, et le dessin reapparait sans trou ni saut
// de mise en page.
function artCommune(e, tierId, taille){
  const dessin = (taille === 'grande' ? carteArtSvg : miniArtSvg)(e.code, tierId);
  const u = urlPhoto(e && e.photo);
  if(!u) return dessin;
  return dessin
    + `<img class="art-photo" src="${echapperTexte(u)}" alt="" loading="lazy"`
    + ` decoding="async" onerror="this.nextElementSibling&&this.nextElementSibling.remove();this.remove()">`
    + `<span class="art-voile"></span>`;
}

// L'attribution, obligatoire pour les licences CC BY et CC BY-SA.
function creditPhoto(e){
  if(!e || !e.photo || !e.photoAuteur) return '';
  const licence = e.photoLicence ? ' · ' + echapperTexte(e.photoLicence) : '';
  const texte = 'Photo : ' + echapperTexte(e.photoAuteur) + licence;
  return e.photoSource
    ? `<p class="carte-credit"><a href="${echapperTexte(e.photoSource)}" target="_blank" rel="noopener">${texte}</a></p>`
    : `<p class="carte-credit">${texte}</p>`;
}

function miniArtSvg(code, tierId){""",
u'urlPhoto, artCommune et creditPhoto')

# --- 2. la requete demande les colonnes, avec repli ------------------------
js = rempl(js,
u"""  const champsCommune = 'communes(code,nom,departement,population,latitude,longitude,tier,rang,palier_total)';""",
u"""  // du plus complet au plus simple, ici aussi : tant que photos-colonnes.sql
  // n'est pas passe, la seconde variante fait tourner le site comme avant
  const CHAMPS_COMMUNE = [
    'communes(code,nom,departement,population,latitude,longitude,tier,rang,palier_total,photo,photo_auteur,photo_licence,photo_source)',
    'communes(code,nom,departement,population,latitude,longitude,tier,rang,palier_total)',
  ];""",
u'champs commune avec photo')

js = rempl(js,
u"""  let data = null, error = null;
  for(const champs of variantes){
        ({ data, error } = await toutesLesLignes(() => sb
      .from('possessions').select(champs + champsCommune).eq('joueur_id', uid)));
    if(!error) break;
  }
  if(error){ console.error(error); return; }""",
u"""  let data = null, error = null;
  boucle:
  for(const champsCommune of CHAMPS_COMMUNE){
    for(const champs of variantes){
      ({ data, error } = await toutesLesLignes(() => sb
        .from('possessions').select(champs + champsCommune).eq('joueur_id', uid)));
      if(!error) break boucle;
    }
  }
  if(error){ console.error(error); return; }""",
u'boucle sur les deux jeux de champs')

js = rempl(js,
u"""      conquiseLe: row.conquise_le ? new Date(row.conquise_le).getTime() : 0,
      etiquette: row.etiquette || ''
    });""",
u"""      conquiseLe: row.conquise_le ? new Date(row.conquise_le).getTime() : 0,
      etiquette: row.etiquette || '',
      photo: c.photo || '', photoAuteur: c.photo_auteur || '',
      photoLicence: c.photo_licence || '', photoSource: c.photo_source || ''
    });""",
u'les colonnes photo dans collectionMap')

# --- 3. la vignette de la Collection ---------------------------------------
js = rempl(js,
u"""        <div class="mini-art">${miniArtSvg(entry.code, entry.tier.id)}<span class="mini-dept">""",
u"""        <div class="mini-art">${artCommune(entry, entry.tier.id)}<span class="mini-dept">""",
u'photo sur la vignette')

# --- 4. la grande carte de la fiche ----------------------------------------
js = rempl(js,
u"""              <div class="carte-art">${carteArtSvg(entry.code, tier.id)}<span class="carte-dept">${echapperTexte(entry.dept)}</span></div>""",
u"""              <div class="carte-art">${artCommune(entry, tier.id, 'grande')}<span class="carte-dept">${echapperTexte(entry.dept)}</span></div>""",
u'photo sur la fiche')

# --- 5. le credit, en bas du corps de la fiche ------------------------------
js = rempl(js,
u"""          <div class="fc-etiq-sugg">${suggestionsEtiquette(entry)}</div>
        </div>`}
      </div>
    </div>`);""",
u"""          <div class="fc-etiq-sugg">${suggestionsEtiquette(entry)}</div>
        </div>`}
        ${creditPhoto(entry)}
      </div>
    </div>`);""",
u'credit photo en bas de la fiche')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .ct-avert{ font-size:0.75rem; color:#7F91AB; text-align:center; margin:9px 0 0; line-height:1.5; }""",
u"""  /* ---------- Les photos des communes ---------- */
  /* L'image se pose PAR-DESSUS le dessin, qui reste en place dessous. Si
     elle ne charge pas, onerror la retire et le dessin est deja la : pas
     de trou, pas de saut de mise en page.
     L'image et le voile sont emis par le JS uniquement quand il y a une
     photo : une carte sans photo garde exactement l'aspect d'avant. */
  .art-photo{
    position:absolute; inset:0; width:100%; height:100%;
    object-fit:cover; display:block; border:0; z-index:1;
  }
  /* Le degrade fait deux choses. Il garde le numero de departement lisible
     sur une photo claire, et il REMET LA COULEUR DE RARETE : sans lui, une
     carte a photo perd le bleu ou le vert qui la fait reconnaitre d'un coup
     d'oeil dans la grille, et toutes les cartes se ressemblent. */
  .art-voile{
    position:absolute; inset:0; z-index:2; pointer-events:none;
    background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(10,22,41,0.62) 100%);
  }
  .mini.commun     .art-voile, .fiche.commun     .art-voile{ background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(126,139,160,0.72) 100%); }
  .mini.peucommun  .art-voile, .fiche.peucommun  .art-voile{ background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(18,110,72,0.78) 100%); }
  .mini.rare       .art-voile, .fiche.rare       .art-voile{ background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(28,84,178,0.80) 100%); }
  .mini.legendaire .art-voile, .fiche.legendaire .art-voile{ background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(156,112,18,0.80) 100%); }
  /* sur une photo, le numero de departement en blanc a 28 % disparait */
  .mini-art:has(.art-photo) .mini-dept,
  .carte-art:has(.art-photo) .carte-dept{
    color:rgba(255,255,255,0.62); text-shadow:0 1px 4px rgba(10,22,41,0.55);
  }
  /* la pastille du departement, le bouclier, l'etiquette : au-dessus de tout.
     Le dessin SVG est volontairement exclu, sinon il repasserait devant la
     photo. */
  .mini-art  > *:not(svg):not(.art-photo):not(.art-voile),
  .carte-art > *:not(svg):not(.art-photo):not(.art-voile){ z-index:3; }

  .carte-credit{
    margin:12px 0 0; font-size:0.62rem; line-height:1.35; color:#7F91AB;
    text-align:center;
  }
  .carte-credit a{ color:inherit; text-decoration:underline; text-underline-offset:2px; }
  .carte-credit a:hover{ color:#fff; }

  .ct-avert{ font-size:0.75rem; color:#7F91AB; text-align:center; margin:9px 0 0; line-height:1.5; }""",
u'styles des photos')

ecrire('style.css', css)

print(u'patch45 applique.')
