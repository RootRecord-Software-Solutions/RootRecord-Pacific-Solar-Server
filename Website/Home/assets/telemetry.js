(function (global) {
  var API = "https://api.rootrecord.cloud";

  function finite(n) {
    if (n === null || n === undefined || n === "") return null;
    var v = Number(n);
    return Number.isFinite(v) ? v : null;
  }

  function fmt(n) {
    var v = finite(n);
    return v === null ? null : v.toLocaleString();
  }

  function parseTime(value) {
    if (typeof value === "number" && Number.isFinite(value)) {
      return value < 1e12 ? value * 1000 : value;
    }
    if (typeof value !== "string" || !value) return null;
    var cleaned = value.replace(/\s+HST$/i, "").trim();
    var t = Date.parse(cleaned);
    return Number.isNaN(t) ? null : t;
  }

  function formatHst(value, withDate) {
    var n = typeof value === "number" ? value : parseTime(value);
    if (n === null) return null;
    var d = new Date(n);
    if (Number.isNaN(d.getTime())) return null;
    var opts = {
      timeZone: "Pacific/Honolulu",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23"
    };
    if (withDate) {
      opts.year = "numeric";
      opts.month = "2-digit";
      opts.day = "2-digit";
    }
    var parts = new Intl.DateTimeFormat("en-US", opts).formatToParts(d);
    var map = {};
    parts.forEach(function (p) {
      if (p.type !== "literal") map[p.type] = p.value;
    });
    var clock = map.hour + ":" + map.minute + ":" + map.second;
    if (!withDate) return clock + " HST";
    return map.year + "-" + map.month + "-" + map.day + " " + clock + " HST";
  }

  function agePhrase(ms) {
    if (ms === null || ms === undefined) return null;
    var s = Math.max(0, Math.round((Date.now() - ms) / 1000));
    if (s < 5) return "Updated just now";
    if (s < 60) return "Updated " + s + " sec ago";
    var m = Math.round(s / 60);
    if (m < 90) return "Updated " + m + " min ago";
    var h = Math.round(m / 60);
    return "Updated " + h + " hr ago";
  }

  function pct(n) {
    var v = finite(n);
    if (v === null) return null;
    return (Math.round(v * 10) / 10).toFixed(1) + "%";
  }

  function watts(n) {
    var v = finite(n);
    if (v === null) return null;
    var rounded = Math.round(v * 10) / 10;
    var text = Math.abs(rounded - Math.round(rounded)) < 0.05 ? String(Math.round(rounded)) : rounded.toFixed(1);
    return text + " W";
  }

  function deviceReading(devices, name) {
    var d = devices && devices[name];
    if (!d) return null;
    var power = d.watts || {};
    var soc = d.soc || {};
    var at = parseTime(soc.at || power.at);
    var reading = {
      soc: finite(soc.soc),
      solar: finite(power.solar_input_power),
      acOut: finite(power.ac_output_power),
      acIn: finite(power.ac_input_power),
      usbc: finite(power.usbc_output_power),
      chargeSource: typeof power.charge_source === "string" ? power.charge_source : "",
      at: at
    };
    if (reading.soc === null && reading.solar === null && reading.acOut === null && reading.usbc === null) {
      return null;
    }
    return reading;
  }

  function moonReading(status) {
    if (!status || typeof status !== "object") return null;
    var phase = finite(status.phase);
    var illumination = finite(status.illumination);
    var name = status.phase_name ? String(status.phase_name) : null;
    if (phase === null && illumination === null && !name) return null;
    return {
      phase: phase,
      name: name,
      illumination: illumination,
      nextName: status.next_phase ? String(status.next_phase) : null,
      nextDate: status.next_phase_date ? String(status.next_phase_date) : null,
      at: parseTime(status.fetched_at)
    };
  }

  function fieldReadings(ops) {
    var power = ops && ops.power && ops.power.devices;
    var weather = ops && ops.weather && ops.weather.report;
    var volcano = ops && ops.kilauea && ops.kilauea.status;
    var generated = weather && weather.generated ? String(weather.generated) : null;
    return {
      river: deviceReading(power, "river2pro"),
      delta: deviceReading(power, "delta2"),
      weatherAt: parseTime(generated),
      weatherText: generated,
      kilauea: volcano ? {
        at: parseTime(volcano.at),
        alert: volcano.alert_level ? String(volcano.alert_level) : null,
        code: volcano.color_code ? String(volcano.color_code) : null,
        headline: volcano.headline ? String(volcano.headline) : null,
        erupting: typeof volcano.erupting === "boolean" ? volcano.erupting : null
      } : null,
      moon: moonReading(
        (ops && ops.weather && ops.weather.moon) ||
          (ops && ops.moon && ops.moon.status)
      ),
      asOf: ops && ops.as_of ? String(ops.as_of) : null
    };
  }

  function readJson(path) {
    return fetch(API + path, { cache: "no-store", credentials: "omit" }).then(function (r) {
      if (!r.ok) throw new Error("http");
      return r.json();
    });
  }

  function readState() {
    return readJson("/api/state").then(function (d) {
      if (!d || d.ok === false || !d.stats) throw new Error("nodata");
      return d;
    });
  }

  function readOps() {
    return readJson("/api/operations").then(function (d) {
      if (!d || d.ok !== true) throw new Error("nodata");
      return d;
    });
  }

  var SOON_MS = 24 * 60 * 60 * 1000;

  function noticePhase(doc, nowMs) {
    var list = doc && Array.isArray(doc.windows) ? doc.windows : [];
    var chosen = null;
    list.forEach(function (item) {
      if (!item || item.enabled === false) return;
      var down = parseTime(item.down_at);
      var up = parseTime(item.up_at);
      if (down === null || up === null || up <= down || nowMs >= up) return;
      var phase = nowMs >= down ? "down" : "upcoming";
      if (phase === "upcoming" && down - nowMs > SOON_MS) return;
      if (!chosen) {
        chosen = { phase: phase, window: item, down: down, up: up };
        return;
      }
      var activeWins = phase === "down" && chosen.phase !== "down";
      var sooner = phase === chosen.phase && up < chosen.up;
      if (activeWins || sooner) chosen = { phase: phase, window: item, down: down, up: up };
    });
    return chosen;
  }

  function readNotice() {
    return fetch("/service-notice.json", { cache: "no-store", credentials: "omit" }).then(function (r) {
      if (!r.ok) return { windows: [] };
      return r.json();
    }).catch(function () {
      return { windows: [] };
    });
  }

  global.RRTelemetry = {
    finite: finite,
    fmt: fmt,
    parseTime: parseTime,
    formatHst: formatHst,
    agePhrase: agePhrase,
    pct: pct,
    watts: watts,
    fieldReadings: fieldReadings,
    readState: readState,
    readOps: readOps,
    noticePhase: noticePhase,
    readNotice: readNotice
  };
})(window);
