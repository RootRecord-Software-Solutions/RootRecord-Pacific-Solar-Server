(function () {
  var BASE = document.body.getAttribute("data-radio-base") || "https://api.rootrecord.cloud/radio";
  var audio = document.getElementById("radio-out");
  var stateEl = document.getElementById("radio-state");
  var led = document.getElementById("radio-led");
  var musicEl = document.getElementById("radio-music");
  var blurbEl = document.getElementById("radio-blurb");
  var reportEl = document.getElementById("radio-report");
  if (!audio || !stateEl || !musicEl || !reportEl) return;

  if (!audio.getAttribute("src")) audio.src = BASE + "/live.mp3";
  audio.autoplay = true;
  audio.playsInline = true;

  function setState(text, on) {
    stateEl.textContent = text;
    if (led) led.classList.toggle("up", !!on);
  }

  function paint(data) {
    musicEl.textContent = (data && data.music) || "On the air";
    if (blurbEl) blurbEl.textContent = (data && data.description) || "";
    reportEl.textContent = (data && data.report) || "";
  }

  function start() {
    var pending = audio.play();
    if (pending && pending.catch) pending.catch(function () {});
  }

  fetch(BASE + "/now.json", { cache: "no-store" }).then(function (res) {
    if (!res.ok) throw new Error("now");
    return res.json();
  }).then(paint).catch(function () {});
  setInterval(function () {
    fetch(BASE + "/now.json", { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("now");
      return res.json();
    }).then(paint).catch(function () {});
  }, 5000);

  setState("ON AIR", true);
  start();
  audio.addEventListener("pause", start);
  audio.addEventListener("error", function () {
    setState("QUIET", false);
    musicEl.textContent = "The station is not reachable.";
    setTimeout(start, 2000);
  });
  setInterval(function () {
    if (audio.paused) start();
  }, 1000);
})();
