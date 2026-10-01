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
      at: at
    };
    if (reading.soc === null && reading.solar === null && reading.acOut === null && reading.usbc === null) {
      return null;
    }
    return reading;
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
    readOps: readOps
  };
})(window);
