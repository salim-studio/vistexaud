// vistexaud playground: client-side mirror of the text branch.
(function () {
  var KEYWORDS = {
    sport: ["football", "match", "sport", "goal", "match"],
    tech: ["ai", "software", "computer", "model", "tech"],
    health: ["health", "doctor", "medical"],
    economy: ["economy", "market", "bank", "money", "earnings"]
  };

  function detectLang(text) {
    var ar = (text.match(/[\u0600-\u06FF]/g) || []).length;
    var en = (text.match(/[A-Za-z]/g) || []).length;
    if (ar > en && ar > 2) return "ar";
    if (en > ar && en > 2) return "en";
    return "unknown";
  }

  function classify(text) {
    var lower = text.toLowerCase();
    var best = "general", bestScore = 0;
    for (var k in KEYWORDS) {
      var s = 0;
      KEYWORDS[k].forEach(function (w) { if (lower.indexOf(w) !== -1) s++; });
      if (s > bestScore) { bestScore = s; best = k; }
    }
    return bestScore === 0 ? "general" : best;
  }

  function summarize(text, n) {
    var sents = text.split(/[.!?\n]+/).map(function (s) { return s.trim(); }).filter(Boolean);
    if (!sents.length) return "";
    var freq = {};
    (text.toLowerCase().match(/\w+/g) || []).forEach(function (w) { freq[w] = (freq[w] || 0) + 1; });
    var scored = sents.map(function (s) {
      var score = 0;
      (s.toLowerCase().match(/\w+/g) || []).forEach(function (w) { score += freq[w] || 0; });
      return { s: s, score: score };
    });
    scored.sort(function (a, b) { return b.score - a.score; });
    return scored.slice(0, n || 2).map(function (x) { return x.s; }).join(". ");
  }

  var input = document.getElementById("pg-input");
  function run() {
    var t0 = performance.now();
    var text = input.value;
    document.getElementById("pg-lang").textContent = detectLang(text);
    document.getElementById("pg-cat").textContent = classify(text);
    document.getElementById("pg-sum").textContent = summarize(text) || "—";
    document.getElementById("pg-ms").textContent = (performance.now() - t0).toFixed(2) + " ms";
  }
  input.addEventListener("input", run);
  run();

  // Tabs
  document.querySelectorAll(".tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (b) { b.classList.remove("active"); });
      document.querySelectorAll("pre.code").forEach(function (p) { p.classList.remove("active"); });
      btn.classList.add("active");
      document.getElementById(btn.getAttribute("data-tab")).classList.add("active");
    });
  });

  // Copy install command
  document.getElementById("copy-install").addEventListener("click", function () {
    var cmd = "pip install opencv-python numpy";
    if (navigator.clipboard) navigator.clipboard.writeText(cmd);
    this.textContent = "Copied";
    var self = this;
    setTimeout(function () { self.textContent = "Copy"; }, 1500);
  });
})();
