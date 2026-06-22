(function () {
  "use strict";
  var C = window.CATALOGUE;
  if (!C) {
    document.getElementById("cats").innerHTML =
      '<p style="text-align:center;padding:60px;color:#8A6B7C">Catalogue data not loaded. Run the build pipeline.</p>';
    return;
  }

  // Brand overrides (site-sampled accent + real logo).
  if (C.brand && C.brand.accent) document.documentElement.style.setProperty("--accent", C.brand.accent);
  var logo = document.getElementById("logo");
  logo.src = (C.brand && C.brand.logo) ? C.brand.logo : "assets/brand/logo.png";

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function isGold(badge) { return badge && /premium/i.test(badge); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  var VARIANT_COLORS = {
    red: "#D7263D", green: "#2E7D32", pink: "#E8587A", gray: "#9E9E9E",
    grey: "#9E9E9E", blue: "#1E88E5", yellow: "#E0A800", white: "#FFFFFF",
    black: "#222222", multicolor: "linear-gradient(135deg,#E8587A,#E0A800,#1E88E5,#2E7D32)"
  };
  function variantStyle(name) {
    var key = String(name).toLowerCase().trim();
    var c = VARIANT_COLORS[key];
    if (!c) return "background:var(--accent)";
    return c.indexOf("gradient") >= 0 ? ("background:" + c) : ("background:" + c);
  }

  // Nav
  var nav = document.getElementById("nav");
  C.categories.forEach(function (cat) {
    var a = el("a", null, esc(cat.icon) + " " + esc(cat.name));
    a.href = "#" + cat.id;
    a.dataset.id = cat.id;
    nav.appendChild(a);
  });

  // Sections
  var root = document.getElementById("cats");
  C.categories.forEach(function (cat) {
    var sec = el("section", "cat");
    sec.id = cat.id;
    sec.appendChild(el("div", "cat-head",
      '<h2>' + esc(cat.icon) + " " + esc(cat.name) + '</h2><span class="count">' +
      cat.products.length + ' designs</span>'));
    sec.appendChild(el("p", "cat-blurb", esc(cat.blurb)));
    sec.appendChild(el("hr", "stitch"));
    var grid = el("div", "grid");
    cat.products.forEach(function (p) {
      var card = el("div", "card");
      card.tabIndex = 0;
      var hasGallery = p.gallery && p.gallery.length > 1;
      var dots = (p.variants && p.variants.length)
        ? '<span class="dots">' + p.variants.map(function (v) {
            return '<i title="' + esc(v) + '" style="' + variantStyle(v) + '"></i>'; }).join("") + "</span>"
        : '<span class="tag">' + esc(p.detail || "100% handmade") + "</span>";
      card.innerHTML =
        '<div class="thumb"><img loading="lazy" src="' + p.base_image + '" alt="' + esc(p.name) + '" />' +
        (p.badge ? '<span class="badge ' + (isGold(p.badge) ? "gold" : "") + '">★ ' + esc(p.badge) + "</span>" : "") +
        (hasGallery ? '<span class="more">📷 ' + p.gallery.length + "</span>" : "") +
        '</div><div class="meta"><div class="name">' + esc(p.name) + '</div>' +
        '<div class="row"><span class="price">' + esc(p.price_display) + "</span>" + dots + "</div></div>";
      card.addEventListener("click", function () { openLB(p); });
      card.addEventListener("keydown", function (e) { if (e.key === "Enter") openLB(p); });
      grid.appendChild(card);
    });
    sec.appendChild(grid);
    root.appendChild(sec);
  });

  // Footer
  var ct = C.contact;
  document.getElementById("footer").innerHTML =
    '<div class="foot-cta"><h3>We accept bulk orders</h3>' +
    '<p>Gifting hampers, baby showers, return gifts — reach out for bulk pricing.</p>' +
    '<a class="btn btn-primary" href="https://wa.me/' + ct.whatsapp.replace(/\D/g, "") + '">💬 WhatsApp ' + esc(ct.whatsapp) + "</a></div>" +
    '<div class="quotes">' + C.testimonials.map(function (t) {
      return '<div class="quote"><p>"' + esc(t.quote) + '"</p><span>— ' + esc(t.author) + "</span></div>"; }).join("") +
    "</div>" +
    '<div class="foot-bottom"><a href="https://littlepinkllama.com">' + esc(ct.website) + "</a>" +
    '<a href="mailto:' + ct.email + '">' + esc(ct.email) + "</a>" +
    '<a href="https://instagram.com/little_pink_llama_">' + esc(ct.instagram) + "</a></div>";

  // Scrollspy
  var links = Array.prototype.slice.call(document.querySelectorAll("nav.cats a"));
  var spy = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) links.forEach(function (l) {
        l.classList.toggle("active", l.dataset.id === e.target.id); });
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  C.categories.forEach(function (cat) { spy.observe(document.getElementById(cat.id)); });

  // Lightbox
  var lb = document.getElementById("lb"), img = document.getElementById("lbImg"),
      strip = document.getElementById("lbStrip");
  var frames = [], cur = 0;
  function openLB(p) {
    frames = (p.gallery && p.gallery.length) ? p.gallery : [p.base_image];
    cur = 0;
    document.getElementById("lbName").textContent = p.name;
    document.getElementById("lbPrice").textContent = p.price_display;
    var multi = frames.length > 1;
    document.getElementById("lbPrev").style.display = multi ? "block" : "none";
    document.getElementById("lbNext").style.display = multi ? "block" : "none";
    strip.style.display = multi ? "flex" : "none";
    strip.innerHTML = frames.map(function (f, i) {
      return '<img data-i="' + i + '" class="' + (i === 0 ? "on" : "") + '" src="' + f + '" alt="" />'; }).join("");
    Array.prototype.forEach.call(strip.children, function (t) {
      t.onclick = function () { cur = +t.dataset.i; render(); }; });
    render();
    lb.classList.add("open"); lb.setAttribute("aria-hidden", "false");
  }
  function render() {
    img.src = frames[cur];
    Array.prototype.forEach.call(strip.children, function (t, i) {
      t.classList.toggle("on", i === cur); });
  }
  function close() { lb.classList.remove("open"); lb.setAttribute("aria-hidden", "true"); }
  document.getElementById("lbClose").onclick = close;
  document.getElementById("lbPrev").onclick = function () { cur = (cur - 1 + frames.length) % frames.length; render(); };
  document.getElementById("lbNext").onclick = function () { cur = (cur + 1) % frames.length; render(); };
  lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (frames.length > 1 && e.key === "ArrowRight") document.getElementById("lbNext").click();
    if (frames.length > 1 && e.key === "ArrowLeft") document.getElementById("lbPrev").click();
  });
})();
