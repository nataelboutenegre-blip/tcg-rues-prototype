# patch401 (10/11/2026) : un bandeau Discord en haut de l'onglet Clan : le même pseudo sur le Discord que dans
# le jeu, pour que le bot des clans ouvre le salon du clan et les salons de diplomatie (s2-135 : trouvé ou pas).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, """// patch400 : la diplomatie (s2-134)
const clanDiplo = { etat: null, choix: '', confirmer: null };""",
"""// patch401 : le bandeau Discord (s2-135) : 'trouve', 'introuvable' ou null (on ne sait pas)
let discordStatut = null;
async function chargerDiscordStatut(){
  try{ const { data, error } = await sb.rpc('discord_moi_statut'); discordStatut = error ? null : (data || null); }
  catch(e){ discordStatut = null; }
}
function bandeauDiscordClan(c){
  const moi = (c.membres || []).find(m => m.moi);
  const pseudo = moi && moi.pseudo ? `<b>«\u00a0${echapperTexte(moi.pseudo)}\u00a0»</b>` : 'ton pseudo du jeu';
  if(discordStatut === 'trouve') return `<div class="cd-bandeau ok">${ICONE_DISCORD}<p>Le bot des clans t’a trouvé sur le Discord : tu vois le salon de ton clan et ses salons de diplomatie.</p></div>`;
  const perdu = discordStatut === 'introuvable';
  return `<div class="cd-bandeau${perdu ? ' alerte' : ''}">${ICONE_DISCORD}<div>
    <p>${perdu ? '<b>Le bot des clans ne te trouve pas sur le Discord</b> : tu ne vois ni le salon de ton clan ni ses salons de diplomatie.'
                : 'Sur le Discord, le bot des clans t’ouvre le salon de ton clan et ses salons de diplomatie.'}
    L’idéal : <b>le même pseudo sur le Discord que dans le jeu</b> (${pseudo}). Un pseudo sur le serveur TerraFront suffit ; majuscules et accents ne comptent pas.${perdu ? ' Le bot repasse toutes les 10 minutes.' : ''}</p>
    <a class="cd-lien" href="${LIEN_DISCORD}" target="_blank" rel="noopener">Rejoindre le Discord</a></div></div>`;
}
// patch400 : la diplomatie (s2-134)
const clanDiplo = { etat: null, choix: '', confirmer: null };""")
rep(A, """  if(SAISON2) await Promise.all([chargerClanEch(), chargerClanDiplo()]);   // patch194, patch400""",
"""  if(SAISON2) await Promise.all([chargerClanEch(), chargerClanDiplo(), chargerDiscordStatut()]);   // patch194, patch400, patch401""")
rep(A, """      ${blocJour}
      ${candGererHtml(c)}   <!-- patch307 -->""", """      ${bandeauDiscordClan(c)}   <!-- patch401 -->
      ${blocJour}
      ${candGererHtml(c)}   <!-- patch307 -->""")
rep('style.css', "/* patch400 : la diplomatie */", """/* patch401 : le bandeau Discord de l'onglet Clan */
.cd-bandeau{ display:flex; gap:10px; align-items:flex-start; margin:12px 0 4px; padding:10px 12px; border-radius:12px;
  background:rgba(88,101,242,.12); border:1px solid rgba(88,101,242,.4); color:#DCE5F0; font-size:.8rem; line-height:1.45; }
.cd-bandeau > svg{ flex:none; width:22px; height:22px; color:#8E9BFF; margin-top:1px; }
.cd-bandeau p{ margin:0; }
.cd-bandeau b{ color:#fff; }
.cd-bandeau .cd-lien{ display:inline-block; margin-top:7px; padding:5px 11px; border-radius:999px; background:#5865F2; color:#fff; font-weight:700; font-size:.75rem; text-decoration:none; }
.cd-bandeau.alerte{ background:rgba(240,180,41,.12); border-color:rgba(240,180,41,.5); }
.cd-bandeau.alerte > svg{ color:#F0B429; }
.cd-bandeau.ok{ align-items:center; background:rgba(43,212,139,.08); border-color:rgba(43,212,139,.35); font-size:.76rem; }
.cd-bandeau.ok > svg{ color:#2BD48B; width:18px; height:18px; }
/* patch400 : la diplomatie */""")
print('patch401 ok')
