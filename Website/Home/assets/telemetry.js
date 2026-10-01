(function (global) {
  var API = "https://api.rootrecord.cloud";

  function finite(n) {
    var v = Number(n);
    return Number.isFinite(v) ? v : null;
  }

  function fmt(n) {
    var v = finite(n);
    return v === null ? "—" : v.toLocaleString();
  }

  function utcClock(ms) {
    var n = finite(ms);
    if (n === null || n <= 0) return null;
    if (n < 1e12) n = n * 1000;
    var d = new Date(n);
    if (Number.isNaN(d.getTime())) return null;
    function pad(x) { return String(x).padStart(2, "0"); }
    return pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes()) + ":" + pad(d.getUTCSeconds()) + " UTC";
  }

  function deviceLine(devices, name) {
    var d = devices && devices[name];
    if (!d) return null;
    var parts = [];
    if (d.soc && finite(d.soc.soc) !== null) {
      parts.push((Math.round(Number(d.soc.soc) * 10) / 10) + "%");
    }
    if (d.watts && finite(d.watts.solar_input_power) !== null) {
      parts.push((Math.round(Number(d.watts.solar_input_power) * 10) / 10) + " W solar");
    }
    return parts.length ? parts.join(" · ") : null;
  }

  function fieldReadings(ops) {
    var power = ops && ops.power && ops.power.devices;
    var weather = ops && ops.weather && ops.weather.report;
    var volcano = ops && ops.kilauea && ops.kilauea.status;
    return {
      river: deviceLine(power, "river2pro"),
      delta: deviceLine(power, "delta2"),
      weather: weather && weather.generated ? String(weather.generated) : null,
      kilauea: volcano && (volcano.headline || volcano.alert_level) ? String(volcano.headline || volcano.alert_level) : null,
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
    utcClock: utcClock,
    fieldReadings: fieldReadings,
    readState: readState,
    readOps: readOps
  };
})(window);
