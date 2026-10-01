(function () {
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var globeEl = document.getElementById("globe");
  var globe = null;
  var disposed = false;
  var hidden = false;
  var spinOn = false;
  var pullTimer = 0;

  function reduced() {
    return !!(reduceQuery && reduceQuery.matches);
  }

  function failGlobe() {
    if (globeEl) globeEl.hidden = true;
    var note = document.getElementById("globe-fallback");
    if (note) note.hidden = false;
  }

  function finitePair(lat, lng) {
    var a = Number(lat);
    var b = Number(lng);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
    if (Math.abs(a) > 90 || Math.abs(b) > 180) return null;
    return { lat: a, lng: b };
  }

  function placePart(value) {
    if (typeof value !== "string") return "";
    var text = value.trim();
    if (!text || text.length > 40) return "";
    if (!/^[A-Za-zÀ-ÿ .,'’\-]+$/.test(text)) return "";
    return text;
  }

  function near(a, b) {
    if (!a || !b) return false;
    var dLng = Math.abs(a.lng - b.lng);
    if (dLng > 180) dLng = 360 - dLng;
    return Math.abs(a.lat - b.lat) < 2 && dLng < 2;
  }

  function publicScene(d) {
    var points = [];
    var hawaii = null;
    var mainland = null;
    (d.points || []).forEach(function (p) {
      var pos = finitePair(p && p.lat, p && p.lng);
      if (!pos || !p.type) return;
      if (p.type === "origin") hawaii = pos;
      else if (p.type !== "dest" && p.type !== "remote" && !mainland) mainland = pos;
    });
    if (hawaii) points.push({ lat: hawaii.lat, lng: hawaii.lng, type: "hawaii", label: "Hawaiʻi" });
    if (mainland) points.push({ lat: mainland.lat, lng: mainland.lng, type: "mainland", label: "Mainland Server" });

    var vercel = { lat: 37.7749, lng: -122.4194 };
    points.push({
      lat: vercel.lat,
      lng: vercel.lng,
      type: "vercel",
      label: "Vercel · Transmitter / Receiver"
    });

    (d.points || []).forEach(function (p) {
      if (!p || (p.type !== "dest" && p.type !== "remote")) return;
      var pos = finitePair(p.lat, p.lng);
      if (!pos) return;
      var raw = typeof p.label === "string" ? p.label.split("·")[0] : "";
      var city = placePart(raw.split(",")[0]);
      var country = placePart(raw.indexOf(",") >= 0 ? raw.slice(raw.indexOf(",") + 1) : "");
      var label = [city, country].filter(Boolean).join(", ") || "Endpoint";
      points.push({ lat: pos.lat, lng: pos.lng, type: "endpoint", label: label });
    });

    var arcs = [];
    (d.arcs || []).forEach(function (a) {
      if (!a) return;
      var start = finitePair(a.startLat, a.startLng);
      var end = finitePair(a.endLat, a.endLng);
      if (!start || !end) return;
      var city = placePart(a.city);
      var country = placePart(a.country);
      var link = !city;
      if (!link && !country && !city) return;
      var fromHi = near(start, hawaii);
      var label = link ? "Root Record Network" : [city, country].filter(Boolean).join(", ");
      if (!label) return;
      arcs.push({
        startLat: start.lat,
        startLng: start.lng,
        endLat: end.lat,
        endLng: end.lng,
        color: link ? "#7dd3fc" : fromHi ? "#22c55e" : "#38bdf8",
        altitude: Number(a.altitude) > 0 && Number(a.altitude) < 1 ? Number(a.altitude) : link ? 0.22 : 0.16,
        stroke: a.stroke,
        label: label
      });
    });

    if (mainland) {
      arcs.push({
        startLat: mainland.lat,
        startLng: mainland.lng,
        endLat: vercel.lat,
        endLng: vercel.lng,
        color: "#7dd3fc",
        altitude: 0.18,
        stroke: 1.2,
        label: "Vercel · Transmitter / Receiver"
      });
    }
    if (hawaii) {
      arcs.push({
        startLat: hawaii.lat,
        startLng: hawaii.lng,
        endLat: vercel.lat,
        endLng: vercel.lng,
        color: "#22c55e",
        altitude: 0.2,
        stroke: 1.1,
        label: "Vercel · Transmitter / Receiver"
      });
    }

    return { points: points, arcs: arcs };
  }

  function draw(d) {
    if (!globe || !d) return;
    var scene = publicScene(d);
    globe.pointsData(scene.points);
    globe.arcsData(scene.arcs);
  }

  function plainEarth() {
    return Globe()(globeEl)
      .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-night.jpg")
      .backgroundColor("rgba(0,0,0,0)")
      .showAtmosphere(true)
      .atmosphereColor("#3a1c71")
      .atmosphereAltitude(0.18);
  }

  if (globeEl && typeof Globe === "function") {
    try {
      globe = Globe()(globeEl)
        .globeImageUrl("/assets/earth/night.jpg")
        .backgroundColor("rgba(0,0,0,0)")
        .showAtmosphere(true)
        .atmosphereColor("#8eb6ff")
        .atmosphereAltitude(0.13)
        .arcColor(function (d) { return d.color || "#22c55e"; })
        .arcAltitude(function (d) { return d.altitude || 0.16; })
        .arcStroke(function (d) {
          var s = Number(d && d.stroke);
          if (!isFinite(s) || s <= 0) s = 1.2;
          return Math.max(0.12, Math.min(0.28, s * 0.12));
        })
        .arcDashLength(0.4)
        .arcDashGap(0.28)
        .arcDashAnimateTime(reduced() ? 0 : 2800)
        .arcLabel(function (d) { return d.label || "Connection"; })
        .pointColor(function (d) {
          if (d.type === "hawaii") return "#ffffff";
          if (d.type === "mainland") return "#7dd3fc";
          if (d.type === "vercel") return "#ffffff";
          return "#ff6b9d";
        })
        .pointAltitude(function (d) { return d.type === "endpoint" ? 0.012 : 0.02; })
        .pointRadius(function (d) {
          if (d.type === "vercel") return 0.48;
          return d.type === "endpoint" ? 0.18 : 0.42;
        })
        .pointLabel(function (d) { return d.label || ""; })
        .pointsMerge(false);

      var controls = globe.controls();
      controls.enableZoom = false;
      controls.enablePan = false;
      globe.pointOfView({ lat: 16, lng: -156, altitude: 2.15 });
      var renderer = globe.renderer && globe.renderer();
      if (renderer && renderer.setPixelRatio) {
        var cap = window.innerWidth < 800 ? 1.15 : 1.5;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, cap));
      }

      spinOn = reduced() ? false : localStorage.getItem("rr-home:spin") !== "off";
      var spinBtn = document.getElementById("spin");
      function applySpin() {
        controls.autoRotate = !!(spinOn && !reduced() && !hidden);
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
      globe._rrApplySpin = applySpin;

      var canvas = globeEl.querySelector("canvas");
      if (canvas) {
        canvas.addEventListener("webglcontextlost", function (event) {
          event.preventDefault();
          failGlobe();
        });
      }
    } catch (err) {
      try {
        globe = plainEarth();
        var fallbackControls = globe.controls();
        fallbackControls.enableZoom = false;
        fallbackControls.autoRotate = !reduced();
        fallbackControls.autoRotateSpeed = 0.35;
        globe.pointOfView({ lat: 16, lng: -156, altitude: 2.15 });
      } catch (err2) {
        globe = null;
        failGlobe();
      }
    }
  } else {
    failGlobe();
  }

  if (window.RRTelemetry && globe) {
    function pull() {
      window.RRTelemetry.readState().then(draw).catch(function () {});
    }
    pull();
    pullTimer = window.setInterval(pull, 5000);
  }

  function onVisibility() {
    hidden = document.hidden;
    if (!globe) return;
    if (hidden) {
      if (globe.pauseAnimation) globe.pauseAnimation();
    } else if (globe.resumeAnimation) {
      globe.resumeAnimation();
    }
    if (globe._rrApplySpin) globe._rrApplySpin();
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    if (pullTimer) window.clearInterval(pullTimer);
    document.removeEventListener("visibilitychange", onVisibility);
    window.removeEventListener("pagehide", dispose);
    if (globe && globe.pauseAnimation) globe.pauseAnimation();
    var renderer = globe && globe.renderer && globe.renderer();
    if (renderer) {
      renderer.dispose();
      if (renderer.forceContextLoss) renderer.forceContextLoss();
    }
  }

  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("pagehide", dispose);
})();