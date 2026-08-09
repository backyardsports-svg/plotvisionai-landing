/* PlotVisionAI runtime configuration - single place to set the preview link and
   the signup endpoint. Public values only. Never put a Supabase service-role key
   here: this file is served to the browser. The Edge Function must do the insert
   with its own server-side key.

   PREVIEW_URL      current public PlotVisionAI app
   SIGNUP_ENDPOINT  Supabase Edge Function URL that records the address
   SIGNUP_ANON_KEY  public publishable/anon key, sent as apikey + Bearer if present
   CONSENT_VERSION  version stamp for the consent copy shown next to the form
   States: with both set the address is posted to the endpoint and the preview
   opens on success. With PREVIEW_URL set but no endpoint the form still demands a
   valid address, makes no request, and states on the page that nothing is recorded.
   With no PREVIEW_URL the form is disabled outright. */
window.PV_CONFIG = {
  PREVIEW_URL: "https://getplotvisionai.com",
  SIGNUP_ENDPOINT: "https://dtryhdykdbncxxwgqmta.supabase.co/functions/v1/register-preview-signup",
  SIGNUP_ANON_KEY: "sb_publishable_oNlZDcyFna0_ZIfCSFzk0g_FYO6ALAd",
  SIGNUP_SOURCE: "free-preview",
  CONSENT_VERSION: "2026-07-31"
};
