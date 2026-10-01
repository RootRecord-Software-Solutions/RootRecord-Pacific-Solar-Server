(function () {
  var T = window.RRTelemetry;

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
    if (riverSub) riverSub.textContent = solarCaption("river-solar");
    if (deltaSub) deltaSub.textContent = solarCaption("delta-solar");
    setGauge("gauge-river", text("river-soc"));
    setGauge("gauge-delta", text("delta-soc"));
  }

  function watch(id) {
    var node = document.getElementById(id);
    if (!node) return;
    var observer = new MutationObserver(paintFlow);
    observer.observe(node, { childList: true, characterData: true, subtree: true });
  }

  ["river-soc", "delta-soc", "river-solar", "delta-solar", "river-ac", "delta-ac"].forEach(watch);
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
