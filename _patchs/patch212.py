# -*- coding: utf-8 -*-
u"""
patch212 — filtre Clans de la carte : tout le monde reste, le clan est un contour.
Idée de Maroli (Discord, 26 octobre). Aperçu validé par Nataël (« très bien ton idée »,
version C) : chaque joueur garde sa couleur ; un trait épais de la couleur du clan
fait le tour du territoire du clan (par l'extérieur, sans traits à l'intérieur).
De loin (départements), un département tenu par un membre de clan est cerclé
de la couleur du clan. Sans SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)

js = lire('app.js')
assert 'patch212' not in js

# 1. le filtre ne cache plus personne et ne repeint plus : il note le clan
js = rep(js, u"""  if(CLANS && CALQUES.clans){
    peindreClans(CV.donnees.joueurs);   // patch110
    // patch177 : le filtre Clans ne montre que les joueurs qui sont dans un clan
    const { liste, joueurs } = CV.donnees;
    for(const [id, j] of [...joueurs]){
      if(j.clan) continue;
      if(id === ID_MOI) j.nb = 0; else joueurs.delete(id);
    }
    CV.donnees.liste = liste.filter(e => { const j = joueurs.get(e.joueur); return j && j.clan; });
  }
""", u"""  // patch212 : le filtre Clans ne cache plus personne ; chaque joueur garde
  // sa couleur et le territoire du clan est cerclé de la couleur du clan
  if(CLANS && CALQUES.clans) peindreClans(CV.donnees.joueurs);   // patch110
""")
js = rep(js, u"""    if(!k) continue;
    j.couleur = k.couleur;
    j.fonce = couleurFoncee(k.couleur);
    j.clan = k.tag;
""", u"""    if(!k) continue;
    j.clanCouleur = k.couleur;   // patch212 : plus de repeinte, un contour
    j.clan = k.tag;
""")

# 2. de pres : un contour par clan, par l'exterieur du territoire
js = rep(js, u"""          if(etaitAMoi) perduPris.addPath(p);
          if(!parJoueur.has(c.joueur)) parJoueur.set(c.joueur, new Path2D());
          parJoueur.get(c.joueur).addPath(p);
""", u"""          if(etaitAMoi) perduPris.addPath(p);
          if(!parJoueur.has(c.joueur)) parJoueur.set(c.joueur, new Path2D());
          parJoueur.get(c.joueur).addPath(p);
          const jc = parClan && joueurs.get(c.joueur);   // patch212
          if(jc && jc.clan){
            if(!parClan.has(jc.clan)) parClan.set(jc.clan, { couleur: jc.clanCouleur, chemin: new Path2D() });
            parClan.get(jc.clan).chemin.addPath(p);
          }
""")
js = rep(js, u"""      const perduLibre = new Path2D();
      const perduPris = new Path2D();
""", u"""      const perduLibre = new Path2D();
      const perduPris = new Path2D();
      const parClan = CLANS && CALQUES.clans ? new Map() : null;   // patch212
""")
js = rep(js, u"""      // le lisere des communes reprises : trace apres les fonds, sinon la
      // couleur du nouveau proprietaire le recouvrirait
      if(passage){""", u"""      // patch212 : le tour du territoire de chaque clan, trace seulement a
      // l'exterieur (decoupe pair-impair) : pas de traits entre deux membres
      if(parClan) for(const { couleur, chemin } of parClan.values()){
        const dehors = new Path2D();
        dehors.rect(-MAP_W, -MAP_H, MAP_W * 3, MAP_H * 3);
        dehors.addPath(chemin);
        ctx.save();
        ctx.clip(dehors, 'evenodd');
        ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(9); ctx.stroke(chemin);
        ctx.strokeStyle = couleur; ctx.lineWidth = trait(6); ctx.stroke(chemin);
        ctx.restore();
      }
      // le lisere des communes reprises : trace apres les fonds, sinon la
      // couleur du nouveau proprietaire le recouvrirait
      if(passage){""")

# 3. de loin : departement tenu par un membre de clan, cercle de la couleur du clan
js = rep(js, u"""        ctx.globalAlpha = opaciteJoueur(info.joueur, info.force);
        ctx.fillStyle = j.couleur;
        ctx.fill(cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]));
        ctx.globalAlpha = 1;
""", u"""        ctx.globalAlpha = opaciteJoueur(info.joueur, info.force);
        ctx.fillStyle = j.couleur;
        const cd = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);
        ctx.fill(cd);
        ctx.globalAlpha = 1;
        if(CLANS && CALQUES.clans && j.clan){   // patch212
          ctx.save(); ctx.clip(cd);
          ctx.strokeStyle = j.clanCouleur; ctx.lineWidth = trait(7); ctx.stroke(cd);
          ctx.restore();
        }
""")
ecrire('app.js', js)
print('patch212 ok')
