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
//
// Déploiement : vérification du JWT DÉSACTIVÉE pour cette fonction
// (Stripe n'a pas de jeton Supabase ; c'est la signature qui protège).

import Stripe from "npm:stripe@16.12.0";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-06-20",
  httpClient: Stripe.createFetchHttpClient(),
});
const cryptoProvider = Stripe.createSubtleCryptoProvider();
const base = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
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
