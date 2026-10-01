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
  var stormTimer = 0;
  var stormSig = "";

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

  var STORM_MAP = "https://mapservices.weather.noaa.gov/tropical/rest/services/tropical/NHC_tropical_weather_summary/MapServer";

  function stormQuery(layer, where) {
    return STORM_MAP + "/" + layer + "/query?where=" + encodeURIComponent(where || "1=1") +
      "&outFields=*&returnGeometry=true&f=geojson&outSR=4326&geometryPrecision=3";
  }

  function stormTitle(props) {
    var p = props || {};
    var name = p.stormname || p.stormid || p.binnumber || "Storm";
    var code = String(p.stormtype || "").toUpperCase();
    var kind = code === "HU" || code === "TY" ? "Hurricane" :
      code === "TS" ? "Tropical storm" :
      code === "TD" ? "Tropical depression" :
      code === "PTC" || code === "STD" ? "Potential tropical cyclone" : "";
    return kind ? kind + " " + name : String(name);
  }

  function linePaths(geo, kind, names) {
    var out = [];
    var features = geo && geo.features;
    if (!Array.isArray(features)) return out;
    features.forEach(function (f) {
      if (!f || !f.geometry || f.geometry.type !== "LineString") return;
      var props = f.properties || {};
      if (!props.stormname && names && props.binnumber && names[props.binnumber]) {
        props = Object.assign({}, props, { stormname: names[props.binnumber] });
      }
      var pts = [];
      function pushPath() {
        if (pts.length >= 2) out.push({ kind: kind, points: pts, props: props });
        pts = [];
      }
      (f.geometry.coordinates || []).forEach(function (c) {
        if (!c || c.length < 2) return;
        var pos = finitePair(c[1], c[0]);
        if (!pos) return;
        if (pts.length && Math.abs(pos.lng - pts[pts.length - 1].lng) > 180) pushPath();
        pts.push(pos);
      });
      pushPath();
    });
    return out;
  }

  function ringArea(ring) {
    var total = 0;
    var i;
    for (i = 1; i < ring.length; i++) {
      var lon1 = ring[i - 1][0] * Math.PI / 180;
      var lat1 = ring[i - 1][1] * Math.PI / 180;
      var lon2 = ring[i][0] * Math.PI / 180;
      var lat2 = ring[i][1] * Math.PI / 180;
      var dlon = lon2 - lon1;
      if (dlon > Math.PI) dlon -= 2 * Math.PI;
      if (dlon < -Math.PI) dlon += 2 * Math.PI;
      total += dlon * (Math.sin(lat1) + Math.sin(lat2));
    }
    return Math.abs(total) / 2;
  }

  function cleanRing(ring) {
    var out = [];
    (ring || []).forEach(function (c) {
      if (!c || c.length < 2) return;
      var lng = Number(c[0]);
      var lat = Number(c[1]);
      if (!Number.isFinite(lng) || !Number.isFinite(lat) || Math.abs(lat) > 90) return;
      // Keep the ring off the exact dateline so the fill stays the cone,
      // not the rest of the planet.
      if (lng >= 180) lng = 179.9;
      if (lng <= -180) lng = -179.9;
      var prev = out[out.length - 1];
      if (prev && Math.abs(prev[0] - lng) < 0.08 && Math.abs(prev[1] - lat) < 0.08) return;
      if (prev && Math.abs(prev[0] - lng) > 180) return;
      out.push([lng, lat]);
    });
    if (out.length < 4) return null;
    // The cone has to stay the small patch. A ring that encloses most of the
    // sphere is the same outline wound the other way, and that fill paints the earth.
    var area = ringArea(out);
    if (area > 2 * Math.PI) {
      out.reverse();
      area = ringArea(out);
    }
    if (area > 0.5) return null;
    var minLng = 180;
    var maxLng = -180;
    var minLat = 90;
    var maxLat = -90;
    out.forEach(function (p) {
      if (p[0] < minLng) minLng = p[0];
      if (p[0] > maxLng) maxLng = p[0];
      if (p[1] < minLat) minLat = p[1];
      if (p[1] > maxLat) maxLat = p[1];
    });
    if (maxLng - minLng > 100 || maxLat - minLat > 70) return null;
    var first = out[0];
    var last = out[out.length - 1];
    if (first[0] !== last[0] || first[1] !== last[1]) out.push([first[0], first[1]]);
    return out;
  }

  function cleanPolygons(geometry) {
    if (!geometry) return [];
    var parts = [];
    if (geometry.type === "Polygon") parts = [geometry.coordinates];
    else if (geometry.type === "MultiPolygon") parts = geometry.coordinates;
    var out = [];
    parts.forEach(function (poly) {
      if (!poly || !poly.length) return;
      var outer = cleanRing(poly[0]);
      if (!outer) return;
      out.push({ type: "Polygon", coordinates: [outer] });
    });
    return out;
  }

  function zoneFeatures(geo, kind) {
    var out = [];
    var features = geo && geo.features;
    if (!Array.isArray(features)) return out;
    features.forEach(function (f) {
      if (!f || !f.geometry) return;
      var props = f.properties || {};
      if (kind === "wind" && Number(props.tau) !== 0) return;
      cleanPolygons(f.geometry).forEach(function (geometry) {
        out.push({ kind: kind, geometry: geometry, props: props });
      });
    });
    return out;
  }

  function nameByBin(geo) {
    var names = {};
    var features = geo && geo.features;
    if (!Array.isArray(features)) return names;
    features.forEach(function (f) {
      var p = f && f.properties;
      if (p && p.binnumber && p.stormname) names[p.binnumber] = p.stormname;
    });
    return names;
  }

  function trackLabel(d) {
    var title = stormTitle(d.props);
    return d.kind === "forecast" ? title + ", forecast track" : title + ", past track";
  }

  function zoneLabel(d) {
    var title = stormTitle(d.props);
    if (d.kind === "cone") return title + ", forecast cone";
    var r = Number(d.props && d.props.radii);
    if (r >= 64) return title + ", hurricane-force winds";
    if (r >= 50) return title + ", storm-force winds";
    return title + ", tropical-storm-force winds";
  }

  function zoneFill(d) {
    if (d.kind === "cone") return "rgba(255, 196, 72, 0.14)";
    var r = Number(d.props && d.props.radii);
    if (r >= 64) return "rgba(255, 72, 72, 0.20)";
    if (r >= 50) return "rgba(255, 160, 48, 0.16)";
    return "rgba(125, 196, 255, 0.13)";
  }

  function zoneStroke(d) {
    if (d.kind === "cone") return "rgba(255, 210, 110, 0.55)";
    var r = Number(d.props && d.props.radii);
    if (r >= 64) return "rgba(255, 120, 120, 0.7)";
    if (r >= 50) return "rgba(255, 180, 80, 0.6)";
    return "rgba(160, 210, 255, 0.55)";
  }

  function bindStormStyle() {
    if (!globe || globe._rrStorm || typeof globe.pathsData !== "function") return;
    globe._rrStorm = true;
    globe
      .pathPoints(function (d) { return d.points; })
      .pathPointLat("lat")
      .pathPointLng("lng")
      .pathPointAlt(0.006)
      .pathColor(function (d) {
        return d.kind === "forecast" ? "rgba(255, 196, 72, 0.92)" : "rgba(255, 244, 220, 0.8)";
      })
      .pathStroke(function (d) { return d.kind === "forecast" ? 0.16 : 0.22; })
      .pathDashLength(function (d) { return d.kind === "forecast" ? 0.32 : 1; })
      .pathDashGap(function (d) { return d.kind === "forecast" ? 0.14 : 0; })
      .pathDashAnimateTime(0)
      .pathLabel(trackLabel)
      .pathTransitionDuration(0)
      .polygonGeoJsonGeometry(function (d) { return d.geometry; })
      .polygonCapCurvatureResolution(45)
      .polygonAltitude(0.001)
      .polygonCapColor(zoneFill)
      .polygonSideColor(function () { return "rgba(0,0,0,0)"; })
      .polygonStrokeColor(zoneStroke)
      .polygonLabel(zoneLabel)
      .polygonsTransitionDuration(0);
  }

  function showStorms(paths, zones) {
    if (!globe) return;
    bindStormStyle();
    var sig = paths.length + ":" + zones.length + ":" +
      paths.map(function (d) { return (d.props && (d.props.stormname || d.props.binnumber)) || ""; }).join(",") + "|" +
      zones.map(function (d) { return (d.props && (d.props.stormname || d.props.stormid || "")) + (d.props && d.props.radii || ""); }).join(",");
    if (sig === stormSig) return;
    stormSig = sig;
    globe.pathsData(paths);
    globe.polygonsData(zones);
  }

  function pullStorms() {
    if (!globe || disposed) return;
    Promise.all([
      readQuakeFeed(stormQuery(11)).catch(function () { return null; }),
      readQuakeFeed(stormQuery(6)).catch(function () { return null; }),
      readQuakeFeed(stormQuery(7)).catch(function () { return null; }),
      readQuakeFeed(stormQuery(16, "tau=0")).catch(function () { return null; })
    ]).then(function (packs) {
      if (!globe || disposed) return;
      if (!packs[0] && !packs[1] && !packs[2] && !packs[3]) return;
      var names = nameByBin(packs[1]);
      var coneNames = nameByBin(packs[2]);
      Object.keys(coneNames).forEach(function (k) { if (!names[k]) names[k] = coneNames[k]; });
      var paths = linePaths(packs[0], "past", names).concat(linePaths(packs[1], "forecast", names));
      var zones = zoneFeatures(packs[2], "cone").concat(zoneFeatures(packs[3], "wind"));
      showStorms(paths, zones);
    }).catch(function () {});
  }

  function startStorms() {
    if (!globe || stormTimer) return;
    pullStorms();
    stormTimer = window.setInterval(pullStorms, 5 * 60 * 1000);
  }

  function draw(d) {
    if (!globe || !d) return;
    var scene = publicScene(d);
    globe.pointsData(scene.points);
    globe.arcsData(scene.arcs);
  }

  var NIGHT_EARTH = "/assets/earth/night.jpg?v=20261001z";

  function storedSpin() {
    try {
      return localStorage.getItem("rr-home:spin") !== "off";
    } catch (err) {
      return true;
    }
  }

  function plainEarth() {
    return Globe()(globeEl)
      .globeImageUrl(NIGHT_EARTH)
      .backgroundColor("rgba(0,0,0,0)")
      .showAtmosphere(true)
      .atmosphereColor("#8eb6ff")
      .atmosphereAltitude(0.13);
  }

  if (globeEl && typeof Globe === "function") {
    try {
      globe = Globe()(globeEl)
        .globeImageUrl(NIGHT_EARTH)
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

      spinOn = reduced() ? false : storedSpin();
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
          try {
            localStorage.setItem("rr-home:spin", spinOn ? "on" : "off");
          } catch (err) {}
          applySpin();
        });
      }
      applySpin();
      globe._rrApplySpin = applySpin;
      startQuakes();
      startStorms();

      var canvas = globeEl.querySelector("canvas");
      if (canvas) {
        canvas.addEventListener("webglcontextlost", function (event) {
          event.preventDefault();
          failGlobe();
        });
      }
    } catch (err) {
      try {
        if (globe) {
          var kept = globe.controls();
          kept.autoRotate = !reduced();
          kept.autoRotateSpeed = document.body.classList.contains("broadcast") ? 1.05 : 0.35;
        } else {
          globe = plainEarth();
          var fallbackControls = globe.controls();
          fallbackControls.enableZoom = false;
          fallbackControls.autoRotate = !reduced();
          fallbackControls.autoRotateSpeed = document.body.classList.contains("broadcast") ? 1.05 : 0.35;
          globe.pointOfView({ lat: 16, lng: -156, altitude: 2.15 });
        }
        startQuakes();
        startStorms();
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
    if (stormTimer) window.clearInterval(stormTimer);
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