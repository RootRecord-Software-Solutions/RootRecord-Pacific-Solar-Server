(function () {
  var T = window.RRTelemetry;
  if (!T) return;

  function text(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function led(id, up) {
    var el = document.getElementById(id);
    if (!el) return;
    el.className = up ? "led up" : "led";
  }

  function showOrDash(id, value) {
    text(id, value == null || value === "" ? "—" : value);
  }

  var stateSeen = false;

  function paintState(d) {
    var s = (d && d.stats) || {};
    var hi = T.finite(s.hawaiiActiveFlows);
    var main = T.finite(s.localActiveFlows);
    var flows = T.finite(s.activeFlows);
    var ends = T.finite(s.endpoints);
    var live = hi !== null || main !== null || flows !== null || ends !== null;
    text("net-status", live ? "LIVE" : "NO SIGNAL");
    led("net-dot", live);
    showOrDash("hi-flows", hi === null ? null : T.fmt(hi));
    showOrDash("ms-flows", main === null ? null : T.fmt(main));
    showOrDash("active-flows", flows === null ? null : T.fmt(flows));
    showOrDash("endpoints", ends === null ? null : T.fmt(ends));
    showOrDash("field-hi", hi === null ? null : T.fmt(hi) + " flows");
    showOrDash("field-ms", main === null ? null : T.fmt(main) + " flows");

    var hiLabel = hi === null ? "No signal" : T.fmt(hi) + " flows";
    var msLabel = main === null ? "No signal" : T.fmt(main) + " flows";
    text("val-hi", hiLabel);
    text("val-ms", msLabel);
    led("led-hi", hi !== null);
    led("led-ms", main !== null);

    var clock = T.utcClock(s.updated || (d && d.ts));
    var last = document.getElementById("last-update");
    if (clock && last) {
      last.textContent = clock;
      last.dataset.source = "state";
      text("last-label", "Last update");
    }
    var feed = document.getElementById("feed-line");
    if (feed) feed.textContent = live ? "Network feed live" : "Network feed has no counts";
    stateSeen = true;
  }

  function paintStateMiss() {
    text("net-status", "UNREACHABLE");
    led("net-dot", false);
    if (!stateSeen) {
      ["hi-flows", "ms-flows", "active-flows", "endpoints", "field-hi", "field-ms"].forEach(function (id) {
        text(id, "—");
      });
      text("val-hi", "No signal");
      text("val-ms", "No signal");
      led("led-hi", false);
      led("led-ms", false);
    }
    var feed = document.getElementById("feed-line");
    if (feed && !stateSeen) feed.textContent = "Network feed unreachable";
    if (feed && stateSeen) feed.textContent = "Network feed unreachable";
  }

  var opsSeen = false;

  function paintOps(ops) {
    var r = T.fieldReadings(ops);
    showOrDash("river", r.river);
    showOrDash("delta", r.delta);
    showOrDash("weather", r.weather);
    showOrDash("kilauea", r.kilauea);
    var asof = document.getElementById("field-asof");
    if (asof) asof.textContent = r.asOf ? "Last known · " + r.asOf : "Last known · No data";

    var energy = [r.river && ("River " + r.river), r.delta && ("Delta " + r.delta)].filter(Boolean).join(" · ");
    text("val-energy", energy || "No signal");
    text("val-weather", r.weather || "No signal");
    text("val-geology", r.kilauea || "No signal");
    led("led-energy", !!energy);
    led("led-weather", !!r.weather);
    led("led-geology", !!r.kilauea);
    var last = document.getElementById("last-update");
    if (r.asOf && last && last.dataset.source !== "state" && (last.textContent === "—" || last.dataset.source === "ops")) {
      last.textContent = r.asOf;
      last.dataset.source = "ops";
      text("last-label", "Last known");
    }
    opsSeen = true;
  }

  function paintOpsMiss() {
    if (opsSeen) return;
    ["river", "delta", "weather", "kilauea"].forEach(function (id) { text(id, "No data"); });
    var asof = document.getElementById("field-asof");
    if (asof) asof.textContent = "Last known · No data";
    text("val-energy", "No signal");
    text("val-weather", "No signal");
    text("val-geology", "No signal");
    led("led-energy", false);
    led("led-weather", false);
    led("led-geology", false);
  }

  function tickState() {
    T.readState().then(paintState).catch(paintStateMiss);
  }

  function tickOps() {
    T.readOps().then(paintOps).catch(paintOpsMiss);
  }

  tickState();
  tickOps();
  setInterval(tickState, 5000);
  setInterval(tickOps, 60000);
})();
