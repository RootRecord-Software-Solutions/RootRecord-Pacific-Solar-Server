(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var globeEl = document.getElementById("globe");
  var globe = null;

  if (globeEl && typeof Globe === "function") {
    globe = Globe()(globeEl)
      .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-night.jpg")
      .backgroundColor("rgba(0,0,0,0)")
      .showAtmosphere(true)
      .atmosphereColor("#3a1c71")
      .atmosphereAltitude(0.18)
      .arcColor(function (d) { return d.color || "#22c55e"; })
      .arcAltitude(function (d) { return d.altitude || 0.16; })
      .arcStroke(function (d) {
        var s = Number(d && d.stroke);
        if (!isFinite(s) || s <= 0) s = 1.2;
        return Math.max(0.1, Math.min(0.22, s * 0.12));
      })
      .arcDashLength(0.4)
      .arcDashGap(0.28)
      .arcDashAnimateTime(reduce ? 0 : 2200)
      .arcLabel(function (d) { return d.label || "Connection"; })
      .pointColor(function (d) {
        if (d.type === "hawaii") return "#ffffff";
        if (d.type === "mainland") return "#38bdf8";
        return "#ff6b9d";
      })
      .pointAltitude(function (d) { return d.type === "endpoint" ? 0.01 : 0.02; })
      .pointRadius(function (d) { return d.type === "endpoint" ? 0.18 : 0.35; })
      .pointLabel(function (d) { return d.label || ""; })
      .pointsMerge(false);

    var controls = globe.controls();
    controls.enableZoom = false;
    var spinOn = reduce ? false : localStorage.getItem("rr-home:spin") !== "off";
    var spinBtn = document.getElementById("spin");
    function applySpin() {
      controls.autoRotate = spinOn;
      controls.autoRotateSpeed = 0.35;
      if (!spinBtn) return;
      spinBtn.textContent = spinOn ? "Stop spin" : "Resume spin";
      spinBtn.setAttribute("aria-pressed", spinOn ? "true" : "false");
    }
    if (spinBtn) {
      spinBtn.addEventListener("click", function () {
        spinOn = !spinOn;
        localStorage.setItem("rr-home:spin", spinOn ? "on" : "off");
        applySpin();
      });
    }
    applySpin();
  }

  function finitePair(lat, lng) {
    var a = Number(lat);
    var b = Number(lng);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
    return { lat: a, lng: b };
  }

  function publicPoint(p) {
    var pos = p && finitePair(p.lat, p.lng);
    if (!pos) return null;
    if (p.type === "origin") return { lat: pos.lat, lng: pos.lng, type: "hawaii", label: "Hawaiʻi" };
    if (p.type === "remote" || p.type === "dest") {
      var place = [p.city, p.country].filter(Boolean).join(", ");
      return { lat: pos.lat, lng: pos.lng, type: "endpoint", label: place || "Endpoint" };
    }
    return null;
  }

  function publicArc(a) {
    if (!a) return null;
    var place = [a.city, a.country].filter(Boolean).join(", ");
    if (!place) return null;
    var start = finitePair(a.startLat, a.startLng);
    var end = finitePair(a.endLat, a.endLng);
    if (!start || !end) return null;
    return {
      startLat: start.lat,
      startLng: start.lng,
      endLat: end.lat,
      endLng: end.lng,
      color: a.color || "#22c55e",
      altitude: Number(a.altitude) || 0.16,
      stroke: a.stroke,
      label: place
    };
  }

  function draw(d) {
    if (!globe || !d) return;
    var points = [];
    var mainland = null;
    (d.points || []).forEach(function (p) {
      var pub = publicPoint(p);
      if (pub) {
        points.push(pub);
        return;
      }
      var pos = p && finitePair(p.lat, p.lng);
      if (!mainland && pos) {
        mainland = { lat: pos.lat, lng: pos.lng, type: "mainland", label: "Mainland Server" };
      }
    });
    if (mainland) points.push(mainland);
    var arcs = [];
    (d.arcs || []).forEach(function (a) {
      var arc = publicArc(a);
      if (arc) arcs.push(arc);
    });
    globe.pointsData(points);
    globe.arcsData(arcs);
  }

  if (window.RRTelemetry && globe) {
    function pull() {
      window.RRTelemetry.readState().then(draw).catch(function () {});
    }
    pull();
    setInterval(pull, 5000);
  }

  document.querySelectorAll(".node-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("aria-controls");
      var panel = document.getElementById(id);
      var open = btn.getAttribute("aria-expanded") !== "true";
      document.querySelectorAll(".node-btn").forEach(function (other) {
        other.setAttribute("aria-expanded", "false");
      });
      document.querySelectorAll(".expand").forEach(function (item) { item.hidden = true; });
      if (open && panel) {
        btn.setAttribute("aria-expanded", "true");
        panel.hidden = false;
      }
    });
  });
})();
