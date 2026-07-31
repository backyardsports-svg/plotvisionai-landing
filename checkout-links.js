/* PlotVisionAI checkout links — the one place to change a payment URL.
   Public values only; a Stripe Payment Link is safe to publish.

   Every buy button on the site carries data-checkout="<key>" and script.js
   resolves it here. A key set to null has no Payment Link yet: the button then
   falls back to the contact route with the plan pre-selected and is labelled as
   an activation request, never as completed checkout.

   The markup keeps a working href of its own so the site still functions with
   JavaScript off. For a live product that href is the same Stripe URL listed
   below; for an unreleased one it is the contact fallback. When you change a
   URL here, change the matching href in the page too — the QA link check will
   flag any pair that drifts apart. */
window.PV_CHECKOUT = {
  /* Where an unreleased plan sends people instead of dead-ending. */
  CONTACT_ROUTE: "contact.html",

  links: {
    /* Consumer plans — live */
    homeownerPass: "https://buy.stripe.com/7sY3cvcnv8oa2tU2BYcMM06",
    professional: "https://buy.stripe.com/4gM00j9bjawi2tUb8ucMM07",
    creditPack100: "https://buy.stripe.com/7sY00j9bjbAm4C2a4qcMM08",

    /* Corporate — only the pilot has a Payment Link so far */
    corporatePilot: "https://buy.stripe.com/eVqeVd4V3awi2tU3G2cMM09",

    /* Approved and priced, Payment Links not generated yet. The recurring
       Stripe products and prices exist; these stay null until the links are
       created, and the buttons request activation in the meantime. */
    starter: null,
    team5_monthly: null,
    team5_annual: null,
    team10_monthly: null,
    team10_annual: null,
    team15_monthly: null,
    team15_annual: null,
    team25_monthly: null,
    team25_annual: null,
    enterprise: null,
    creditPack1000: null,
    creditPack5000: null
  },

  /* What the contact fallback should say it is about. plan and billing are put
     in the query string so the contact form can pre-select them. */
  requests: {
    starter: { plan: "Starter", billing: "one-time" },
    team5_monthly: { plan: "Team 5", billing: "monthly" },
    team5_annual: { plan: "Team 5", billing: "annual" },
    team10_monthly: { plan: "Team 10", billing: "monthly" },
    team10_annual: { plan: "Team 10", billing: "annual" },
    team15_monthly: { plan: "Team 15", billing: "monthly" },
    team15_annual: { plan: "Team 15", billing: "annual" },
    team25_monthly: { plan: "Team 25", billing: "monthly" },
    team25_annual: { plan: "Team 25", billing: "annual" },
    enterprise: { plan: "Enterprise", billing: "custom" },
    creditPack1000: { plan: "1,000 credit pack", billing: "one-time" },
    creditPack5000: { plan: "5,000 credit pack", billing: "one-time" }
  }
};
