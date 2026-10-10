# -*- coding: utf-8 -*-
u"""
patch109 — ordinateur : la colonne de gauche devient un rail à boussole.

Pour s'éloigner du menu de WikiMasters (colonne large, libellés, pastille
sur l'onglet actif). Uniquement sur ordinateur avec une souris : le
téléphone et les tablettes tactiles ne changent pas.

- Rail de 76 px avec toutes les icônes ; au survol (ou au clavier), il
  glisse à 236 px et montre les libellés PAR-DESSUS la page, sans la décaler.
- Le Tirage devient une boussole ronde, dorée, en haut du rail.
- L'onglet actif est marqué par l'aiguille dorée (un triangle), plus par un
  fond coloré.
- Le logo se réduit à « TF » rail fermé ; Discord, déconnexion et liens
  légaux réapparaissent rail ouvert.
CSS seulement. Aucun SQL.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

css = lire('style.css')
assert 'patch109' not in css, u'patch109 deja applique'
css += u"""
/* ---------- patch109 : rail à boussole sur ordinateur ---------- */
@media (min-width: 721px) and (hover: hover){
  .app-shell{ padding-left: 76px; }
  .sidebar{
    position: fixed; left:0; top:0; bottom:0; height:100vh; z-index: 60;
    width: 76px; padding: 16px 8px 12px;
    overflow-x: hidden; overflow-y: auto; scrollbar-width: none;
    background: #0b1830;
    transition: width .22s ease, box-shadow .22s ease;
  }
  .sidebar::-webkit-scrollbar{ display:none; }
  .sidebar:hover, .sidebar:focus-within{ width: 236px; box-shadow: 14px 0 34px rgba(0,0,0,.45); }

  /* logo : « TF » rail fermé, le nom complet rail ouvert */
  .sidebar-top{ flex-direction:column; align-items:flex-start; gap:10px; }
  .sidebar .brand{ font-size:0; padding: 0 0 0 12px; flex:none; white-space:nowrap; }
  .sidebar .brand::before{ content:'T'; font-size:1.7rem; }
  .sidebar .brand span{ font-size:0; }
  .sidebar .brand span::before{ content:'F'; font-size:1.7rem; }
  .sidebar:hover .brand, .sidebar:focus-within .brand{ font-size:1.7rem; }
  .sidebar:hover .brand::before, .sidebar:focus-within .brand::before,
  .sidebar:hover .brand span::before, .sidebar:focus-within .brand span::before{ content:none; }
  .sidebar:hover .brand span, .sidebar:focus-within .brand span{ font-size:inherit; }
  .sidebar .regles-btn{ margin: 0 0 0 14px; }

  /* les onglets : icône seule, libellé quand le rail est ouvert */
  .tabs-row{ margin-top: 10px; gap: 2px; }
  .tab{ font-size:0; white-space:nowrap; padding: 12px 0 12px 20px; gap: 14px; border-radius:10px; }
  .sidebar:hover .tab, .sidebar:focus-within .tab{ font-size:.95rem; }
  .tab:hover{ background: rgba(169,188,212,0.08); }
  .tab.active{ background: none; }
  .tab.active::before{
    left: 2px; top: 50%; bottom:auto; width:0; height:0; border-radius:0; background:none;
    transform: translateY(-50%);
    border-top: 6px solid transparent; border-bottom: 6px solid transparent;
    border-left: 9px solid var(--c-legendaire);
  }
  /* pastilles : petit rond sur l'icône rail fermé */
  .tab .tab-badge{ font-size:.66rem; position:absolute; left:36px; top:5px; min-width:17px; height:17px; padding:0 4px; margin:0; }
  .sidebar:hover .tab .tab-badge, .sidebar:focus-within .tab .tab-badge{ position:static; margin-left:auto; margin-right:10px; }

  /* le Tirage devient la boussole */
  .tab[data-tab="tirage"]{
    width:56px; height:56px; padding:0; margin: 4px 0 10px 2px; border-radius:50%;
    justify-content:center; color: var(--c-legendaire); overflow:visible;
    background: radial-gradient(circle, #1F3A60, #0F1F38);
    border: 3px solid var(--c-legendaire);
    box-shadow: 0 0 0 4px #0b1830, 0 6px 16px rgba(0,0,0,.45);
  }
  .tab[data-tab="tirage"]::after{
    content:''; position:absolute; inset:5px; border-radius:50%;
    border:1px dashed rgba(240,180,41,.5); pointer-events:none;
  }
  .tab[data-tab="tirage"] .icon, .tab[data-tab="tirage"] .icon svg{ width:24px; height:24px; color: var(--c-legendaire); }
  .tab[data-tab="tirage"]:hover{ background: radial-gradient(circle, #27497A, #13284A); }
  .tab[data-tab="tirage"].active{ box-shadow: 0 0 0 4px #0b1830, 0 0 18px 2px rgba(240,180,41,.45); }
  .tab[data-tab="tirage"].active::before{ left:-8px; }
  /* le libellé « Tirage » sort de la boussole, rail ouvert */
  .sidebar:hover .tab[data-tab="tirage"], .sidebar:focus-within .tab[data-tab="tirage"]{ font-size:0; }
  .sidebar:hover .tab[data-tab="tirage"]::after, .sidebar:focus-within .tab[data-tab="tirage"]::after{ content:'Tirage'; inset:auto; left:72px; border:0; font-size:.95rem; color:#fff; white-space:nowrap; }

  /* le bas du rail */
  .sidebar-footer{ padding: 12px 0 2px; font-size:0; }
  .sidebar-footer .lien-discord{ font-size:0; justify-content:center; padding:9px 0; width:44px; margin: 0 0 6px 8px; }
  .sidebar-footer .lien-discord svg{ width:18px; height:18px; }
  .sidebar-footer #whoami, .sidebar-footer .link-btn, .sidebar-footer .liens-legaux{ display:none; }
  .sidebar:hover .sidebar-footer, .sidebar:focus-within .sidebar-footer{ font-size:.75rem; padding: 12px 10px 2px; }
  .sidebar:hover .sidebar-footer .lien-discord, .sidebar:focus-within .sidebar-footer .lien-discord{ font-size:.8rem; justify-content:flex-start; width:auto; padding:7px 10px; margin: 0 0 10px; }
  .sidebar:hover .sidebar-footer #whoami, .sidebar:focus-within .sidebar-footer #whoami,
  .sidebar:hover .sidebar-footer .link-btn, .sidebar:focus-within .sidebar-footer .link-btn{ display:block; }
  .sidebar:hover .sidebar-footer .liens-legaux, .sidebar:focus-within .sidebar-footer .liens-legaux{ display:block; white-space:normal; }
}
@media (min-width: 721px) and (hover: hover) and (prefers-reduced-motion: reduce){
  .sidebar{ transition:none; }
}
"""
ecrire('style.css', css)
print(u'patch109 applique')
