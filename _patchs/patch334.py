# patch334 (3/11/2026) : une défense revient toutes les 24 h (idée de H34VEN, validée
# par Oshannir et Nataël), avec s2-93. Toujours deux défenses au plus par attaque.
# - Défense et tableau de bord : « deux défenses utilisées · une revient dans 7h »
#   (champ defense_revient de sieges_contre_moi ; sans lui, l'ancien texte) ;
# - Combat (côté attaquant) : « Le défenseur a utilisé ses deux défenses (une
#   revient dans 7h) » (colonne derniere_defense ; si elle manque, l'ancienne lecture) ;
# - Règles : la défense qui revient.
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')
H = pathlib.Path('index.html')
h = H.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

def reph(avant, apres, n=1):
    global h
    c = h.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    h = h.replace(avant, apres)

# 1. le texte « deux défenses utilisées », avec le retour de la prochaine
rep("""function formatDuree(ms){""", """// patch334 : une défense revient toutes les 24 h (s2-93)
function noteDefensesUtilisees(m){
  const t = m && m.defense_revient ? new Date(m.defense_revient).getTime() : 0;
  if(!t) return 'deux défenses utilisées';
  const reste = t - Date.now();
  return reste > 0 ? `deux défenses utilisées · une revient dans ${formatDuree(reste)}` : 'une défense revient';
}
function formatDuree(ms){""")
rep("""      action = m.defense_utilisee ? '<span class="df-note">deux défenses utilisées</span>'""",
    """      action = m.defense_utilisee ? `<span class="df-note">${noteDefensesUtilisees(m)}</span>`   // patch334""")
rep("""    const action = bouclier ? '' : m.defense_utilisee ? '<span class="mfo-note">deux défenses utilisées</span>'""",
    """    const action = bouclier ? '' : m.defense_utilisee ? `<span class="mfo-note">${noteDefensesUtilisees(m)}</span>`   // patch334""")

# 2. côté attaquant : quand une défense revient au défenseur
rep("""    .select('commune_code, victoires_consecutives, dernier_round, defense_utilisee')
    .eq('attacker_id', uid)
    .then(r => r.error""", """    .select('commune_code, victoires_consecutives, dernier_round, defense_utilisee, derniere_defense')   // patch334
    .eq('attacker_id', uid)
    .then(r => r.error ? sb.from('sieges').select('commune_code, victoires_consecutives, dernier_round, defense_utilisee').eq('attacker_id', uid) : r)
    .then(r => r.error""")
rep("""    if(victoires > 0 && siege && siege.defense_utilisee){
      note = 'Le défenseur a utilisé ses deux défenses';""", """    if(victoires > 0 && siege && siege.defense_utilisee){
      const rev = siege.derniere_defense ? new Date(siege.derniere_defense).getTime() + 86400000 - now : 0;   // patch334
      note = 'Le défenseur a utilisé ses deux défenses' + (rev > 0 ? ` (une revient dans ${formatDuree(rev)})` : '');""")

# 3. les règles
reph("""<p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense pour <b>1 énergie</b>, deux fois par attaque. Réussie, l'attaquant perd une victoire.</p>""",
     """<p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense pour <b>1 énergie</b>, deux fois par attaque. Une défense utilisée revient <b>24 h</b> plus tard (deux au plus). Réussie, l'attaquant perd une victoire.</p><!-- patch334 -->""")
reph("""<li>Tu as droit à <b>deux défenses par attaque</b>. Si la série de l'attaquant retombe à zéro, tu les récupères pour sa prochaine attaque.</li>""",
     """<li>Tu as droit à <b>deux défenses par attaque</b>. Une défense utilisée revient <b>24 h</b> après ta dernière défense, jusqu'à deux : une attaque laissée en plan peut toujours être repoussée. Si la série de l'attaquant retombe à zéro, tu les récupères toutes pour sa prochaine attaque.</li><!-- patch334 -->""")

F.write_text(s, encoding='utf-8')
H.write_text(h, encoding='utf-8')
print('patch334 appliqué')
