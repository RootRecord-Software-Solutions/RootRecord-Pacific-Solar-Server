(function () {
  var BASE = document.body.getAttribute("data-radio-base") || "https://api.rootrecord.cloud/radio";
  var OPEN_MS = 12000;
  var GAP_MS = 10 * 60 * 1000;
  var POLL_MS = 20000;
  var DUCK = 0.25;
  var FULL = 1;
  var SILENCE = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

  var TITLES = {
    nws_weather: "NWS Hawaiʻi",
    official_weather: "Official weather",
    hurricane_desk: "Hurricane",
    kilauea_report: "Kīlauea",
    earthquake_report: "Earthquake",
    energy_report: "Energy",
    solar_desk: "Solar",
    bandwidth_desk: "Bandwidth",
    security_desk: "Security",
    system_perf: "Systems",
    morning_report: "Morning",
    midday_report: "Midday",
    late_report: "Late",
    remaining_tasks: "Tasks",
    boot_brief: "Boot"
  };

  var listen = document.getElementById("radio-listen");
  var stateEl = document.getElementById("radio-state");
  var led = document.getElementById("radio-led");
  var musicEl = document.getElementById("radio-music");
  var blurbEl = document.getElementById("radio-blurb");
  var reportEl = document.getElementById("radio-report");
  if (!listen || !stateEl || !musicEl || !reportEl) return;

  var music = new Audio();
  var report = new Audio();
  music.preload = "auto";
  report.preload = "auto";

  var tracks = [];
  var order = [];
  var orderAt = 0;
  var lastTrack = "";
  var reports = [];
  var seen = {};
  var primed = false;
  var updates = [];
  var rotation = [];
  var rotAt = 0;
  var playing = null;
  var replay = null;
  var started = false;
  var opened = false;
  var gapTimer = 0;
  var pollTimer = 0;
  var musicFails = 0;
  var attempt = 0;
  var STORE = "rr-radio-local";

  function localWanted() {
    try { return localStorage.getItem(STORE) !== "0"; }
    catch (e) { return true; }
  }

  function rememberLocal(on) {
    try { localStorage.setItem(STORE, on ? "1" : "0"); }
    catch (e) {}
  }

  function paintToggle(on) {
    listen.hidden = false;
    listen.disabled = false;
    listen.setAttribute("aria-pressed", on ? "true" : "false");
    listen.textContent = on ? "Local playback on" : "Local playback off";
  }

  function setState(text, on) {
    stateEl.textContent = text;
    if (led) led.classList.toggle("up", !!on);
  }

  function trackLabel(name) {
    return String(name || "")
      .replace(/\.[^.]+$/, "")
      .replace(/^My_Workspace-/, "")
      .replace(/_/g, " ");
  }

  function reportTitle(id) {
    return TITLES[id] || String(id || "").replace(/_/g, " ");
  }

  function ramp(to) {
    music.volume = to;
  }

  function shuffle(list) {
    var copy = list.slice();
    var i;
    for (i = copy.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var swap = copy[i];
      copy[i] = copy[j];
      copy[j] = swap;
    }
    return copy;
  }

  function playMusic() {
    if (!tracks.length) return;
    if (orderAt >= order.length) {
      order = shuffle(tracks);
      orderAt = 0;
      if (order.length > 1 && order[0] && order[0].name === lastTrack) {
        var first = order[0];
        order[0] = order[1];
        order[1] = first;
      }
    }
    var row = order[orderAt++];
    var name = row && row.name ? row.name : String(row || "");
    var mine = ++attempt;
    lastTrack = name;
    music.src = BASE + "/music/" + encodeURIComponent(name);
    musicEl.textContent = (row && row.title) || trackLabel(name);
    if (blurbEl) blurbEl.textContent = (row && row.description) || "";
    var pending = music.play();
    if (pending && pending.catch) {
      pending.catch(function (err) {
        if (mine !== attempt || !started) return;
        if (err && err.name === "NotAllowedError") {
          if (orderAt > 0) orderAt -= 1;
          waitForListen();
          return;
        }
        musicFails += 1;
        if (musicFails > tracks.length + 2) {
          setState("QUIET", false);
          return;
        }
        playMusic();
      });
    }
  }

  function waitForListen() {
    started = false;
    clearTimeout(gapTimer);
    clearInterval(pollTimer);
    pollTimer = 0;
    music.pause();
    report.pause();
    setState("OFF", false);
    musicEl.textContent = "Waiting";
    if (blurbEl) blurbEl.textContent = "";
    paintToggle(false);
  }

  function stopPlayback() {
    started = false;
    clearTimeout(gapTimer);
    clearInterval(pollTimer);
    pollTimer = 0;
    music.pause();
    report.pause();
    rememberLocal(false);
    paintToggle(false);
    setState("OFF", false);
  }

  function canResume(el) {
    return !!(el.src && el.currentTime > 0 && !el.ended);
  }

  music.addEventListener("playing", function () {
    musicFails = 0;
    setState("ON AIR", true);
  });

  music.addEventListener("ended", function () {
    if (started) playMusic();
  });

  function armGap() {
    clearTimeout(gapTimer);
    if (!started || playing || updates.length || rotation.length) return;
    var wait = opened ? GAP_MS : OPEN_MS;
    opened = true;
    gapTimer = setTimeout(function () {
      enqueueRotation();
      pump();
    }, wait);
  }

  function beginReport(item) {
    playing = { id: item.id, file: item.file, mtime: item.mtime };
    report.src = BASE + "/reports/" + encodeURIComponent(item.file) + "?v=" + item.mtime;
    reportEl.textContent = reportTitle(item.id);
    ramp(DUCK);
    var pending = report.play();
    if (pending && pending.catch) {
      pending.catch(function () {
        finishReport();
      });
    }
  }

  function finishReport() {
    if (!playing) return;
    var done = playing;
    playing = null;
    reportEl.textContent = "";
    ramp(FULL);
    if (replay && done && replay.id === done.id && replay.mtime > done.mtime) {
      var again = replay;
      replay = null;
      beginReport(again);
      return;
    }
    replay = null;
    pump();
  }

  report.addEventListener("ended", finishReport);
  report.addEventListener("error", function () {
    if (playing) finishReport();
  });

  function pump() {
    if (!started || playing) return;
    if (updates.length) {
      clearTimeout(gapTimer);
      beginReport(updates.shift());
      return;
    }
    if (rotation.length) {
      clearTimeout(gapTimer);
      beginReport(rotation.shift());
      return;
    }
    armGap();
  }

  function queued(list, id) {
    var i;
    for (i = 0; i < list.length; i++) {
      if (list[i].id === id) return i;
    }
    return -1;
  }

  function enqueueUpdate(item) {
    if (playing && playing.id === item.id) {
      if (item.mtime > playing.mtime) replay = item;
      return;
    }
    var at = queued(updates, item.id);
    if (at >= 0) {
      if (item.mtime >= updates[at].mtime) updates[at] = item;
      return;
    }
    rotation = rotation.filter(function (row) { return row.id !== item.id; });
    updates.push(item);
    if (started && !playing) pump();
  }

  function enqueueRotation() {
    if (!reports.length) return;
    var item = reports[rotAt % reports.length];
    rotAt += 1;
    if (playing && playing.id === item.id) {
      if (reports.length < 2) return;
      item = reports[rotAt % reports.length];
      rotAt += 1;
    }
    if (queued(updates, item.id) >= 0 || queued(rotation, item.id) >= 0) return;
    rotation.push(item);
  }

  function applyCatalog(data) {
    tracks = (data.music || []).filter(function (row) { return row && row.name; }).map(function (row) {
      return {
        name: row.name,
        title: row.title || trackLabel(row.name),
        description: row.description || ""
      };
    });
    reports = (data.reports || []).filter(function (row) { return row && row.id && row.file; });
    var live = {};
    reports.forEach(function (row) { live[row.id] = true; });
    updates = updates.filter(function (row) { return live[row.id]; });
    rotation = rotation.filter(function (row) { return live[row.id]; });
    Object.keys(seen).forEach(function (id) {
      if (!live[id]) delete seen[id];
    });
    if (!primed) {
      reports.forEach(function (row) { seen[row.id] = row.mtime; });
      primed = true;
      return;
    }
    reports.forEach(function (row) {
      var prev = seen[row.id];
      if (prev == null || row.mtime > prev) {
        enqueueUpdate(row);
        seen[row.id] = row.mtime;
      }
    });
  }

  function fetchCatalog() {
    return fetch(BASE + "/catalog.json", { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("catalog");
      return res.json();
    });
  }

  function poll() {
    fetchCatalog().then(applyCatalog).catch(function () {});
  }

  function unlock(el) {
    el.muted = true;
    el.src = SILENCE;
    var pending = el.play();
    var done = pending && pending.then ? pending : Promise.resolve();
    return done.then(function () {
      el.pause();
      el.currentTime = 0;
      el.muted = false;
    }).catch(function () {
      el.muted = false;
    });
  }

  function startPlayback() {
    if (!tracks.length) {
      listen.hidden = false;
      listen.disabled = false;
      setState("QUIET", false);
      musicEl.textContent = "No music is on the stream.";
      if (blurbEl) blurbEl.textContent = "";
      return;
    }
    started = true;
    music.volume = FULL;
    rememberLocal(true);
    paintToggle(true);
    playMusic();
    armGap();
    if (!pollTimer) pollTimer = setInterval(poll, POLL_MS);
  }

  function resumePlayback() {
    if (canResume(music)) {
      started = true;
      rememberLocal(true);
      paintToggle(true);
      music.volume = playing ? DUCK : FULL;
      var pending = music.play();
      if (pending && pending.catch) {
        pending.catch(function (err) {
          if (err && err.name === "NotAllowedError") waitForListen();
        });
      }
      if (playing && canResume(report)) {
        var reportPlay = report.play();
        if (reportPlay && reportPlay.catch) reportPlay.catch(function () { finishReport(); });
      } else if (!playing) {
        pump();
      }
      if (!pollTimer) pollTimer = setInterval(poll, POLL_MS);
      return;
    }
    startPlayback();
  }

  listen.addEventListener("click", function () {
    if (started) {
      stopPlayback();
      return;
    }
    listen.disabled = true;
    setState("STARTING", false);
    var primed = music.src && music.src.indexOf("data:audio/wav") !== 0;
    var ready = primed ? Promise.resolve() : unlock(music).then(function () { return unlock(report); });
    ready.then(function () {
      return fetchCatalog();
    }).then(function (data) {
      applyCatalog(data);
      resumePlayback();
    }).catch(function () {
      paintToggle(false);
      setState("QUIET", false);
      musicEl.textContent = "The stream is not reachable.";
    });
  });

  paintToggle(false);
  listen.disabled = true;
  setState("STARTING", false);
  fetchCatalog().then(function (data) {
    applyCatalog(data);
    if (localWanted()) startPlayback();
    else {
      paintToggle(false);
      setState("OFF", false);
      musicEl.textContent = "Waiting";
    }
  }).catch(function () {
    paintToggle(false);
    setState("QUIET", false);
    musicEl.textContent = "The stream is not reachable.";
  });

  window.addEventListener("pagehide", function () {
    clearInterval(pollTimer);
    clearTimeout(gapTimer);
  });
})();
