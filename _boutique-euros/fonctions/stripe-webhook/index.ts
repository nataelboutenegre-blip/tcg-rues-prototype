// TerraFront — fonction Edge « stripe-webhook »
//
// Stripe l'appelle à chaque événement de paiement. C'est la SEULE porte par
// laquelle un objet payé arrive dans un compte.
//  - la signature Stripe est vérifiée : un faux message est rejeté (400) ;
//  - chaque événement est enregistré par la base dans la même transaction
//    que son effet : rejoué, il ne fait rien ;
//  - en cas d'erreur de la base, on répond 500 et Stripe réessaie plus tard.
//
// Événements à cocher dans Stripe (Développeurs > Webhooks) :
//   checkout.session.completed
//   checkout.session.async_payment_succeeded
//   checkout.session.expired
//   charge.refunded
//   charge.dispute.created
//
// Secrets à définir dans Supabase (Edge Functions > Secrets) :
//   STRIPE_SECRET_KEY       sk_test_...
//   STRIPE_WEBHOOK_SECRET   whsec_... (donné par Stripe à la création du webhook)
//   RESEND_API_KEY          re_... (email de confirmation ; sans elle, rien n'est envoyé)
//   EMAIL_EXPEDITEUR        TerraFront <boutique@terrafront.fr> (domaine vérifié dans Resend)
//
// Déploiement : vérification du JWT DÉSACTIVÉE pour cette fonction
// (Stripe n'a pas de jeton Supabase ; c'est la signature qui protège).

import Stripe from "npm:stripe@16.12.0";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

// Clés Supabase : anciennes variables (SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY)
// ou nouvelles clés (SUPABASE_PUBLISHABLE_KEYS / SUPABASE_SECRET_KEYS, en JSON).
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

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-06-20",
  httpClient: Stripe.createFetchHttpClient(),
});
const cryptoProvider = Stripe.createSubtleCryptoProvider();
const base = createClient(Deno.env.get("SUPABASE_URL")!, cleSupabase("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEYS"), {
  auth: { persistSession: false },
});

function idDe(x: string | { id: string } | null | undefined): string | null {
  if (!x) return null;
  return typeof x === "string" ? x : x.id;
}

async function appeler(fonction: string, args: Record<string, unknown>): Promise<string> {
  const { data, error } = await base.rpc(fonction, args);
  if (error) throw new Error(`${fonction} : ${error.message}`);
  return String(data);
}


// ---------- email de confirmation (CGV art. 2 et 3 : support durable) ----------

const VENDEUR = "Nataël Boutenegre, entrepreneur individuel, nom commercial TerraFront — " +
  "RCS Angoulême 131 743 601 — SIRET 131 743 601 00018 — 22 rue Pasteur, 16160 Gond-Pontouvre — contact@terrafront.fr";

const euros = (c: number) => (c / 100).toFixed(2).replace(".", ",") + " €";
const dateFr = (iso: string) => new Date(iso).toLocaleString("fr-FR", {
  timeZone: "Europe/Paris", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit",
});
const echapper = (t: string) => t.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]!));

async function envoyerConfirmation(session: Stripe.Checkout.Session): Promise<void> {
  const cle = Deno.env.get("RESEND_API_KEY");
  const destinataire = session.customer_details?.email ?? session.customer_email;
  if (!cle || !destinataire) {
    console.warn("Email de confirmation non envoyé (clé Resend ou adresse manquante)", session.id);
    return;
  }
  const { data: c, error } = await base.rpc("euros_commande_pour_email", { p_session: session.id });
  if (error || !c) { console.error("Email : commande introuvable", session.id, error); return; }

  const immediate = c.livraison === "immediate";
  const livraison = immediate
    ? "Tu as demandé à recevoir l'objet immédiatement après le paiement, et tu as reconnu perdre ainsi ton " +
      "droit de rétractation (article L221-28, 13°, du Code de la consommation). L'objet est déjà dans ta garde-robe."
    : `Tu as gardé ton droit de rétractation : l'objet arrivera dans ta garde-robe le ${dateFr(c.livrer_apres)}. ` +
      "D'ici là, tu peux te rétracter sans motif en répondant à cet email (ou avec le formulaire en annexe des CGV) ; " +
      "tu seras remboursé sous 14 jours.";
  const cgv = c.cgv_pdf_url
    ? `Les conditions générales de vente acceptées (version ${echapper(c.cgv_version)}) sont jointes à cet email.`
    : `Conditions générales de vente acceptées : version ${echapper(c.cgv_version)}.`;

  const html = `<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:560px;margin:auto;color:#1d2433;line-height:1.5">
<h2 style="margin:0 0 12px">Merci pour ton achat !</h2>
<table style="border-collapse:collapse;width:100%;margin:0 0 16px">
<tr><td style="padding:4px 0;color:#5b6475">Objet</td><td style="padding:4px 0;text-align:right"><b>${echapper(c.article)}</b></td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Prix payé</td><td style="padding:4px 0;text-align:right">${euros(c.prix_centimes)} TTC</td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Date</td><td style="padding:4px 0;text-align:right">${dateFr(c.payee_le)}</td></tr>
<tr><td style="padding:4px 0;color:#5b6475">Commande</td><td style="padding:4px 0;text-align:right;font-family:monospace;font-size:12px">${c.commande_id}</td></tr>
</table>
<p>${livraison}</p>
<p>Cet objet d'apparence ne donne aucun avantage de jeu. Tu bénéficies de la garantie légale de conformité
des contenus numériques (articles L224-25-12 et suivants du Code de la consommation).</p>
<p>${cgv}</p>
<p style="font-size:12px;color:#5b6475">En cas de litige, écris d'abord à contact@terrafront.fr. Si ta réclamation n'aboutit pas, tu peux saisir gratuitement le médiateur CM2C, 49 rue de Ponthieu, 75008 Paris — https://www.cm2c.net/declarer-un-litige.php</p>
<p style="font-size:12px;color:#5b6475">TVA non applicable, article 293 B du CGI.<br>${echapper(VENDEUR)}</p>
</div>`;

  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${cle}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: Deno.env.get("EMAIL_EXPEDITEUR") ?? "TerraFront <boutique@terrafront.fr>",
      to: [destinataire],
      reply_to: "contact@terrafront.fr",
      subject: `TerraFront — confirmation de ta commande : ${c.article}`,
      html,
      attachments: c.cgv_pdf_url
        ? [{ path: c.cgv_pdf_url, filename: `CGV-TerraFront-${c.cgv_version}.pdf` }]
        : undefined,
    }),
  });
  if (!r.ok) console.error("Resend :", r.status, await r.text());
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Méthode non autorisée", { status: 405 });

  const signature = req.headers.get("Stripe-Signature");
  const brut = await req.text(); // le corps EXACT, sinon la signature ne correspond pas
  let evt: Stripe.Event;
  try {
    evt = await stripe.webhooks.constructEventAsync(
      brut, signature ?? "", Deno.env.get("STRIPE_WEBHOOK_SECRET")!, undefined, cryptoProvider,
    );
  } catch {
    return new Response("Signature invalide", { status: 400 });
  }

  try {
    let resultat = "ignore";
    switch (evt.type) {
      case "checkout.session.completed":
      case "checkout.session.async_payment_succeeded": {
        const s = evt.data.object as Stripe.Checkout.Session;
        if (s.payment_status !== "paid") break; // paiement différé : on attend async_payment_succeeded
        resultat = await appeler("euros_confirmer_paiement", {
          p_evenement: evt.id,
          p_session: s.id,
          p_paiement: idDe(s.payment_intent),
          p_montant: s.amount_total,
          p_devise: s.currency,
        });
        // un seul email par paiement : pas sur un événement rejoué ni sur une anomalie.
        // Un échec d'envoi ne bloque pas la livraison (il est seulement journalisé).
        if (resultat === "livree" || resultat === "en_attente_14_jours") {
          await envoyerConfirmation(s).catch((e) => console.error("Email :", e));
        }
        break;
      }
      case "checkout.session.expired": {
        const s = evt.data.object as Stripe.Checkout.Session;
        resultat = await appeler("euros_expirer", { p_evenement: evt.id, p_session: s.id });
        break;
      }
      case "charge.refunded": {
        const c = evt.data.object as Stripe.Charge;
        if (!c.refunded) break; // remboursement partiel : à traiter à la main
        resultat = await appeler("euros_annuler_remboursee", {
          p_evenement: evt.id, p_paiement: idDe(c.payment_intent), p_motif: "remboursement",
        });
        break;
      }
      case "charge.dispute.created": {
        const d = evt.data.object as Stripe.Dispute;
        resultat = await appeler("euros_annuler_remboursee", {
          p_evenement: evt.id, p_paiement: idDe(d.payment_intent), p_motif: "contestation",
        });
        break;
      }
    }
    console.log(evt.type, evt.id, resultat);
    return new Response(JSON.stringify({ recu: true, resultat }), {
      status: 200, headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    console.error(evt.type, evt.id, e);
    return new Response("Erreur, Stripe réessaiera", { status: 500 });
  }
});
