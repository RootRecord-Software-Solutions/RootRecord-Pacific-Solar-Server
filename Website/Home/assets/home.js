(function () {
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var globeEl = document.getElementById("globe");
  var globe = null;
  var disposed = false;
  var hidden = false;
  var spinOn = false;
  var pullTimer = 0;
  var quakeTimer = 0;
  var quakeSig = "";

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
      label: "Website Node"
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
        label: "Website Node"
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
        label: "Website Node"
      });
    }

    return { points: points, arcs: arcs };
  }

  function quakeLabel(d) {
    var mag = Number(d.mag);
    var magText = Number.isFinite(mag) ? "M" + (Math.round(mag * 10) / 10).toFixed(1) : "Earthquake";
    var place = typeof d.place === "string" ? d.place.replace(/\s+/g, " ").trim() : "";
    if (place.length > 140) place = place.slice(0, 140);
    return place ? magText + ", " + place : magText;
  }

  function quakeElement(d) {
    var hold = document.createElement("span");
    hold.className = "quake-dot";
    var core = document.createElement("span");
    core.className = "quake-core";
    var mag = Number(d.mag);
    if (mag >= 6) core.classList.add("quake-m6");
    else if (mag >= 5) core.classList.add("quake-m5");
    else if (mag >= 4) core.classList.add("quake-m4");
    var shift = 0;
    var id = String(d.id || "");
    for (var i = 0; i < id.length; i++) shift = (shift + id.charCodeAt(i)) % 16;
    core.style.animationDelay = (-shift / 10) + "s";
    var label = quakeLabel(d);
    core.title = label;
    core.setAttribute("role", "img");
    core.setAttribute("aria-label", label);
    hold.appendChild(core);
    return hold;
  }

  function eventsFromGeo(geo, into, seen) {
    var features = geo && geo.features;
    if (!Array.isArray(features)) return;
    features.forEach(function (f) {
      if (!f || !f.geometry || f.geometry.type !== "Point") return;
      var coords = f.geometry.coordinates || [];
      var pos = finitePair(coords[1], coords[0]);
      if (!pos) return;
      var props = f.properties || {};
      if (props.type && props.type !== "earthquake") return;
      var id = String(f.id || props.code || (pos.lat + "," + pos.lng));
      if (seen[id]) return;
      seen[id] = true;
      var mag = Number(props.mag);
      into.push({
        id: id,
        lat: pos.lat,
        lng: pos.lng,
        mag: Number.isFinite(mag) ? mag : null,
        place: typeof props.place === "string" ? props.place : ""
      });
    });
  }

  function showQuakes(list) {
    if (!globe || typeof globe.htmlElementsData !== "function") return;
    var sig = list.map(function (d) { return d.id; }).join("|");
    if (sig === quakeSig) return;
    quakeSig = sig;
    globe
      .htmlElementsData(list)
      .htmlAltitude(0.012)
      .htmlTransitionDuration(0)
      .htmlElement(quakeElement);
  }

  function readQuakeFeed(url) {
    return fetch(url, { cache: "no-store", credentials: "omit" }).then(function (r) {
      if (r.status === 204) return { features: [] };
      if (!r.ok) throw new Error("http");
      return r.json();
    });
  }

  function pullQuakes() {
    if (!globe || disposed) return;
    var start = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 19);
    var hawaii = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&orderby=time&minmagnitude=1&minlatitude=18.5&maxlatitude=22.5&minlongitude=-160.5&maxlongitude=-154.5&starttime=" + encodeURIComponent(start);
    var globalFeed = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson";
    Promise.all([
      readQuakeFeed(globalFeed).catch(function () { return null; }),
      readQuakeFeed(hawaii).catch(function () { return null; })
    ]).then(function (packs) {
      if (!globe || disposed) return;
      if (!packs[0] && !packs[1]) return;
      var list = [];
      var seen = {};
      eventsFromGeo(packs[0], list, seen);
      eventsFromGeo(packs[1], list, seen);
      if (list.length > 250) list = list.slice(0, 250);
      showQuakes(list);
    }).catch(function () {});
  }

  function startQuakes() {
    if (!globe || quakeTimer) return;
    pullQuakes();
    quakeTimer = window.setInterval(pullQuakes, 5 * 60 * 1000);
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
        controls.autoRotateSpeed = document.body.classList.contains("broadcast") ? 1.05 : 0.35;
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
      startQuakes();

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
        fallbackControls.autoRotateSpeed = document.body.classList.contains("broadcast") ? 1.05 : 0.35;
        globe.pointOfView({ lat: 16, lng: -156, altitude: 2.15 });
        startQuakes();
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

  function fitGlobe() {
    if (!globe || !globeEl) return;
    var w = globeEl.clientWidth || window.innerWidth;
    var h = globeEl.clientHeight || window.innerHeight;
    if (w < 2 || h < 2) return;
    if (typeof globe.width === "function") globe.width(w);
    if (typeof globe.height === "function") globe.height(h);
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
    if (quakeTimer) window.clearInterval(quakeTimer);
    document.removeEventListener("visibilitychange", onVisibility);
    window.removeEventListener("resize", fitGlobe);
    if (window.visualViewport) window.visualViewport.removeEventListener("resize", fitGlobe);
    window.removeEventListener("pagehide", dispose);
    if (globe && globe.pauseAnimation) globe.pauseAnimation();
    var renderer = globe && globe.renderer && globe.renderer();
    if (renderer) {
      renderer.dispose();
      if (renderer.forceContextLoss) renderer.forceContextLoss();
    }
  }

  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("resize", fitGlobe);
  if (window.visualViewport) window.visualViewport.addEventListener("resize", fitGlobe);
  window.addEventListener("pagehide", dispose);
  fitGlobe();
})();