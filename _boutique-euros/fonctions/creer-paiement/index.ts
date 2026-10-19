// TerraFront — fonction Edge « creer-paiement »
//
// Appelée par le jeu quand le joueur clique sur « Payer et recevoir l'objet ».
// 1. vérifie le joueur et sa commande avec SON jeton (euros_preparer_commande :
//    article actif, cases cochées, OG, plafond des mineurs, prix du catalogue) ;
// 2. crée la page de paiement Stripe avec le prix du SERVEUR ;
// 3. relie la commande à la session Stripe (clé service, jamais exposée) ;
// 4. renvoie l'adresse de la page Stripe, le jeu y redirige le joueur.
//
// Secrets à définir dans Supabase (Edge Functions > Secrets) :
//   STRIPE_SECRET_KEY   sk_test_... (puis sk_live_... le jour de l'ouverture)
//   SITE_URL            https://terrafront.fr
// SUPABASE_URL, SUPABASE_ANON_KEY et SUPABASE_SERVICE_ROLE_KEY sont fournis
// automatiquement par Supabase.
//
// Déploiement : vérification du JWT ACTIVÉE (réglage par défaut).

import Stripe from "npm:stripe@16.12.0";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const SITE_URL = Deno.env.get("SITE_URL") ?? "https://terrafront.fr";
const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-06-20",
  httpClient: Stripe.createFetchHttpClient(),
});

const ENTETES = {
  "Access-Control-Allow-Origin": SITE_URL,
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

function reponse(corps: unknown, statut = 200): Response {
  return new Response(JSON.stringify(corps), { status: statut, headers: ENTETES });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: ENTETES });
  if (req.method !== "POST") return reponse({ erreur: "Méthode non autorisée" }, 405);

  const jeton = req.headers.get("Authorization");
  if (!jeton) return reponse({ erreur: "Non connecté" }, 401);

  let corps: Record<string, unknown>;
  try {
    corps = await req.json();
  } catch {
    return reponse({ erreur: "Requête invalide" }, 400);
  }

  // 1. le joueur, avec son propre jeton : auth.uid() côté base = ce joueur
  const commeJoueur = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_ANON_KEY")!, {
    global: { headers: { Authorization: jeton } },
    auth: { persistSession: false },
  });
  const { data: utilisateur } = await commeJoueur.auth.getUser();
  if (!utilisateur?.user) return reponse({ erreur: "Non connecté" }, 401);

  const { data: commande, error: refus } = await commeJoueur.rpc("euros_preparer_commande", {
    p_article: String(corps.article ?? ""),
    p_livraison: String(corps.livraison ?? ""),
    p_case_cgv: corps.case_cgv === true,
    p_case_immediate: corps.case_immediate === true,
    p_case_renonciation: corps.case_renonciation === true,
    p_cgv_version: String(corps.cgv_version ?? ""),
    p_date_naissance: typeof corps.date_naissance === "string" ? corps.date_naissance : null,
  });
  // les refus de la base sont des phrases écrites pour le joueur
  if (refus) return reponse({ erreur: refus.message }, 400);

  // 2. la page de paiement Stripe, avec le prix venu de la base
  let session: Stripe.Checkout.Session;
  try {
    session = await stripe.checkout.sessions.create({
      mode: "payment",
      locale: "fr",
      line_items: [{
        quantity: 1,
        price_data: {
          currency: "eur",
          unit_amount: commande.prix_centimes,
          product_data: {
            name: `TerraFront — ${commande.nom}`,
            description: commande.livraison === "immediate"
              ? "Objet d'apparence, livré immédiatement (renonciation à la rétractation acceptée)"
              : "Objet d'apparence, livré 14 jours après le paiement (droit de rétractation conservé)",
          },
        },
      }],
      customer_email: utilisateur.user.email ?? undefined,
      client_reference_id: commande.commande_id,
      metadata: { commande_id: commande.commande_id },
      payment_intent_data: { metadata: { commande_id: commande.commande_id } },
      expires_at: Math.floor(Date.now() / 1000) + 30 * 60, // 30 minutes (minimum Stripe)
      success_url: `${SITE_URL}/?paiement=ok`,
      cancel_url: `${SITE_URL}/?paiement=annule`,
    });
  } catch (e) {
    console.error("Stripe :", e);
    return reponse({ erreur: "Le paiement est indisponible pour le moment. Réessaie plus tard." }, 502);
  }

  // 3. relier la commande à la session, avec la clé service (côté serveur seulement)
  const commeServeur = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { persistSession: false },
  });
  const { error: liaison } = await commeServeur.rpc("euros_lier_session", {
    p_commande: commande.commande_id,
    p_session: session.id,
  });
  if (liaison) {
    console.error("Liaison :", liaison);
    await stripe.checkout.sessions.expire(session.id).catch(() => {});
    return reponse({ erreur: "Le paiement est indisponible pour le moment. Réessaie plus tard." }, 500);
  }

  // 4. le jeu redirige vers Stripe
  return reponse({ url: session.url });
});
