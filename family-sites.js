/*
 * Sister sites for the site-wide footer.
 * Add a business to FAMILY_SITES and it appears on every page.
 * Past about 10 sites, stop growing this footer line and link to a
 * single directory page instead.
 */
var FAMILY_SITES = [
  {
    name: "Landforms USA",
    href: "https://www.landformsusa.com/",
    title: "Cedar Rapids landscape design & installation"
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
  }
];

(function () {
  var LEAD = "More Iowa businesses by Darin Chamberlin: ";
  var SEPARATOR = " \u00b7 ";

  function render(root) {
    root.textContent = "";

    var lead = document.createElement("span");
    lead.textContent = LEAD;
    root.appendChild(lead);

    FAMILY_SITES.forEach(function (site, index) {
      if (index > 0) root.appendChild(document.createTextNode(SEPARATOR));
      var link = document.createElement("a");
      link.href = site.href;
      link.title = site.title;
      link.textContent = site.name;
      root.appendChild(link);
    });
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
