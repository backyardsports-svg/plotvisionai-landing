/*
 * Partner sites for the site-wide footer.
 * Add a business here and it shows on every page except the site itself.
 * The same line is also written into each page's HTML so it works with
 * JavaScript off. Update that markup when this list changes.
 * The line wraps; keep names short so phones stay tidy.
 */
var FAMILY_SITES = [
  {
    name: "Landforms USA",
    href: "https://www.landformsusa.com/",
    title: "Cedar Rapids landscape design & installation"
  },
  {
    name: "Landscape Designs Online",
    href: "https://www.landscapedesignsonline.com/",
    title: "online landscape design plans"
  },
  {
    name: "Plot Vision AI",
    href: "https://getplotvisionai.com/",
    title: "AI yard design app"
  },
  {
    name: "Cedar Rapids Scrap",
    href: "https://scrapmetalcedarrapids.com/",
    title: "scrap metal pickup & prices"
  },
  {
    name: "Resinate Coatings",
    href: "https://www.resinatecoatings.com/",
    title: "epoxy floor coatings"
  },
  {
    name: "Des Moines Scrap",
    href: "https://desmoinesscrap.com/",
    title: "Des Moines scrap metal pickup"
  },
  {
    name: "Des Moines Epoxy",
    href: "https://desmoinesepoxy.com/",
    title: "Des Moines epoxy floors"
  },
  {
    name: "Dallas Scrap Pickup",
    href: "https://dallasscrappickup.com/",
    title: "Dallas\u2013Fort Worth scrap pickup"
  },
  {
    name: "Dallas Epoxy Coatings",
    href: "https://dallasepoxycoatings.com/",
    title: "Dallas\u2013Fort Worth epoxy floors"
  },
  {
    name: "Phoenix Scrap Pickup",
    href: "https://phoenixscrappickup.com/",
    title: "Phoenix scrap metal pickup"
  },
  {
    name: "Phoenix Epoxy Garage",
    href: "https://phoenixepoxygarage.com/",
    title: "Phoenix garage floor epoxy"
  },
  {
    name: "Tampa Scrap Pickup",
    href: "https://tampascrappickup.com/",
    title: "Tampa scrap metal pickup"
  },
  {
    name: "Tampa Epoxy Pros",
    href: "https://tampaepoxypros.com/",
    title: "Tampa epoxy floors"
  },
  {
    name: "Atlanta Scrap Pickup",
    href: "https://atlantascrappickup.com/",
    title: "Atlanta scrap metal pickup"
  },
  {
    name: "Atlanta Floor Coatings",
    href: "https://atlantafloorcoatings.com/",
    title: "Atlanta epoxy floor coatings"
  },
  {
    name: "Denver Scrap Buyer",
    href: "https://denverscrapbuyer.com/",
    title: "Denver scrap metal buyer"
  },
  {
    name: "Denver Epoxy Garage",
    href: "https://denverepoxygarage.com/",
    title: "Denver garage floor epoxy"
  }
];

(function () {
  var LEAD = "Check out our partner sites: ";
  var SEPARATOR = " \u00b7 ";
  var THIS_SITE = "landscapedesignsonline.com";

  function hostOf(url) {
    var match = String(url || "").match(/^https?:\/\/([^\/]+)/i);
    if (!match) return "";
    return match[1].replace(/^www\./i, "").toLowerCase();
  }

  function visibleSites() {
    var here = hostOf(window.location.href);
    return FAMILY_SITES.filter(function (site) {
      var host = hostOf(site.href);
      if (!host) return false;
      if (host === THIS_SITE) return false;
      if (here && host === here) return false;
      return true;
    });
  }

  function render(root) {
    var sites = visibleSites();
    if (!sites.length) return;

    var frag = document.createDocumentFragment();
    var lead = document.createElement("span");
    lead.textContent = LEAD;
    frag.appendChild(lead);

    sites.forEach(function (site, index) {
      if (index > 0) frag.appendChild(document.createTextNode(SEPARATOR));
      var link = document.createElement("a");
      link.href = site.href;
      link.title = site.title;
      link.textContent = site.name;
      frag.appendChild(link);
    });

    root.textContent = "";
    root.appendChild(frag);
  }

  function mount() {
    var nodes = document.querySelectorAll("[data-family-sites]");
    for (var i = 0; i < nodes.length; i++) render(nodes[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
