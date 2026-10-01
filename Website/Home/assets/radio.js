(function () {
  var BASE = document.body.getAttribute("data-radio-base") || "https://api.rootrecord.cloud/radio";
  var audio = document.getElementById("radio-out");
  var listen = document.getElementById("radio-listen");
  var stateEl = document.getElementById("radio-state");
  var led = document.getElementById("radio-led");
  var musicEl = document.getElementById("radio-music");
  var blurbEl = document.getElementById("radio-blurb");
  var reportEl = document.getElementById("radio-report");
  if (!audio || !listen || !stateEl || !musicEl || !reportEl) return;

  var src = BASE + "/live.mp3";
  audio.preload = "none";
  audio.src = src;

  function setState(text, on) {
    stateEl.textContent = text;
    if (led) led.classList.toggle("up", !!on);
  }

  function showListen(on) {
    listen.hidden = !on;
    listen.disabled = false;
    listen.textContent = "Listen";
    listen.setAttribute("aria-pressed", on ? "false" : "true");
  }

  function paint(data) {
    musicEl.textContent = (data && data.music) || "On the air";
    if (blurbEl) blurbEl.textContent = (data && data.description) || "";
    reportEl.textContent = (data && data.report) || "";
  }

  function pull() {
    fetch(BASE + "/now.json", { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("now");
      return res.json();
    }).then(paint).catch(function () {});
  }

  function openSpeakers() {
    var pending = audio.play();
    if (pending && pending.then) {
      pending.then(function () {
        showListen(false);
        setState("ON AIR", true);
      }).catch(function () {
        showListen(true);
        setState("ON AIR", true);
      });
      return;
    }
    showListen(false);
    setState("ON AIR", true);
  }

  listen.addEventListener("click", function () {
    if (!audio.paused && !audio.ended) return;
    openSpeakers();
  });

  audio.addEventListener("playing", function () {
    showListen(false);
    setState("ON AIR", true);
  });

  audio.addEventListener("error", function () {
    setState("QUIET", false);
    musicEl.textContent = "The station is not reachable.";
    showListen(true);
  });

  setState("ON AIR", true);
  musicEl.textContent = "On the air";
  showListen(false);
  pull();
  setInterval(pull, 5000);
  openSpeakers();
})();
