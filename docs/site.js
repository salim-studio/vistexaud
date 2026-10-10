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
  // Shared results store for the JSON report (must exist before run() below)
  window.VXA_RESULTS = { text: null, image: null, video: null, audio: null };
  function run() {
    var t0 = performance.now();
    var text = input.value;
    var lang = detectLang(text), cat = classify(text), sum = summarize(text);
    document.getElementById("pg-lang").textContent = lang;
    document.getElementById("pg-cat").textContent = cat;
    document.getElementById("pg-sum").textContent = sum || "—";
    var ms = performance.now() - t0;
    document.getElementById("pg-ms").textContent = ms.toFixed(2) + " ms";
    window.VXA_RESULTS.text = { lang: lang, category: cat, summary: sum, latency_ms: +ms.toFixed(2) };
  }
  input.addEventListener("input", run);
  run();

  // Quickstart tabs (scoped: playground has its own tabs below)
  document.querySelectorAll("#quickstart .tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("#quickstart .tab").forEach(function (b) { b.classList.remove("active"); });
      document.querySelectorAll("#quickstart pre.code").forEach(function (p) { p.classList.remove("active"); });
      btn.classList.add("active");
      document.getElementById(btn.getAttribute("data-tab")).classList.add("active");
    });
  });

  // Playground modality tabs
  document.querySelectorAll("#pg-tabs .tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("#pg-tabs .tab").forEach(function (b) { b.classList.remove("active"); });
      document.querySelectorAll(".ppane").forEach(function (p) { p.classList.remove("active"); });
      btn.classList.add("active");
      document.getElementById(btn.getAttribute("data-ptab")).classList.add("active");
    });
  });

  // ---- Image bench: brightness / contrast / edge density / dominant channel ----
  var imgCanvas = document.getElementById("img-canvas");
  function analyzeImage(source, name) {
    var t0 = performance.now();
    var ctx = imgCanvas.getContext("2d");
    var iw = source.videoWidth || source.naturalWidth || source.width;
    var ih = source.videoHeight || source.naturalHeight || source.height;
    var scale = Math.min(1, 640 / iw);
    var w = Math.max(1, Math.round(iw * scale)), h = Math.max(1, Math.round(ih * scale));
    imgCanvas.width = w; imgCanvas.height = h;
    ctx.drawImage(source, 0, 0, w, h);
    var d = ctx.getImageData(0, 0, w, h).data;
    var n = w * h, sumL = 0, sumL2 = 0, sumR = 0, sumG = 0, sumB = 0;
    var lum = new Float32Array(n);
    for (var i = 0; i < n; i++) {
      var r = d[i * 4], g = d[i * 4 + 1], b = d[i * 4 + 2];
      var l = 0.299 * r + 0.587 * g + 0.114 * b;
      lum[i] = l; sumL += l; sumL2 += l * l; sumR += r; sumG += g; sumB += b;
    }
    var mean = sumL / n;
    var contrast = Math.sqrt(Math.max(0, sumL2 / n - mean * mean));
    // Sobel edge density on a stride-2 grid (fast preview of edge load)
    var step = 2, edges = 0, cells = 0;
    for (var y = 1; y < h - 1; y += step) {
      for (var x = 1; x < w - 1; x += step) {
        var gx = -lum[(y - 1) * w + x - 1] - 2 * lum[y * w + x - 1] - lum[(y + 1) * w + x - 1]
                 + lum[(y - 1) * w + x + 1] + 2 * lum[y * w + x + 1] + lum[(y + 1) * w + x + 1];
        var gy = -lum[(y - 1) * w + x - 1] - 2 * lum[(y - 1) * w + x] - lum[(y - 1) * w + x + 1]
                 + lum[(y + 1) * w + x - 1] + 2 * lum[(y + 1) * w + x] + lum[(y + 1) * w + x + 1];
        if (Math.sqrt(gx * gx + gy * gy) > 100) edges++;
        cells++;
      }
    }
    var dom = sumR >= sumG && sumR >= sumB ? "red" : (sumG >= sumB ? "green" : "blue");
    var ms = performance.now() - t0;
    document.getElementById("img-dims").textContent = iw + "x" + ih;
    document.getElementById("img-bright").textContent = mean.toFixed(1) + " / 255";
    document.getElementById("img-contrast").textContent = contrast.toFixed(1);
    document.getElementById("img-edge").textContent = (100 * edges / Math.max(1, cells)).toFixed(1) + " %";
    document.getElementById("img-dom").textContent = dom;
    document.getElementById("img-ms").textContent = ms.toFixed(1) + " ms";
    document.getElementById("img-name").textContent = name || "";
    window.VXA_RESULTS.image = { name: name || "sample", width: iw, height: ih,
      brightness: +mean.toFixed(1), contrast: +contrast.toFixed(1),
      edge_density_pct: +(100 * edges / Math.max(1, cells)).toFixed(1),
      dominant_channel: dom, latency_ms: +ms.toFixed(1) };
  }
  document.getElementById("img-file").addEventListener("change", function (e) {
    var f = e.target.files[0];
    if (!f) return;
    var img = new Image();
    img.onload = function () { analyzeImage(img, f.name); URL.revokeObjectURL(img.src); };
    img.src = URL.createObjectURL(f);
  });
  document.getElementById("img-sample").addEventListener("click", function () {
    var c = document.createElement("canvas");
    c.width = 640; c.height = 360;
    var x = c.getContext("2d");
    var gr = x.createLinearGradient(0, 0, 640, 360);
    gr.addColorStop(0, "#7C3AED"); gr.addColorStop(0.55, "#06B6D4"); gr.addColorStop(1, "#F59E0B");
    x.fillStyle = gr; x.fillRect(0, 0, 640, 360);
    x.fillStyle = "#0B1020";
    x.beginPath(); x.arc(200, 170, 80, 0, 7); x.fill();
    x.fillRect(360, 90, 160, 160);
    x.fillStyle = "#FFFFFF"; x.font = "bold 64px sans-serif"; x.fillText("VXA", 250, 320);
    analyzeImage(c, "vxa-sample");
  });

  // ---- Video bench: per-frame brightness + frame-diff motion, FPS, sparkline ----
  var vidEl = document.getElementById("vid-el");
  var motionCv = document.getElementById("motion-canvas");
  var vidState = null;
  function stopVideo() {
    if (vidState && vidState.raf) cancelAnimationFrame(vidState.raf);
    if (vidState && vidState.stream) vidState.stream.getTracks().forEach(function (t) { t.stop(); });
    vidState = null;
    try { vidEl.pause(); } catch (e) {}
    document.getElementById("vid-fps").textContent = "idle";
    document.getElementById("vid-verdict").textContent = "stopped";
  }
  function startVideo(name) {
    stopVideo();
    var off = document.createElement("canvas");
    off.width = 160; off.height = 90;
    var octx = off.getContext("2d", { willReadFrequently: true });
    var mctx = motionCv.getContext("2d");
    var prev = null, series = [], bSum = 0, mSum = 0, frames = 0, lastT = performance.now(), fps = 0;
    window.VXA_RESULTS.video = { name: name, frames: 0 };
    function drawSpark() {
      mctx.fillStyle = "#060B1C"; mctx.fillRect(0, 0, 640, 90);
      mctx.strokeStyle = "#F59E0B"; mctx.lineWidth = 2; mctx.beginPath();
      series.forEach(function (v, i) {
        var x = (i / Math.max(1, 119)) * 640, y = 86 - Math.min(1, v / 40) * 80;
        if (i === 0) mctx.moveTo(x, y); else mctx.lineTo(x, y);
      });
      mctx.stroke();
    }
    function loop() {
      if (!vidState) return;
      var now = performance.now();
      fps = fps * 0.9 + (1000 / Math.max(1, now - lastT)) * 0.1;
      lastT = now;
      if (vidEl.readyState >= 2 && vidEl.videoWidth) {
        var t0 = performance.now();
        octx.drawImage(vidEl, 0, 0, 160, 90);
        var d = octx.getImageData(0, 0, 160, 90).data;
        var n = 160 * 90, b = 0, diff = 0;
        var cur = new Uint8Array(n);
        for (var i = 0; i < n; i++) {
          var l = (d[i * 4] + d[i * 4 + 1] + d[i * 4 + 2]) / 3;
          cur[i] = l; b += l;
          if (prev && Math.abs(l - prev[i]) > 25) diff++;
        }
        prev = cur;
        var motion = prev ? 100 * diff / n : 0;
        frames++; bSum += b / n; mSum += motion;
        series.push(motion); if (series.length > 120) series.shift();
        drawSpark();
        var ms = performance.now() - t0;
        document.getElementById("vid-fps").textContent = fps.toFixed(1) + " fps";
        document.getElementById("vid-frames").textContent = frames;
        document.getElementById("vid-motion").textContent = (mSum / frames).toFixed(1) + " %";
        document.getElementById("vid-bright").textContent = (bSum / frames).toFixed(1);
        document.getElementById("vid-ms").textContent = ms.toFixed(1) + " ms";
        var verdict = (mSum / frames) > 3 ? "motion detected" : "static scene";
        document.getElementById("vid-verdict").textContent = verdict;
        window.VXA_RESULTS.video = { name: name, frames: frames, fps: +fps.toFixed(1),
          avg_motion_pct: +(mSum / frames).toFixed(1), avg_brightness: +(bSum / frames).toFixed(1),
          verdict: verdict, last_sample_ms: +ms.toFixed(1) };
      }
      vidState.raf = requestAnimationFrame(loop);
    }
    vidState = { raf: 0, stream: null };
    loop();
  }
  document.getElementById("vid-file").addEventListener("change", function (e) {
    var f = e.target.files[0];
    if (!f) return;
    vidEl.srcObject = null;
    vidEl.src = URL.createObjectURL(f);
    vidEl.play().catch(function () {});
    document.getElementById("vid-name").textContent = f.name;
    startVideo(f.name);
  });
  document.getElementById("vid-cam").addEventListener("click", function () {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      document.getElementById("vid-verdict").textContent = "webcam unsupported";
      return;
    }
    navigator.mediaDevices.getUserMedia({ video: true }).then(function (s) {
      vidEl.srcObject = s;
      vidEl.play().catch(function () {});
      document.getElementById("vid-name").textContent = "webcam";
      startVideo("webcam");
      if (vidState) vidState.stream = s;
    }).catch(function () {
      document.getElementById("vid-verdict").textContent = "camera denied";
    });
  });
  document.getElementById("vid-stop").addEventListener("click", stopVideo);

  // ---- Audio bench: waveform + energy/VAD + spectral label + pitch ----
  var audEl = document.getElementById("aud-el");
  var waveCv = document.getElementById("wave-canvas");
  var actx = null, mediaRec = null, recChunks = [];
  function getCtx() {
    if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)();
    if (actx.state === "suspended") actx.resume();
    return actx;
  }
  function drawWave(samples) {
    var x = waveCv.getContext("2d");
    x.fillStyle = "#060B1C"; x.fillRect(0, 0, 640, 160);
    x.strokeStyle = "#06B6D4"; x.lineWidth = 1.5; x.beginPath();
    var step = Math.max(1, Math.floor(samples.length / 640));
    for (var i = 0; i < 640; i++) {
      var v = samples[Math.min(samples.length - 1, i * step)] || 0;
      var y = 80 - Math.max(-1, Math.min(1, v)) * 70;
      if (i === 0) x.moveTo(i, y); else x.lineTo(i, y);
    }
    x.stroke();
  }
  function analyzeAudio(samples, sr, name) {
    var t0 = performance.now();
    var n = samples.length, energy = 0;
    for (var i = 0; i < n; i++) energy += samples[i] * samples[i];
    energy = n ? energy / n : 0;
    var speech = energy > 0.01;
    // spectral centroid via a compact real DFT (mirrors AudioClassifier)
    var N = Math.min(n, 512), num = 0, den = 0, zc = 0;
    var prevS = samples[0] > 0;
    for (var i = 1; i < n; i += 2) {
      var cur = samples[i] > 0;
      if (cur !== prevS) zc++;
      prevS = cur;
    }
    for (var k = 1; k <= N / 2; k++) {
      var re = 0, im = 0;
      for (var m = 0; m < N; m++) {
        var a = 2 * Math.PI * k * m / N;
        re += samples[m] * Math.cos(a);
        im -= samples[m] * Math.sin(a);
      }
      var mag = Math.sqrt(re * re + im * im);
      num += (k * sr / N) * mag;
      den += mag;
    }
    var centroid = den ? num / den : 0;
    var zcr = n ? zc / (n / 2) : 0;
    var label = "silence", score = 0.99;
    if (energy >= 1e-4) {
      if (centroid < 1200 && zcr < 0.15) { label = "speech"; score = 0.8; }
      else if (centroid > 2500 && zcr > 0.2) { label = "music"; score = 0.7; }
      else { label = "noise"; score = 0.6; }
    }
    // pitch via autocorrelation, 50..500 Hz (mirrors PitchEstimator)
    var mean = 0;
    for (var j = 0; j < n; j++) mean += samples[j];
    mean /= Math.max(1, n);
    var bestLag = 0, bestVal = 0;
    var minLag = Math.floor(sr / 500), maxLag = Math.min(n - 1, Math.floor(sr / 50));
    for (var lag = minLag; lag <= maxLag; lag += 2) {
      var c = 0;
      for (var m2 = 0; m2 + lag < n; m2 += 4) c += (samples[m2] - mean) * (samples[m2 + lag] - mean);
      if (c > bestVal) { bestVal = c; bestLag = lag; }
    }
    var pitch = bestLag > 0 && bestVal > 0 ? sr / bestLag : 0;
    var ms = performance.now() - t0;
    drawWave(samples);
    document.getElementById("aud-dur").textContent = (n / sr).toFixed(2) + " s";
    document.getElementById("aud-vad").textContent = speech ? "speech (" + energy.toFixed(4) + ")" : "silence";
    document.getElementById("aud-label").textContent = label + " " + score.toFixed(2);
    document.getElementById("aud-pitch").textContent = pitch ? pitch.toFixed(1) + " Hz" : "—";
    document.getElementById("aud-energy").textContent = energy.toFixed(5);
    document.getElementById("aud-ms").textContent = ms.toFixed(1) + " ms";
    document.getElementById("aud-name").textContent = name || "";
    window.VXA_RESULTS.audio = { name: name || "sample", duration_s: +(n / sr).toFixed(2),
      speech: speech, energy: +energy.toFixed(5), label: label, score: score,
      pitch_hz: +pitch.toFixed(1), latency_ms: +ms.toFixed(1) };
  }
  function decodeAndRun(buf, name, url) {
    getCtx().decodeAudioData(buf).then(function (decoded) {
      var ch = decoded.getChannelData(0);
      var samples = new Float32Array(ch.length);
      if (decoded.numberOfChannels > 1) {
        var ch2 = decoded.getChannelData(1);
        for (var i = 0; i < ch.length; i++) samples[i] = (ch[i] + ch2[i]) / 2;
      } else { samples.set(ch); }
      if (url) { audEl.src = url; }
      analyzeAudio(samples, decoded.sampleRate, name);
    }).catch(function () {
      document.getElementById("aud-label").textContent = "decode failed";
    });
  }
  document.getElementById("aud-file").addEventListener("change", function (e) {
    var f = e.target.files[0];
    if (!f) return;
    var url = URL.createObjectURL(f);
    f.arrayBuffer().then(function (buf) { decodeAndRun(buf, f.name, url); });
  });
  document.getElementById("aud-sample").addEventListener("click", function () {
    var sr = 16000, s = new Float32Array(sr);
    for (var i = 0; i < sr; i++) s[i] = 0.3 * Math.sin(2 * Math.PI * 220 * i / sr);
    audEl.removeAttribute("src");
    analyzeAudio(s, sr, "220Hz-tone");
  });
  document.getElementById("aud-rec").addEventListener("click", function () {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      document.getElementById("aud-label").textContent = "recording unsupported";
      return;
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      recChunks = [];
      mediaRec = new MediaRecorder(stream);
      mediaRec.ondataavailable = function (e) { if (e.data.size) recChunks.push(e.data); };
      mediaRec.onstop = function () {
        stream.getTracks().forEach(function (t) { t.stop(); });
        var blob = new Blob(recChunks, { type: mediaRec.mimeType || "audio/webm" });
        var url = URL.createObjectURL(blob);
        blob.arrayBuffer().then(function (buf) { decodeAndRun(buf, "mic-recording", url); });
        document.getElementById("aud-stop").disabled = true;
      };
      mediaRec.start();
      document.getElementById("aud-stop").disabled = false;
      document.getElementById("aud-name").textContent = "recording…";
    }).catch(function () {
      document.getElementById("aud-label").textContent = "mic denied";
    });
  });
  document.getElementById("aud-stop").addEventListener("click", function () {
    if (mediaRec && mediaRec.state !== "inactive") mediaRec.stop();
  });

  // ---- JSON report ----
  document.getElementById("report-btn").addEventListener("click", function () {
    var report = { tool: "vistexaud-playground", at: new Date().toISOString(), results: window.VXA_RESULTS };
    var blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "vistexaud-report.json";
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  });
  document.getElementById("copy-install").addEventListener("click", function () {
    var cmd = "pip install opencv-python numpy";
    if (navigator.clipboard) navigator.clipboard.writeText(cmd);
    this.textContent = "Copied";
    var self = this;
    setTimeout(function () { self.textContent = "Copy"; }, 1500);
  });
})();
