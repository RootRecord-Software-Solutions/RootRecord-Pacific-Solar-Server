(function () {
  var BASE = "https://api.rootrecord.cloud/radio";
  var audio = document.getElementById("radio-out");
  var program = document.getElementById("b-program");
  if (!audio) return;

  audio.autoplay = true;
  audio.playsInline = true;
  audio.preload = "auto";
  if (!audio.getAttribute("src")) audio.src = BASE + "/live.mp3";

  function paint(data) {
    if (!program || !data) return;
    var music = data.music || "Radio";
    var report = data.report ? " · " + data.report : "";
    program.textContent = music + report;
  }

  function pull() {
    fetch(BASE + "/now.json", { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("now");
      return res.json();
    }).then(paint).catch(function () {});
  }

  function resume() {
    var pending = audio.play();
    if (pending && pending.catch) pending.catch(function () {});
  }

  var quiet = 0;
  audio.addEventListener("pause", resume);
  audio.addEventListener("stalled", resume);
  audio.addEventListener("waiting", resume);
  audio.addEventListener("error", function () {
    setTimeout(resume, 1000);
  });
  // Replacing the stream address is the cut. Do it only after a long gap
  // with no media at all, not when the buffer is merely refilling.
  setInterval(function () {
    if (!audio.paused && audio.readyState > 0) {
      quiet = 0;
      return;
    }
    if (audio.paused) resume();
    if (audio.readyState > 0) return;
    quiet += 1;
    if (quiet < 15) return;
    quiet = 0;
    audio.src = BASE + "/live.mp3?t=" + Date.now();
    resume();
  }, 1000);

  pull();
  setInterval(pull, 5000);
  resume();
})();
