(function () {
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var globeEl = document.getElementById("globe");
  var globe = null;
  var disposed = false;
  var hidden = false;
  var spinOn = false;
  var earthPivot = null;
  var cloudsMesh = null;
  var moon = null;
  var sunMesh = null;
  var planets = [];
  var rafId = 0;
  var pullTimer = 0;
  var nightApplied = false;

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
    return { points: points, arcs: arcs };
  }

  function subsolar(date) {
    var start = Date.UTC(date.getUTCFullYear(), 0, 0);
    var day = (Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()) - start) / 86400000;
    var decl = 23.44 * Math.sin((Math.PI / 180) * (360 / 365) * (day - 81));
    var hours = date.getUTCHours() + date.getUTCMinutes() / 60 + date.getUTCSeconds() / 3600;
    var lng = 15 * (12 - hours);
    while (lng > 180) lng -= 360;
    while (lng < -180) lng += 360;
    return { lat: decl, lng: lng };
  }

  function sunVector(date) {
    var sub = subsolar(date || new Date());
    var phi = (90 - sub.lat) * Math.PI / 180;
    var theta = (90 - sub.lng) * Math.PI / 180;
    return {
      x: Math.sin(phi) * Math.cos(theta),
      y: Math.cos(phi),
      z: Math.sin(phi) * Math.sin(theta)
    };
  }

  function tuneLights(sun) {
    var scene = globe.scene && globe.scene();
    if (!scene) return;
    scene.traverse(function (obj) {
      if (obj.isAmbientLight) obj.intensity = 0.28;
      if (obj.isDirectionalLight) {
        obj.intensity = Math.PI * 1.15;
        obj.position.set(sun.x * 400, sun.y * 400, sun.z * 400);
      }
    });
  }

  function applyNight(sun) {
    if (nightApplied) return;
    var mat = globe.globeMaterial && globe.globeMaterial();
    if (!mat || !mat.map || !mat.map.constructor) return;
    var img = new Image();
    img.onload = function () {
      if (disposed || !mat.map) return;
      var night = new mat.map.constructor(img);
      night.needsUpdate = true;
      night.colorSpace = mat.map.colorSpace;
      night.anisotropy = mat.map.anisotropy || 1;
      night.wrapS = mat.map.wrapS;
      night.wrapT = mat.map.wrapT;
      night.flipY = mat.map.flipY;
      var Vec = null;
      globe.scene().traverse(function (obj) {
        if (!Vec && obj.isDirectionalLight) Vec = obj.position.constructor;
      });
      if (!Vec) return;
      var uniformSun = new Vec(sun.x, sun.y, sun.z);
      mat.onBeforeCompile = function (shader) {
        shader.uniforms.uNight = { value: night };
        shader.uniforms.uSun = { value: uniformSun };
        shader.vertexShader = shader.vertexShader
          .replace("#include <common>", "#include <common>\nvarying vec3 vWorldNormal;")
          .replace("#include <beginnormal_vertex>", "#include <beginnormal_vertex>\nvWorldNormal = normalize(mat3(modelMatrix) * objectNormal);");
        shader.fragmentShader = shader.fragmentShader
          .replace("#include <common>", "#include <common>\nuniform sampler2D uNight;\nuniform vec3 uSun;\nvarying vec3 vWorldNormal;")
          .replace("#include <opaque_fragment>", "outgoingLight += texture2D(uNight, vMapUv).rgb * (1.0 - smoothstep(-0.08, 0.28, dot(normalize(vWorldNormal), normalize(uSun)))) * 1.25;\n#include <opaque_fragment>");
      };
      mat.customProgramCacheKey = function () { return "rr-earth-night"; };
      mat.needsUpdate = true;
      nightApplied = true;
    };
    img.onerror = function () {};
    img.src = "/assets/earth/night.jpg";
  }

  function findEarth() {
    var mat = globe.globeMaterial && globe.globeMaterial();
    var scene = globe.scene && globe.scene();
    if (!mat || !scene) return;
    scene.traverse(function (obj) {
      if (obj.isMesh && obj.material === mat && !earthPivot) earthPivot = obj.parent || null;
      if (obj.isMesh && obj.material && obj.material !== mat && obj.material.transparent && obj.material.map && !cloudsMesh) {
        cloudsMesh = obj;
      }
    });
  }

  function addBodies(sun) {
    if (moon || !earthPivot) return;
    var scene = globe.scene();
    var mesh = null;
    scene.traverse(function (obj) {
      if (!mesh && obj.isMesh && obj.parent === earthPivot && obj.geometry) mesh = obj;
    });
    if (!mesh || !mesh.geometry || !mesh.constructor || !mesh.material || !mesh.material.constructor) return;
    var Mesh = mesh.constructor;
    var Phong = mesh.material.constructor;
    var moonMat = new Phong({ color: 0xb7b9c2, shininess: 4 });
    moon = new Mesh(mesh.geometry, moonMat);
    moon.scale.setScalar(0.22);
    scene.add(moon);
    var sunMat = new Phong({ color: 0xfff6df, emissive: 0xfff1c4, emissiveIntensity: 0.9 });
    sunMesh = new Mesh(mesh.geometry, sunMat);
    sunMesh.scale.setScalar(0.045);
    sunMesh.position.set(sun.x * 520, sun.y * 520, sun.z * 520);
    scene.add(sunMesh);
    var tones = [0xb9aa96, 0x7e6d5e];
    for (var i = 0; i < tones.length; i++) {
      var body = new Mesh(mesh.geometry, new Phong({ color: tones[i], shininess: 1 }));
      body.scale.setScalar(0.03 + i * 0.012);
      body.userData.radius = 640 + i * 90;
      body.userData.rate = 0.012 + i * 0.007;
      body.userData.phase = i * 2.2;
      body.userData.lift = 0.22 + i * 0.18;
      scene.add(body);
      planets.push(body);
    }
    placeBodies(0);
  }

  function placeBodies(seconds) {
    if (moon) {
      var ang = reduced() ? 0.7 : seconds * 0.04;
      moon.position.set(Math.cos(ang) * 176, Math.sin(ang * 0.37) * 26, Math.sin(ang) * 176);
    }
    if (reduced()) return;
    planets.forEach(function (body) {
      var ang = seconds * body.userData.rate + body.userData.phase;
      var radius = body.userData.radius;
      body.position.set(Math.cos(ang) * radius, Math.sin(ang) * radius * body.userData.lift, Math.sin(ang) * radius * 0.72);
    });
  }

  function spinStep() {
    if (disposed || hidden || reduced() || !spinOn || !earthPivot) return;
    earthPivot.rotation.y += 0.00055;
    if (cloudsMesh) cloudsMesh.rotation.y += 0.00004;
  }

  function frame(now) {
    if (disposed) return;
    rafId = window.requestAnimationFrame(frame);
    if (hidden) return;
    spinStep();
    placeBodies((now || 0) / 1000);
  }

  function draw(d) {
    if (!globe || !d) return;
    var scene = publicScene(d);
    globe.pointsData(scene.points);
    globe.arcsData(scene.arcs);
  }

  if (globeEl && typeof Globe === "function") {
    try {
      globe = Globe()(globeEl)
        .globeImageUrl("/assets/earth/day.jpg")
        .bumpImageUrl("/assets/earth/topology.png")
        .cloudsImageUrl("/assets/earth/clouds.png")
        .cloudsAltitude(0.008)
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
          return "#ff6b9d";
        })
        .pointAltitude(function (d) { return d.type === "endpoint" ? 0.012 : 0.02; })
        .pointRadius(function (d) { return d.type === "endpoint" ? 0.18 : 0.42; })
        .pointLabel(function (d) { return d.label || ""; })
        .pointsMerge(false);

      var controls = globe.controls();
      controls.enableZoom = false;
      controls.enablePan = false;
      controls.autoRotate = false;
      globe.pointOfView({ lat: 16, lng: -156, altitude: 2.15 });
      var renderer = globe.renderer && globe.renderer();
      if (renderer && renderer.setPixelRatio) {
        var cap = window.innerWidth < 800 ? 1.15 : 1.5;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, cap));
      }
      var sun = sunVector(new Date());
      tuneLights(sun);

      spinOn = reduced() ? false : localStorage.getItem("rr-home:spin") !== "off";
      var spinBtn = document.getElementById("spin");
      function applySpinLabel() {
        if (!spinBtn) return;
        spinBtn.textContent = spinOn ? "Stop spin" : "Resume spin";
        spinBtn.setAttribute("aria-pressed", spinOn ? "true" : "false");
      }
      if (spinBtn) {
        spinBtn.addEventListener("click", function () {
          spinOn = !spinOn;
          localStorage.setItem("rr-home:spin", spinOn ? "on" : "off");
          applySpinLabel();
        });
      }
      applySpinLabel();

      var tries = 0;
      function whenReady() {
        if (disposed || !globe) return;
        var mat = globe.globeMaterial && globe.globeMaterial();
        if (mat && mat.map) {
          if (mat.bumpScale !== undefined) mat.bumpScale = 8;
          applyNight(sun);
          findEarth();
          addBodies(sun);
          return;
        }
        tries += 1;
        if (tries < 30) window.setTimeout(whenReady, 200);
      }
      whenReady();
      rafId = window.requestAnimationFrame(frame);

      var canvas = globeEl.querySelector("canvas");
      if (canvas) {
        canvas.addEventListener("webglcontextlost", function (event) {
          event.preventDefault();
          failGlobe();
        });
      }
    } catch (err) {
      globe = null;
      failGlobe();
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
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    if (rafId) window.cancelAnimationFrame(rafId);
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
