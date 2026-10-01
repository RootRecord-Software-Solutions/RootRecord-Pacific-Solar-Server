(function () {
  var T = window.RRTelemetry;
  if (!T) return;

  var STATE_STALE_MS = 20000;
  var ENERGY_STALE_MS = 20 * 60 * 1000;
  var WEATHER_STALE_MS = 3 * 60 * 60 * 1000;
  var GEO_STALE_MS = 6 * 60 * 60 * 1000;

  function text(id, value) {
    var node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function paintStatusWord() {
    var node = document.getElementById("net-status");
    if (!node) return;
    var shown = stateWord;
    if (stateWord === "LIVE" && node.getAttribute("data-live-label")) {
      shown = node.getAttribute("data-live-label");
    }
    node.textContent = shown;
  }

  function led(id, mode) {
    var node = document.getElementById(id);
    if (!node) return;
    node.className = mode === "live" ? "led up" : mode === "stale" ? "led stale" : "led";
  }

  var stateSeen = false;
  var stateAt = null;
  var stateLive = false;
  var stateWord = "LOADING";
  var opsSeen = false;
  var opsAt = null;
  var lastReadings = null;

  function wordFrom(hasSignal, fresh) {
    if (!navigator.onLine) return "OFFLINE";
    if (!hasSignal) return "NO PUBLIC SIGNAL";
    if (!fresh) return "STALE";
    return "LIVE";
  }

  function paintAge() {
    var node = document.getElementById("net-fresh");
    if (!node) return;
    if (stateWord === "LOADING") {
      node.textContent = "Loading public telemetry...";
      return;
    }
    if (stateWord === "LIVE" && stateAt) {
      node.textContent = T.agePhrase(stateAt);
      return;
    }
    if (stateWord === "STALE" && stateAt) {
      node.textContent = "Last known observation · " + T.agePhrase(stateAt).replace("Updated ", "");
      return;
    }
    if (stateWord === "OFFLINE") {
      node.textContent = stateAt ? "Public feed unavailable · " + T.agePhrase(stateAt) : "Public feed unavailable";
      return;
    }
    node.textContent = "No public signal";
  }

  function obsWord(at, limit) {
    if (at === null || at === undefined) return "NO PUBLIC SIGNAL";
    if (Date.now() - at > limit) return "STALE";
    return "REPORTING";
  }

  function paintState(d) {
    var s = (d && d.stats) || {};
    var hi = T.finite(s.hawaiiActiveFlows);
    var main = T.finite(s.localActiveFlows);
    var flows = T.finite(s.activeFlows);
    var ends = T.finite(s.endpoints);
    var has = hi !== null || main !== null || flows !== null || ends !== null;
    stateSeen = true;
    stateAt = Date.now();
    stateLive = true;
    stateWord = wordFrom(has, true);
    paintStatusWord();
    led("net-dot", stateWord === "LIVE" ? "live" : stateWord === "STALE" ? "stale" : "off");
    text("hi-flows", hi === null ? "NO READING" : T.fmt(hi));
    text("ms-flows", main === null ? "NO READING" : T.fmt(main));
    text("active-flows", flows === null ? "NO READING" : T.fmt(flows));
    text("endpoints", ends === null ? "NO READING" : T.fmt(ends));
    text("field-hi", hi === null ? "NO READING" : T.fmt(hi) + " flows");
    text("field-ms", main === null ? "NO READING" : T.fmt(main) + " flows");
    text("val-hi", hi === null ? "NO PUBLIC SIGNAL" : T.fmt(hi) + " flows");
    text("val-ms", main === null ? "NO PUBLIC SIGNAL" : T.fmt(main) + " flows");
    var clock = T.formatHst(stateAt, false);
    text("last-update", clock || "—");
    text("last-label", "Last update");
    var feed = document.getElementById("feed-line");
    if (feed) {
      feed.textContent = stateWord === "LIVE" ? "Network feed live" : stateWord === "NO PUBLIC SIGNAL" ? "No public signal" : stateWord;
    }
    text("arch-runtime", has ? "Reporting" : "No public runtime signal");
    text("val-runtime", has ? "Reporting" : "No public signal");
    led("led-runtime", has ? "live" : "off");
    paintAge();
  }

  function paintStateMiss() {
    stateLive = false;
    if (!navigator.onLine) stateWord = "OFFLINE";
    else if (stateSeen) stateWord = "STALE";
    else stateWord = "NO PUBLIC SIGNAL";
    paintStatusWord();
    led("net-dot", stateWord === "STALE" ? "stale" : "off");
    if (!stateSeen) {
      ["hi-flows", "ms-flows", "active-flows", "endpoints"].forEach(function (id) {
        text(id, "NO READING");
      });
      ["field-hi", "field-ms", "val-hi", "val-ms"].forEach(function (id) {
        text(id, "NO PUBLIC SIGNAL");
      });
      text("arch-runtime", "No public runtime signal");
      text("val-runtime", "No public signal");
      led("led-runtime", "off");
    }
    var feed = document.getElementById("feed-line");
    if (feed) feed.textContent = stateWord === "OFFLINE" ? "Public feed unavailable" : stateSeen ? "Last known observation" : "No public signal";
    paintAge();
  }

  function deviceLine(reading) {
    if (!reading) return "NO READING";
    var parts = [];
    if (reading.soc !== null) parts.push(T.pct(reading.soc));
    if (reading.solar !== null) parts.push(T.watts(reading.solar) + " solar");
    return parts.length ? parts.join(" · ") : "NO READING";
  }

  function fillDevice(prefix, reading, staleMs) {
    if (!reading) {
      text(prefix + "-soc", "NO READING");
      text(prefix + "-solar", "NO READING");
      text(prefix + "-ac", "NO READING");
      text(prefix + "-usb", "NO READING");
      text(prefix + "-at", "—");
      text("st-" + prefix, "NO PUBLIC SIGNAL");
      text("val-" + prefix, "NO READING");
      text("at-" + prefix, "—");
      return;
    }
    text(prefix + "-soc", reading.soc === null ? "NO READING" : T.pct(reading.soc));
    text(prefix + "-solar", reading.solar === null ? "NO READING" : T.watts(reading.solar));
    text(prefix + "-ac", reading.acOut === null ? "NO READING" : T.watts(reading.acOut));
    text(prefix + "-usb", reading.usbc === null ? "NO READING" : T.watts(reading.usbc));
    text(prefix + "-at", reading.at ? T.formatHst(reading.at, true) : "—");
    text("st-" + prefix, obsWord(reading.at, staleMs));
    text("val-" + prefix, deviceLine(reading));
    text("at-" + prefix, reading.at ? T.formatHst(reading.at, true) : "—");
  }

  function bar(name, value, textValue, at) {
    if (value === null || value === undefined) return null;
    return { name: name, value: value, text: textValue, at: at };
  }

  function paintCharts(r) {
    if (!window.RRCharts) return;
    window.RRCharts.bars(document.getElementById("chart-soc"), {
      label: "Current state of charge",
      question: "How does stored energy compare between River and Delta right now?",
      max: 100,
      empty: "No public signal",
      bars: [
        r.river ? bar("River", r.river.soc, T.pct(r.river.soc), r.river.at) : null,
        r.delta ? bar("Delta", r.delta.soc, T.pct(r.delta.soc), r.delta.at) : null
      ].filter(Boolean)
    });
    window.RRCharts.bars(document.getElementById("chart-solar"), {
      label: "Current solar input",
      question: "What solar input is each system reporting right now?",
      empty: "No public signal",
      bars: [
        r.river ? bar("River", r.river.solar, T.watts(r.river.solar), r.river.at) : null,
        r.delta ? bar("Delta", r.delta.solar, T.watts(r.delta.solar), r.delta.at) : null
      ].filter(Boolean)
    });
    window.RRCharts.bars(document.getElementById("chart-output"), {
      label: "Current AC output",
      question: "What AC output is each system reporting right now?",
      empty: "No public signal",
      bars: [
        r.river ? bar("River", r.river.acOut, T.watts(r.river.acOut), r.river.at) : null,
        r.delta ? bar("Delta", r.delta.acOut, T.watts(r.delta.acOut), r.delta.at) : null
      ].filter(Boolean)
    });
  }

  var MOON_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function moonDateLabel(iso) {
    var match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!match) return "";
    var month = MOON_MONTHS[Number(match[2]) - 1];
    if (!month) return "";
    return month + " " + Number(match[3]);
  }

  function moonLitPath(phase) {
    if (phase === null || phase === undefined || !Number.isFinite(phase)) return "";
    var p = ((phase % 1) + 1) % 1;
    var radius = 46;
    var cx = 50;
    var cy = 50;
    if (p < 0.005 || p > 0.995) return "";
    if (Math.abs(p - 0.5) < 0.008) {
      return "M " + cx + " " + (cy - radius) + " a " + radius + " " + radius + " 0 1 1 0 " + (2 * radius) + " a " + radius + " " + radius + " 0 1 1 0 " + (-2 * radius) + " Z";
    }
    var waxing = p < 0.5;
    var curve = Math.cos(2 * Math.PI * p);
    var rx = Math.max(0.4, Math.abs(curve) * radius);
    var outer = waxing ? 1 : 0;
    var term = curve >= 0 ? outer : (outer ? 0 : 1);
    return "M " + cx + " " + (cy - radius)
      + " A " + radius + " " + radius + " 0 0 " + outer + " " + cx + " " + (cy + radius)
      + " A " + rx.toFixed(2) + " " + radius + " 0 0 " + term + " " + cx + " " + (cy - radius)
      + " Z";
  }

  function drawMoon(phase) {
    var path = document.getElementById("moon-lit");
    if (path) path.setAttribute("d", moonLitPath(phase));
  }

  function paintMoonClock() {
    var node = document.getElementById("moon-when");
    if (!node) return;
    var parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "Pacific/Honolulu",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23"
    }).formatToParts(new Date());
    var map = {};
    parts.forEach(function (part) {
      if (part.type !== "literal") map[part.type] = part.value;
    });
    if (!map.month || !map.day || map.hour === undefined || !map.minute) return;
    node.textContent = map.month.toUpperCase() + " " + Number(map.day) + " · " + map.hour + ":" + map.minute + " HST";
  }

  function paintMoon(moon) {
    if (!document.getElementById("moon-phase-name")) return;
    paintMoonClock();
    if (!moon) {
      text("moon-phase-name", "Unavailable");
      text("moon-illum", "Saved reading is not on the feed");
      text("moon-next", "Next phase unavailable");
      drawMoon(null);
      return;
    }
    text("moon-phase-name", moon.name || "Moon");
    text("moon-illum", moon.illumination === null ? "Illumination unavailable" : Math.round(moon.illumination) + "% illuminated");
    var next = moon.nextName ? "Next · " + moon.nextName : "Next phase unavailable";
    var when = moon.nextName ? moonDateLabel(moon.nextDate) : "";
    text("moon-next", when ? next + " · " + when : next);
    drawMoon(moon.phase);
  }

  function paintOps(ops) {
    var r = T.fieldReadings(ops);
    lastReadings = r;
    opsSeen = true;
    opsAt = Date.now();
    text("river", deviceLine(r.river));
    text("delta", deviceLine(r.delta));
    fillDevice("river", r.river, ENERGY_STALE_MS);
    fillDevice("delta", r.delta, ENERGY_STALE_MS);

    var weatherValue = r.weatherAt ? T.formatHst(r.weatherAt, true) : (r.weatherText || null);
    text("weather", weatherValue || "NO READING");
    text("weather-at", weatherValue || "—");
    text("st-weather", r.weatherAt || r.weatherText ? obsWord(r.weatherAt, WEATHER_STALE_MS) : "NO PUBLIC SIGNAL");
    text("val-weather", weatherValue || "NO PUBLIC SIGNAL");
    text("at-weather", weatherValue || "—");
    led("led-weather", weatherValue ? "live" : "off");

    var geo = r.kilauea;
    var geoValue = null;
    if (geo) {
      geoValue = [geo.headline, geo.alert, geo.code].filter(Boolean).join(" · ");
      text("kilauea-level", geo.alert || "NO READING");
      text("kilauea-code", geo.code || "NO READING");
      text("kilauea-line", geo.headline || "NO READING");
      text("kilauea-at", geo.at ? T.formatHst(geo.at, true) : "—");
      if (geo.erupting === true) text("kilauea-erupt", "Eruption reported");
      else if (geo.erupting === false) text("kilauea-erupt", "No eruption reported");
      else text("kilauea-erupt", "NO READING");
    } else {
      ["kilauea-level", "kilauea-code", "kilauea-line", "kilauea-erupt"].forEach(function (id) {
        text(id, "NO READING");
      });
      text("kilauea-at", "—");
    }
    text("kilauea", geoValue || "NO READING");
    text("st-geology", geo ? obsWord(geo.at, GEO_STALE_MS) : "NO PUBLIC SIGNAL");
    text("val-geology", geoValue || "NO PUBLIC SIGNAL");
    text("at-geology", geo && geo.at ? T.formatHst(geo.at, true) : "—");
    led("led-geology", geoValue ? "live" : "off");

    var energyBits = [r.river && ("River " + deviceLine(r.river)), r.delta && ("Delta " + deviceLine(r.delta))].filter(Boolean);
    text("val-energy", energyBits.length ? energyBits.join(" · ") : "NO PUBLIC SIGNAL");
    led("led-energy", energyBits.length ? "live" : "off");

    var asof = document.getElementById("field-asof");
    if (asof) asof.textContent = r.asOf ? "Last known · " + r.asOf : "Last known · No public signal";
    text("ops-fresh", "Updated just now");
    paintCharts(r);
    paintMoon(r.moon);
  }

  function paintOpsMiss() {
    text("ops-fresh", opsSeen ? "Last known observation" : "Public feed unavailable");
    if (opsSeen) return;
    paintMoon(null);
    ["river", "delta", "weather", "kilauea"].forEach(function (id) { text(id, "NO READING"); });
    var asof = document.getElementById("field-asof");
    if (asof) asof.textContent = "Last known · No public signal";
    text("val-energy", "NO PUBLIC SIGNAL");
    text("val-weather", "NO PUBLIC SIGNAL");
    text("val-geology", "NO PUBLIC SIGNAL");
    led("led-energy", "off");
    led("led-weather", "off");
    led("led-geology", "off");
    fillDevice("river", null, ENERGY_STALE_MS);
    fillDevice("delta", null, ENERGY_STALE_MS);
    text("st-weather", "NO PUBLIC SIGNAL");
    text("st-geology", "NO PUBLIC SIGNAL");
    if (window.RRCharts) {
      ["chart-soc", "chart-solar", "chart-output"].forEach(function (id) {
        window.RRCharts.bars(document.getElementById(id), { bars: [], empty: "No public signal" });
      });
    }
  }

  var noticeDoc = { windows: [] };

  function planNode() {
    var node = document.getElementById("net-plan");
    if (node) return node;
    var fresh = document.getElementById("net-fresh");
    if (!fresh || !fresh.parentNode) return null;
    node = document.createElement("p");
    node.id = "net-plan";
    node.className = "fine";
    node.hidden = true;
    fresh.parentNode.insertBefore(node, fresh.nextSibling);
    return node;
  }

  function countText(value) {
    var n = T.finite(value);
    return n === null ? null : T.fmt(n);
  }

  function applyNotice() {
    var chosen = T.noticePhase ? T.noticePhase(noticeDoc, Date.now()) : null;
    var plan = planNode();
    var feed = document.getElementById("feed-line");
    if (!chosen) {
      if (plan) plan.hidden = true;
      return;
    }
    var back = T.formatHst(chosen.up, true);
    var down = T.formatHst(chosen.down, true);
    var known = chosen.window.last_known || {};
    var knownAt = T.formatHst(known.at, true);
    if (chosen.phase === "down") {
      stateWord = "PLANNED DOWN";
      paintStatusWord();
      led("net-dot", "stale");
      var hi = countText(known.hawaii);
      var main = countText(known.mainland);
      var flows = countText(known.flows);
      var ends = countText(known.endpoints);
      if (hi !== null) {
        text("hi-flows", hi);
        text("field-hi", hi + " flows");
        text("val-hi", hi + " flows");
      }
      if (main !== null) {
        text("ms-flows", main);
        text("field-ms", main + " flows");
        text("val-ms", main + " flows");
      }
      if (flows !== null) text("active-flows", flows);
      if (ends !== null) text("endpoints", ends);
      text("last-label", "Last known");
      text("last-update", knownAt || "—");
      text("net-fresh", back ? "Expected back online · " + back : "Expected back online");
      if (plan) {
        plan.hidden = false;
        plan.textContent = "Planned service window. The counts above are the last known network state.";
      }
      if (feed) feed.textContent = back ? "Planned service window · expected back " + back : "Planned service window";
      return;
    }
    if (plan) {
      plan.hidden = false;
      plan.textContent = "Planned pause " + (down || "soon") + ". Expected back online " + (back || "later") + ".";
    }
  }

  function tickState() {
    if (stateAt && Date.now() - stateAt > STATE_STALE_MS && stateWord === "LIVE") {
      stateWord = navigator.onLine ? "STALE" : "OFFLINE";
      paintStatusWord();
      led("net-dot", stateWord === "STALE" ? "stale" : "off");
      var feed = document.getElementById("feed-line");
      if (feed) feed.textContent = "Last known observation";
    }
    paintAge();
    T.readState().then(function (d) {
      paintState(d);
      applyNotice();
    }).catch(function () {
      paintStateMiss();
      applyNotice();
    });
  }

  function tickNotice() {
    if (!T.readNotice) return;
    T.readNotice().then(function (doc) {
      noticeDoc = doc || { windows: [] };
      applyNotice();
    });
  }

  function tickOps() {
    T.readOps().then(paintOps).catch(paintOpsMiss);
  }

  tickNotice();
  tickState();
  tickOps();
  paintMoonClock();
  var stateTimer = setInterval(tickState, 5000);
  var opsTimer = setInterval(tickOps, 60000);
  var noticeTimer = setInterval(tickNotice, 60000);
  var moonTimer = setInterval(paintMoonClock, 30000);
  window.addEventListener("offline", function () {
    paintStateMiss();
    applyNotice();
  });
  window.addEventListener("online", tickState);
  window.addEventListener("pagehide", function () {
    clearInterval(stateTimer);
    clearInterval(opsTimer);
    clearInterval(noticeTimer);
    clearInterval(moonTimer);
  });
})();
