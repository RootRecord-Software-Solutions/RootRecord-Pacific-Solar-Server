(function () {
  var params = new URLSearchParams(location.search);
  if (params.get("broadcast") !== "1") return;

  document.body.classList.add("yt-broadcast");
  var base = "https://api.rootrecord.cloud/radio";
  var audio = document.createElement("audio");
  audio.id = "radio-out";
  audio.src = base + "/live.mp3";
  audio.autoplay = true;
  audio.playsInline = true;
  audio.preload = "auto";
  document.body.appendChild(audio);

  var line = document.createElement("div");
  line.className = "b-onair";
  line.innerHTML = '<span class="b-onair-k">ON AIR</span><span id="b-program">Radio</span>';
  var top = document.querySelector(".b-top");
  if (top) top.appendChild(line);

  function paint(data) {
    var el = document.getElementById("b-program");
    if (!el || !data) return;
    var music = data.music || "Radio";
    var report = data.report ? " · " + data.report : "";
    el.textContent = music + report;
  }

  function pull() {
    fetch(base + "/now.json", { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("now");
      return res.json();
    }).then(paint).catch(function () {});
  }

  function start() {
    var pending = audio.play();
    if (pending && pending.catch) pending.catch(function () {});
  }

  pull();
  setInterval(pull, 5000);
  start();
  audio.addEventListener("pause", start);
})();
