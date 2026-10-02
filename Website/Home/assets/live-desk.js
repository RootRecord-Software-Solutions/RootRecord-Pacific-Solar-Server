(function () {
  var T = window.RRTelemetry;

  function viewportSize() {
    // Layout viewport, same box OBS uses for the browser source.
    // documentElement.clientWidth/clientHeight can be smaller and, with a
    // negative translate, slide the desk off the left edge.
    return {
      vw: window.innerWidth,
      vh: window.innerHeight
    };
  }

  function fitDesk() {
    var hud = document.querySelector(".broadcast-hud");
    if (!hud) return;
    var view = viewportSize();
    if (view.vw < 2 || view.vh < 2) return;
    // Contain the 1920×1080 desk. Cover (Math.max) crops the gauges.
    var scale = Math.min(view.vw / 1920, view.vh / 1080);
    if (!isFinite(scale) || scale <= 0) scale = 1;
    var x = (view.vw - 1920 * scale) / 2;
    var y = (view.vh - 1080 * scale) / 2;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    hud.style.transform = "translate(" + x + "px," + y + "px) scale(" + scale + ")";
  }

  fitDesk();
  window.addEventListener("resize", fitDesk);
  if (window.visualViewport) window.visualViewport.addEventListener("resize", fitDesk);

  function text(id) {
    var node = document.getElementById(id);
    return node ? node.textContent : "";
  }

  function numberFrom(raw, unit) {
    var source = String(raw || "");
    if (/NO READING|NO PUBLIC|—/.test(source)) return null;
    if (unit === "%" && source.indexOf("%") === -1) return null;
    if (unit === "W" && source.indexOf("W") === -1) return null;
    var match = source.replace(/,/g, "").match(/(-?\d+(?:\.\d+)?)/);
    if (!match) return null;
    var value = Number(match[1]);
    return Number.isFinite(value) ? value : null;
  }

  function setGauge(id, raw) {
    var node = document.getElementById(id);
    if (!node) return;
    var pct = numberFrom(raw, "%");
    var clamped = pct === null ? 0 : Math.max(0, Math.min(100, pct));
    node.style.setProperty("--p", clamped + "%");
  }

  function sum(ids, unit) {
    var total = 0;
    var count = 0;
    ids.forEach(function (id) {
      var value = numberFrom(text(id), unit);
      if (value === null) return;
      total += value;
      count += 1;
    });
    return count ? total : null;
  }

  function mean(ids, unit) {
    var total = 0;
    var count = 0;
    ids.forEach(function (id) {
      var value = numberFrom(text(id), unit);
      if (value === null) return;
      total += value;
      count += 1;
    });
    return count ? total / count : null;
  }

  function solarCaption(id) {
    var raw = text(id);
    return numberFrom(raw, "W") === null ? raw : raw + " solar";
  }

  function ringCaption(prefix) {
    var label = document.getElementById(prefix + "-acin-label");
    var incoming = text(prefix + "-acin");
    if (label && /generator/i.test(label.textContent) && numberFrom(incoming, "W") !== null) {
      return incoming + " generator";
    }
    return solarCaption(prefix + "-solar");
  }

  function paintFlow() {
    var solar = sum(["river-solar", "delta-solar"], "W");
    var bank = mean(["river-soc", "delta-soc"], "%");
    var ac = sum(["river-ac", "delta-ac"], "W");
    var flowIn = document.getElementById("flow-in");
    var flowBank = document.getElementById("flow-bank");
    var flowOut = document.getElementById("flow-out");
    if (flowIn) flowIn.textContent = solar === null || !T ? "—" : T.watts(solar);
    if (flowBank) flowBank.textContent = bank === null || !T ? "—" : T.pct(bank);
    if (flowOut) flowOut.textContent = ac === null || !T ? "—" : T.watts(ac);
    var riverSub = document.getElementById("ring-river-sub");
    var deltaSub = document.getElementById("ring-delta-sub");
    if (riverSub) riverSub.textContent = ringCaption("river");
    if (deltaSub) deltaSub.textContent = ringCaption("delta");
    setGauge("gauge-river", text("river-soc"));
    setGauge("gauge-delta", text("delta-soc"));
  }

  function watch(id) {
    var node = document.getElementById(id);
    if (!node) return;
    var observer = new MutationObserver(paintFlow);
    observer.observe(node, { childList: true, characterData: true, subtree: true });
  }

  ["river-soc", "delta-soc", "river-solar", "delta-solar", "river-ac", "delta-ac", "river-acin", "delta-acin"].forEach(watch);
  paintFlow();

  function clock() {
    var parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "Pacific/Honolulu",
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23"
    }).formatToParts(new Date());
    var map = {};
    parts.forEach(function (part) {
      if (part.type !== "literal") map[part.type] = part.value;
    });
    var date = document.getElementById("b-date");
    var time = document.getElementById("b-time");
    if (date && map.weekday && map.month && map.day) {
      date.textContent = map.weekday + " " + map.month + " " + Number(map.day) + " · HST";
    }
    if (time && map.hour !== undefined && map.minute && map.second) {
      time.textContent = map.hour + ":" + map.minute + ":" + map.second;
    }
  }

  clock();
  window.setInterval(clock, 1000);
})();
