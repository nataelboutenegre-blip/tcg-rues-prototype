// TerraFront — fonction Edge « discord-clans » (2 novembre 2026)
//
// Tient le Discord à jour avec les clans du jeu, toute seule (pg_cron l'appelle
// toutes les 10 minutes, voir _discord/clans-auto.sql). Même travail que
// _discord/clans-discord.py, qu'il fallait lancer à la main :
//  - catégorie « 🏰 Clans » et salon public « 🏰│recrutement-clans » ;
//  - pour chaque clan : un rôle « 🏰 [SIGLE] Nom » à la couleur du clan et un
//    salon privé que seuls ses membres (et le bot) voient ;
//  - donne le rôle aux membres présents sur le Discord, le retire à ceux qui
//    ont quitté le clan ;
//  - seuls les membres du clan (par leur rôle) et le bot voient le salon :
//    tout accès à son nom y est retiré (décision du 4/11 : un ancien chef ou
//    un ancien membre gardait l'accès et pouvait encore écrire ; le chef ne
//    peut donc plus inviter quelqu'un d'extérieur) ;
//  - clan dissous : son rôle est vidé (plus personne ne voit le salon), le
//    salon reste (à supprimer à la main).
// Un pseudo du jeu est reconnu sur le Discord par son nom d'utilisateur, son
// nom affiché ou son pseudo de serveur (majuscules, accents et ponctuation
// ignorés), ou par la table discord_correspondances.
//
// Modes (dans le corps de l'appel) : « simulation » (rien ne change, le journal
// dit ce qui serait fait) ou « actif ». Chaque passage écrit une ligne dans
// discord_sync_journal.
//
// Secret à définir dans Supabase (Edge Functions > Secrets) :
//   DISCORD_BOT_TOKEN   le jeton du bot TerraFront (le même que ~/.terrafront-bot)
// Facultatif : DISCORD_GUILD_ID (sinon le bot doit être sur un seul serveur).
//
// Déploiement : vérification du JWT DÉSACTIVÉE (l'appel est protégé par
// l'en-tête x-clans-secret, comparé à la base).

const API = "https://discord.com/api/v10";
const CATEGORIE = "🏰 Clans";
const PUBLIC = "🏰│recrutement-clans";
const PUBLIC_SUJET = "Tu cherches un clan ou des membres ? Présente-toi : sigle, nom du clan, ce que vous visez sur le Front. 8 membres au plus par clan.";
const PREFIXE_ROLE = "🏰 [";
const VOIR = 0x400n, ECRIRE = 0x800n, GERER_MSG = 0x2000n, LIENS = 0x4000n, FICHIERS = 0x8000n, HISTORIQUE = 0x10000n, REACTIONS = 0x40n;
const DROITS_MEMBRE = VOIR | ECRIRE | LIENS | FICHIERS | HISTORIQUE | REACTIONS;
const DROITS_BOT = VOIR | ECRIRE | GERER_MSG | HISTORIQUE;

export type Clan = { tag: string; nom: string; couleur?: string | null; chef?: string | null; membres: string[] };
type Fetch = (url: string, init?: RequestInit) => Promise<Response>;
export type Options = {
  jeton: string;
  clans: Clan[];
  correspondances?: Record<string, string>;
  simulation: boolean;
  guildId?: string | null;
  fetchFn?: Fetch;
  pause?: (ms: number) => Promise<void>;
};
export type Rapport = { actions: string[]; avertissements: string[]; introuvables: string[]; erreurs: string[] };

export function cle(nom: string | null | undefined): string {
  return (nom ?? "").normalize("NFD").toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
}
export function nomSalon(c: Clan): string {
  const base = c.nom.normalize("NFD").toLowerCase().replace(/\p{M}/gu, "").replace(/[^\p{L}\p{N}]/gu, "-")
    .split("-").filter((x) => x).join("-");
  return `🔒│${c.tag.toLowerCase()}-${base}`;
}
const big = (x: unknown) => BigInt(String(x ?? "0"));

export async function synchroniser(o: Options): Promise<Rapport> {
  const f: Fetch = o.fetchFn ?? fetch;
  const pause = o.pause ?? ((ms) => new Promise((ok) => setTimeout(ok, ms)));
  const R: Rapport = { actions: [], avertissements: [], introuvables: [], erreurs: [] };
  const SIM = o.simulation;

  // un appel à Discord ; les écritures attendent un peu (limites de Discord)
  async function appel(methode: string, chemin: string, corps?: unknown, fatal = true): Promise<any> {
    for (let essai = 0; essai < 6; essai++) {
      const init: RequestInit = { method: methode, headers: { Authorization: "Bot " + o.jeton, "User-Agent": "TerraFrontBot (terrafront.fr, 2)" } };
      if (corps !== undefined) { (init.headers as Record<string, string>)["Content-Type"] = "application/json"; init.body = JSON.stringify(corps); }
      const r = await f(API + chemin, init);
      const texte = await r.text();
      if (r.status === 429) {
        let attente = 2000;
        try { attente = Math.ceil((Number(JSON.parse(texte).retry_after) || 2) * 1000) + 300; } catch { /* 2 s */ }
        await pause(attente); continue;
      }
      if (r.status >= 400) {
        const msg = `Discord a refusé ${methode} ${chemin} (${r.status}) : ${texte.slice(0, 300)}`;
        if (fatal) throw new Error(msg);
        R.erreurs.push(msg);
        return null;
      }
      if (methode !== "GET") await pause(350);
      return texte.trim() ? JSON.parse(texte) : {};
    }
    throw new Error("Discord limite trop les appels : nouvel essai au prochain passage.");
  }
  // une modification : faite en mode actif, seulement notée en simulation
  async function faire<T>(texte: string, fn: () => Promise<T>): Promise<T | null> {
    R.actions.push((SIM ? "SIMULÉ  " : "FAIT    ") + texte);
    return SIM ? null : await fn();
  }

  // ---------------------------------------------------------------- le serveur
  const moi = await appel("GET", "/users/@me");
  let G = o.guildId || "";
  if (!G) {
    const serveurs = await appel("GET", "/users/@me/guilds");
    if (serveurs.length !== 1) throw new Error(`Le bot est sur ${serveurs.length} serveurs : il doit être seulement sur celui de TerraFront (ou définir DISCORD_GUILD_ID).`);
    G = serveurs[0].id;
  }
  const EVERYONE = G;
  const membres: any[] = [];
  for (let apres = "0"; ;) {
    const page = await appel("GET", `/guilds/${G}/members?limit=1000&after=${apres}`, undefined, false);
    if (page === null) throw new Error("Discord refuse la liste des membres : activer « Server Members Intent » dans le portail développeur.");
    membres.push(...page.filter((m: any) => !m.user?.bot));
    if (page.length < 1000) break;
    apres = page[page.length - 1].user.id;
  }
  const index = new Map<string, Set<string>>();
  for (const m of membres) for (const n of [m.user.username, m.user.global_name, m.nick]) {
    if (!n) continue;
    const k = cle(n);
    if (!index.has(k)) index.set(k, new Set());
    index.get(k)!.add(m.user.id);
  }
  const parId = new Map<string, any>(membres.map((m) => [m.user.id, m]));
  const nomDe = (id: string) => parId.get(id)?.user?.username ?? id;
  const CORR = new Map<string, string>(Object.entries(o.correspondances ?? {}).map(([k, v]) => [cle(k), cle(v)]));
  const trouver = (pseudo: string) => [...(index.get(CORR.get(cle(pseudo)) ?? cle(pseudo)) ?? [])];

  const roles: any[] = await appel("GET", `/guilds/${G}/roles`);
  const salons: any[] = await appel("GET", `/guilds/${G}/channels`);

  // ---------------------------------------------------------------- 1. catégorie et salon public
  let cat = salons.find((s) => s.type === 4 && s.name === CATEGORIE);
  if (!cat) cat = await faire(`catégorie ${CATEGORIE}`, () => appel("POST", `/guilds/${G}/channels`, { name: CATEGORIE, type: 4 }));
  const CAT_ID: string | null = cat?.id ?? null;
  const pub = salons.find((s) => s.type === 0 && (s.name === PUBLIC || cle(s.name).endsWith("recrutementclans")));
  if (!pub) await faire(`salon public ${PUBLIC}`, () => appel("POST", `/guilds/${G}/channels`, { name: PUBLIC, type: 0, topic: PUBLIC_SUJET, parent_id: CAT_ID }));

  // ---------------------------------------------------------------- 2. chaque clan
  const tags = new Set<string>();
  for (const clan of o.clans) {
    const tag = clan.tag; tags.add(tag);
    const nomRole = `${PREFIXE_ROLE}${tag}] ${clan.nom}`;
    const couleur = parseInt(String(clan.couleur || "#8E9AAF").replace("#", ""), 16);

    // le rôle
    let role = roles.find((r) => String(r.name).startsWith(`${PREFIXE_ROLE}${tag}]`));
    if (role) {
      if (role.name !== nomRole || role.color !== couleur) {
        const id = role.id;
        await faire(`[${tag}] rôle renommé ou recoloré : ${nomRole}`, () => appel("PATCH", `/guilds/${G}/roles/${id}`, { name: nomRole, color: couleur }));
      }
    } else {
      role = await faire(`[${tag}] rôle ${nomRole}`, () => appel("POST", `/guilds/${G}/roles`, { name: nomRole, color: couleur, hoist: false, mentionable: true }));
      if (role) roles.push(role);
    }
    const rid: string | null = role?.id ?? null;

    // le salon privé (retrouvé par le sigle écrit dans son sujet)
    const marque = `[${tag}]`;
    const sujet = `Salon privé du clan ${marque} ${clan.nom} : seuls ses membres le voient.`;
    let salon = salons.find((s) => s.type === 0 && s.parent_id === CAT_ID && String(s.topic ?? "").includes(marque));
    const existantes = new Map<string, any>((salon?.permission_overwrites ?? []).map((x: any) => [x.id, x]));
    const base = [
      { id: EVERYONE, type: 0, allow: "0", deny: String(VOIR), quoi: "tout le monde : caché" },
      { id: moi.id, type: 1, allow: String(DROITS_BOT), deny: "0", quoi: "le bot" },
    ];
    if (rid) base.push({ id: rid, type: 0, allow: String(DROITS_MEMBRE), deny: "0", quoi: "le rôle du clan" });
    let sid: string | null = null;
    if (salon) {
      sid = salon.id;
      // renommé seulement si le nom change vraiment (Discord limite les renommages)
      if (cle(salon.name) !== cle(nomSalon(clan)) || salon.topic !== sujet) {
        await faire(`[${tag}] salon renommé : ${nomSalon(clan)}`, () => appel("PATCH", `/channels/${sid}`, { name: nomSalon(clan), topic: sujet }));
      }
      for (const b of base) {
        const e = existantes.get(b.id);
        if (!e || big(e.allow) !== big(b.allow) || big(e.deny) !== big(b.deny)) {
          await faire(`[${tag}] droits du salon (${b.quoi})`, () => appel("PUT", `/channels/${sid}/permissions/${b.id}`, { type: b.type, allow: b.allow, deny: b.deny }));
        }
      }
    } else {
      const ow = base.map(({ quoi: _q, ...x }) => x);
      salon = await faire(`[${tag}] salon privé ${nomSalon(clan)}`, () => appel("POST", `/guilds/${G}/channels`, { name: nomSalon(clan), type: 0, topic: sujet, parent_id: CAT_ID, permission_overwrites: ow }));
      sid = salon?.id ?? null;
      if (sid) {
        salons.push(salon);
        await appel("POST", `/channels/${sid}/messages`, { allowed_mentions: { parse: [] }, content:
          `🏰 **Salon privé du clan ${marque} ${clan.nom}**\n` +
          "Seuls les membres du clan le voient : le bot donne l'accès aux membres du jeu qui sont sur le Discord, et le retire à ceux qui quittent le clan.\n" +
          "Un membre qui n'est pas encore sur le Discord doit d'abord rejoindre le serveur." }, false);
      }
    }
    // seuls les membres (par le rôle) et le bot : tout accès à son nom est retiré
    if (sid) {
      for (const [uid, e] of existantes) {
        if (Number(e.type) !== 1 || uid === moi.id) continue;
        await faire(`[${tag}] accès à son nom retiré à ${nomDe(uid)} (le salon est réservé aux membres du clan)`, () =>
          appel("DELETE", `/channels/${sid}/permissions/${uid}`, undefined, false));
      }
    }

    // les membres
    const voulus = new Set<string>();
    for (const p of clan.membres) {
      const ids = trouver(p);
      if (ids.length === 1) voulus.add(ids[0]);
      else if (!ids.length) R.introuvables.push(p);
      else R.avertissements.push(`[${tag}] ${p} : plusieurs membres possibles, l'ajouter dans discord_correspondances`);
    }
    const actuels = new Set<string>(membres.filter((m) => rid && (m.roles ?? []).includes(rid)).map((m) => m.user.id));
    for (const uid of voulus) if (!actuels.has(uid)) {
      await faire(`[${tag}] rôle donné à ${nomDe(uid)}`, () => rid ? appel("PUT", `/guilds/${G}/members/${uid}/roles/${rid}`, undefined, false) : Promise.resolve(null));
    }
    for (const uid of actuels) if (!voulus.has(uid)) {
      await faire(`[${tag}] rôle retiré à ${nomDe(uid)} (n'est plus dans le clan)`, () => appel("DELETE", `/guilds/${G}/members/${uid}/roles/${rid}`, undefined, false));
    }
  }

  // ---------------------------------------------------------------- 3. clans dissous
  for (const r of roles) {
    if (!String(r.name).startsWith(PREFIXE_ROLE)) continue;
    const tag = String(r.name).slice(PREFIXE_ROLE.length).split("]")[0];
    if (tags.has(tag)) continue;
    const porteurs = membres.filter((m) => (m.roles ?? []).includes(r.id));
    for (const m of porteurs) {
      await faire(`${r.name} (clan dissous) : rôle retiré à ${m.user.username}`, () => appel("DELETE", `/guilds/${G}/members/${m.user.id}/roles/${r.id}`, undefined, false));
    }
    if (porteurs.length) R.avertissements.push(`${r.name} : le clan n'existe plus, son salon reste (à supprimer à la main si tu veux).`);
  }
  R.introuvables = [...new Set(R.introuvables)].sort();
  return R;
}

// ------------------------------------------------------------------ l'appel (Supabase)
if (typeof (globalThis as any).Deno !== "undefined") {
  const D = (globalThis as any).Deno;
  const cleSupabase = (ancienne: string, nouvelles: string): string => {
    const v = D.env.get(ancienne);
    if (v) return v;
    try { const p = Object.values(JSON.parse(D.env.get(nouvelles) ?? "{}"))[0]; if (typeof p === "string" && p) return p; } catch { /* rien */ }
    throw new Error(`Clé Supabase introuvable (${ancienne} / ${nouvelles})`);
  };
  D.serve(async (req: Request) => {
    const { createClient } = await import("npm:@supabase/supabase-js@2.45.4");
    const base = createClient(D.env.get("SUPABASE_URL")!, cleSupabase("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEYS"), { auth: { persistSession: false } });
    const { data: ok } = await base.rpc("discord_sync_verifier", { p_secret: req.headers.get("x-clans-secret") ?? "" });
    if (ok !== true) return new Response("non", { status: 401 });
    let mode = "simulation";
    try { const b = await req.json(); if (b && b.mode === "actif") mode = "actif"; } catch { /* simulation */ }
    const journal = async (ok: boolean, resume: string, details: unknown) => {
      await base.from("discord_sync_journal").insert({ mode, ok, resume, details });
    };
    try {
      const jeton = D.env.get("DISCORD_BOT_TOKEN");
      if (!jeton) throw new Error("Secret DISCORD_BOT_TOKEN manquant (Edge Functions > Secrets).");
      const { data, error } = await base.rpc("discord_clans_donnees");
      if (error) throw new Error("discord_clans_donnees : " + error.message);
      const R = await synchroniser({ jeton, clans: data?.clans ?? [], correspondances: data?.correspondances ?? {}, simulation: mode !== "actif", guildId: D.env.get("DISCORD_GUILD_ID") });
      const resume = `${(data?.clans ?? []).length} clan(s) · ${R.actions.length} changement(s)` +
        (R.introuvables.length ? ` · ${R.introuvables.length} joueur(s) pas trouvé(s) sur le Discord` : "") +
        (R.erreurs.length ? ` · ${R.erreurs.length} refus de Discord` : "");
      // un passage sans rien à faire n'encombre pas le journal (sauf en simulation)
      if (R.actions.length || R.erreurs.length || mode !== "actif") await journal(true, resume, R);
      return new Response(JSON.stringify({ ok: true, resume, ...R }), { headers: { "Content-Type": "application/json" } });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      await journal(false, msg, null);
      return new Response(JSON.stringify({ ok: false, erreur: msg }), { status: 500, headers: { "Content-Type": "application/json" } });
    }
  });
}
