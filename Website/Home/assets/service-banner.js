(function () {
  var T = window.RRTelemetry;
  var root = document.getElementById("service-banner");
  var closeBtn = document.getElementById("service-banner-close");
  if (!T || !root || !T.readNotice || !T.noticePhase) return;

  function dismissed(id) {
    try {
      return sessionStorage.getItem("rr-service-dismissed") === id;
    } catch (err) {
      return false;
    }
  }

  function show(chosen) {
    var id = String((chosen.window && chosen.window.id) || "");
    if (!id || dismissed(id)) return;
    root.setAttribute("data-window", id);
    var title = document.getElementById("service-banner-title");
    var body = document.getElementById("service-banner-body");
    var back = document.getElementById("service-banner-back");
    var down = T.formatHst(chosen.down, true);
    var up = T.formatHst(chosen.up, true);
    var known = chosen.window.last_known || {};
    var knownAt = T.formatHst(known.at, true);
    var note = chosen.window.note ? String(chosen.window.note) + " " : "";
    if (chosen.phase === "down") {
      if (title) title.textContent = "Service window in progress";
      if (body) body.textContent = note + "Live network readings are paused. Last known state was recorded " + (knownAt || "before this window") + ".";
    } else {
      if (title) title.textContent = "Planned service window";
      if (body) body.textContent = note + "Live network readings are expected to pause at " + (down || "the scheduled time") + ".";
    }
    if (back) back.textContent = up ? "Expected back online · " + up : "Expected back online time is not set.";
    root.hidden = false;
    if (closeBtn) closeBtn.focus();
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      var id = root.getAttribute("data-window") || "";
      root.hidden = true;
      try {
        if (id) sessionStorage.setItem("rr-service-dismissed", id);
      } catch (err) {
        /* the banner still closes */
      }
    });
  }

  T.readNotice().then(function (doc) {
    var chosen = T.noticePhase(doc, Date.now());
    if (chosen) show(chosen);
  });
})();
