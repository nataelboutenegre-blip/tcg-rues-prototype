# patch386 : les 4 volets de Combat élargissaient la page sur téléphone quand le texte est agrandi
# (Arkhannou, Android, 8/11 20 h 37 : la page dépassait à droite, la fenêtre d'assaut était coupée).
# Reproduit au banc : texte à 115 %, écran de 360 px -> page de 391 px.
# - taille du texte des volets bornée par la largeur de l'écran (min(rem, vw)) : l'agrandissement
#   du texte d'Android ne les élargit plus ;
# - les volets peuvent rétrécir (min-width:0), la pastille rapetisse ;
# - filet de sécurité : si ça ne tient toujours pas, la rangée défile sur elle-même au lieu
#   d'élargir la page.
import pathlib

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch386' not in c
c += """
/* patch386 : les volets de Combat tiennent toujours dans l'écran (texte agrandi sur Android) */
#panel-combat .volets, #panel-defense .volets, #panel-batiments .volets{ max-width:100%; box-sizing:border-box; overflow-x:auto; scrollbar-width:none; }
#panel-combat .volets::-webkit-scrollbar, #panel-defense .volets::-webkit-scrollbar, #panel-batiments .volets::-webkit-scrollbar{ display:none; }
@media (max-width: 720px){
  #panel-combat .volet, #panel-defense .volet, #panel-batiments .volet{ min-width:0; font-size:min(.92rem, 3.7vw); padding-left:min(8px, 1.6vw); padding-right:min(8px, 1.6vw); gap:4px; }
  #panel-combat .volet-badge, #panel-defense .volet-badge, #panel-batiments .volet-badge{ min-width:min(16px, 4.4vw); height:min(16px, 4.4vw); padding:0 3px; font-size:min(.62rem, 2.6vw); }
}
"""
C.write_text(c, encoding='utf-8')
print('patch386 ok')
