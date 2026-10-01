(function () {
  var canvas = document.getElementById("starfield");
  if (!canvas || !canvas.getContext) return;

  var ctx = canvas.getContext("2d", { alpha: false });
  if (!ctx) return;

  var base = document.createElement("canvas");
  var bctx = base.getContext("2d", { alpha: false });
  if (!bctx) return;

  var sprite = document.createElement("canvas");
  sprite.width = 64;
  sprite.height = 64;
  var sctx = sprite.getContext("2d");
  if (sctx) {
    var glow = sctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    glow.addColorStop(0, "rgba(255,255,255,1)");
    glow.addColorStop(0.14, "rgba(232,240,255,0.5)");
    glow.addColorStop(0.42, "rgba(186,204,232,0.1)");
    glow.addColorStop(1, "rgba(186,204,232,0)");
    sctx.fillStyle = glow;
    sctx.fillRect(0, 0, 64, 64);
  }

  var COLORS = ["#ffffff", "#f5f8ff", "#e6eefc", "#d4e0f3", "#c3d2ec", "#f3f0e8"];
  var stars = [];
  var w = 0;
  var h = 0;
  var dpr = 1;
  var rafId = 0;
  var running = false;
  var disposed = false;
  var resizeQueued = false;
  var seed = 1;
  var motionQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;

  function reduced() {
    return !!(motionQuery && motionQuery.matches);
  }

  function rand() {
    seed = (seed + 0x6d2b79f5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  function starCount() {
    var area = w * h;
    var cores = navigator.hardwareConcurrency || 8;
    var save = navigator.connection && navigator.connection.saveData;
    var small = w < 800;
    var density = small ? 0.00095 : 0.00078;
    var cap = 1800;
    if (cores <= 4) {
      density *= 0.75;
      cap = 1100;
    }
    if (cores <= 2 || save) {
      density *= 0.65;
      cap = 560;
    }
    var floor = Math.min(small ? 420 : 780, cap);
    return Math.max(floor, Math.min(cap, Math.round(area * density)));
  }

  function build() {
    var count = starCount();
    var aspect = w / Math.max(h, 1);
    var cols = Math.max(8, Math.ceil(Math.sqrt(count * aspect)));
    var rows = Math.max(6, Math.ceil(count / cols));
    var cellW = w / cols;
    var cellH = h / rows;
    stars = new Array(count);
    var n = 0;
    seed = 0x524f4f54;
    for (var row = 0; row < rows && n < count; row++) {
      for (var col = 0; col < cols && n < count; col++) {
        var roll = rand();
        var layer = roll < 0.7 ? 0 : roll < 0.93 ? 1 : 2;
        var colorPick = rand();
        var colorIndex = colorPick < 0.06 ? 5 : Math.floor(rand() * 5);
        var radius;
        var alpha;
        var halo = 0;
        var tw = 0;
        if (layer === 0) {
          radius = 0.45 + rand() * 0.8;
          alpha = 0.5 + rand() * 0.4;
        } else if (layer === 1) {
          radius = 0.85 + rand() * 0.7;
          alpha = 0.68 + rand() * 0.32;
          if (rand() < 0.4) halo = 3.2 + rand() * 3.4;
          if (rand() < 0.45) tw = 0.22 + rand() * 0.28;
        } else {
          radius = 1.25 + rand() * 0.85;
          alpha = 0.9 + rand() * 0.1;
          halo = 6.5 + rand() * 7.5;
          tw = 0.18 + rand() * 0.26;
        }
        stars[n] = {
          x: (col + rand()) * cellW,
          y: (row + rand()) * cellH,
          r: radius,
          a: alpha,
          color: COLORS[colorIndex],
          halo: halo,
          tw: tw,
          phase: rand() * 6.283185307179586
        };
        n++;
      }
    }
  }

  function paintHaze(c) {
    var span = Math.max(w, h);
    var spots = [
      [0.16, 0.24, 0.5, "rgba(32, 42, 72, 0.16)"],
      [0.8, 0.7, 0.4, "rgba(22, 32, 58, 0.12)"],
      [0.52, 0.1, 0.28, "rgba(46, 54, 82, 0.07)"],
      [0.58, 0.86, 0.34, "rgba(18, 28, 52, 0.09)"]
    ];
    var i;
    for (i = 0; i < spots.length; i++) {
      var spot = spots[i];
      var x = spot[0] * w;
      var y = spot[1] * h;
      var rad = spot[2] * span;
      var g = c.createRadialGradient(x, y, 0, x, y, rad);
      g.addColorStop(0, spot[3]);
      g.addColorStop(1, "rgba(0,0,0,0)");
      c.fillStyle = g;
      c.fillRect(x - rad, y - rad, rad * 2, rad * 2);
    }
    c.save();
    c.translate(w * 0.3, h * 0.42);
    c.rotate(-0.62);
    var band = c.createLinearGradient(0, -h * 0.16, 0, h * 0.16);
    band.addColorStop(0, "rgba(0,0,0,0)");
    band.addColorStop(0.5, "rgba(96, 110, 146, 0.045)");
    band.addColorStop(1, "rgba(0,0,0,0)");
    c.fillStyle = band;
    c.fillRect(-w, -h * 0.16, w * 2, h * 0.32);
    c.restore();
  }

  function paintStar(c, s, alpha) {
    if (s.halo && sprite) {
      c.globalAlpha = alpha * 0.8;
      c.drawImage(sprite, s.x - s.halo, s.y - s.halo, s.halo * 2, s.halo * 2);
    }
    c.globalAlpha = alpha;
    c.fillStyle = s.color;
    if (s.r <= 1.15) {
      c.fillRect(s.x - s.r, s.y - s.r, s.r * 2, s.r * 2);
    } else {
      c.beginPath();
      c.arc(s.x, s.y, s.r, 0, 6.283185307179586);
      c.fill();
    }
  }

  function paintBase() {
    base.width = Math.max(1, Math.round(w * dpr));
    base.height = Math.max(1, Math.round(h * dpr));
    bctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    bctx.globalAlpha = 1;
    bctx.fillStyle = "#000011";
    bctx.fillRect(0, 0, w, h);
    paintHaze(bctx);
    var i;
    for (i = 0; i < stars.length; i++) {
      if (!stars[i].tw) paintStar(bctx, stars[i], stars[i].a);
    }
    bctx.globalAlpha = 1;
  }

  function paintDynamic(now) {
    var t = now || 0;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.drawImage(base, 0, 0);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var i;
    var s;
    var alpha;
    for (i = 0; i < stars.length; i++) {
      s = stars[i];
      if (!s.tw) continue;
      if (reduced()) {
        alpha = s.a;
      } else {
        alpha = s.a * (0.9 + 0.1 * Math.sin(t * 0.001 * s.tw + s.phase));
      }
      paintStar(ctx, s, alpha);
    }
    ctx.globalAlpha = 1;
  }

  function layout() {
    if (disposed) return;
    var nextW = canvas.clientWidth;
    var nextH = canvas.clientHeight;
    if (nextW < 2 || nextH < 2) {
      nextW = window.innerWidth;
      nextH = window.innerHeight;
    }
    w = nextW;
    h = nextH;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.round(w * dpr));
    canvas.height = Math.max(1, Math.round(h * dpr));
    build();
    paintBase();
    paintDynamic(performance.now());
    if (reduced()) stop();
    else start();
  }

  function frame(now) {
    if (!running || disposed) return;
    paintDynamic(now);
    rafId = window.requestAnimationFrame(frame);
  }

  function start() {
    if (running || disposed || reduced()) return;
    running = true;
    rafId = window.requestAnimationFrame(frame);
  }

  function stop() {
    running = false;
    if (rafId) {
      window.cancelAnimationFrame(rafId);
      rafId = 0;
    }
  }

  function scheduleLayout() {
    if (resizeQueued || disposed) return;
    resizeQueued = true;
    window.requestAnimationFrame(function () {
      resizeQueued = false;
      layout();
    });
  }

  function onVisibility() {
    if (disposed) return;
    if (document.hidden || reduced()) {
      stop();
      return;
    }
    start();
  }

  function onMotion() {
    if (disposed) return;
    paintDynamic(performance.now());
    if (reduced()) stop();
    else if (!document.hidden) start();
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    stop();
    window.removeEventListener("resize", scheduleLayout);
    window.removeEventListener("pagehide", dispose);
    document.removeEventListener("visibilitychange", onVisibility);
    if (window.visualViewport) {
      window.visualViewport.removeEventListener("resize", scheduleLayout);
    }
    if (motionQuery) {
      if (motionQuery.removeEventListener) motionQuery.removeEventListener("change", onMotion);
      else if (motionQuery.removeListener) motionQuery.removeListener(onMotion);
    }
  }

  window.addEventListener("resize", scheduleLayout);
  window.addEventListener("pagehide", dispose);
  document.addEventListener("visibilitychange", onVisibility);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", scheduleLayout);
  }
  if (motionQuery) {
    if (motionQuery.addEventListener) motionQuery.addEventListener("change", onMotion);
    else if (motionQuery.addListener) motionQuery.addListener(onMotion);
  }

  layout();
})();
