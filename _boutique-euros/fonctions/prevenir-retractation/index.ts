// TerraFront — fonction Edge « prevenir-retractation »
//
// Appelée par le jeu juste après qu'un joueur a cliqué « Changer d'avis et être
// remboursé » (livraison différée). Elle envoie à contact@terrafront.fr un
// e-mail par demande pas encore signalée (pseudo, objet, montant, date limite,
// lien direct vers le paiement dans Stripe), puis les marque comme signalées.
// Un envoi raté reste en attente et repart au prochain appel.
//
// Secrets (déjà en place pour stripe-webhook) : RESEND_API_KEY, EMAIL_EXPEDITEUR.
// SUPABASE_URL et les clés Supabase sont fournies par Supabase.
// Déploiement : vérification du JWT DÉSACTIVÉE (la fonction vérifie le joueur).

import { createClient } from "npm:@supabase/supabase-js@2.45.4";

function cleSupabase(ancienne: string, nouvelles: string): string {
  const v = Deno.env.get(ancienne);
  if (v) return v;
  try {
    const liste = JSON.parse(Deno.env.get(nouvelles) ?? "{}");
    const premiere = Object.values(liste)[0];
    if (typeof premiere === "string" && premiere) return premiere;
  } catch { /* rien */ }
  throw new Error(`Clé Supabase introuvable (${ancienne} / ${nouvelles})`);
}

const SITE_URL = Deno.env.get("SITE_URL") ?? "https://terrafront.fr";
const DESTINATAIRE = "contact@terrafront.fr";
const ENTETES = {
  "Access-Control-Allow-Origin": SITE_URL,
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};
const reponse = (corps: unknown, statut = 200) => new Response(JSON.stringify(corps), { status: statut, headers: ENTETES });
const euros = (c: number) => (c / 100).toFixed(2).replace(".", ",") + " €";
const dateFr = (iso: string) => new Date(iso).toLocaleString("fr-FR", {
  timeZone: "Europe/Paris", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit",
});
const echapper = (t: string) => String(t ?? "").replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]!));

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: ENTETES });
  if (req.method !== "POST") return reponse({ erreur: "Méthode non autorisée" }, 405);

  // seul un joueur connecté peut déclencher l'envoi (il ne reçoit rien en retour)
  const jeton = req.headers.get("Authorization");
  if (!jeton) return reponse({ erreur: "Non connecté" }, 401);
  const commeJoueur = createClient(Deno.env.get("SUPABASE_URL")!, cleSupabase("SUPABASE_ANON_KEY", "SUPABASE_PUBLISHABLE_KEYS"), {
    global: { headers: { Authorization: jeton } }, auth: { persistSession: false },
  });
  const { data: u } = await commeJoueur.auth.getUser();
  if (!u?.user) return reponse({ erreur: "Non connecté" }, 401);

  const base = createClient(Deno.env.get("SUPABASE_URL")!, cleSupabase("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEYS"), {
    auth: { persistSession: false },
  });
  const { data: liste, error } = await base.rpc("euros_retractations_a_prevenir");
  if (error) { console.error("Rétractations :", error); return reponse({ ok: false }, 500); }
  if (!Array.isArray(liste) || !liste.length) return reponse({ ok: true, envoyes: 0 });

  const cle = Deno.env.get("RESEND_API_KEY");
  if (!cle) { console.warn("Rétractation non signalée : secret RESEND_API_KEY introuvable ou vide"); return reponse({ ok: false }, 500); }

  const faits: string[] = [];
  for (const d of liste) {
    const lien = d.paiement ? `https://dashboard.stripe.com/payments/${encodeURIComponent(d.paiement)}` : "https://dashboard.stripe.com/payments";
    const html = `<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:560px;margin:auto;color:#1d2433;line-height:1.5">
<h2 style="margin:0 0 12px">Demande de remboursement (rétractation)</h2>
<p>Un joueur a changé d'avis sur un achat en livraison différée. L'objet ne lui sera pas livré : il faut le <b>rembourser dans Stripe</b>.</p>
<table style="border-collapse:collapse;width:100%;margin:0 0 16px">
<tr><td style="padding:4px 0;color:#5b6475">Joueur</td><td style="padding:4px 0;text-align:right"><b>${echapper(d.pseudo || "compte supprimé")}</b></td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Objet</td><td style="padding:4px 0;text-align:right">${echapper(d.article)}</td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Montant</td><td style="padding:4px 0;text-align:right">${euros(Number(d.prix_centimes))}</td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Payé le</td><td style="padding:4px 0;text-align:right">${d.payee_le ? dateFr(d.payee_le) : "—"}</td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Demande le</td><td style="padding:4px 0;text-align:right">${dateFr(d.retractation_le)}</td></tr>
<tr><td style="padding:4px 0;color:#5b6475">À rembourser avant le</td><td style="padding:4px 0;text-align:right"><b>${dateFr(d.rembourser_avant)}</b></td></tr>
</table>
<p><a href="${lien}" style="display:inline-block;background:#635BFF;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none">Ouvrir le paiement dans Stripe</a></p>
<p style="font-size:12px;color:#5b6475">Dans Stripe : bouton « Rembourser », montant complet. Le jeu passe ensuite la commande en « Remboursé » tout seul. Commande ${echapper(d.id)}.</p>
</div>`;
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${cle}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: Deno.env.get("EMAIL_EXPEDITEUR") ?? "TerraFront <boutique@terrafront.fr>",
        to: [DESTINATAIRE],
        subject: `TerraFront — remboursement à faire : ${d.article} (${euros(Number(d.prix_centimes))})`,
        html,
      }),
    });
    if (r.ok) faits.push(d.id);
    else console.error("Resend :", r.status, await r.text());
  }
  if (faits.length) {
    const { error: e2 } = await base.rpc("euros_retractations_prevenues", { p_ids: faits });
    if (e2) console.error("Marquage :", e2);
  }
  return reponse({ ok: true, envoyes: faits.length });
});
