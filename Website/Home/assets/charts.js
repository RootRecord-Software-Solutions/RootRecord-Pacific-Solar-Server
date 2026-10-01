(function (global) {
  var T = global.RRTelemetry;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function stamp(ms) {
    if (!T) return "";
    return T.formatHst(ms, true) || "";
  }

  function empty(node, message) {
    clear(node);
    node.appendChild(el("p", "empty-note", message || "No public signal"));
  }

  function table(columns, rows, caption) {
    var wrap = el("div", "table-wrap");
    var tableNode = el("table", "data-table");
    var cap = el("caption", "sr", caption);
    tableNode.appendChild(cap);
    var head = document.createElement("thead");
    var hr = document.createElement("tr");
    columns.forEach(function (name) {
      hr.appendChild(el("th", null, name));
    });
    head.appendChild(hr);
    tableNode.appendChild(head);
    var body = document.createElement("tbody");
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      row.forEach(function (cell) {
        tr.appendChild(el("td", null, cell));
      });
      body.appendChild(tr);
    });
    tableNode.appendChild(body);
    wrap.appendChild(tableNode);
    return wrap;
  }

  function tipFor(host) {
    var tip = host.querySelector(".chart-tip");
    if (!tip) {
      tip = el("div", "chart-tip");
      tip.hidden = true;
      host.appendChild(tip);
    }
    return tip;
  }

  function showTip(host, text, x, y) {
    var tip = tipFor(host);
    tip.textContent = text;
    tip.hidden = false;
    var rect = host.getBoundingClientRect();
    var left = x - rect.left + 10;
    var top = y - rect.top + 12;
    if (left > rect.width - 140) left = rect.width - 140;
    if (left < 4) left = 4;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }

  function hideTip(host) {
    var tip = host.querySelector(".chart-tip");
    if (tip) tip.hidden = true;
  }

  function bars(node, spec) {
    if (!node) return;
    var items = (spec.bars || []).filter(function (b) {
      return b && Number.isFinite(b.value);
    });
    if (!items.length) {
      empty(node, spec.empty || "No public signal");
      return;
    }
    clear(node);
    var max = spec.max;
    items.forEach(function (b) {
      if (!Number.isFinite(max) || b.value > max) max = b.value;
    });
    if (!Number.isFinite(max) || max <= 0) max = 1;

    var svgNs = "http://www.w3.org/2000/svg";
    var rowH = 28;
    var height = items.length * rowH + 8;
    var svg = document.createElementNS(svgNs, "svg");
    svg.setAttribute("viewBox", "0 0 320 " + height);
    svg.setAttribute("class", "chart-svg");
    svg.setAttribute("role", "img");
    var title = document.createElementNS(svgNs, "title");
    title.textContent = spec.label || "Chart";
    svg.appendChild(title);
    var desc = document.createElementNS(svgNs, "desc");
    desc.textContent = items.map(function (b) {
      return b.name + " " + (b.text || b.value);
    }).join(". ");
    svg.appendChild(desc);

    items.forEach(function (b, i) {
      var y = 8 + i * rowH;
      var w = Math.max(0, Math.min(168, (b.value / max) * 168));
      var track = document.createElementNS(svgNs, "rect");
      track.setAttribute("x", "108");
      track.setAttribute("y", String(y));
      track.setAttribute("width", "168");
      track.setAttribute("height", "10");
      track.setAttribute("class", "bar-track");
      svg.appendChild(track);
      var bar = document.createElementNS(svgNs, "rect");
      bar.setAttribute("x", "108");
      bar.setAttribute("y", String(y));
      bar.setAttribute("width", String(w));
      bar.setAttribute("height", "10");
      bar.setAttribute("class", "bar-fill");
      svg.appendChild(bar);
      var name = document.createElementNS(svgNs, "text");
      name.setAttribute("x", "0");
      name.setAttribute("y", String(y + 9));
      name.setAttribute("class", "bar-name");
      name.textContent = b.name;
      svg.appendChild(name);
      var value = document.createElementNS(svgNs, "text");
      value.setAttribute("x", "284");
      value.setAttribute("y", String(y + 9));
      value.setAttribute("class", "bar-value");
      value.textContent = b.text || String(b.value);
      svg.appendChild(value);
    });

    var frame = el("div", "chart");
    frame.appendChild(svg);
    frame.addEventListener("pointermove", function (event) {
      var rect = svg.getBoundingClientRect();
      var y = event.clientY - rect.top;
      var index = Math.floor((y / rect.height) * items.length);
      if (index < 0 || index >= items.length) {
        hideTip(frame);
        return;
      }
      var item = items[index];
      var when = item.at ? stamp(item.at) : "Current reading";
      showTip(frame, item.name + " · " + (item.text || item.value) + " · " + when, event.clientX, event.clientY);
    });
    frame.addEventListener("pointerleave", function () { hideTip(frame); });
    node.appendChild(frame);
    node.appendChild(table(
      ["Name", "Value", "Observed"],
      items.map(function (b) {
        return [b.name, b.text || String(b.value), b.at ? stamp(b.at) : "Current reading"];
      }),
      spec.question || spec.label || "Current readings"
    ));
  }

  function seriesPoints(spec, rangeMs) {
    var now = Date.now();
    return (spec.series || []).filter(function (p) {
      return p && Number.isFinite(p.t) && Number.isFinite(p.v) && (rangeMs ? p.t >= now - rangeMs : true);
    }).sort(function (a, b) { return a.t - b.t; });
  }

  function line(node, spec) {
    if (!node) return;
    var ranges = spec.ranges || [];
    var active = spec.activeRange || (ranges[0] && ranges[0].ms) || null;

    function draw(rangeMs) {
      var points = seriesPoints(spec, rangeMs);
      clear(node);
      if (points.length < 2) {
        empty(node, spec.empty || "No historical series in the public feed.");
        if (spec.current) {
          node.appendChild(el("p", "fine", "Current " + spec.current));
        }
        return;
      }
      if (ranges.length) {
        var bar = el("div", "ranges");
        ranges.forEach(function (range) {
          var button = el("button", "range", range.label);
          button.type = "button";
          button.setAttribute("aria-pressed", range.ms === rangeMs ? "true" : "false");
          button.addEventListener("click", function () { draw(range.ms); });
          bar.appendChild(button);
        });
        node.appendChild(bar);
      }
      var minV = points[0].v;
      var maxV = points[0].v;
      points.forEach(function (p) {
        if (p.v < minV) minV = p.v;
        if (p.v > maxV) maxV = p.v;
      });
      if (minV === maxV) {
        minV -= 1;
        maxV += 1;
      }
      var w = 320;
      var h = 140;
      var pad = 16;
      var svgNs = "http://www.w3.org/2000/svg";
      var svg = document.createElementNS(svgNs, "svg");
      svg.setAttribute("viewBox", "0 0 " + w + " " + h);
      svg.setAttribute("class", "chart-svg");
      svg.setAttribute("role", "img");
      var title = document.createElementNS(svgNs, "title");
      title.textContent = spec.label || "History";
      svg.appendChild(title);
      var coords = points.map(function (p, i) {
        var x = pad + (i / (points.length - 1)) * (w - pad * 2);
        var y = pad + (1 - (p.v - minV) / (maxV - minV)) * (h - pad * 2);
        return { x: x, y: y, p: p };
      });
      var d = coords.map(function (c, i) {
        return (i ? "L" : "M") + c.x.toFixed(1) + " " + c.y.toFixed(1);
      }).join(" ");
      if (spec.kind === "area") {
        var area = document.createElementNS(svgNs, "path");
        var last = coords[coords.length - 1];
        var first = coords[0];
        area.setAttribute("d", d + " L" + last.x.toFixed(1) + " " + (h - pad) + " L" + first.x.toFixed(1) + " " + (h - pad) + " Z");
        area.setAttribute("class", "area-fill");
        svg.appendChild(area);
      }
      var path = document.createElementNS(svgNs, "path");
      path.setAttribute("d", d);
      path.setAttribute("class", "line-stroke");
      svg.appendChild(path);
      var latest = coords[coords.length - 1];
      var dot = document.createElementNS(svgNs, "circle");
      dot.setAttribute("cx", latest.x.toFixed(1));
      dot.setAttribute("cy", latest.y.toFixed(1));
      dot.setAttribute("r", "2.5");
      dot.setAttribute("class", "line-now");
      svg.appendChild(dot);
      var frame = el("div", "chart");
      frame.appendChild(svg);
      frame.addEventListener("pointermove", function (event) {
        var rect = svg.getBoundingClientRect();
        var x = ((event.clientX - rect.left) / rect.width) * w;
        var best = coords[0];
        var bestDist = Math.abs(coords[0].x - x);
        coords.forEach(function (c) {
          var dist = Math.abs(c.x - x);
          if (dist < bestDist) {
            best = c;
            bestDist = dist;
          }
        });
        var valueText = spec.format ? spec.format(best.p.v) : String(best.p.v);
        showTip(frame, stamp(best.p.t) + " · " + valueText, event.clientX, event.clientY);
      });
      frame.addEventListener("pointerleave", function () { hideTip(frame); });
      node.appendChild(frame);
      var shown = points.length > 8 ? points.slice(points.length - 8) : points;
      node.appendChild(table(
        ["Observed", "Value"],
        shown.map(function (p) {
          return [stamp(p.t), spec.format ? spec.format(p.v) : String(p.v)];
        }),
        spec.question || spec.label || "Observations"
      ));
      node.appendChild(el("p", "fine", "Latest " + (spec.format ? spec.format(latest.p.v) : latest.p.v) + " · " + stamp(latest.p.t)));
    }

    draw(active);
  }

  global.RRCharts = {
    bars: bars,
    line: line
  };
})(window);
