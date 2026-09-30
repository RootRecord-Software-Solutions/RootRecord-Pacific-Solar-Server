const $ = (id) => document.getElementById(id);

let presets = [];
let providers = [];
const providerSel = { discord: "dream", slack: "dream", telegram: "dream", post: "exact", core: "dream", feedback: "exact" };
const replies = { discord: null, slack: null, telegram: null };
/** Discord message currently loaded for PATCH edit (null = normal send). */
let discordEditId = null;
let discordHistoryCache = [];
const feedbackState = {
  items: [],
  selectedId: null,
  templates: [],
  busy: false,
  discordSel: null,
  slackSel: null,
  targets: {
    discord: "1545287392552943768",
    slack: "C0BLMGBVAMD",
  },
};
/** After summarize/preview fills the draft, Send posts as-is (no second Grok pass). */
const draftReadyExact = { discord: false, slack: false, telegram: false, post: false, feedback: false };
const surfaceBusy = { discord: false, slack: false, telegram: false, post: false, feedback: false };

const coreState = {
  sessionId: null,
  messages: [],
  lastQuestion: "",
  lastAnswer: "",
  enhanceText: "",
  enhanceProvider: "",
  busy: false,
  pending: false,
  pendingLabel: "",
};

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $(`page-${btn.dataset.page}`).classList.add("active");
    window.avaDesktop?.deskUiSave?.({ page: btn.dataset.page }).catch(() => {});
    if (btn.dataset.page === "links") renderLinks();
    if (btn.dataset.page === "release") refreshRelease();
    if (btn.dataset.page === "crons") refreshCrons();
    if (btn.dataset.page === "reports") refreshReports();
    if (btn.dataset.page === "weather-gifs") refreshWeatherGifsPage();
    if (btn.dataset.page === "biz") refreshBiz();
    if (btn.dataset.page === "finance") refreshFinance();
    if (btn.dataset.page === "core") refreshCoreStatus();
    if (btn.dataset.page === "feedback") refreshFeedbackPage();
    if (btn.dataset.page === "minecraft") refreshMinecraft();
    if (btn.dataset.page === "stream") refreshStreamOps();
    if (btn.dataset.page === "audio") refreshAudioPage();
    if (btn.dataset.page === "sites") refreshSitesPage();
    if (btn.dataset.page === "backgrounds") refreshBackgroundsPage();
    if (btn.dataset.page === "automation") refreshAutomationPage();
    if (btn.dataset.page === "terminal") refreshTerminalLive();
    if (btn.dataset.page === "settings") {
      refreshStartupPreference();
      refreshConnectionForm();
      refreshGitSyncPrefs();
      refreshDeskFeatures();
      refreshStartTimer();
      refreshShutdownTimer();
      refreshOpsBanner();
      refreshGovernance();
      refreshLedger();
    }
    if (btn.dataset.page === "clear") syncPurgeButton();
  });
});

function syncPurgeButton() {
  const btn = $("purge-big-red");
  const box = $("purge-confirm");
  if (!btn || !box) return;
  btn.disabled = !box.checked || btn.dataset.busy === "1";
}

async function refreshStartupPreference() {
  const result = await window.avaDesktop?.deskUiGet?.();
  const input = $("start-ava-on-launch");
  if (input) input.checked = result?.state?.startAvaOnLaunch === true;
}

$("start-ava-on-launch-save")?.addEventListener("click", async () => {
  const input = $("start-ava-on-launch");
  const status = $("start-ava-on-launch-status");
  try {
    const result = await window.avaDesktop?.deskUiSave?.({
      startAvaOnLaunch: Boolean(input?.checked),
    });
    if (status) status.textContent = result?.ok ? "Saved." : "Could not save startup preference.";
  } catch (err) {
    if (status) status.textContent = `Could not save startup preference: ${err?.message || err}`;
  }
});

$("purge-confirm")?.addEventListener("change", () => syncPurgeButton());

$("purge-big-red")?.addEventListener("click", async () => {
  const btn = $("purge-big-red");
  const st = $("purge-status");
  const box = $("purge-confirm");
  if (!btn || !box?.checked || !window.avaDesktop?.operatorPurge) return;
  if (btn.dataset.busy === "1") return;
  btn.dataset.busy = "1";
  btn.disabled = true;
  btn.textContent = "Ending…";
  if (st) {
    st.textContent =
      "Writing purge flag, disabling Ava Task Scheduler jobs, stopping processes…";
  }
  try {
    const res = await window.avaDesktop.operatorPurge();
    if (st) {
      const killed = Array.isArray(res?.killed) ? res.killed.length : 0;
      st.textContent = res?.ok
        ? `Done. Killed ${killed} process group(s). Desk is closing.\nOpen Ava Desk again when you want Ava back.`
        : `Purge reported a problem: ${res?.detail || "unknown"}\n${JSON.stringify(res, null, 2).slice(0, 1200)}`;
    }
  } catch (err) {
    if (st) st.textContent = `Purge failed: ${err?.message || err}`;
    btn.dataset.busy = "0";
    btn.textContent = "End everything";
    syncPurgeButton();
  }
});

function paintDeskLifecycleStatus(payload) {
  const el = $("desk-lifecycle-status");
  if (!el) return;
  if (!payload) {
    el.textContent = "";
    return;
  }
  if (payload.phase === "music-restore") {
    const ok = payload.music?.ok;
    const track = payload.track ? ` · ${payload.track}` : "";
    el.textContent = ok
      ? `Music bed restored${track}`
      : `Music bed restore failed${payload.music?.detail ? ` · ${payload.music.detail}` : ""}`;
    return;
  }
  const morning = payload.morning;
  const ui = payload.ui;
  const parts = [];
  if (morning?.summary) parts.push(morning.summary);
  if (ui?.musicWanted) parts.push("Last session had music bed on — restoring.");
  if (ui?.page && ui.page !== "terminal") parts.push(`Tab: ${ui.page}`);
  el.textContent = parts.join(" · ") || "";
  if (morning?.missing) el.classList.add("warn-inline");
  else el.classList.remove("warn-inline");
}

function restoreDeskPage(page) {
  const id = String(page || "").trim();
  if (!id) return;
  const btn = document.querySelector(`.tab[data-page="${id}"]`);
  if (btn && !btn.classList.contains("active")) btn.click();
}

async function applyDeskUiRestore() {
  try {
    const res = await window.avaDesktop?.deskUiGet?.();
    const st = res?.state;
    if (st?.page) restoreDeskPage(st.page);
  } catch {
    /* ignore */
  }
  try {
    const morning = await window.avaDesktop?.morningReportCheck?.();
    paintDeskLifecycleStatus({ phase: "start", morning, ui: (await window.avaDesktop?.deskUiGet?.())?.state });
  } catch {
    /* ignore */
  }
}
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const RESPONSE_LOG_KEY = "ava-ivy-response-log-v1";
const RESPONSE_LOG_LIMIT = 80;
const RESPONSE_LOG_SURFACES = ["discord", "slack", "telegram", "post", "core", "feedback"];

function loadResponseLogStore() {
  try {
    const raw = localStorage.getItem(RESPONSE_LOG_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    const out = {};
    for (const s of RESPONSE_LOG_SURFACES) {
      out[s] = Array.isArray(parsed?.[s]) ? parsed[s] : [];
    }
    return out;
  } catch {
    return Object.fromEntries(RESPONSE_LOG_SURFACES.map((s) => [s, []]));
  }
}

function saveResponseLogStore(store) {
  try {
    localStorage.setItem(RESPONSE_LOG_KEY, JSON.stringify(store));
  } catch {
    /* quota / private mode */
  }
}

function formatLogTime(ts) {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return String(ts || "");
  }
}

function renderResponseLog(surface) {
  const host = $(`${surface}-response-log`);
  const meta = $(`${surface}-response-log-meta`);
  if (!host) return;
  const store = loadResponseLogStore();
  const entries = store[surface] || [];
  if (meta) {
    meta.textContent = entries.length
      ? `${entries.length} saved · newest first · persists on this machine`
      : "No responses yet — rewrites, summaries, compares, and sends land here.";
  }
  if (!entries.length) {
    host.innerHTML = "<div class='msg meta'>(empty)</div>";
    return;
  }
  host.innerHTML = entries
    .map((e) => {
      const head = [
        `<span class="kind">${escapeHtml(e.kind || "response")}</span>`,
        e.provider ? `<span>${escapeHtml(e.provider)}</span>` : "",
        e.via ? `<span>${escapeHtml(e.via)}</span>` : "",
        `<span>${escapeHtml(formatLogTime(e.at))}</span>`,
      ]
        .filter(Boolean)
        .join("");
      return `<article class="response-log-entry"><div class="head">${head}</div><pre class="body">${escapeHtml(e.text || "")}</pre></article>`;
    })
    .join("");
}

function appendResponseLog(surface, { kind, text, provider = "", via = "", meta = "" } = {}) {
  const body = String(text || "").trim();
  if (!body || !RESPONSE_LOG_SURFACES.includes(surface)) return;
  const store = loadResponseLogStore();
  const entry = {
    at: Date.now(),
    kind: String(kind || "response"),
    provider: String(provider || ""),
    via: String(via || ""),
    meta: String(meta || ""),
    text: body.slice(0, 20000),
  };
  store[surface] = [entry, ...(store[surface] || [])].slice(0, RESPONSE_LOG_LIMIT);
  saveResponseLogStore(store);
  renderResponseLog(surface);
}

function clearResponseLog(surface) {
  const store = loadResponseLogStore();
  store[surface] = [];
  saveResponseLogStore(store);
  renderResponseLog(surface);
}

function autosizeDraft(el) {
  if (!el) return;
  el.style.height = "auto";
  const next = Math.max(160, Math.min(el.scrollHeight + 4, Math.floor(window.innerHeight * 0.55)));
  el.style.height = `${next}px`;
}

function wireDraftAutosize(id) {
  const el = $(id);
  if (!el) return;
  const run = () => autosizeDraft(el);
  el.addEventListener("input", run);
  run();
}

function renderHistory(el, messages, { replyId = null, onPick = null, surface = null } = {}) {
  el.innerHTML = (messages || [])
    .map((m) => {
      const id = m.id ? String(m.id) : "";
      const who = escapeHtml(m.who || "?");
      const clickable = id && onPick ? " clickable" : "";
      const selected = id && replyId === id ? " msg-reply-target" : "";
      const selfCls = m.self ? " msg-self" : "";
      const dataId = id
        ? ` data-id="${escapeHtml(id)}" data-who="${who}" data-self="${m.self ? "1" : "0"}" data-text="${escapeHtml(String(m.text || "").slice(0, 2000))}"`
        : "";
      const badge = m.self ? ` <span class="hint-inline">(ava)</span>` : "";
      return `<div class="msg${clickable}${selected}${selfCls}"${dataId}><span class="who">${who}</span>${badge}: ${escapeHtml(m.text || "")}</div>`;
    })
    .join("") || "<div class='msg'>(no messages)</div>";

  if (onPick) {
    el.querySelectorAll(".msg.clickable").forEach((node) => {
      node.addEventListener("click", () => {
        onPick({
          id: node.dataset.id,
          who: node.dataset.who,
          self: node.dataset.self === "1",
          text: node.dataset.text || "",
          surface,
        });
      });
    });
  }
  el.scrollTop = el.scrollHeight;
}

function setDiscordEditMode(on) {
  const save = $("discord-save-edit");
  const cancel = $("discord-cancel-edit");
  const send = $("discord-send");
  if (save) save.classList.toggle("hidden", !on);
  if (cancel) cancel.classList.toggle("hidden", !on);
  if (send) send.classList.toggle("hidden", on);
}

function updateDiscordSelectionBar(pick) {
  const editBtn = $("discord-edit-load");
  const delBtn = $("discord-delete");
  const canEdit = Boolean(pick?.id && pick.self);
  // Delete: Ava's own always; others try (needs Manage Messages)
  const canDelete = Boolean(pick?.id);
  if (editBtn) editBtn.classList.toggle("hidden", !canEdit);
  if (delBtn) delBtn.classList.toggle("hidden", !canDelete);
}

function setReplyBar(surface, reply) {
  replies[surface] = reply;
  const bar = $(`${surface}-reply-bar`);
  const whoEl = $(`${surface}-reply-who`);
  if (!bar || !whoEl) return;
  if (reply?.id) {
    bar.classList.remove("hidden");
    const shortId = reply.id.length > 8 ? `…${reply.id.slice(-6)}` : reply.id;
    const tag = reply.self ? "ava" : "msg";
    whoEl.textContent = `${tag} @${reply.who} (${shortId})`;
  } else {
    bar.classList.add("hidden");
    whoEl.textContent = "?";
  }
  if (surface === "discord") {
    updateDiscordSelectionBar(reply);
    if (!reply?.id) {
      discordEditId = null;
      setDiscordEditMode(false);
    }
  }
}

function fillSelect(sel, items, { placeholder, nameFn } = {}) {
  sel.innerHTML = "";
  if (placeholder) {
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = placeholder;
    sel.appendChild(blank);
  }
  for (const item of items || []) {
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = nameFn ? nameFn(item) : item.name || item.id;
    sel.appendChild(opt);
  }
}

function fillPresets(surface) {
  const sel = $("post-preset");
  const filtered = presets.filter((p) => p.surface === surface);
  sel.innerHTML = "";
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = "(pick preset or type ID below)";
  sel.appendChild(blank);
  for (const p of filtered) {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = `${p.key} — ${p.label}`;
    sel.appendChild(opt);
  }
}

function markDraftReadyExact(surface, draftId) {
  draftReadyExact[surface] = true;
  const el = $(draftId);
  if (!el || el.dataset.readyBound) return;
  el.dataset.readyBound = "1";
  el.addEventListener("input", () => {
    draftReadyExact[surface] = false;
  });
}

function stripRewritePreamble(text) {
  return String(text || "")
    .replace(
      /^(here'?s\s+(the\s+)?(rewritten|revised|updated)\s+(message|reply|draft|version)[^\n]*:\s*)/i,
      "",
    )
    .replace(/^(rewritten\s+(message|reply)\s+in\s+ava[^\n]*:\s*)/i, "")
    .trim();
}

function renderProviders(containerId, surfaceKey) {
  const host = $(containerId);
  if (!host) return;
  host.innerHTML = "";
  const list = providers.length
    ? providers
    : [
        { id: "exact", label: "Exactly the same" },
        { id: "dream", label: "Dream / Grok" },
        { id: "cursor", label: "Cursor" },
        { id: "ollama", label: "Ollama" },
        { id: "google", label: "Google" },
      ];
  for (const p of list) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = p.label || p.id;
    btn.title = p.detail || p.model || p.id;
    if (p.configured === false) btn.style.opacity = "0.45";
    if (providerSel[surfaceKey] === p.id) btn.classList.add("active-provider");
    btn.addEventListener("click", () => {
      providerSel[surfaceKey] = p.id;
      // Choosing a rewrite provider means Send may rewrite again.
      if (p.id !== "exact" && draftReadyExact[surfaceKey] != null) {
        draftReadyExact[surfaceKey] = false;
      }
      host.querySelectorAll("button").forEach((b) => b.classList.remove("active-provider"));
      btn.classList.add("active-provider");
    });
    host.appendChild(btn);
  }
}

function showCompare(elId, results) {
  const el = $(elId);
  if (!el) return;
  el.classList.add("show");
  el.textContent = (results || [])
    .map((r) => {
      const head = `── ${r.provider || "?"} · ${r.via || ""}${r.detail ? ` · ${r.detail}` : ""}`;
      return `${head}\n${r.text || "(empty)"}\n`;
    })
    .join("\n");
}

function discordChannelId() {
  const priv = $("discord-private").value;
  return priv || $("discord-channel").value;
}

async function refreshDiscord() {
  const channelId = discordChannelId();
  const hist = await window.avaDesktop.history({
    surface: "discord",
    channelId,
    limit: 150,
  });
  discordHistoryCache = hist.messages || [];
  renderHistory($("discord-history"), hist.messages, {
    replyId: replies.discord?.id || null,
    surface: "discord",
    onPick: (pick) => {
      // Prefer full text from cache (dataset HTML-escapes)
      const full = discordHistoryCache.find((m) => String(m.id) === String(pick.id));
      const merged = {
        ...pick,
        text: full?.text ?? pick.text ?? "",
        self: full?.self ?? pick.self,
      };
      setReplyBar("discord", merged);
      $("discord-history").querySelectorAll(".msg").forEach((node) => {
        node.classList.toggle("msg-reply-target", node.dataset.id === pick.id);
      });
      // Ava messages: auto-load into draft for edit (can't copy from history easily)
      if (merged.self && merged.id) {
        discordEditId = merged.id;
        $("discord-draft").value = merged.text || "";
        autosizeDraft($("discord-draft"));
        draftReadyExact.discord = true;
        setDiscordEditMode(true);
        $("discord-status").textContent = `editing …${String(merged.id).slice(-6)} — change text, then Save edit`;
      } else {
        // Others: reply target only
        if (discordEditId) {
          discordEditId = null;
          setDiscordEditMode(false);
        }
      }
      $("discord-draft").focus();
    },
  });
  $("discord-status").textContent = hist.ok
    ? `loaded ${hist.messages?.length || 0} msgs${hist.botName ? ` · bot ${hist.botName}` : ""}`
    : hist.detail || "fail";
}

async function loadDiscordEdit() {
  const pick = replies.discord;
  if (!pick?.id || !pick.self) {
    $("discord-status").textContent = "select an Ava message to edit";
    return;
  }
  const full = discordHistoryCache.find((m) => String(m.id) === String(pick.id));
  const text = full?.text ?? pick.text ?? "";
  discordEditId = pick.id;
  $("discord-draft").value = text;
  autosizeDraft($("discord-draft"));
  draftReadyExact.discord = true;
  setDiscordEditMode(true);
  replies.discord = { ...pick, text };
  $("discord-status").textContent = `editing message …${String(pick.id).slice(-6)} — Save edit or Cancel`;
  $("discord-draft").focus();
}

async function saveDiscordEdit() {
  const channelId = discordChannelId();
  const text = ($("discord-draft").value || "").trim();
  if (!discordEditId || !channelId || !text) {
    $("discord-status").textContent = "need selected Ava message + text";
    return;
  }
  if (surfaceBusy.discord) {
    $("discord-status").textContent = "busy";
    return;
  }
  surfaceBusy.discord = true;
  $("discord-status").textContent = "saving edit…";
  try {
    const r = await window.avaDesktop.discordEdit({
      channelId,
      messageId: discordEditId,
      text,
    });
    if (!r?.ok) {
      $("discord-status").textContent = `edit failed · ${r?.detail || "?"}`;
      return;
    }
    appendResponseLog("discord", {
      kind: "edit",
      text,
      provider: "exact",
      via: "discord-patch",
      meta: `id ${r.id || discordEditId}`,
    });
    discordEditId = null;
    setDiscordEditMode(false);
    $("discord-draft").value = "";
    setReplyBar("discord", null);
    $("discord-status").textContent = `edited · ${r.id || "?"}`;
    await refreshDiscord();
  } catch (err) {
    $("discord-status").textContent = String(err.message || err);
  } finally {
    surfaceBusy.discord = false;
  }
}

function cancelDiscordEdit() {
  discordEditId = null;
  setDiscordEditMode(false);
  $("discord-status").textContent = "edit cancelled";
}

async function deleteDiscordSelected() {
  const pick = replies.discord;
  const channelId = discordChannelId();
  if (!pick?.id || !channelId) {
    $("discord-status").textContent = "select a message to delete";
    return;
  }
  const label = pick.self ? "Ava's message" : `message from ${pick.who}`;
  if (!confirm(`Delete ${label} (…${String(pick.id).slice(-6)})?\n\nBots can always delete their own. Others need Manage Messages.`)) {
    return;
  }
  if (surfaceBusy.discord) return;
  surfaceBusy.discord = true;
  $("discord-status").textContent = "deleting…";
  try {
    const r = await window.avaDesktop.discordDelete({
      channelId,
      messageId: pick.id,
    });
    if (!r?.ok) {
      $("discord-status").textContent = `delete failed · ${r?.detail || "?"}`;
      return;
    }
    appendResponseLog("discord", {
      kind: "delete",
      text: pick.text || `(deleted ${pick.id})`,
      provider: "exact",
      via: "discord-delete",
      meta: `id ${pick.id}`,
    });
    if (discordEditId === pick.id) {
      discordEditId = null;
      setDiscordEditMode(false);
      $("discord-draft").value = "";
    }
    setReplyBar("discord", null);
    $("discord-status").textContent = `deleted · ${pick.id}`;
    await refreshDiscord();
  } catch (err) {
    $("discord-status").textContent = String(err.message || err);
  } finally {
    surfaceBusy.discord = false;
  }
}

async function refreshSlack() {
  const channelId = $("slack-channel").value;
  const hist = await window.avaDesktop.history({
    surface: "slack",
    channelId,
    limit: 150,
  });
  renderHistory($("slack-history"), hist.messages, {
    replyId: replies.slack?.id || null,
    onPick: (pick) => {
      setReplyBar("slack", pick);
      $("slack-draft").focus();
    },
  });
  $("slack-status").textContent = hist.ok
    ? `loaded ${hist.messages?.length || 0} msgs`
    : hist.detail || "fail";
}

async function refreshTelegram() {
  const channelId = $("telegram-chat").value.trim();
  const hist = await window.avaDesktop.history({
    surface: "telegram",
    channelId,
    limit: 150,
  });
  renderHistory($("telegram-history"), hist.messages, {
    replyId: replies.telegram?.id || null,
    onPick: (pick) => {
      setReplyBar("telegram", pick);
      $("telegram-draft").focus();
    },
  });
  $("telegram-status").textContent = `context ${hist.messages?.length || 0} msgs${hist.detail ? ` · ${hist.detail}` : ""}`;
}

async function refreshPostHistory() {
  const surface = $("post-surface").value;
  let channelId = $("post-channel").value.trim();
  const asPreset = presets.find(
    (p) => p.key === channelId.toLowerCase() || p.id === channelId,
  );
  if (asPreset) channelId = asPreset.id;
  const meta = $("post-history-meta");
  const host = $("post-history");
  if (!channelId) {
    host.innerHTML = "";
    meta.textContent = "Pick a channel first.";
    return;
  }
  meta.textContent = "loading…";
  try {
    const hist = await window.avaDesktop.history({
      surface,
      channelId,
      limit: 150,
    });
    renderHistory(host, hist.messages, {
      onPick: (pick) => {
        if (pick?.id) $("post-ref").value = String(pick.id);
        $("post-draft").focus();
      },
    });
    const n = hist.messages?.length || 0;
    meta.textContent = hist.ok
      ? `${n} msgs · ${hist.detail || surface}`
      : hist.detail || "fail";
  } catch (err) {
    host.innerHTML = "";
    meta.textContent = String(err.message || err);
  }
}

async function previewRewrite(surface, draftId, channelId, statusId, compareId, compare = false) {
  const text = $(draftId).value.trim();
  if (!text) {
    $(statusId).textContent = "Type a draft first.";
    return;
  }
  $(statusId).textContent = compare ? "comparing providers…" : `rewriting via ${providerSel[surface]}…`;
  try {
    const r = await window.avaDesktop.rewritePreview({
      surface: surface === "post" ? $("post-surface").value : surface,
      channelId,
      text,
      provider: providerSel[surface],
      compare,
    });
    if (compare && r.results) {
      showCompare(compareId, r.results);
      $(statusId).textContent = `compared ${r.results.length} providers`;
      const blob = (r.results || [])
        .map((x) => `── ${x.provider || "?"} · ${x.via || ""}\n${x.text || ""}`)
        .join("\n\n");
      appendResponseLog(surface, {
        kind: "compare",
        text: blob,
        provider: "all",
        via: "compare",
      });
      return;
    }
    if (r.text) {
      $(draftId).value = stripRewritePreamble(r.text);
      autosizeDraft($(draftId));
      markDraftReadyExact(surface, draftId);
      appendResponseLog(surface, {
        kind: "rewrite",
        text: $(draftId).value,
        provider: r.provider || providerSel[surface],
        via: r.via || "",
      });
    }
    $(statusId).textContent = `preview · ${r.provider || providerSel[surface]} · ${r.via || ""}${r.detail ? ` · ${r.detail}` : ""} · Send will post as-is`;
  } catch (err) {
    $(statusId).textContent = String(err.message || err);
  }
}

async function summarizeSurface(surface, channelId, draftId, statusId) {
  if (!channelId) {
    $(statusId).textContent = "Pick a channel first.";
    return;
  }
  if (surfaceBusy[surface]) {
    $(statusId).textContent = "busy — wait for the current job";
    return;
  }
  surfaceBusy[surface] = true;
  $(statusId).textContent = "summarizing last 50–100 messages…";
  try {
    const r = await window.avaDesktop.summarize({
      surface,
      channelId,
      provider: providerSel[surface] === "exact" ? "dream" : providerSel[surface],
      limit: 150,
    });
    if (!r.ok) {
      $(statusId).textContent = r.detail || "summarize failed";
      return;
    }
    $(draftId).value = stripRewritePreamble(r.text || "");
    autosizeDraft($(draftId));
    markDraftReadyExact(surface, draftId);
    appendResponseLog(surface, {
      kind: "summary",
      text: $(draftId).value,
      provider: r.provider || "",
      via: r.via || "",
      meta: `${r.messageCount || "?"} msgs`,
    });
    $(statusId).textContent = `summary · ${r.messageCount || "?"} msgs · ${r.provider || ""} · ${r.via || ""} · Send will post as-is`;
  } catch (err) {
    $(statusId).textContent = String(err.message || err);
  } finally {
    surfaceBusy[surface] = false;
  }
}

async function sendSurface(surface, draftId, channelId, statusId) {
  const text = $(draftId).value.trim();
  if (surface === "discord" && discordEditId) {
    $(statusId).textContent = "in edit mode — use Save edit (or Cancel edit)";
    return;
  }
  if (!channelId || !text) {
    $(statusId).textContent = "Need channel + text.";
    return;
  }
  if (surfaceBusy[surface]) {
    $(statusId).textContent = "already sending — ignored double click";
    return;
  }
  const provider = providerSel[surface];
  // Don't run Dream/Grok a second time after Summarize / Preview already filled the draft.
  const rewrite = provider !== "exact" && !draftReadyExact[surface];
  surfaceBusy[surface] = true;
  $(statusId).textContent = rewrite
    ? `sending via ${provider}…`
    : draftReadyExact[surface]
      ? "sending exact (already rewritten — no second Grok pass)…"
      : "sending exact…";
  try {
    const r = await window.avaDesktop.send({
      surface,
      channelId,
      text,
      refId: replies[surface]?.id || undefined,
      rewrite,
      provider: rewrite ? provider : "exact",
    });
    draftReadyExact[surface] = false;
    appendResponseLog(surface, {
      kind: "send",
      text: r.text || text,
      provider: r.provider || (rewrite ? provider : "exact"),
      via: r.via || "",
      meta: r.id ? `id ${r.id}` : "",
    });
    $(statusId).textContent = `sent · ${r.provider || provider} · ${r.via || ""} · id ${r.id || "?"}`;
    $(draftId).value = "";
    autosizeDraft($(draftId));
    setReplyBar(surface, null);
    if (surface === "discord") await refreshDiscord();
    if (surface === "slack") await refreshSlack();
    if (surface === "telegram") await refreshTelegram();
  } catch (err) {
    $(statusId).textContent = String(err.message || err);
  } finally {
    surfaceBusy[surface] = false;
  }
}

function fmtMs(ms) {
  if (ms == null) return "—";
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m`;
  return `${Math.round(m / 60)}h`;
}

function fmtCountdown(ms) {
  if (ms == null || !Number.isFinite(ms)) return "—";
  if (ms <= 0) return "now";
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
  if (m > 0) return `${m}m ${String(sec).padStart(2, "0")}s`;
  return `${sec}s`;
}

function countdownLabel(nextAt, now = Date.now()) {
  if (!nextAt || !Number.isFinite(nextAt) || nextAt <= 0) return "—";
  const left = nextAt - now;
  return left <= 0 ? "now" : `next ${fmtCountdown(left)}`;
}

function tickCountdowns(root = document) {
  const now = Date.now();
  root.querySelectorAll("[data-next-at]").forEach((el) => {
    const nextAt = Number(el.dataset.nextAt);
    if (!Number.isFinite(nextAt) || nextAt <= 0) {
      el.textContent = el.dataset.nextEmpty || "—";
      el.classList.remove("due-now");
      return;
    }
    el.textContent = countdownLabel(nextAt, now);
    el.classList.toggle("due-now", nextAt - now <= 0);
  });
}

function fmtAge(ts) {
  if (!ts) return "never";
  return `${fmtMs(Date.now() - Number(ts))} ago`;
}

async function refreshCrons() {
  const meta = $("cron-meta");
  const host = $("cron-table");
  meta.textContent = "Loading cron status…";
  try {
    const st = await window.avaDesktop.cronStatus();
    if (!st?.ok && !st?.jobs) {
      meta.textContent =
        st?.detail ||
        "cron API unavailable — is Ava brain up on :8787? Try Refresh.";
      host.innerHTML = "";
      $("cron-status").textContent = JSON.stringify(st, null, 2);
      return;
    }
    meta.textContent = [
      st.started ? "runner: active" : "runner: idle/not started yet",
      st.runnerEnvDisabled ? "AVA_CRON_RUNNER=0" : null,
      `${(st.jobs || []).length} jobs`,
      `${(st.jobs || []).filter((j) => j.running).length} running`,
      `${(st.jobs || []).filter((j) => j.disabled).length} disabled`,
    ]
      .filter(Boolean)
      .join(" · ");

    host.innerHTML = "";
    for (const job of st.jobs || []) {
      const row = document.createElement("div");
      row.className = `cron-row${job.disabled ? " disabled" : ""}`;
      const active = !job.disabled;
      const nextAt = active ? Number(job.nextAt || 0) : 0;
      row.innerHTML = `
        <div>
          <div class="id">${escapeHtml(job.id)}</div>
          <div class="muted">${escapeHtml(job.cronHint || "")}</div>
        </div>
        <div>every ${fmtMs(job.everyMs)}</div>
        <div class="cron-state">
          <span>${job.running ? "running" : job.disabled ? "disabled" : "active"}</span>
          ${
            active
              ? `<span class="cron-countdown" data-next-at="${nextAt || ""}">${countdownLabel(nextAt)}</span>`
              : ""
          }
        </div>
        <div class="muted">last ${fmtAge(job.lastFiredAt)}</div>
        <div class="actions"></div>
      `;
      const actions = row.querySelector(".actions");
      const runBtn = document.createElement("button");
      runBtn.type = "button";
      runBtn.textContent = "Run now";
      runBtn.onclick = async () => {
        $("cron-status").textContent = `running ${job.id}…`;
        const r = await window.avaDesktop.cronRun(job.id);
        $("cron-status").textContent = JSON.stringify(r, null, 2).slice(0, 2000);
        await refreshCrons();
      };
      const tog = document.createElement("button");
      tog.type = "button";
      tog.textContent = job.disabled ? "Enable" : "Disable";
      tog.onclick = async () => {
        await window.avaDesktop.cronConfig({
          toggleId: job.id,
          enabled: job.disabled,
        });
        await refreshCrons();
      };
      const every = document.createElement("button");
      every.type = "button";
      every.textContent = "Set interval";
      every.onclick = async () => {
        const raw = window.prompt(
          `Interval ms for ${job.id} (blank = default ${job.baseEveryMs})`,
          String(job.everyMs || job.baseEveryMs || ""),
        );
        if (raw == null) return;
        const n = Number(raw);
        await window.avaDesktop.cronConfig({
          setEveryMs: { id: job.id, everyMs: Number.isFinite(n) ? n : 0 },
        });
        await refreshCrons();
      };
      actions.append(runBtn, tog, every);
      host.appendChild(row);
    }
    $("cron-status").textContent = "";
    tickCountdowns(host);
    ensureCronLive();
  } catch (err) {
    meta.textContent = String(err.message || err);
    $("cron-status").textContent =
      `Brain must be up on ${lastBrainUrl || "the selected connection"} — Settings → Connection, or ~/ava/bin/start-ava-desktop.sh`;
  }
}

let cronTickTimer = null;
let cronRefreshTimer = null;
function ensureCronLive() {
  if (!cronTickTimer) {
    cronTickTimer = setInterval(() => tickCountdowns(), 1000);
  }
  if (!cronRefreshTimer) {
    cronRefreshTimer = setInterval(() => {
      if ($("page-crons")?.classList.contains("active")) refreshCrons();
      if ($("page-reports")?.classList.contains("active")) refreshReports();
    }, 20_000);
  }
}

function fmtHst(ts) {
  if (!ts) return "—";
  const value = typeof ts === "number" ? ts : Date.parse(String(ts));
  if (!Number.isFinite(value)) return "—";
  return new Date(value).toLocaleString("en-US", {
    timeZone: "Pacific/Honolulu",
    hour12: false,
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function reportStatusPill(status) {
  const s = String(status || "upcoming");
  return `<span class="report-pill ${escapeHtml(s)}">${escapeHtml(s)}</span>`;
}

function paintCurrentReport(st) {
  const cur = st?.current || {};
  const meta = $("reports-current-meta");
  const preview = $("reports-current-preview");
  if (meta) {
    meta.textContent = cur.exists
      ? `${cur.current ? "Current" : "Latest"} ${cur.name || "morning-report-current.md"} · ${fmtHst(cur.mtimeMs)} · ${Math.max(1, Math.round((cur.bytes || 0) / 1024))} KB`
      : "No current report yet — paste one below.";
  }
  if (preview) {
    const text = String(cur.text || "").trim();
    preview.textContent = text ? text.slice(0, 1200) : "(empty)";
  }
}

function paintReportOverview(st) {
  const host = $("reports-overview");
  const meta = $("reports-readiness-meta");
  if (!host || !meta) return;
  const slots = st?.dailyReportsDue?.slots || {};
  const generation = st?.generation?.reports || {};
  const audio = st?.generatedAudio || {};
  const labels = { morning: "Morning", midday: "Noon", evening: "Evening", late: "Late evening" };
  const order = ["morning", "midday", "evening", "late"];
  const freshness = st?.freshness || {};
  const stale = freshness.stale || [];
  const next = Number(st?.readiness?.nextAt || 0);
  meta.textContent = [
    `Poll ${st?.readiness?.status || "unknown"}${next ? ` · next ${fmtHst(next)}` : ""}`,
    freshness.ok ? "all required metrics fresh" : `stale: ${stale.join(", ") || freshness.detail || "not validated"}`,
  ].join(" · ");
  host.innerHTML = `<div class="cron-row report-row report-overview-head"><strong>Report</strong><strong>Schedule</strong><strong>Status</strong><strong>Path</strong><strong>Audio</strong></div>`;
  for (const kind of order) {
    const slot = slots[kind] || {};
    const cfg = generation[kind] || {};
    const files = audio[kind] || [];
    const audioLabel = files.length
      ? files.map((f) => `${String(f.name || "").endsWith(".wav") ? "WAV" : "MP3"} ${Math.round((f.size || 0) / 1024)} KB`).join(" · ")
      : "no generated audio";
    const row = document.createElement("div");
    row.className = `cron-row report-row ${slot.status || ""}`;
    row.innerHTML = `
      <div><strong>${escapeHtml(labels[kind])}</strong><div class="muted">${escapeHtml(kind)}</div></div>
      <div class="muted">${escapeHtml(slot.scheduled_at || "—")}</div>
      <div>${reportStatusPill(slot.status || "pending")}</div>
      <div class="muted">Text ${escapeHtml(cfg.engine || "local")} · MP3 ${escapeHtml(cfg.mp3 || "local")}</div>
      <div class="muted">${escapeHtml(audioLabel)}</div>
    `;
    host.appendChild(row);
  }
}

async function refreshReports() {
  const meta = $("reports-meta");
  const dueHost = $("reports-due");
  const recHost = $("reports-recurring");
  const genHost = $("reports-generated");
  if (!meta || !dueHost) return;
  meta.textContent = "Loading reports…";
  try {
    const st = await window.avaDesktop.reportsStatus();
    if (!st?.ok && !st?.dueToday) {
      meta.textContent = st?.detail || "reports API unavailable — is Ava brain up?";
      dueHost.innerHTML = "";
      recHost.innerHTML = "";
      genHost.innerHTML = "";
      paintCurrentReport(null);
      $("reports-status").textContent = JSON.stringify(st, null, 2);
      return;
    }
    paintCurrentReport(st);
    paintReportOverview(st);
    const dailySlots = st.dailyReportsDue?.slots || {};
    const dailyRows = Object.values(dailySlots);
    meta.textContent = [
      `HST ${st.hstDay || "?"}`,
      `${dailyRows.filter((r) => !["done", "skipped_optional"].includes(r.status)).length} report slots open`,
      `${(st.generated || []).length} generated`,
      st.asleep ? "asleep" : null,
    ]
      .filter(Boolean)
      .join(" · ");

    dueHost.innerHTML = "";
    for (const [kind, r] of Object.entries(dailySlots)) {
      const row = document.createElement("div");
      row.className = `cron-row report-row ${r.status || ""}`;
      row.innerHTML = `
        <div>
          <div class="id">${escapeHtml(kind)}</div>
          <div class="muted">${escapeHtml(r.scheduled_at || "")}</div>
        </div>
        <div>${reportStatusPill(r.status)}</div>
        <div class="muted">Text ${escapeHtml(r.engine_req || "local")} · MP3 ${escapeHtml(r.mp3_req || "local")}</div>
        <div class="muted">${r.completed_at ? `completed ${escapeHtml(fmtHst(r.completed_at))}` : r.error ? escapeHtml(r.error) : "not completed"}</div>
        <div></div>
      `;
      dueHost.appendChild(row);
    }

    recHost.innerHTML = "";
    for (const r of st.recurring || []) {
      const row = document.createElement("div");
      row.className = "cron-row report-row";
      const nextAt = Number(r.nextAt || 0);
      row.innerHTML = `
        <div>
          <div class="id">${escapeHtml(r.label || r.id)}</div>
          <div class="muted">${escapeHtml(r.when || "")}${r.lastKey ? ` · last ${escapeHtml(r.lastKey)}` : ""}</div>
        </div>
        <div class="muted">recurring</div>
        <div class="cron-countdown" data-next-at="${nextAt || ""}">${countdownLabel(nextAt)}</div>
        <div class="muted">last ${r.lastAt ? fmtHst(r.lastAt) : "—"}</div>
        <div></div>
      `;
      recHost.appendChild(row);
    }

    genHost.innerHTML = "";
    for (const f of st.generated || []) {
      const row = document.createElement("div");
      row.className = "cron-row report-row generated";
      row.innerHTML = `
        <div>
          <div class="id">${escapeHtml(f.label || f.name)}</div>
          <div class="muted">${escapeHtml(f.rel || f.path || "")}</div>
        </div>
        <div class="muted">${escapeHtml(f.kind || "")}${f.dir ? " · folder" : ""}</div>
        <div class="muted">${f.mtime ? fmtHst(f.mtime) : "—"}</div>
        <div class="muted">${f.bytes != null ? `${Math.round(f.bytes / 1024)} KB` : ""}</div>
        <div></div>
      `;
      genHost.appendChild(row);
    }

    $("reports-status").textContent = "";
    await refreshReportGenToggles();
    await refreshReportAudioManual(st);
    if (typeof tickCountdowns === "function") tickCountdowns();
    if (typeof ensureCronLive === "function") ensureCronLive();
  } catch (e) {
    meta.textContent = String(e?.message || e);
  }
}

async function refreshReportGenToggles() {
  const host = $("reports-gen-toggles");
  const statusEl = $("reports-gen-status");
  if (!host) return;
  try {
    const res = await fetch(`${brainBaseUrl()}/api/reports/generation`, { cache: "no-store" });
    const st = await res.json();
    const reports = st?.reports || st?.config?.reports || {};
    const kinds = ["morning", "midday", "evening", "late", "hourly", "slot"].filter((k) => reports[k]);
    const labels = {
      morning: "Morning",
      midday: "Midday",
      evening: "Evening",
      late: "Late",
      hourly: "Hourly",
      slot: "Slot",
    };
    host.innerHTML = "";
    for (const kind of kinds) {
      const rowCfg = reports[kind] || {};
      const row = document.createElement("div");
      row.className = "cron-row report-row";
      const eng = document.createElement("select");
      eng.title = "Text engine";
      for (const v of ["local", "cloud"]) {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = v === "local" ? "Text: Local" : "Text: Cloud";
        if ((rowCfg.engine || "local") === v) o.selected = true;
        eng.appendChild(o);
      }
      const mp3 = document.createElement("select");
      mp3.title = "MP3 path";
      for (const v of ["local", "cloud"]) {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = v === "local" ? "MP3: Local" : "MP3: Cloud";
        if ((rowCfg.mp3 || "local") === v) o.selected = true;
        mp3.appendChild(o);
      }
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.textContent = "Save";
      saveBtn.className = "primary";
      saveBtn.onclick = async () => {
        if (statusEl) statusEl.textContent = "Saving…";
        const r = await fetch(`${brainBaseUrl()}/api/reports/generation`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            reports: { [kind]: { engine: eng.value, mp3: mp3.value } },
          }),
        });
        const out = await r.json();
        if (statusEl) statusEl.textContent = out?.ok ? `Saved ${kind}` : JSON.stringify(out);
        await refreshReportGenToggles();
      };
      row.innerHTML = `<div><strong>${labels[kind] || kind}</strong></div>`;
      const controls = document.createElement("div");
      controls.className = "row wrap";
      controls.appendChild(eng);
      controls.appendChild(mp3);
      controls.appendChild(saveBtn);
      row.appendChild(controls);
      host.appendChild(row);
    }
  } catch (e) {
    host.innerHTML = `<div class="muted">${escapeHtml(String(e?.message || e))}</div>`;
  }
}

async function refreshReportAudioManual(reportBoard = null) {
  const host = $("reports-audio-manual");
  const statusEl = $("reports-audio-status");
  if (!host) return;
  try {
    const res = await fetch(`${brainBaseUrl()}/api/reports/audio-manual`, {
      cache: "no-store",
    });
    const st = await res.json();
    if (!st?.ok) {
      host.innerHTML = `<div class="muted">${escapeHtml(st?.detail || "unavailable")}</div>`;
      return;
    }
    const cands = st.candidates || [];
    const labels = { morning: "Morning (10:00)", midday: "Noon (11:55)", evening: "Evening (17:15)", late: "Late (22:00)" };
    host.innerHTML = "";
    for (const kind of st.kinds || ["morning", "midday", "evening"]) {
      const slot = (st.slots || {})[kind] || {};
      const generated = reportBoard?.generatedAudio?.[kind] || [];
      const row = document.createElement("div");
      row.className = "cron-row report-row";
      const sel = document.createElement("select");
      sel.dataset.kind = kind;
      sel.className = "reports-audio-select";
      const opt0 = document.createElement("option");
      opt0.value = "";
      opt0.textContent = "(none)";
      sel.appendChild(opt0);
      let matched = false;
      for (const c of cands) {
        const opt = document.createElement("option");
        opt.value = c.path;
        opt.textContent = `${c.name} · ${c.rel || ""}`;
        if (slot.path && c.path === slot.path) {
          opt.selected = true;
          matched = true;
        }
        sel.appendChild(opt);
      }
      if (slot.path && !matched) {
        const opt = document.createElement("option");
        opt.value = slot.path;
        opt.textContent = slot.exists ? slot.path : `(missing) ${slot.path}`;
        opt.selected = true;
        sel.appendChild(opt);
      }
      const auto = document.createElement("input");
      auto.type = "checkbox";
      auto.checked = !!slot.auto_play;
      auto.title = "Auto-play on schedule";
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.textContent = "Save";
      saveBtn.className = "primary";
      saveBtn.onclick = async () => {
        statusEl.textContent = "Saving…";
        const body = {
          kind,
          path: sel.value || "",
          auto_play: !!auto.checked,
          clear: !sel.value,
        };
        const r = await fetch(`${brainBaseUrl()}/api/reports/audio-manual`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const j = await r.json();
        statusEl.textContent = JSON.stringify(j, null, 2);
        await refreshReportAudioManual();
      };
      const playBtn = document.createElement("button");
      playBtn.type = "button";
      playBtn.textContent = "Play now";
      playBtn.onclick = async () => {
        statusEl.textContent = "Playing…";
        const r = await fetch(`${brainBaseUrl()}/api/reports/audio-manual/play`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kind, path: sel.value || null }),
        });
        const j = await r.json();
        statusEl.textContent = JSON.stringify(j, null, 2);
      };
      const left = document.createElement("div");
      const generatedLabel = generated.length
        ? `generated: ${generated.map((f) => f.name).join(" + ")}`
        : "no generated current audio";
      left.innerHTML = `<div class="id">${escapeHtml(labels[kind] || kind)}</div>
        <div class="muted">${escapeHtml(generatedLabel)} · manual ${slot.exists ? "fallback ready" : slot.path ? "missing file" : "not set"} · auto ${slot.auto_play ? "ON" : "off"}</div>`;
      const mid = document.createElement("div");
      mid.appendChild(sel);
      const autoWrap = document.createElement("label");
      autoWrap.className = "check";
      autoWrap.style.display = "flex";
      autoWrap.style.gap = "0.35rem";
      autoWrap.style.alignItems = "center";
      autoWrap.appendChild(auto);
      autoWrap.appendChild(document.createTextNode("Auto-play"));
      const actions = document.createElement("div");
      actions.className = "row wrap";
      actions.appendChild(autoWrap);
      actions.appendChild(saveBtn);
      actions.appendChild(playBtn);
      row.appendChild(left);
      row.appendChild(mid);
      row.appendChild(actions);
      host.appendChild(row);
    }
    if (statusEl && !statusEl.textContent) {
      statusEl.textContent = st.note || "";
    }
  } catch (e) {
    host.innerHTML = `<div class="muted">${escapeHtml(String(e?.message || e))}</div>`;
  }
}

async function refreshWeatherGifsPage() {
  const meta = $("wg-meta");
  const upHost = $("wg-updater");
  const dirHost = $("wg-dirs");
  const stEl = $("wg-status");
  if (!meta || !upHost) return;
  meta.textContent = "Loading leftover weather GIF board…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/weather-gifs`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      meta.textContent = d?.detail || "weather GIF API unavailable";
      if (stEl) stEl.textContent = JSON.stringify(d, null, 2).slice(0, 2000);
      return;
    }
    const up = d.updater || {};
    meta.textContent = [
      d.message || "Collector moved off Ava-core",
      d.collector || up.abs || null,
    ]
      .filter(Boolean)
      .join(" · ");

    upHost.innerHTML = "";
    const urow = document.createElement("div");
    urow.className = "cron-row";
    urow.innerHTML = `
      <div>
        <div class="id">Weather GIF collector</div>
        <div class="muted">${escapeHtml(d.collector || up.abs || "")}</div>
      </div>
      <div>workstations collector</div>
      <div class="muted">C: live tree</div>
      <div class="muted">${escapeHtml(d.message || "Weather GIFs live under Media public images/weather.")}</div>
      <div class="actions"></div>
    `;
    const uact = urow.querySelector(".actions");
    const openCol = document.createElement("button");
    openCol.type = "button";
    openCol.textContent = "Open";
    openCol.onclick = () => window.avaDesktop.openFolder("weatherGifsCollector");
    uact.append(openCol);
    upHost.appendChild(urow);

    if (dirHost) {
      dirHost.innerHTML = "";
      const dirs = (d.directories || []).filter(
        (x) => x.kind !== "archive-product" && x.kind !== "location-current",
      );
      for (const dir of dirs) {
        const row = document.createElement("div");
        row.className = "cron-row";
        row.innerHTML = `
          <div>
            <div class="id">${escapeHtml(dir.kind)}</div>
            <div class="muted">${escapeHtml(dir.abs || dir.rel || "")}</div>
          </div>
          <div>${Number(dir.files || 0)} leftover file${dir.files === 1 ? "" : "s"}</div>
          <div class="muted">${dir.latestMtimeMs ? fmtAge(dir.latestMtimeMs) : "—"}</div>
          <div class="muted">${dir.latestMtimeMs ? fmtHst(dir.latestMtimeMs) : ""}</div>
          <div class="actions"></div>
        `;
        const actions = row.querySelector(".actions");
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.textContent = "Open";
        openBtn.onclick = () => window.avaDesktop.openPath(dir.abs);
        actions.append(openBtn);
        dirHost.appendChild(row);
      }
      if (!dirs.length) {
        dirHost.innerHTML = `<div class="cron-row"><div class="muted">No leftover Ava-core GIF folders.</div></div>`;
      }
    }
    if (stEl) stEl.textContent = d.message || "Collector is workstations/weather-gif-collector on C:.";
  } catch (err) {
    meta.textContent = String(err.message || err);
    if (stEl) stEl.textContent = `Brain must be up on ${lastBrainUrl || "the selected connection"}`;
  }
}

/* ——— Biz / time tracking ——— */
let bizBusy = false;
let bizCache = null;
let bizTimer = null;

function fmtBizWhen(ms) {
  if (!Number.isFinite(Number(ms))) return "—";
  try {
    return new Date(Number(ms)).toLocaleString("en-US", {
      timeZone: "Pacific/Honolulu",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return "—";
  }
}

function drawBizLineChart(el, seriesList, { yMax, unit = "%", labels = [] } = {}) {
  if (!el) return;
  const w = 560;
  const h = 160;
  const pad = 18;
  const all = seriesList.flatMap((s) => (s.values || []).filter((v) => v != null));
  if (!all.length) {
    el.innerHTML = '<p class="empty">No samples yet — keep Ava running and this fills in.</p>';
    return;
  }
  let max = yMax != null ? yMax : Math.max(...all, 1);
  max = Math.max(max * 1.08, 1);
  const n = Math.max(...seriesList.map((s) => (s.values || []).length), 2);
  const xAt = (i) => pad + (i / Math.max(1, n - 1)) * (w - pad * 2);
  const yAt = (v) => pad + (1 - Number(v) / max) * (h - pad * 2);
  const grid = [0.25, 0.5, 0.75]
    .map((f) => {
      const y = pad + f * (h - pad * 2);
      return `<line x1="${pad}" x2="${w - pad}" y1="${y}" y2="${y}" stroke="rgba(184,255,92,0.08)" />`;
    })
    .join("");
  const layers = seriesList
    .map((s) => {
      const pts = (s.values || [])
        .map((v, i) => (v == null ? null : `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`))
        .filter(Boolean);
      if (pts.length < 2) return "";
      return `<polyline fill="none" stroke="${s.color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" points="${pts.join(" ")}" />`;
    })
    .join("");
  const left = escapeHtml(labels[0] || "");
  const right = escapeHtml(labels[labels.length - 1] || "");
  el.innerHTML =
    `<svg class="plot" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img">${grid}${layers}` +
    `<text x="${pad}" y="${h - 4}" fill="#8aa394" font-size="10">${left}</text>` +
    `<text x="${w - pad}" y="${h - 4}" fill="#8aa394" font-size="10" text-anchor="end">${right}</text>` +
    `<text x="${w - pad}" y="${pad + 2}" fill="#b8ff5c" font-size="10" text-anchor="end">${escapeHtml(String(Math.round(max)))}${escapeHtml(unit)}</text>` +
    `</svg>`;
}

function drawBizHoursBars(el, rows = []) {
  if (!el) return;
  if (!rows.length) {
    el.innerHTML = '<p class="empty">No hours logged yet.</p>';
    return;
  }
  const w = 560;
  const h = 160;
  const pad = 22;
  const max = Math.max(...rows.flatMap((r) => [r.alexH || 0, r.avaH || 0]), 1) * 1.15;
  const slot = (w - pad * 2) / rows.length;
  const bars = rows
    .map((r, i) => {
      const x0 = pad + i * slot;
      const bw = Math.max(4, slot * 0.32);
      const alexH = Number(r.alexH) || 0;
      const avaH = Number(r.avaH) || 0;
      const ah = (alexH / max) * (h - pad * 2);
      const vh = (avaH / max) * (h - pad * 2);
      const yA = h - pad - ah;
      const yV = h - pad - vh;
      const label = escapeHtml(String(r.day || "").slice(5));
      return (
        `<rect x="${(x0 + slot * 0.12).toFixed(1)}" y="${yA.toFixed(1)}" width="${bw.toFixed(1)}" height="${ah.toFixed(1)}" fill="#7dc8ff" rx="2" />` +
        `<rect x="${(x0 + slot * 0.48).toFixed(1)}" y="${yV.toFixed(1)}" width="${bw.toFixed(1)}" height="${vh.toFixed(1)}" fill="#b8ff5c" rx="2" />` +
        `<text x="${(x0 + slot * 0.5).toFixed(1)}" y="${h - 6}" fill="#8aa394" font-size="9" text-anchor="middle">${label}</text>`
      );
    })
    .join("");
  el.innerHTML =
    `<svg class="plot" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img">` +
    `<text x="${pad}" y="${pad}" fill="#7dc8ff" font-size="10">Alex</text>` +
    `<text x="${pad + 40}" y="${pad}" fill="#b8ff5c" font-size="10">Ava</text>` +
    `<text x="${w - pad}" y="${pad}" fill="#b8ff5c" font-size="10" text-anchor="end">${escapeHtml(String(Math.round(max)))}h</text>` +
    `${bars}</svg>`;
}

function renderBiz(data) {
  bizCache = data;
  const meta = $("biz-meta");
  if (meta) {
    const ava = data?.ava || {};
    meta.textContent = [
      data?.hstDay || "",
      ava.online ? `Ava up ${ava.uptimeLabel || ""}` : "Ava down",
      data?.active?.alex?.active ? "Alex clocked in" : "Alex clocked out",
      `CPU ${Number(data?.cpu?.host || 0).toFixed(0)}%`,
    ]
      .filter(Boolean)
      .join(" · ");
  }
  const today = data?.today || {};
  const week = data?.week || {};
  const ava = data?.ava || {};
  const cpu = data?.cpu || {};
  if ($("biz-kpis")) {
    $("biz-kpis").innerHTML = [
      financeKpi("Alex today", today.alexLabel || "0m", data?.active?.alex?.active ? "clocked in" : "clocked out"),
      financeKpi("Ava today", today.avaLabel || "0m", ava.online ? "dev online" : "offline"),
      financeKpi("7d Alex", `${week.alexH ?? 0}h`, "operator"),
      financeKpi("7d Ava", `${week.avaH ?? 0}h`, "uptime = dev"),
    ].join("");
  }
  const projSel = $("biz-project");
  const catSel = $("biz-category");
  if (projSel) {
    const cur = projSel.value || data?.active?.alex?.projectId || "proj-ava";
    projSel.innerHTML = (data?.projects || [])
      .map(
        (p) =>
          `<option value="${escapeHtml(p.id)}"${p.id === cur ? " selected" : ""}>${escapeHtml(p.name)}</option>`,
      )
      .join("");
  }
  if (catSel) {
    const cur = catSel.value || data?.active?.alex?.categoryId || "cat-dev";
    catSel.innerHTML = (data?.categories || [])
      .map(
        (c) =>
          `<option value="${escapeHtml(c.id)}"${c.id === cur ? " selected" : ""}>${escapeHtml(c.name)}</option>`,
      )
      .join("");
  }
  drawBizHoursBars($("biz-hours-chart"), data?.charts?.hours7 || []);
  const series = data?.cpu?.series || [];
  drawBizLineChart(
    $("biz-cpu-chart"),
    [
      { color: "#e8d48a", values: series.map((r) => r.host) },
      { color: "#b8ff5c", values: series.map((r) => r.ava) },
      { color: "#7dc8ff", values: series.map((r) => r.ollama) },
    ],
    {
      unit: "%",
      labels: series.length
        ? [fmtBizWhen(series[0].t), fmtBizWhen(series[series.length - 1].t)]
        : [],
    },
  );
  const procsEl = $("biz-procs");
  if (procsEl) {
    const procs = data?.cpu?.procs || [];
    procsEl.innerHTML = procs.length
      ? procs
          .map(
            (p) =>
              `<div class="term-proc ${escapeHtml(p.kind === "ollama" ? "ollama" : "ava")}">` +
              `<strong>${escapeHtml(p.kind)} · ${Number(p.cpu || 0).toFixed(1)}%</strong>` +
              `<div class="hint">pid ${escapeHtml(String(p.pid))} · ram ${Number(p.mem || 0).toFixed(1)}% · ${escapeHtml(p.etime || "")}<br>${escapeHtml((p.comm || "").slice(0, 48))}</div>` +
              `</div>`,
          )
          .join("")
      : '<p class="hint-inline">No Ava/Ollama processes sampled yet.</p>';
  }
  const entriesEl = $("biz-entries");
  if (entriesEl) {
    const rows = data?.entries || [];
    entriesEl.innerHTML = rows.length
      ? rows
          .slice(0, 24)
          .map((e) => {
            const who = e.personId === "ava" ? "Ava" : "Alex";
            const mins = Math.max(1, Math.round((Number(e.ms) || 0) / 60000));
            return (
              `<div class="biz-entry"><span class="who">${escapeHtml(who)}</span>` +
              `<span class="dur">${mins}m</span>` +
              `<span>${escapeHtml(e.description || e.source || "")}</span>` +
              `<span class="dur">${escapeHtml(fmtBizWhen(e.startAt))}</span></div>`
            );
          })
          .join("")
      : '<p class="hint-inline">No time entries yet. Clock in from here or DM Ava.</p>';
  }
  if ($("biz-clock-in")) $("biz-clock-in").disabled = Boolean(data?.active?.alex?.active);
  if ($("biz-clock-out")) $("biz-clock-out").disabled = !data?.active?.alex?.active;
}

async function refreshBiz() {
  if (!window.avaDesktop?.biz) {
    if ($("biz-status")) $("biz-status").textContent = "Biz IPC unavailable — restart desktop.";
    return;
  }
  if ($("biz-status")) $("biz-status").textContent = "loading…";
  try {
    const data = await window.avaDesktop.biz();
    if (!data?.ok && !data?.today) {
      if ($("biz-status")) $("biz-status").textContent = data?.detail || "biz failed";
      return;
    }
    renderBiz(data);
    if ($("biz-status")) $("biz-status").textContent = `ok · ${data.hstDay || ""} · host ${Number(data.cpu?.host || 0).toFixed(0)}%`;
  } catch (err) {
    if ($("biz-status")) $("biz-status").textContent = err?.message || String(err);
  }
}

async function runBizAction(body) {
  if (bizBusy) return null;
  bizBusy = true;
  if ($("biz-status")) $("biz-status").textContent = "working…";
  try {
    const data = await window.avaDesktop.bizAction(body);
    if (data?.ok || data?.today) renderBiz(data);
    if ($("biz-status")) {
      $("biz-status").textContent = data?.ok
        ? `ok · ${body.action}`
        : data?.detail || "failed";
    }
    return data;
  } catch (err) {
    if ($("biz-status")) $("biz-status").textContent = err?.message || String(err);
    return null;
  } finally {
    bizBusy = false;
  }
}

function ensureBizTimer() {
  if (bizTimer) return;
  bizTimer = setInterval(() => {
    if (document.getElementById("page-biz")?.classList.contains("active")) {
      refreshBiz().catch(() => {});
    }
  }, 45000);
}

/* ——— Finance suite (Stripe + ops ledger) ——— */
let financeBusy = false;
let financeCache = null;

function fmtUsd(n) {
  if (n == null || n === "" || !Number.isFinite(Number(n))) return "—";
  return Number(n).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
  });
}

function fmtAgeMs(ms) {
  if (!Number.isFinite(Number(ms))) return "";
  const m = Math.max(0, Math.round(Number(ms) / 60000));
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 48) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

function financeKpi(label, value, hint) {
  return `<div class="mc-kpi"><label>${escapeHtml(label)}</label><strong>${escapeHtml(value)}</strong>${
    hint ? `<div class="hint">${escapeHtml(hint)}</div>` : ""
  }</div>`;
}

function categoryOptions(selected, extra = []) {
  const cats = [...new Set([...(financeCache?.ops?.expenseCategories || [
    "hosting", "domains", "cloudflare", "software", "hardware", "utilities", "ads", "travel", "ops", "other",
  ]), ...extra, selected].filter(Boolean))];
  return cats
    .map(
      (c) =>
        `<option value="${escapeHtml(c)}"${c === selected ? " selected" : ""}>${escapeHtml(c)}</option>`,
    )
    .join("");
}

function renderFinance(data) {
  financeCache = data;
  const stripe = data?.stripe || {};
  const ops = data?.ops || {};
  const sum = ops.summary || {};
  const wishes = data?.wishlists || {};
  const review = data?.review || {};
  const meta = $("finance-meta");
  const kpis = $("finance-kpis");
  const note = $("finance-stripe-note");
  const projectsHost = $("finance-projects");
  const wishHost = $("finance-wishlists");
  const reviewHost = $("finance-review-list");
  const status = $("finance-status");
  if (!meta || !kpis) return;

  const age = stripe.ageMs != null ? fmtAgeMs(stripe.ageMs) : "";
  const wlSum = wishes.summary || {};
  meta.textContent = [
    stripe.configured ? (stripe.ok ? "Stripe live" : `Stripe ${stripe.reason || "error"}`) : "Stripe not configured",
    age ? `snapshot ${age}` : null,
    `${sum.projectCount || 0} projects · ${sum.accountCount || 0} accounts`,
    `${wlSum.listCount || 0} wishlists`,
    "not player Gold",
  ]
    .filter(Boolean)
    .join(" · ");

  const optimal = data?.optimal || {};
  const optSum = optimal.summary || {};
  const delta = Number(optimal.deltaMonthlyUsd);
  const deltaHint = Number.isFinite(delta)
    ? delta > 0.5
      ? `${fmtUsd(delta)} over budget`
      : delta < -0.5
        ? `${fmtUsd(Math.abs(delta))} under budget`
        : "on target"
    : "";
  const venmo = data?.venmo || {};
  const vy = venmo.ytd || {};
  kpis.innerHTML = [
    financeKpi("Stripe available", fmtUsd(stripe.usdAvailable), stripe.explain?.healthyTiming ? "healthy timing" : age || ""),
    financeKpi("Stripe pending", fmtUsd(stripe.usdPending), stripe.ok ? "in transit" : stripe.reason || ""),
    financeKpi("Stripe 30d income", fmtUsd(stripe.income30dUsd), stripe.fees30dUsd != null ? `fees ${fmtUsd(stripe.fees30dUsd)}` : ""),
    financeKpi("Stripe 30d payouts", fmtUsd(stripe.payouts30dUsd), ""),
    financeKpi("Optimal /mo", fmtUsd(optSum.monthlyUsd), `${optSum.lineCount || 0} budget lines`),
    financeKpi("Actual expense /mo", fmtUsd(sum.expensesMonthlyUsd), `${sum.expenseCount || 0} lines`),
    financeKpi("Actual vs optimal", fmtUsd(Number.isFinite(delta) ? delta : null), deltaHint),
    financeKpi("Ops income /mo", fmtUsd(sum.otherIncomeMonthlyUsd), `${sum.incomeCount || 0} lines`),
    financeKpi("Ops net /mo", fmtUsd(sum.netOtherMonthlyUsd), sum.staleIds?.length ? `${sum.staleIds.length} stale` : ""),
    financeKpi("Wishlist wanted", fmtUsd(wlSum.wantedUsd), `${wlSum.itemCount || 0} items`),
    financeKpi("Profit", fmtUsd(data?.pnl?.totals?.profitUsd), data?.pnl?.plain?.split("\n")?.[0] || "RR full P&L"),
    financeKpi("Revenue", fmtUsd(data?.pnl?.totals?.revenueUsd), `Stripe ${fmtUsd(data?.pnl?.stripe?.rr?.incomeUsd)} + deposits`),
    financeKpi("Costs", fmtUsd(data?.pnl?.totals?.costsUsd), `Ava · Starlink external ${fmtUsd(data?.pnl?.starlink?.accruedUsd)}`),
    financeKpi("~Profit /mo", fmtUsd(data?.pnl?.totals?.runRateMonthly?.profitUsd), `costs ${fmtUsd(data?.pnl?.totals?.runRateMonthly?.costsUsd)}/mo`),
    financeKpi("RR P&L", fmtUsd(vy.pnlUsd), `${venmo.entity || "Root Record"} · from ${venmo.reportingStart || "2026-05-31"}`),
    financeKpi("RR ops P&L", fmtUsd(vy.opsPnlUsd), `net cost ${fmtUsd(vy.opsNetCostUsd)} · ${venmo.reportedTxnCount || 0} txns`),
    financeKpi(
      "RR digital assets",
      fmtUsd(vy.digitalAssetsNetCostUsd ?? vy.digitalAssetsUsd ?? 0),
      `gross ${fmtUsd(vy.digitalAssetsUsd)} − credits ${fmtUsd(vy.digitalAssetsCreditsUsd)}`,
    ),
    financeKpi("RR deposits", fmtUsd(vy.returnsUsd ?? vy.opsReturnsUsd), "Root Record / others → revenue"),
    financeKpi("Context P&L", fmtUsd(venmo.contextYtd?.pnlUsd), `all Venmo · ${venmo.txnCount || 0} txns · cash ${fmtUsd(venmo.endingUsd)}`),
  ].join("");

  const fullNote = $("finance-full-note");
  if (fullNote) {
    fullNote.textContent = data?.pnl?.plain || fullNote.textContent;
  }
  const fullKpis = $("finance-full-kpis");
  if (fullKpis && data?.pnl?.totals) {
    const t = data.pnl.totals;
    const s = data.pnl.stripe || {};
    fullKpis.innerHTML = [
      financeKpi("Stripe available", fmtUsd(s.availableUsd), `pending ${fmtUsd(s.pendingUsd)}`),
      financeKpi("Stripe RR income", fmtUsd(s.rr?.incomeUsd), `${s.rr?.paymentCount || 0} payments · fees ${fmtUsd(s.rr?.feesUsd)}`),
      financeKpi(
        "Paid to Stripe",
        fmtUsd(s.spend?.totalUsd ?? s.rr?.feesUsd),
        `processing ${fmtUsd(s.spend?.processingUsd)} · billing ${fmtUsd(s.spend?.billingUsd)} · tax ${fmtUsd(s.spend?.taxUsd)}`,
      ),
      financeKpi("Starlink external", fmtUsd(data.pnl.starlink?.accruedUsd), `${data.pnl.starlink?.days || 0}d · not in Ava P&L`),
      financeKpi("Venmo ops costs", fmtUsd(data.pnl.venmo?.opsNetCostsUsd ?? data.pnl.venmo?.opsCostsUsd), `surplus ${fmtUsd(data.pnl.venmo?.opsSurplusUsd)} → revenue`),
    ].join("");
  }
  const spendHost = $("finance-stripe-spend");
  if (spendHost) {
    const spend = data?.pnl?.stripe?.spend;
    if (spend?.txns?.length) {
      const rows = spend.txns
        .map(
          (t) => `<tr>
            <td>${escapeHtml(t.date)}</td>
            <td>${escapeHtml(t.kind)}</td>
            <td>${escapeHtml(t.label)}</td>
            <td class="num neg">${escapeHtml(fmtUsd(t.amountUsd))}</td>
          </tr>`,
        )
        .join("");
      spendHost.innerHTML = `<p class="hint-inline">${escapeHtml(spend.note || "Paid to Stripe Inc. on this seller account.")}</p>
        <table class="fin-pnl-table"><thead><tr><th>Date</th><th>Kind</th><th>What</th><th>Amount</th></tr></thead><tbody>${rows}</tbody></table>`;
    } else {
      spendHost.innerHTML = "";
    }
  }
  const fullMonths = $("finance-full-months");
  if (fullMonths) {
    const rows = (data?.pnl?.months || [])
      .map(
        (m) => `<tr>
          <td>${escapeHtml(m.month)}</td>
          <td class="num pos">${escapeHtml(fmtUsd(m.revenueUsd))}</td>
          <td class="num neg">${escapeHtml(fmtUsd(m.costsUsd))}</td>
          <td class="num ${Number(m.profitUsd) >= 0 ? "pos" : "neg"}">${escapeHtml(fmtUsd(m.profitUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.stripeIncomeUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.venmoNetCostsUsd ?? m.venmoCostsUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.starlinkUsd))}</td>
        </tr>`,
      )
      .join("");
    fullMonths.innerHTML = rows
      ? `<table class="fin-pnl-table"><thead><tr><th>Month</th><th>Revenue</th><th>Costs</th><th>Profit</th><th>Stripe</th><th>Venmo</th><th>Starlink</th></tr></thead><tbody>${rows}</tbody></table>`
      : "";
  }
  const incTxnsHost = $("finance-income-txns");
  if (incTxnsHost) {
    const incRows = (data?.pnl?.incomeTxns || [])
      .map(
        (t) => `<tr>
          <td>${escapeHtml(t.date || "")}</td>
          <td class="muted">${escapeHtml(t.source || "")}</td>
          <td>${escapeHtml(t.label || "")}</td>
          <td class="num pos">${escapeHtml(fmtUsd(t.amountUsd))}</td>
        </tr>`,
      )
      .join("");
    incTxnsHost.innerHTML = incRows
      ? `<p class="hint-inline">Every official income txn — Stripe Pro + digital assets (Coinbase) + Venmo deposits.</p><table class="fin-pnl-table"><thead><tr><th>Date</th><th>Source</th><th>What</th><th>Amount</th></tr></thead><tbody>${incRows}</tbody></table>`
      : `<p class="hint-inline">No official income txns yet.</p>`;
  }
  const costTxnsHost = $("finance-cost-txns");
  if (costTxnsHost) {
    const costRows = (data?.pnl?.costTxns || [])
      .map(
        (t) => `<tr>
          <td>${escapeHtml(t.date || "")}</td>
          <td class="muted">${escapeHtml(t.source || "")}</td>
          <td class="muted">${escapeHtml(t.category || "")}</td>
          <td>${escapeHtml(t.label || "")}</td>
          <td class="num neg">${escapeHtml(fmtUsd(t.amountUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(t.runningUsd))}</td>
        </tr>`,
      )
      .join("");
    costTxnsHost.innerHTML = costRows
      ? `<p class="hint-inline">Ava cost txns (Venmo CSV + Stripe fees). Starlink is external.</p><table class="fin-pnl-table"><thead><tr><th>Date</th><th>Source</th><th>Category</th><th>What</th><th>Amount</th><th>Running</th></tr></thead><tbody>${costRows}</tbody></table>`
      : `<p class="hint-inline">No official cost txns yet.</p>`;
  }

  const pnlNote = $("finance-pnl-note");
  if (pnlNote) {
    pnlNote.textContent = venmo.plain || venmo.note || "Deposits (Root Record / others) = revenue. Coinbase = digital assets (income source, not marketing).";
  }
  const pnlKpis = $("finance-pnl-kpis");
  if (pnlKpis) {
    pnlKpis.innerHTML = (venmo.reportedMonths || [])
      .map((m) =>
        financeKpi(
          m.month,
          fmtUsd(m.pnlUsd),
          `ops ${fmtUsd(m.opsPnlUsd)} · digital assets ${fmtUsd(m.digitalAssetsUsd ?? m.marketingUsd)} · ret ${fmtUsd(m.returnsUsd)}`,
        ),
      )
      .join("");
  }
  const pnlMonths = $("finance-pnl-months");
  if (pnlMonths) {
    const rrRows = (venmo.reportedMonths || [])
      .map(
        (m) => `<tr>
          <td>${escapeHtml(m.month)}</td>
          <td class="num">${escapeHtml(fmtUsd(m.costsUsd ?? m.reportedCostsUsd))}</td>
          <td class="num pos">${escapeHtml(fmtUsd(m.returnsUsd ?? m.reportedReturnsUsd))}</td>
          <td class="num ${Number(m.pnlUsd ?? m.reportedPnlUsd) >= 0 ? "pos" : "neg"}">${escapeHtml(fmtUsd(m.pnlUsd ?? m.reportedPnlUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.opsPnlUsd ?? m.reportedOpsPnlUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.digitalAssetsUsd ?? m.reportedDigitalAssetsUsd ?? m.marketingUsd))}</td>
        </tr>`,
      )
      .join("");
    const ctxRows = (venmo.months || [])
      .map(
        (m) => `<tr>
          <td>${escapeHtml(m.month)}${m.reportedTxnCount ? "" : " <span class=\"muted\">context</span>"}</td>
          <td class="num">${escapeHtml(fmtUsd(m.costsUsd))}</td>
          <td class="num pos">${escapeHtml(fmtUsd(m.returnsUsd))}</td>
          <td class="num ${Number(m.pnlUsd) >= 0 ? "pos" : "neg"}">${escapeHtml(fmtUsd(m.pnlUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.opsPnlUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.digitalAssetsUsd ?? m.marketingUsd))}</td>
          <td class="num">${escapeHtml(fmtUsd(m.personalUsd))}</td>
        </tr>`,
      )
      .join("");
    pnlMonths.innerHTML =
      (rrRows
        ? `<p class="hint-inline">Official RR months (from ${escapeHtml(venmo.reportingStart || "2026-05-31")})</p><table class="fin-pnl-table"><thead><tr><th>Month</th><th>Costs</th><th>Returns</th><th>P&amp;L</th><th>Ops P&amp;L</th><th>Digital assets</th></tr></thead><tbody>${rrRows}</tbody></table>`
        : "") +
      (ctxRows
        ? `<p class="hint-inline">Full Venmo context (pre-start kept)</p><table class="fin-pnl-table"><thead><tr><th>Month</th><th>Costs</th><th>Returns</th><th>P&amp;L</th><th>Ops P&amp;L</th><th>Digital assets</th><th>Personal</th></tr></thead><tbody>${ctxRows}</tbody></table>`
        : `<p class="hint-inline">No Venmo statements imported yet.</p>`);
  }
  const pnlTxns = $("finance-pnl-txns");
  if (pnlTxns) {
    const cats = venmo.categories || ["digital-assets", "marketing", "domains", "software", "personal", "return", "ops"];
    const txnRows = (venmo.txns || [])
      .map((t) => {
        const amt = Number(t.amountUsd) || 0;
        const opts = cats
          .map(
            (c) =>
              `<option value="${escapeHtml(c)}"${c === t.category ? " selected" : ""}>${escapeHtml(c)}</option>`,
          )
          .join("");
        return `<tr>
          <td>${escapeHtml(t.date || "")}</td>
          <td class="muted">${t.rrReporting ? "RR" : "ctx"}</td>
          <td>${escapeHtml(t.label || t.to || "")}</td>
          <td><select data-venmo-id="${escapeHtml(t.id)}" class="fin-venmo-cat">${opts}</select></td>
          <td class="num ${amt >= 0 ? "pos" : "neg"}">${escapeHtml(fmtUsd(amt))}</td>
          <td class="num">${escapeHtml(fmtUsd(t.rrReporting ? t.runningRrPnlUsd : t.runningPnlUsd))}</td>
        </tr>`;
      })
      .join("");
    pnlTxns.innerHTML = txnRows
      ? `<table class="fin-pnl-table"><thead><tr><th>Date</th><th></th><th>Merchant</th><th>Category</th><th>Amount</th><th>Running P&amp;L</th></tr></thead><tbody>${txnRows}</tbody></table>`
      : "";
  }

  const expl = stripe.explain;
  const explBits = [];
  if (stripe.plain) explBits.push(stripe.plain);
  if (expl?.healthyTiming) explBits.push("Penny-level negative + pending cover — not an incident.");
  else if (expl?.pendingCoversDeficit) explBits.push("Pending covers available deficit (fee/payout timing).");
  else if (expl && expl.avail < 0) explBits.push("Available is negative and pending does not cover it — check payouts/disputes.");
  note.textContent = explBits.join(" · ");

  const dl = $("fin-project-list");
  if (dl) {
    dl.innerHTML = (ops.projects || [])
      .map((p) => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name || p.id)}</option>`)
      .join("");
  }
  const catSel = $("fin-category");
  if (catSel && !(catSel.dataset.ready === "1")) {
    catSel.innerHTML = categoryOptions(catSel.value || "hosting");
    catSel.dataset.ready = "1";
  }

  const optNote = $("finance-optimal-note");
  if (optNote) {
    optNote.textContent = optimal.note || "Target spend for development + resources — not invoices.";
  }
  const optHost = $("finance-optimal");
  if (optHost) {
    optHost.innerHTML = "";
    for (const line of optimal.lines || []) {
      const row = document.createElement("div");
      row.className = "fin-line fin-optimal";
      const mo =
        line.period === "year"
          ? (Number(line.amountUsd) || 0) / 12
          : line.period === "week"
            ? ((Number(line.amountUsd) || 0) * 52) / 12
            : Number(line.amountUsd) || 0;
      row.innerHTML = `
        <form class="fin-opt-edit" data-id="${escapeHtml(line.id)}">
          <input name="label" type="text" value="${escapeHtml(line.label || "")}" />
          <input name="amount" type="number" step="0.01" min="0" value="${Number(line.amountUsd) || 0}" />
          <select name="period">
            ${["month", "year", "week"]
              .map(
                (p) =>
                  `<option value="${p}"${line.period === p ? " selected" : ""}>/${p}</option>`,
              )
              .join("")}
          </select>
          <select name="category">${categoryOptions(line.category || "ops")}</select>
          <input name="note" type="text" value="${escapeHtml(line.note || "")}" placeholder="Note" />
          <span class="hint-inline">~${escapeHtml(fmtUsd(mo))}/mo</span>
          <button type="submit">Save</button>
          <button type="button" class="danger-inline fin-opt-del">Delete</button>
        </form>
      `;
      optHost.appendChild(row);
    }
  }

  if (wishHost) {
    wishHost.innerHTML = "";
    for (const wl of wishes.lists || []) {
      const card = document.createElement("article");
      card.className = "fin-project fin-wishlist";
      card.innerHTML = `
        <div class="fin-project-head">
          <div>
            <h4>${escapeHtml(wl.name || wl.id)}</h4>
            <p class="hint-inline">${escapeHtml(wl.note || wl.id)}</p>
          </div>
          <button type="button" class="danger-inline fin-wl-del" data-id="${escapeHtml(wl.id)}">Delete list</button>
        </div>
        <div class="fin-wl-items"></div>
        <form class="fin-form fin-wl-item-form" data-id="${escapeHtml(wl.id)}">
          <input name="label" type="text" placeholder="Item name" required />
          <input name="url" type="url" placeholder="https://… item URL" required />
          <input name="price" type="number" step="0.01" min="0" placeholder="Price USD" required />
          <button type="submit" class="primary">Add item</button>
        </form>
      `;
      const itemsHost = card.querySelector(".fin-wl-items");
      for (const it of wl.items || []) {
        const row = document.createElement("div");
        row.className = "fin-line fin-wl-row";
        row.innerHTML = `
          <form class="fin-wl-edit" data-list="${escapeHtml(wl.id)}" data-item="${escapeHtml(it.id)}">
            <input name="label" type="text" value="${escapeHtml(it.label || "")}" />
            <input name="url" type="url" value="${escapeHtml(it.url || "")}" placeholder="URL" />
            <input name="price" type="number" step="0.01" min="0" value="${Number(it.priceUsd) || 0}" />
            <select name="status">
              ${["wanted", "bought", "dropped"]
                .map(
                  (s) =>
                    `<option value="${s}"${it.status === s ? " selected" : ""}>${s}</option>`,
                )
                .join("")}
            </select>
            <button type="submit">Save</button>
            <button type="button" class="danger-inline fin-wl-item-del">Delete</button>
            ${
              it.url
                ? `<a class="fin-link" href="${escapeHtml(it.url)}" target="_blank" rel="noreferrer">Open</a>`
                : ""
            }
          </form>
        `;
        itemsHost.appendChild(row);
      }
      wishHost.appendChild(card);
    }
    if (!(wishes.lists || []).length) {
      wishHost.innerHTML = `<p class="hint-inline">No wishlists yet — add Hardware or any named list, then paste item URLs like prices.</p>`;
    }
  }

  projectsHost.innerHTML = "";
  for (const proj of ops.projects || []) {
    const card = document.createElement("article");
    card.className = "fin-project";
    const head = document.createElement("div");
    head.className = "fin-project-head";
    head.innerHTML = `<div><h4>${escapeHtml(proj.name || proj.id)}</h4><p class="hint-inline">${escapeHtml(proj.note || proj.id)}</p></div>`;
    card.appendChild(head);

    for (const acct of proj.accounts || []) {
      const box = document.createElement("div");
      box.className = "fin-account";
      const balInputId = `fin-bal-${proj.id}-${acct.id}`;
      box.innerHTML = `
        <div class="fin-account-head">
          <div>
            <strong>${escapeHtml(acct.name || acct.id)}</strong>
            <span class="fin-kind-pill">${escapeHtml(acct.kind || "cash")}</span>
            <div class="hint-inline">${escapeHtml(acct.note || "")}</div>
          </div>
          <form class="fin-balance-form" data-project="${escapeHtml(proj.id)}" data-account="${escapeHtml(acct.id)}">
            <label>Balance
              <input type="number" step="0.01" value="${Number(acct.balanceUsd) || 0}" id="${escapeHtml(balInputId)}" />
            </label>
            <button type="submit">Set</button>
          </form>
        </div>
        <div class="fin-lines" data-kind-host></div>
      `;
      const linesHost = box.querySelector("[data-kind-host]");
      const groups = [
        ["income", acct.income || []],
        ["expense", acct.expenses || []],
        ["debt", acct.debts || []],
      ];
      for (const [kind, rows] of groups) {
        if (!rows.length) continue;
        const wrap = document.createElement("div");
        wrap.className = "fin-line-group";
        wrap.innerHTML = `<h5>${escapeHtml(kind)}</h5>`;
        for (const row of rows) {
          const amt = kind === "debt" ? row.balanceUsd : row.amountUsd;
          const line = document.createElement("div");
          line.className = kind === "expense" ? "fin-line fin-expense" : "fin-line";
          if (kind === "expense") {
            const recs = row.receipts || [];
            line.innerHTML = `
              <form class="fin-exp-form" data-project="${escapeHtml(proj.id)}" data-account="${escapeHtml(acct.id)}" data-line="${escapeHtml(row.id)}">
                <input name="label" type="text" value="${escapeHtml(row.label || "")}" />
                <input name="amount" type="number" step="0.01" min="0" value="${Number(amt) || 0}" />
                <select name="period">
                  ${["month", "year", "week", "once"]
                    .map(
                      (p) =>
                        `<option value="${p}"${(row.period || "month") === p ? " selected" : ""}>${p}</option>`,
                    )
                    .join("")}
                </select>
                <select name="category">${categoryOptions(row.category || "ops")}</select>
                <input name="note" type="text" value="${escapeHtml(row.note || "")}" placeholder="Note" />
                <button type="submit">Save</button>
                <button type="button" class="fin-rcpt">Receipt</button>
                <button type="button" class="danger-inline fin-del">Delete</button>
              </form>
              <div class="fin-receipts">${
                recs.length
                  ? recs
                      .map(
                        (r) =>
                          `<span class="fin-rcpt-chip"><button type="button" class="fin-rcpt-open" data-abs="${escapeHtml(
                            r.abs || "",
                          )}" data-id="${escapeHtml(r.id)}">${escapeHtml(r.name || r.id)}</button><button type="button" class="danger-inline fin-rcpt-del" data-id="${escapeHtml(
                            r.id,
                          )}">×</button></span>`,
                      )
                      .join("")
                  : `<span class="muted">no receipt</span>`
              }</div>
              ${
                row.paidThrough || row.expires || (row.invoices || []).length
                  ? `<div class="hint-inline">${[
                      row.paidThrough ? `paid through ${escapeHtml(row.paidThrough)}` : "",
                      row.expires ? `expires ${escapeHtml(row.expires)}` : "",
                      (row.invoices || [])
                        .map((i) => `${escapeHtml(i.id)} $${Number(i.amountUsd).toFixed(2)}`)
                        .join(" · "),
                    ]
                      .filter(Boolean)
                      .join(" · ")}</div>`
                  : ""
              }
            `;
          } else {
            line.innerHTML = `
              <div>
                <div class="id">${escapeHtml(row.label || row.id)}</div>
                <div class="muted">${escapeHtml(row.period || (kind === "debt" ? "once" : "month"))}${
                  row.note ? ` · ${escapeHtml(row.note)}` : ""
                }${row.updatedAt ? ` · ${escapeHtml(fmtHst(row.updatedAt))}` : " · never set"}</div>
              </div>
              <form class="fin-line-form" data-project="${escapeHtml(proj.id)}" data-account="${escapeHtml(acct.id)}" data-kind="${escapeHtml(kind)}" data-line="${escapeHtml(row.id)}">
                <input type="number" step="0.01" min="0" value="${Number(amt) || 0}" />
                <button type="submit">Save</button>
                <button type="button" class="danger-inline fin-del">Delete</button>
              </form>
            `;
          }
          wrap.appendChild(line);
        }
        linesHost.appendChild(wrap);
      }
      card.appendChild(box);
    }
    projectsHost.appendChild(card);
  }

  reviewHost.innerHTML = "";
  const suggestions = review.suggestions || [];
  if (!suggestions.length) {
    reviewHost.innerHTML = `<p class="hint-inline">No suggestions${
      review.lastRunAt ? ` · last review ${escapeHtml(fmtHst(review.lastRunAt))}` : ""
    }.</p>`;
  } else {
    if (review.lastRunAt) {
      const p = document.createElement("p");
      p.className = "hint-inline";
      p.textContent = `Last review ${fmtHst(review.lastRunAt)}`;
      reviewHost.appendChild(p);
    }
    for (const s of suggestions) {
      const row = document.createElement("div");
      row.className = `fin-suggest ${escapeHtml(s.severity || "info")}`;
      row.innerHTML = `<span class="report-pill ${escapeHtml(s.severity || "info")}">${escapeHtml(
        s.severity || "info",
      )}</span> <code>${escapeHtml(s.code || "")}</code> ${escapeHtml(s.text || "")}`;
      reviewHost.appendChild(row);
    }
  }

  if (status && data?.ok !== false) status.textContent = "";

  projectsHost.querySelectorAll(".fin-balance-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = form.querySelector("input");
      await runFinanceAction({
        action: "set-balance",
        projectId: form.dataset.project,
        account: form.dataset.account,
        balanceUsd: Number(input?.value),
      });
    });
  });
  projectsHost.querySelectorAll(".fin-line-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = form.querySelector("input");
      await runFinanceAction({
        action: "update-line",
        projectId: form.dataset.project,
        account: form.dataset.account,
        kind: form.dataset.kind,
        lineId: form.dataset.line,
        amountUsd: Number(input?.value),
      });
    });
    form.querySelector(".fin-del")?.addEventListener("click", async () => {
      if (!confirm("Delete this ledger line?")) return;
      await runFinanceAction({
        action: "delete-line",
        projectId: form.dataset.project,
        account: form.dataset.account,
        kind: form.dataset.kind,
        lineId: form.dataset.line,
      });
    });
  });
  projectsHost.querySelectorAll(".fin-exp-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await runFinanceAction({
        action: "update-line",
        projectId: form.dataset.project,
        account: form.dataset.account,
        kind: "expense",
        lineId: form.dataset.line,
        label: form.label.value,
        amountUsd: Number(form.amount.value),
        period: form.period.value,
        category: form.category.value,
        note: form.note.value,
      });
    });
    form.querySelector(".fin-del")?.addEventListener("click", async () => {
      if (!confirm("Delete this expense?")) return;
      await runFinanceAction({
        action: "delete-line",
        projectId: form.dataset.project,
        account: form.dataset.account,
        kind: "expense",
        lineId: form.dataset.line,
      });
    });
    form.querySelector(".fin-rcpt")?.addEventListener("click", async () => {
      const r = await window.avaDesktop.financeReceipt({
        projectId: form.dataset.project,
        account: form.dataset.account,
        lineId: form.dataset.line,
      });
      if (r?.canceled) return;
      if (!r?.ok && !r?.stripe) {
        if ($("finance-status")) $("finance-status").textContent = r?.detail || "receipt failed";
        return;
      }
      renderFinance(r);
    });
    const wrap = form.parentElement;
    wrap?.querySelectorAll(".fin-rcpt-open").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.dataset.abs) window.avaDesktop.openPath(btn.dataset.abs);
      });
    });
    wrap?.querySelectorAll(".fin-rcpt-del").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Remove this receipt?")) return;
        await runFinanceAction({
          action: "delete-receipt",
          projectId: form.dataset.project,
          account: form.dataset.account,
          lineId: form.dataset.line,
          receiptId: btn.dataset.id,
        });
      });
    });
  });

  wishHost?.querySelectorAll(".fin-wl-del").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this wishlist?")) return;
      await runFinanceAction({ action: "delete-wishlist", wishlistId: btn.dataset.id });
    });
  });
  wishHost?.querySelectorAll(".fin-wl-item-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await runFinanceAction({
        action: "add-wishlist-item",
        wishlistId: form.dataset.id,
        label: form.label.value.trim(),
        url: form.url.value.trim(),
        priceUsd: Number(form.price.value),
      });
    });
  });
  wishHost?.querySelectorAll(".fin-wl-edit").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await runFinanceAction({
        action: "update-wishlist-item",
        wishlistId: form.dataset.list,
        itemId: form.dataset.item,
        label: form.label.value.trim(),
        url: form.url.value.trim(),
        priceUsd: Number(form.price.value),
        status: form.status.value,
      });
    });
    form.querySelector(".fin-wl-item-del")?.addEventListener("click", async () => {
      if (!confirm("Delete this wishlist item?")) return;
      await runFinanceAction({
        action: "delete-wishlist-item",
        wishlistId: form.dataset.list,
        itemId: form.dataset.item,
      });
    });
  });
}

async function refreshFinance({ refreshStripe = false } = {}) {
  const meta = $("finance-meta");
  const status = $("finance-status");
  if (!meta) return;
  if (financeBusy) return;
  financeBusy = true;
  meta.textContent = refreshStripe ? "Refreshing Stripe…" : "Loading finance…";
  try {
    const data = await window.avaDesktop.finance({ refresh: refreshStripe });
    if (!data?.ok && !data?.stripe && !data?.ops) {
      meta.textContent = data?.detail || "finance API unavailable — is Ava brain up?";
      if (status) status.textContent = JSON.stringify(data, null, 2);
      return;
    }
    renderFinance(data);
  } catch (err) {
    meta.textContent = String(err.message || err);
    if (status) status.textContent = `Brain must be up on ${lastBrainUrl || "the selected connection"}`;
  } finally {
    financeBusy = false;
  }
}

async function runFinanceAction(body) {
  const status = $("finance-status");
  if (financeBusy) return;
  financeBusy = true;
  if (status) status.textContent = `${body.action || "action"}…`;
  try {
    const data = await window.avaDesktop.financeAction(body);
    if (!data?.ok && !data?.stripe) {
      if (status) status.textContent = data?.detail || JSON.stringify(data, null, 2);
      return;
    }
    renderFinance(data);
    if (status) {
      status.textContent = data.lastReview
        ? `review ${data.lastReview.reason || "ok"} · sent ${data.lastReview.sent ? "yes" : "no"} · ${(data.lastReview.suggestions || []).length} suggestions`
        : "";
    }
  } catch (err) {
    if (status) status.textContent = String(err.message || err);
  } finally {
    financeBusy = false;
  }
}

/* ——— Terminal (live Ava + Ollama, plus ops commands) ——— */
let opsBusy = false;
let termTimer = null;
let termLiveText = "";
let termOpsOverlay = [];
const confirmHints = new Map();

function terminalAppend(line) {
  termOpsOverlay.push(String(line));
  if (termOpsOverlay.length > 80) termOpsOverlay = termOpsOverlay.slice(-80);
  renderTerminalLog();
}

function renderTerminalLog() {
  const el = $("terminal-out");
  if (!el) return;
  const follow = $("terminal-follow")?.checked !== false;
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  const extra = termOpsOverlay.length ? `\n${termOpsOverlay.join("\n")}` : "";
  const next = `${termLiveText || "(no activity yet)"}${extra}`;
  if (el.textContent !== next) {
    el.textContent = next;
    if (follow || atBottom) el.scrollTop = el.scrollHeight;
  }
}

function setOpsBusy(busy, label = "idle") {
  opsBusy = busy;
  const run = $("terminal-run-label");
  if (!busy) {
    /* live poller will set label */
  } else if (run) {
    run.textContent = label;
    run.classList.toggle("busy", true);
    run.classList.toggle("idle", false);
  }
  $("terminal-commands")
    ?.querySelectorAll(".cmd-btn")
    .forEach((btn) => {
      btn.disabled = busy;
    });
  if ($("terminal-cancel")) $("terminal-cancel").disabled = !busy;
}

function termProcLabel(p) {
  const comm = String(p.comm || "proc").replace(/\.exe$/i, "");
  const args = String(p.args || "");
  if (/uvicorn|apps\.core\.main/i.test(args)) return `origin · ${p.pid}`;
  if (/ollama/i.test(comm) && /serve/i.test(args)) return `ollama serve · ${p.pid}`;
  if (/ollama app/i.test(comm) || /ollama app/i.test(args)) return `ollama app · ${p.pid}`;
  return `${comm} · ${p.pid}`;
}

function renderTerminalCpuBars(snap) {
  const host = $("terminal-cpu");
  if (!host) return;
  const procs = Array.isArray(snap?.processes) ? snap.processes : [];
  const shown = [];
  let other = 0;
  let otherN = 0;
  for (const p of procs) {
    const cpu = Number(p.cpu) || 0;
    if (cpu >= 1) shown.push(p);
    else {
      other += cpu;
      otherN += 1;
    }
  }
  shown.sort((a, b) => (Number(b.cpu) || 0) - (Number(a.cpu) || 0));
  const rows = shown.map((p) => {
    const cpu = Number(p.cpu) || 0;
    const kind = p.kind === "ollama" ? "ollama" : "ava";
    const width = Math.max(0, Math.min(100, cpu));
    return (
      `<div class="term-cpu-row ${kind}" title="${escapeHtml(String(p.args || ""))}">` +
      `<div class="term-cpu-meta"><span class="term-cpu-name">${escapeHtml(termProcLabel(p))}</span>` +
      `<span class="term-cpu-pct">${cpu.toFixed(1)}%</span></div>` +
      `<div class="term-cpu-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${cpu.toFixed(1)}">` +
      `<div class="term-cpu-fill" style="width:${width}%"></div></div></div>`
    );
  });
  if (otherN && other >= 1) {
    const width = Math.max(0, Math.min(100, other));
    rows.push(
      `<div class="term-cpu-row other">` +
        `<div class="term-cpu-meta"><span class="term-cpu-name">Other · ${otherN}</span>` +
        `<span class="term-cpu-pct">${other.toFixed(1)}%</span></div>` +
        `<div class="term-cpu-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${other.toFixed(1)}">` +
        `<div class="term-cpu-fill" style="width:${width}%"></div></div></div>`,
    );
  }
  host.innerHTML = rows.join("");
}

function renderTerminalProcs(snap) {
  const host = $("terminal-procs");
  if (!host) return;
  const cards = [];
  const ol = snap?.ollama || {};
  cards.push({
    kind: ol.up ? "ollama" : "ava",
    title: ol.up ? "Ollama up" : "Ollama down",
    hint: [ol.model, ol.baseUrl?.replace(/^https?:\/\//, "")].filter(Boolean).join(" · "),
  });
  for (const m of ol.ps || []) {
    cards.push({
      kind: "ollama",
      title: String(m.name || "model").replace(/:latest$/, ""),
      hint: m.expiresAt ? `loaded · exp ${String(m.expiresAt).slice(11, 19)}` : "loaded",
    });
  }
  for (const w of snap?.inflight || []) {
    cards.push({
      kind: "ollama",
      title: w.kind || "ollama call",
      hint: `${Math.round((w.ms || 0) / 1000)}s${w.model ? ` · ${w.model}` : ""}`,
    });
  }
  for (const id of snap?.runningCrons || []) {
    cards.push({ kind: "cron", title: `cron · ${id}`, hint: "running now" });
  }
  if (!cards.length) {
    host.innerHTML = `<div class="term-proc"><strong>No live processes</strong><div class="hint">Waiting for Ava / Ollama</div></div>`;
  } else {
    host.innerHTML = cards
      .slice(0, 18)
      .map(
        (c) =>
          `<div class="term-proc ${escapeHtml(c.kind)}"><strong>${escapeHtml(c.title)}</strong><div class="hint">${escapeHtml(c.hint || "")}</div></div>`,
      )
      .join("");
  }
  renderTerminalCpuBars(snap);
}

async function refreshTerminalLive() {
  if (!window.avaDesktop?.activity) return;
  try {
    const snap = await window.avaDesktop.activity({ limit: 220 });
    renderTerminalProcs(snap?.ok ? snap : {});
    const run = $("terminal-run-label");
    if (run && !opsBusy) {
      const label = snap?.label || (snap?.ok ? "idle" : snap?.detail || "brain offline");
      run.textContent = label;
      const busy = Boolean(snap?.ollamaBusy || (snap?.inflight || []).length || (snap?.runningCrons || []).length);
      run.classList.toggle("busy", busy);
      run.classList.toggle("idle", !busy);
    }
    const meta = $("terminal-log-meta");
    if (meta) {
      meta.textContent = [
        snap?.logs?.length ? `${snap.logs.length} lines` : "",
        snap?.heartbeat?.pid ? `ava pid ${snap.heartbeat.pid}` : "",
        snap?.ollama?.up ? "ollama" : "ollama down",
      ]
        .filter(Boolean)
        .join(" · ");
    }
    if (Array.isArray(snap?.logs)) {
      termLiveText = snap.logs.join("\n");
    } else if (!snap?.ok) {
      termLiveText = `! ${snap?.detail || "activity unavailable"}`;
    }
    renderTerminalLog();
  } catch (err) {
    termLiveText = `! ${err?.message || err}`;
    renderTerminalLog();
  }
}

async function runOpsCommand(id) {
  if (opsBusy) return;
  const hint = confirmHints.get(id);
  if (hint && !window.confirm(hint)) return;
  setOpsBusy(true, `running · ${id}`);
  try {
    const r = await window.avaDesktop.opsRun(id);
    if (!r?.ok && r?.detail) terminalAppend(`! ${r.detail}`);
  } catch (err) {
    terminalAppend(`! ${err?.message || err}`);
    setOpsBusy(false, "idle");
    refreshTerminalLive().catch(() => {});
  }
}

async function bootTerminal() {
  const catalog = await window.avaDesktop.opsCatalog();
  const host = $("terminal-commands");
  host.innerHTML = "";
  confirmHints.clear();
  for (const group of catalog.groups || []) {
    const section = document.createElement("section");
    section.className = "cmd-group";
    section.dataset.groupId = group.id;

    // Header row: label + count
    const header = document.createElement("div");
    header.className = "cmd-group-header";
    const h2 = document.createElement("h2");
    h2.textContent = group.label;
    const count = document.createElement("span");
    count.className = "cmd-group-count";
    count.textContent = `${(group.commands || []).length}`;
    header.appendChild(h2);
    header.appendChild(count);
    section.appendChild(header);

    const grid = document.createElement("div");
    grid.className = "cmd-grid";
    for (const cmd of group.commands || []) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cmd-btn";
      if (group.id === "danger") btn.classList.add("danger");
      else if (cmd.confirm) btn.classList.add("warn");
      btn.dataset.id = cmd.id;
      btn.dataset.search = `${cmd.label} ${cmd.detail} ${cmd.id} ${group.label}`.toLowerCase();
      btn.innerHTML = `<span class="cmd-label">${escapeHtml(cmd.label)}</span><span class="cmd-detail">${escapeHtml(cmd.detail || "")}</span>`;
      if (cmd.confirm) confirmHints.set(cmd.id, String(cmd.confirm));
      btn.addEventListener("click", () => runOpsCommand(cmd.id));
      grid.appendChild(btn);
    }
    section.appendChild(grid);
    host.appendChild(section);
  }
  window.avaDesktop.onOpsStart((p) => {
    setOpsBusy(true, p?.label || p?.id || "running");
    if (p?.detail) terminalAppend(`# ${p.detail}`);
  });
  window.avaDesktop.onOpsLine((p) => {
    if (p?.line != null) terminalAppend(p.line);
  });
  window.avaDesktop.onOpsDone((p) => {
    setOpsBusy(false, "idle");
    terminalAppend(p?.code ? `# failed (${p.code})` : "# done");
    refreshTerminalLive().catch(() => {});
  });
  $("terminal-clear").onclick = () => {
    termOpsOverlay = [];
    $("terminal-out").textContent = termLiveText || "";
  };
  $("terminal-cancel").onclick = async () => {
    const r = await window.avaDesktop.opsCancel();
    terminalAppend(r?.ok ? "# cancel signaled" : `# cancel failed`);
  };
  if ($("terminal-refresh")) {
    $("terminal-refresh").onclick = () => refreshTerminalLive().catch(() => {});
  }
  $("terminal-cancel").disabled = true;
  $("terminal-filter").oninput = () => {
    const q = $("terminal-filter").value.trim().toLowerCase();
    host.querySelectorAll(".cmd-group").forEach((group) => {
      let any = false;
      group.querySelectorAll(".cmd-btn").forEach((btn) => {
        const show = !q || (btn.dataset.search || "").includes(q);
        btn.classList.toggle("hidden", !show);
        if (show) any = true;
      });
      group.classList.toggle("hidden", q ? !any : false);
    });
  };
  await refreshTerminalLive();
  if (termTimer) clearInterval(termTimer);
  termTimer = setInterval(() => {
    if ($("page-terminal")?.classList.contains("active")) {
      refreshTerminalLive().catch(() => {});
    }
  }, 8000);
}

let mcBusy = false;
let mcLastSize = -1;
let mcTimer = null;

function mcSetMsg(text, err) {
  const el = $("mc-msg");
  if (!el) return;
  el.textContent = text || "";
  el.style.color = err ? "#fecaca" : "";
}

function renderMcStatus(s) {
  const run = !!(s?.running || s?.test?.online);
  const pill = $("mc-pill");
  if (pill) {
    pill.textContent = run ? "Running" : "Stopped";
    pill.className = "mc-pill " + (run ? "ok" : "bad");
  }
  const kpis = $("mc-kpis");
  if (kpis) {
    const rows = [
      ["State", run ? "UP" : "DOWN", (s.pids || []).join(", ") || "no pid"],
      ["Join", s.serverPort ? `:${s.serverPort}` : "—", String(s.motd || "").replace(/§./g, "").slice(0, 42) || "motd"],
      ["RCON", s.rconPort || "—", (s.rconTargets || []).map((t) => `${t.id}:${t.port}`).join(" · ") || ""],
      ["Plugins", String(s.plugins ?? "—"), s.jar || "jar"],
    ];
    kpis.innerHTML = rows
      .map(
        ([label, strong, hint]) =>
          `<div class="mc-kpi"><label>${escapeHtml(label)}</label><strong>${escapeHtml(strong)}</strong><div class="hint">${escapeHtml(hint)}</div></div>`,
      )
      .join("");
  }
  const meta = $("mc-console-meta");
  if (meta) {
    meta.textContent = [s.logFile, s.logBytes != null ? `${s.logBytes} bytes` : ""]
      .filter(Boolean)
      .join(" · ");
  }
  if ($("mc-start")) $("mc-start").disabled = run || mcBusy;
  if ($("mc-stop")) $("mc-stop").disabled = !run || mcBusy;
  if ($("mc-restart")) $("mc-restart").disabled = mcBusy;
}

async function refreshMinecraftLog() {
  const j = await window.avaDesktop.mcLog({ lines: 220, bytes: 200000 });
  const consoleEl = $("mc-console");
  if (!consoleEl) return;
  const follow = $("mc-follow")?.checked;
  const atBottom =
    consoleEl.scrollHeight - consoleEl.scrollTop - consoleEl.clientHeight < 80;
  if (j.size !== mcLastSize || consoleEl.textContent !== (j.text || (j.lines || []).join("\n") || "")) {
    consoleEl.textContent = j.text || (Array.isArray(j.lines) ? j.lines.join("\n") : "") || "(empty log)";
    mcLastSize = j.size;
    if (follow || atBottom) consoleEl.scrollTop = consoleEl.scrollHeight;
  }
}

async function refreshMinecraft() {
  try {
    const s = await window.avaDesktop.mcStatus();
    renderMcStatus(s);
    await refreshMinecraftLog();
  } catch (err) {
    mcSetMsg(String(err?.message || err), true);
  }
}

async function mcControl(action) {
  if (mcBusy) return;
  mcBusy = true;
  mcSetMsg(`${action}…`);
  try {
    const j = await window.avaDesktop.mcControl(action);
    if (j?.ok === false) throw new Error(j.detail || j.message || "control failed");
    mcSetMsg(j.message || `${action} ok`);
    await refreshMinecraft();
  } catch (err) {
    mcSetMsg(String(err?.message || err), true);
  } finally {
    mcBusy = false;
    refreshMinecraft().catch(() => {});
  }
}

async function bootMinecraft() {
  if (!$("page-minecraft")) return;
  $("mc-start").onclick = () => mcControl("start");
  $("mc-restart").onclick = () => mcControl("restart");
  $("mc-stop").onclick = () => mcControl("stop");
  $("mc-refresh").onclick = () => refreshMinecraft();
  $("mc-console-clear").onclick = () => {
    $("mc-console").textContent = "";
    mcLastSize = -1;
  };
  $("mc-rcon-form").onsubmit = async (ev) => {
    ev.preventDefault();
    const cmd = $("mc-rcon-cmd").value.trim();
    if (!cmd) return;
    mcSetMsg(`rcon › ${cmd}`);
    try {
      const j = await window.avaDesktop.mcRcon({ command: cmd, target: "test" });
      const out = j.ok ? j.output || "(ok)" : `ERR ${j.reason || j.detail || "failed"}`;
      const consoleEl = $("mc-console");
      consoleEl.textContent = `${consoleEl.textContent || ""}\n> ${cmd}\n${out}\n`;
      consoleEl.scrollTop = consoleEl.scrollHeight;
      if (!j.ok) mcSetMsg(j.reason || j.detail || "rcon failed", true);
      else {
        mcSetMsg("rcon ok");
        $("mc-rcon-cmd").value = "";
      }
    } catch (err) {
      mcSetMsg(String(err?.message || err), true);
    }
  };
  await refreshMinecraft();
  if (mcTimer) clearInterval(mcTimer);
  mcTimer = setInterval(() => {
    if ($("page-minecraft")?.classList.contains("active")) {
      refreshMinecraft().catch(() => {});
    }
  }, 2500);
}

function streamSetMsg(text, isErr = false) {
  const el = $("stream-msg");
  if (!el) return;
  el.textContent = text || "";
  el.style.color = isErr ? "var(--danger, #ff6b6b)" : "";
}

function streamMetaBody() {
  return {
    title: $("stream-title")?.value || "",
    description: $("stream-description")?.value || "",
  };
}

async function refreshStreamOps() {
  if (!$("page-stream") || !window.avaDesktop?.streamStatus) return;
  try {
    const pack = await window.avaDesktop.streamStatus();
    const st = pack.status || {};
    const watch = pack.watch || {};
    const eta = pack.eta || {};
    if (pack.detail && st.ok === false) {
      streamSetMsg(pack.detail, true);
    } else {
      streamSetMsg(
        st.streaming
          ? `Live · scene ${st.scene || "?"} · kit ${st.kit?.health || "?"}`
          : `Idle · scene ${st.scene || "?"} · kit ${st.kit?.health || "?"}`,
      );
    }
    const mode = st.mode || pack.mode || "daily";
    const modeLabel =
      mode === "hurricane"
        ? "MODE HURRICANE"
        : mode === "kilauea"
          ? "MODE KILAUEA"
          : mode === "all"
            ? "MODE ALL SCENES"
          : mode === "weather"
            ? "MODE WEATHER"
            : "MODE DAILY";
    const mb = $("stream-pill-mode");
    if (mb) {
      mb.textContent = modeLabel;
      mb.classList.toggle("on", mode !== "daily");
    }
    document.querySelectorAll(".stream-modes button").forEach((b) => b.classList.remove("on"));
    const modeBtn = {
      daily: $("stream-mode-daily"),
      all: $("stream-mode-all"),
      weather: $("stream-mode-weather"),
      kilauea: $("stream-mode-kilauea"),
      hurricane: $("stream-mode-hurricane"),
    }[mode];
    if (modeBtn) modeBtn.classList.add("on");
    const sceneName = st.scene || "—";
    const sn = $("stream-scene-now");
    if (sn) sn.textContent = sceneName;
    const sp = $("stream-pill-scene");
    if (sp) {
      sp.textContent = `SCENE ${sceneName}`;
      sp.classList.add("on");
    }
    document.querySelectorAll("[data-stream-scene]").forEach((btn) => {
      btn.classList.toggle("on", btn.dataset.streamScene === sceneName);
    });
    await loadStreamSceneControls(st.scenes || []);
    const livePack = pack.live || {};
    const watchLink = $("stream-watch-link");
    if (watchLink) {
      watchLink.textContent = livePack.watch_url
        ? `Public: ${livePack.watch_url}`
        : "Public live page: avaivy.cloud/live";
    }
    const yt = $("stream-yt");
    if (yt && livePack.embed_url && st.streaming) {
      if (yt.dataset.src !== livePack.embed_url) {
        yt.src = livePack.embed_url;
        yt.dataset.src = livePack.embed_url;
      }
    }
    const live = $("stream-pill-live");
    if (live) {
      live.textContent = st.streaming ? "STREAM LIVE" : "STREAM OFF";
      live.classList.toggle("on", Boolean(st.streaming));
    }
    const wb = $("stream-pill-watch");
    if (wb) {
      wb.textContent =
        watch.erupting || watch.mode === "active"
          ? "ACTIVE"
          : watch.active
            ? "VOLCANO WATCH"
            : "WATCH OFF";
      wb.classList.toggle("on", Boolean(watch.active));
    }
    const kit = st.kit?.health || "?";
    const kb = $("stream-pill-kit");
    if (kb) kb.textContent = `KIT ${String(kit).toUpperCase()}`;
    const eb = $("stream-pill-eta");
    if (eb) {
      const band = eta.band || "quiet";
      eb.textContent =
        `ETA ${band}` + (eta.countdown?.display ? ` ${eta.countdown.display}` : "");
    }
    if (st.title != null && $("stream-title") && document.activeElement !== $("stream-title")) {
      $("stream-title").value = st.title || "";
    }
    if (
      st.description != null &&
      $("stream-description") &&
      document.activeElement !== $("stream-description")
    ) {
      $("stream-description").value = st.description || "";
    }
    $("stream-status").textContent = JSON.stringify(
      { status: st, watch, eta, live: livePack },
      null,
      2,
    );
  } catch (err) {
    streamSetMsg(String(err?.message || err), true);
  }
}

async function refreshStreamPreview() {
  if (!$("page-stream")?.classList.contains("active") || !window.avaDesktop?.streamPreview) return;
  const img = $("stream-preview");
  const off = $("stream-preview-off");
  const yt = $("stream-yt");
  const cap = $("stream-preview-cap");
  try {
    const p = await window.avaDesktop.streamPreview();
    if (p?.image && img) {
      img.src = p.image;
      img.hidden = false;
      if (off) off.hidden = true;
      if (yt) yt.hidden = true;
      if (cap) cap.textContent = `Program · ${p.scene || ""}`;
      return;
    }
  } catch {
    /* fall through to YouTube / placeholder */
  }
  if (yt && yt.dataset.src) {
    yt.hidden = false;
    if (img) img.hidden = true;
    if (off) off.hidden = true;
    if (cap) cap.textContent = "YouTube live";
    return;
  }
  if (img) img.hidden = true;
  if (yt) yt.hidden = true;
  if (off) off.hidden = false;
}

async function streamAction(action, extra = {}) {
  streamSetMsg(`${action}…`);
  try {
    const j = await window.avaDesktop.streamAction({
      action,
      ...streamMetaBody(),
      ...extra,
    });
    if (j?.ok === false) {
      streamSetMsg(j.detail || j.hint || "failed", true);
    } else {
      streamSetMsg(`${action} ok`);
    }
    $("stream-status").textContent = JSON.stringify(j, null, 2);
    await refreshStreamOps();
  } catch (err) {
    streamSetMsg(String(err?.message || err), true);
  }
}

async function bootStreamOps() {
  if (!$("page-stream") || !window.avaDesktop?.streamStatus) return;
  $("stream-refresh").onclick = () => {
    refreshStreamOps();
    refreshStreamPreview();
  };
  $("stream-meta-apply").onclick = () => streamAction("metadata");
  $("stream-meta-restart").onclick = () => streamAction("metadata-restart");
  $("stream-watch-enter").onclick = () => streamAction("watch-enter");
  $("stream-watch-exit").onclick = () => streamAction("watch-exit");
  $("stream-mode-daily") && ($("stream-mode-daily").onclick = () => streamAction("mode-daily"));
  $("stream-mode-all") && ($("stream-mode-all").onclick = () => streamAction("mode-all"));
  $("stream-mode-weather") && ($("stream-mode-weather").onclick = () => streamAction("mode-weather"));
  $("stream-mode-kilauea") && ($("stream-mode-kilauea").onclick = () => streamAction("mode-kilauea"));
  $("stream-mode-hurricane") && ($("stream-mode-hurricane").onclick = () => streamAction("mode-hurricane"));
  $("stream-toast").onclick = () => streamAction("toast");
  $("stream-repair").onclick = () => streamAction("repair");
  await loadStreamSceneControls([]);
  $("stream-hide-all") &&
    ($("stream-hide-all").onclick = () => setAllStreamSceneHidden(true));
  $("stream-show-all") &&
    ($("stream-show-all").onclick = () => setAllStreamSceneHidden(false));
  document.querySelectorAll("[data-stream-reaction]").forEach((btn) => {
    btn.onclick = () =>
      streamAction("reaction", {
        reactionId: btn.dataset.streamReaction,
        body: `Manual · ${btn.textContent.trim()}`,
        comment: false,
      });
  });
  await refreshStreamOps();
  await refreshStreamPreview();
  setInterval(() => {
    if ($("page-stream")?.classList.contains("active")) {
      refreshStreamOps().catch(() => {});
      refreshStreamPreview().catch(() => {});
    }
  }, 4000);
}

function audioVoiceLabel(item) {
  if (!item) return null;
  const name = item.name || item.file || "clip";
  const pri = item.priority_label || item.priority || "";
  return { name, pri, file: item.file || "" };
}

function paintAudioNow(st) {
  const host = $("audio-now");
  if (!host) return;
  const cp = st.currently_playing || {};
  const voice = audioVoiceLabel(cp.voice);
  const music = cp.music || {};
  const lines = [];
  if (voice) {
    lines.push(
      `<div class="audio-line"><span class="audio-name">${escapeHtml(voice.name)}</span>` +
        (voice.pri ? `<span class="audio-pill on">${escapeHtml(String(voice.pri))}</span>` : "") +
        `</div>` +
        (voice.file ? `<div class="muted">${escapeHtml(voice.file)}</div>` : ""),
    );
  } else {
    lines.push(`<div class="audio-line muted">Voice director idle</div>`);
  }
  if (music.track && music.playing) {
    lines.push(
      `<div class="audio-line" style="margin-top:0.45rem">Bed · <span class="audio-name">${escapeHtml(music.track)}</span>` +
        `<span class="audio-pill on">playing</span></div>`,
    );
  } else if (music.held) {
    lines.push(`<div class="audio-line muted" style="margin-top:0.35rem">Bed held for voice</div>`);
  } else {
    lines.push(`<div class="audio-line muted" style="margin-top:0.35rem">No bed track</div>`);
  }
  if (st.paused_item) {
    const p = audioVoiceLabel(st.paused_item);
    if (p) {
      lines.push(
        `<div class="audio-line muted" style="margin-top:0.45rem">Paused under higher priority · ${escapeHtml(p.name)}</div>`,
      );
    }
  }
  host.innerHTML = lines.join("");
}

function paintAudioNext(st) {
  const host = $("audio-next");
  if (!host) return;
  const up = st.up_next || {};
  const voiceQ = Array.isArray(up.voice) ? up.voice : [];
  const lines = [];
  if (up.music) {
    lines.push(
      `<div class="audio-line">Bed · <span class="audio-name">${escapeHtml(String(up.music))}</span></div>`,
    );
  }
  if (voiceQ.length) {
    for (const item of voiceQ.slice(0, 8)) {
      const v = audioVoiceLabel(item);
      if (!v) continue;
      lines.push(
        `<div class="audio-line"><span class="audio-name">${escapeHtml(v.name)}</span>` +
          (v.pri ? `<span class="audio-pill">${escapeHtml(String(v.pri))}</span>` : "") +
          `</div>`,
      );
    }
  } else if (!up.music) {
    lines.push(`<div class="muted">Queue empty</div>`);
  } else {
    lines.push(`<div class="muted">No voice items queued</div>`);
  }
  host.innerHTML = lines.join("");
}

function paintAudioBed(st) {
  const host = $("audio-bed");
  if (!host) return;
  const m = st.music || {};
  const pills = [];
  pills.push(
    `<span class="audio-pill ${m.enabled ? "on" : ""}">${m.enabled ? "enabled" : "off"}</span>`,
  );
  if (m.loop_alive) pills.push(`<span class="audio-pill on">loop</span>`);
  if (m.operator_paused) pills.push(`<span class="audio-pill warn">operator pause</span>`);
  else if (m.hold) pills.push(`<span class="audio-pill warn">voice hold</span>`);
  if (m.single_bed) pills.push(`<span class="audio-pill on">single bed</span>`);
  const nowTrack = m.current && m.player_pid != null ? m.current : "—";
  const pid = m.player_pid != null ? `pid ${m.player_pid}` : "no player";
  host.innerHTML = `
    <div class="audio-line">${pills.join(" ")}</div>
    <div class="audio-line">Now · <span class="audio-name">${escapeHtml(nowTrack)}</span></div>
    <div class="audio-line">Next · ${escapeHtml(m.next || "—")}</div>
    <div class="muted">${escapeHtml(String(m.tracks ?? 0))} tracks · ${escapeHtml(pid)}</div>
    <div class="muted">${escapeHtml(m.dir || "")}</div>
  `;
}

function paintAudioPending(st) {
  const host = $("audio-pending");
  const meta = $("audio-pending-meta");
  if (!host) return;
  const rows = Array.isArray(st.pending) ? st.pending : [];
  if (meta) {
    meta.textContent = rows.length
      ? `${rows.length} voice-related jobs · next fire times in HST countdown`
      : "No voice-related jobs from scheduler";
  }
  host.innerHTML = "";
  for (const job of rows) {
    const row = document.createElement("div");
    row.className = "cron-row";
    const nextAt = Number(job.nextAt || 0);
    const boot = job.morning_boot;
    const bootNote =
      boot && boot.armed
        ? ` · morning-boot armed${boot.until ? ` until ${boot.until}` : ""}`
        : boot && boot.armed === false
          ? " · morning-boot idle"
          : "";
    row.innerHTML = `
      <div>
        <div class="id">${escapeHtml(job.id || "")}</div>
        <div class="muted">${escapeHtml(job.name || job.cronHint || "")}${escapeHtml(bootNote)}</div>
      </div>
      <div class="cron-state">
        <span class="cron-countdown" data-next-at="${nextAt || ""}">${countdownLabel(nextAt)}</span>
      </div>
      <div class="muted">${nextAt ? fmtHst(nextAt) : "—"}</div>
      <div></div>
      <div class="actions"></div>
    `;
    host.appendChild(row);
  }
  tickCountdowns(host);
}

async function refreshAudioPage() {
  const meta = $("audio-meta");
  if (!$("page-audio")) return;
  if (meta) meta.textContent = "Loading radio…";
  try {
    const [voiceRes, radioRes] = await Promise.all([
      fetch(`${brainBaseUrl()}/api/voice/status`, {
        cache: "no-store",
        headers: operatorHeaders(),
      }),
      fetch(`${brainBaseUrl()}/api/radio/status`, {
        cache: "no-store",
        headers: operatorHeaders(),
      }),
    ]);
    const st = await voiceRes.json();
    const radio = await radioRes.json().catch(() => ({}));
    paintRadioControls(radio);
    if (!st?.ok) {
      if (meta) meta.textContent = st?.detail || "voice status unavailable";
      $("audio-status").textContent = JSON.stringify(st, null, 2);
      return;
    }
    const m = st.music || {};
    if (meta) {
      meta.textContent = [
        radio?.on_air ? "ON AIR" : "off air",
        radio?.local_playback ? "local on" : "local off",
        radio?.mic_armed ? "mic armed" : null,
        st.running ? "director running" : "director idle",
        m.enabled ? "bed on" : "bed off",
        m.operator_paused ? "operator pause" : m.hold ? "voice hold" : null,
        `queue ${st.queue_depth ?? 0}`,
      ]
        .filter(Boolean)
        .join(" · ");
    }
    paintAudioNow(st);
    paintAudioNext(st);
    paintAudioBed(st);
    paintAudioPending(st);
    $("audio-status").textContent = "";
    ensureCronLive();
    ensureAudioLive();
    ensureRadioDeskPlayer(radio);
  } catch (err) {
    if (meta) meta.textContent = String(err.message || err);
    if ($("audio-status")) {
      $("audio-status").textContent =
        `Origin must be up on ${lastBrainUrl || "127.0.0.1:8787"} — Settings → Connection`;
    }
  }
}

function paintRadioControls(radio) {
  if (!radio || radio.ok === false) return;
  const local = $("radio-local");
  const onair = $("radio-onair");
  const mic = $("radio-mic");
  const live = $("radio-mic-live");
  const tools = $("radio-tools");
  const open = $("audio-open-local");
  if (local) local.checked = !!radio.local_playback;
  if (onair) onair.checked = !!radio.on_air;
  if (mic) mic.checked = !!radio.mic_armed;
  if ($("radio-hurricane")) $("radio-hurricane").checked = radio.hurricane_on_radio !== false;
  if ($("radio-inserts")) $("radio-inserts").checked = radio.voice_inserts !== false;
  if ($("radio-feedback")) $("radio-feedback").checked = radio.feedback_popup !== false;
  const musicVolume = Math.round(Number(radio.music_volume ?? 0.5) * 100);
  const speechVolume = Math.round(Number(radio.speech_music_volume ?? 0.2) * 100);
  if ($("radio-music-volume")) $("radio-music-volume").value = musicVolume;
  if ($("radio-music-volume-value")) $("radio-music-volume-value").textContent = `${musicVolume}%`;
  if ($("radio-speech-volume")) $("radio-speech-volume").value = speechVolume;
  if ($("radio-speech-volume-value")) $("radio-speech-volume-value").textContent = `${speechVolume}%`;
  if (live) live.classList.toggle("hidden", !radio.mic_armed);
  if (tools) {
    const t = radio.tools || {};
    tools.textContent = [
      radio.on_air ? "ON AIR" : "off air",
      radio.local_playback ? "local speakers on" : "local speakers off",
      t.ffmpeg ? "ffmpeg live ready" : "ffmpeg missing",
    ].join(" · ");
  }
  if (open) {
    const base = brainBaseUrl().replace(/\/$/, "");
    open.href = radio.on_air ? `${base}/radio/listen` : `${base}/radio`;
    open.textContent = radio.on_air ? "Open listen page" : "Open wake page";
  }
}

let radioDeskEs = null;
function ensureRadioDeskPlayer(radio) {
  const player = $("radio-desk-player");
  if (!player) return;
  // Pygame owns Desk speakers. Never also play live.mp3 in this HTML element
  // (that was a second copy of the same bed).
  if (radioDeskEs) {
    try {
      radioDeskEs.close();
    } catch {
      /* ignore */
    }
    radioDeskEs = null;
  }
  try {
    player.pause();
    player.removeAttribute("src");
    player.load?.();
  } catch {
    /* ignore */
  }
  void radio;
}

async function patchRadio(partial) {
  $("audio-status").textContent = "Saving radio…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/radio`, {
      method: "POST",
      headers: { ...operatorHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(partial),
    });
    if (!res.ok) {
      const text = await res.text();
      $("audio-status").textContent = `Radio save failed (${res.status}): ${text.slice(0, 400)}`;
      return null;
    }
    const j = await res.json();
    paintRadioControls(j);
    window.avaDesktop
      ?.deskUiSave?.({
        musicWanted: !!j.local_playback,
        radioLocal: !!j.local_playback,
        radioOnAir: !!j.on_air,
        radioMic: !!j.mic_armed,
      })
      .catch(() => {});
    $("audio-status").textContent = j.on_air
      ? "Saved · on air"
      : j.local_playback
        ? "Saved · local only"
        : "Saved · radio idle";
    await refreshAudioPage();
    return j;
  } catch (err) {
    $("audio-status").textContent = String(err.message || err);
    return null;
  }
}

async function saveRadioFromUi() {
  return patchRadio({
    local_playback: !!$("radio-local")?.checked,
    on_air: !!$("radio-onair")?.checked,
    mic_armed: !!$("radio-mic")?.checked,
    hurricane_on_radio: !!$("radio-hurricane")?.checked,
    voice_inserts: !!$("radio-inserts")?.checked,
    feedback_popup: !!$("radio-feedback")?.checked,
    music_volume: Number($("radio-music-volume")?.value || 50) / 100,
    speech_music_volume: Number($("radio-speech-volume")?.value || 20) / 100,
  });
}

async function audioMusicAction(action) {
  $("audio-status").textContent = `${action}…`;
  try {
    const res = await fetch(`${brainBaseUrl()}/api/voice/music`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({ action }),
    });
    const j = await res.json();
    $("audio-status").textContent = j?.ok === false ? JSON.stringify(j, null, 2) : "";
    const a = String(action || "").toLowerCase();
    // Never force Local on when starting the bed — on-air bed can run muted.
    // Local speakers follow the Local checkbox / explicit Local save only.
    if (a === "stop" || a === "pause") {
      const onAir = !!$("radio-onair")?.checked;
      await patchRadio({ local_playback: false, on_air: onAir });
      return;
    }
    if (a === "start" || a === "resume") {
      // Keep radio.local_playback as the operator left it.
      const local = !!$("radio-local")?.checked;
      if (local) {
        await patchRadio({ local_playback: true });
      } else {
        await patchRadio({ local_playback: false });
      }
      return;
    }
    await refreshAudioPage();
  } catch (err) {
    $("audio-status").textContent = String(err.message || err);
  }
}

let audioRefreshTimer = null;
function ensureAudioLive() {
  if (audioRefreshTimer) return;
  audioRefreshTimer = setInterval(() => {
    if ($("page-audio")?.classList.contains("active")) {
      refreshAudioPage().catch(() => {});
    }
  }, 5000);
}

function wireAudioPage() {
  if (!$("page-audio")) return;
  $("audio-refresh")?.addEventListener("click", () => refreshAudioPage());
  $("radio-save")?.addEventListener("click", () => saveRadioFromUi());
  $("audio-music-pause")?.addEventListener("click", () => audioMusicAction("pause"));
  $("audio-music-resume")?.addEventListener("click", () => audioMusicAction("resume"));
  $("audio-music-start")?.addEventListener("click", () => audioMusicAction("start"));
  $("radio-local")?.addEventListener("change", () => saveRadioFromUi());
  $("radio-onair")?.addEventListener("change", () => saveRadioFromUi());
  $("radio-mic")?.addEventListener("change", () => saveRadioFromUi());
  $("radio-music-volume")?.addEventListener("input", () => {
    $("radio-music-volume-value").textContent = `${$("radio-music-volume").value}%`;
  });
  $("radio-speech-volume")?.addEventListener("input", () => {
    $("radio-speech-volume-value").textContent = `${$("radio-speech-volume").value}%`;
  });
  $("audio-chime-now")?.addEventListener("click", async () => {
    $("audio-status").textContent = "chime…";
    try {
      const res = await fetch(`${brainBaseUrl()}/api/voice/chime`, {
        method: "POST",
        headers: operatorHeaders(),
        body: "{}",
      });
      const j = await res.json();
      $("audio-status").textContent = JSON.stringify(j, null, 2).slice(0, 1200);
      await refreshAudioPage();
    } catch (err) {
      $("audio-status").textContent = String(err.message || err);
    }
  });
}

wireAudioPage();

let streamLastSceneListKey = "";
let streamLastHiddenKey = "";
let streamRotationCfgKey = "";

function sceneShortLabel(scene) {
  const map = {
    "Scene 1 - Weather Board": "Weather",
    "Weather Board": "Weather",
    "Scene 5 - Solar Dashboard": "Solar",
    "Solar Dashboard": "Solar",
    "Scene 6 - Economy Board": "Economy",
    "Economy Board": "Economy",
    "Scene 9 - Goals Report": "Goals",
    "Goals Report": "Goals",
    "Scene 8 - Dev Updates": "Dev",
    "Dev Updates": "Dev",
    "Scene 10 - Support Ava": "Support",
    "Support Ava": "Support",
    "Scene 7 - RootMC Live": "RootMC",
    "RootMC Live": "RootMC",
    "Scene 2 - Storm Desk": "Storm",
    "Scene 3 - Kilauea Watch": "Kilauea",
    "Scene 4 - Quake Desk": "Quake",
    "Quake · Global": "Quake Global",
    "Quake · Big Island": "Quake HI",
    "Be right back": "BRB",
  };
  return map[scene] || scene;
}

function sceneKey(scenes) {
  return (scenes || []).join("\u241f");
}

function modeLabel(mode) {
  return {
    daily: "Daily",
    all: "All scenes",
    weather: "Weather",
    kilauea: "Kilauea",
    hurricane: "Hurricane",
  }[mode] || mode;
}

async function loadStreamSceneControls(scenesFromStatus = []) {
  const scenes =
    Array.isArray(scenesFromStatus) && scenesFromStatus.length
      ? scenesFromStatus.filter(Boolean)
      : [];
  const scenesSig = sceneKey(scenes);
  const host = $("stream-scene-hide");
  const jumpHost = $("stream-scene-btns");
  if (!host || !jumpHost) return;
  let hiddenManual = [];
  let hiddenAuto = [];
  let cfg = {};
  try {
    const j = await fetch(`${brainBaseUrl()}/api/obs/scene-visibility`).then((r) => r.json());
    hiddenManual = Array.isArray(j.hidden_manual) ? j.hidden_manual : [];
    hiddenAuto = Array.isArray(j.hidden_auto) ? j.hidden_auto : [];
  } catch {
    /* ignore */
  }
  try {
    const j = await fetch(`${brainBaseUrl()}/api/obs/rotation-config`).then((r) => r.json());
    cfg = j || {};
  } catch {
    cfg = {};
  }
  const hiddenSet = new Set([...(hiddenManual || []), ...(hiddenAuto || [])]);
  const hiddenSig = [...hiddenSet].sort().join("\u241f");
  const cfgSig = JSON.stringify(cfg || {});
  if (
    scenesSig === streamLastSceneListKey &&
    hiddenSig === streamLastHiddenKey &&
    cfgSig === streamRotationCfgKey
  ) {
    return;
  }
  streamLastSceneListKey = scenesSig;
  streamLastHiddenKey = hiddenSig;
  streamRotationCfgKey = cfgSig;

  jumpHost.innerHTML = "";
  for (const scene of scenes) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.streamScene = scene;
    btn.textContent = sceneShortLabel(scene);
    btn.onclick = () => streamAction("scene", { scene });
    jumpHost.append(btn);
  }

  host.innerHTML = "";
  for (const scene of scenes) {
    const lbl = document.createElement("label");
    lbl.className = "mc-follow";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = hiddenSet.has(scene);
    cb.dataset.sceneHide = scene;
    cb.onchange = updateStreamSceneHidden;
    lbl.append(cb, document.createTextNode(` ${scene}`));
    host.append(lbl);
  }
  renderStreamRotationEditors(scenes, cfg);
}

async function updateStreamSceneHidden() {
  const host = $("stream-scene-hide");
  if (!host) return;
  const boxes = host.querySelectorAll("input[data-scene-hide]");
  const manual = [...boxes].filter((b) => b.checked).map((b) => b.dataset.sceneHide);
  await fetch(`${brainBaseUrl()}/api/obs/scene-visibility`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hidden_manual: manual }),
  });
}

async function setAllStreamSceneHidden(hidden) {
  const host = $("stream-scene-hide");
  if (!host) return;
  const boxes = host.querySelectorAll("input[data-scene-hide]");
  boxes.forEach((b) => {
    b.checked = Boolean(hidden);
  });
  await updateStreamSceneHidden();
  await refreshStreamOps();
}

function asSecInput(v, fallback = 60) {
  const n = Number(v);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(5, Math.min(3600, Math.round(n)));
}

function renderStreamRotationEditors(scenes, cfg) {
  const modeHost = $("stream-rotation-modes");
  const sceneHost = $("stream-rotation-scenes");
  if (!modeHost || !sceneHost) return;
  const modeDwell = cfg.mode_dwell_s || {};
  const sceneDwell = cfg.scene_dwell_s || {};
  const enabled = $("stream-rotation-enabled");
  const interval = $("stream-rotation-interval");
  if (enabled) enabled.checked = cfg.enabled !== false;
  if (interval) interval.value = String(asSecInput(cfg.interval_s, 60));
  if (enabled) enabled.onchange = saveStreamRotationConfig;
  if (interval) interval.onchange = applyStreamRotationInterval;
  modeHost.innerHTML = "";
  sceneHost.innerHTML = "";
  for (const mode of ["daily", "all", "weather", "kilauea", "hurricane"]) {
    const lbl = document.createElement("label");
    lbl.className = "mc-follow";
    lbl.textContent = `${modeLabel(mode)} `;
    const input = document.createElement("input");
    input.type = "number";
    input.min = "5";
    input.max = "3600";
    input.step = "1";
    input.value = String(asSecInput(modeDwell[mode], 60));
    input.dataset.rotationMode = mode;
    input.style.width = "5.5rem";
    input.onchange = saveStreamRotationConfig;
    lbl.append(input);
    modeHost.append(lbl);
  }
  for (const scene of scenes) {
    const lbl = document.createElement("label");
    lbl.className = "mc-follow";
    lbl.textContent = `${sceneShortLabel(scene)} `;
    const input = document.createElement("input");
    input.type = "number";
    input.min = "5";
    input.max = "3600";
    input.step = "1";
    input.value = String(asSecInput(sceneDwell[scene], 60));
    input.dataset.rotationScene = scene;
    input.style.width = "5.5rem";
    input.onchange = saveStreamRotationConfig;
    lbl.append(input);
    sceneHost.append(lbl);
  }
}

function applyStreamRotationInterval() {
  const value = asSecInput($("stream-rotation-interval")?.value, 60);
  document.querySelectorAll("input[data-rotation-mode], input[data-rotation-scene]").forEach((input) => {
    input.value = String(value);
  });
  saveStreamRotationConfig();
}

async function saveStreamRotationConfig() {
  const modeInputs = [...document.querySelectorAll("input[data-rotation-mode]")];
  const sceneInputs = [...document.querySelectorAll("input[data-rotation-scene]")];
  const mode_dwell_s = {};
  const scene_dwell_s = {};
  modeInputs.forEach((el) => {
    mode_dwell_s[el.dataset.rotationMode] = asSecInput(el.value, 60);
  });
  sceneInputs.forEach((el) => {
    scene_dwell_s[el.dataset.rotationScene] = asSecInput(el.value, 60);
  });
  const status = $("stream-rotation-status");
  if (status) status.textContent = "Saving…";
  try {
    const response = await fetch(`${brainBaseUrl()}/api/obs/rotation-config`, {
      method: "POST",
      headers: { ...operatorHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        enabled: $("stream-rotation-enabled")?.checked !== false,
        interval_s: asSecInput($("stream-rotation-interval")?.value, 60),
        mode_dwell_s,
        scene_dwell_s,
      }),
    });
    const result = await response.json();
    if (!response.ok || result?.ok === false) throw new Error(result?.detail || `HTTP ${response.status}`);
    streamRotationCfgKey = JSON.stringify(result || {});
    if (status) status.textContent = result.enabled ? `Saved · every ${result.interval_s}s` : "Saved · switcher off";
  } catch (err) {
    if (status) status.textContent = `Save failed · ${String(err?.message || err)}`;
  }
}

async function refreshSitesPage() {
  if (!$("page-sites")?.classList.contains("active")) return;
  const base = brainBaseUrl();
  try {
    const j = await fetch(`${base}/api/ops/sites-posts`).then((r) => r.json());
    const box = $("sites-latest");
    if (box && j.newest) {
      box.innerHTML = `<div class="mc-kpi"><span class="k">Newest post</span><span class="v">${j.newest.site_label || ""}</span><span class="sub">${j.newest.title || ""} · ${j.newest.date || ""}</span></div>`;
    }
    $("sites-status").textContent = JSON.stringify(j, null, 2);
  } catch (e) {
    $("sites-status").textContent = String(e);
  }
}

const bgState = { catalog: null, key: "solar", paths: [] };

function bgThumbUrl(rel) {
  const base = brainBaseUrl();
  return `${base}/api/media/public/file?path=${encodeURIComponent(rel)}`;
}

function renderBgSelected() {
  const box = $("bg-selected");
  if (!box) return;
  if (!bgState.paths.length) {
    box.innerHTML = `<p class="hint-inline">No images in rotation yet — click library tiles to add.</p>`;
    return;
  }
  box.innerHTML = bgState.paths
    .map((rel, i) => {
      const name = escapeHtml(rel.split("/").pop() || rel);
      return `<div class="bg-selected-row" data-i="${i}">
        <img src="${escapeHtml(bgThumbUrl(rel))}" alt=""/>
        <div class="name">${name}</div>
        <div class="row">
          <button type="button" data-bg-up="${i}" ${i === 0 ? "disabled" : ""}>↑</button>
          <button type="button" data-bg-down="${i}" ${i >= bgState.paths.length - 1 ? "disabled" : ""}>↓</button>
          <button type="button" data-bg-rm="${i}">×</button>
        </div>
      </div>`;
    })
    .join("");
  box.querySelectorAll("[data-bg-rm]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const i = Number(btn.getAttribute("data-bg-rm"));
      bgState.paths.splice(i, 1);
      renderBgSelected();
      renderBgLibrary();
    });
  });
  box.querySelectorAll("[data-bg-up]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const i = Number(btn.getAttribute("data-bg-up"));
      if (i < 1) return;
      const t = bgState.paths[i - 1];
      bgState.paths[i - 1] = bgState.paths[i];
      bgState.paths[i] = t;
      renderBgSelected();
    });
  });
  box.querySelectorAll("[data-bg-down]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const i = Number(btn.getAttribute("data-bg-down"));
      if (i >= bgState.paths.length - 1) return;
      const t = bgState.paths[i + 1];
      bgState.paths[i + 1] = bgState.paths[i];
      bgState.paths[i] = t;
      renderBgSelected();
    });
  });
}

function renderBgLibrary() {
  const box = $("bg-library");
  if (!box) return;
  const lib = bgState.catalog?.library || [];
  if (!lib.length) {
    box.innerHTML = `<p class="hint-inline">No images in media/images/character/</p>`;
    return;
  }
  const selected = new Set(bgState.paths);
  box.innerHTML = lib
    .map((item) => {
      const on = selected.has(item.path) ? " on" : "";
      return `<button type="button" class="bg-card${on}" data-bg-add="${escapeHtml(item.path)}">
        <img src="${escapeHtml(bgThumbUrl(item.path))}" alt=""/>
        <span>${escapeHtml(item.name)}</span>
      </button>`;
    })
    .join("");
  box.querySelectorAll("[data-bg-add]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = btn.getAttribute("data-bg-add");
      if (!p) return;
      if (bgState.paths.includes(p)) {
        bgState.paths = bgState.paths.filter((x) => x !== p);
      } else {
        bgState.paths.push(p);
      }
      renderBgSelected();
      renderBgLibrary();
    });
  });
}

function fillBgPageSelect() {
  const sel = $("bg-page");
  if (!sel) return;
  const pages = bgState.catalog?.pages || [];
  const keys = pages.map((p) => p.key);
  if (!keys.includes(bgState.key) && bgState.key) keys.unshift(bgState.key);
  sel.innerHTML = keys
    .map((k) => {
      const page = pages.find((p) => p.key === k);
      const label = page?.label ? `${k} — ${page.label}` : k;
      return `<option value="${escapeHtml(k)}"${k === bgState.key ? " selected" : ""}>${escapeHtml(label)}</option>`;
    })
    .join("");
}

function loadBgPageIntoForm(key) {
  bgState.key = key || "solar";
  const page = (bgState.catalog?.pages || []).find((p) => p.key === bgState.key);
  $("bg-label").value = page?.label || bgState.key;
  $("bg-sites").value = (page?.sites || []).join(", ");
  $("bg-cycle").value = String(page?.cycle_seconds ?? 18);
  bgState.paths = [...(page?.paths || [])];
  fillBgPageSelect();
  renderBgSelected();
  renderBgLibrary();
}

async function refreshBackgroundsPage() {
  if (!$("page-backgrounds")) return;
  const base = brainBaseUrl();
  try {
    const j = await fetch(`${base}/api/site-backgrounds`, { cache: "no-store" }).then((r) => r.json());
    bgState.catalog = j;
    $("bg-dir").textContent = `Folder: ${j.character_dir || "media/images/character"} · config ${j.config_path || ""}`;
    if (!bgState.key && j.pages?.[0]?.key) bgState.key = j.pages[0].key;
    loadBgPageIntoForm(bgState.key || "solar");
    $("bg-status").textContent = `Loaded ${j.pages?.length || 0} pages · ${j.library?.length || 0} character images`;
  } catch (e) {
    $("bg-status").textContent = String(e);
  }
}

function wireBackgroundsPage() {
  if (!$("page-backgrounds")) return;
  $("bg-refresh")?.addEventListener("click", refreshBackgroundsPage);
  $("bg-page")?.addEventListener("change", (ev) => {
    loadBgPageIntoForm(ev.target.value);
  });
  $("bg-open-folder")?.addEventListener("click", async () => {
    try {
      if (window.avaDesktop?.mediaOpen) {
        // open media root; operator can drill into images/character
        await window.avaDesktop.mediaOpen();
      }
      $("bg-status").textContent = "Opened media folder — go to images/character/";
    } catch (e) {
      $("bg-status").textContent = String(e?.message || e);
    }
  });
  $("bg-create")?.addEventListener("click", () => {
    const key = String($("bg-new-key")?.value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9-_]+/g, "-")
      .replace(/^-+|-+$/g, "");
    if (!key) {
      $("bg-status").textContent = "Enter a page key first.";
      return;
    }
    bgState.key = key;
    if (!bgState.catalog) bgState.catalog = { pages: [], library: [] };
    if (!bgState.catalog.pages.some((p) => p.key === key)) {
      bgState.catalog.pages.push({
        key,
        label: key,
        sites: [],
        cycle_seconds: 18,
        paths: [],
      });
    }
    loadBgPageIntoForm(key);
    $("bg-status").textContent = `Editing new page “${key}” — set images and Save.`;
  });
  $("bg-save")?.addEventListener("click", async () => {
    const key = String($("bg-page")?.value || bgState.key || "").trim();
    if (!key) {
      $("bg-status").textContent = "Pick or create a page key.";
      return;
    }
    const body = {
      label: $("bg-label")?.value || key,
      sites: String($("bg-sites")?.value || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      cycle_seconds: Number($("bg-cycle")?.value || 0),
      paths: [...bgState.paths],
    };
    try {
      const r = await fetch(`${brainBaseUrl()}/api/site-backgrounds/${encodeURIComponent(key)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const j = await r.json();
      $("bg-status").textContent = JSON.stringify(j, null, 2);
      await refreshBackgroundsPage();
      bgState.key = key;
      loadBgPageIntoForm(key);
    } catch (e) {
      $("bg-status").textContent = String(e);
    }
  });
}

const sitesMedia = { images: [], audio: [] };

function renderSitesMediaChips() {
  const box = $("sites-media-chips");
  if (!box) return;
  const bits = [];
  sitesMedia.images.forEach((rel, i) => {
    bits.push(
      `<span class="chip">🖼 ${escapeHtml(rel.split("/").pop() || rel)} <button type="button" data-sites-rm="image" data-i="${i}">×</button></span>`
    );
  });
  sitesMedia.audio.forEach((rel, i) => {
    bits.push(
      `<span class="chip">🔊 ${escapeHtml(rel.split("/").pop() || rel)} <button type="button" data-sites-rm="audio" data-i="${i}">×</button></span>`
    );
  });
  box.innerHTML = bits.join(" ") || `<span class="hint-inline">No media attached yet.</span>`;
  box.querySelectorAll("[data-sites-rm]").forEach((btn) => {
    btn.onclick = () => {
      const kind = btn.getAttribute("data-sites-rm");
      const i = Number(btn.getAttribute("data-i"));
      if (kind === "image") sitesMedia.images.splice(i, 1);
      else sitesMedia.audio.splice(i, 1);
      renderSitesMediaChips();
    };
  });
}

async function sitesUploadFiles(kind, fileList) {
  const base = brainBaseUrl();
  const files = Array.from(fileList || []);
  for (const file of files) {
    const fd = new FormData();
    fd.append("kind", kind === "audio" ? "audio" : "images");
    fd.append("file", file);
    const j = await fetch(`${base}/api/ops/upload`, { method: "POST", body: fd }).then((r) => r.json());
    if (!j?.ok || !j.media_path) throw new Error(j?.detail || "upload failed");
    const bucket = kind === "audio" ? sitesMedia.audio : sitesMedia.images;
    if (!bucket.includes(j.media_path)) bucket.push(j.media_path);
  }
  renderSitesMediaChips();
}

async function sitesAttachMedia(kind) {
  try {
    if (window.avaDesktop?.mediaPick) {
      const r = await window.avaDesktop.mediaPick({
        kind: kind === "audio" ? "audio" : "images",
        title: kind === "audio" ? "Attach sound" : "Attach image",
        import: true,
      });
      if (!r?.ok) throw new Error(r?.detail || "pick failed");
      if (r.canceled) return;
      const bucket = kind === "audio" ? sitesMedia.audio : sitesMedia.images;
      for (const f of r.files || []) {
        const rel = String(f.relative || "").replace(/\\/g, "/");
        if (rel && !bucket.includes(rel)) bucket.push(rel);
      }
      renderSitesMediaChips();
      return;
    }
    const input = $(kind === "audio" ? "sites-file-sound" : "sites-file-image");
    if (input) input.click();
  } catch (e) {
    $("sites-status").textContent = String(e?.message || e);
  }
}

async function bootSitesPage() {
  if (!$("page-sites")) return;
  renderSitesMediaChips();
  wireBackgroundsPage();
  $("sites-refresh")?.addEventListener("click", refreshSitesPage);
  $("sites-add-image")?.addEventListener("click", () => sitesAttachMedia("images"));
  $("sites-add-sound")?.addEventListener("click", () => sitesAttachMedia("audio"));
  $("sites-clear-media")?.addEventListener("click", () => {
    sitesMedia.images = [];
    sitesMedia.audio = [];
    renderSitesMediaChips();
  });
  $("sites-file-image")?.addEventListener("change", async (ev) => {
    try {
      await sitesUploadFiles("images", ev.target.files);
    } catch (e) {
      $("sites-status").textContent = String(e?.message || e);
    }
    ev.target.value = "";
  });
  $("sites-file-sound")?.addEventListener("change", async (ev) => {
    try {
      await sitesUploadFiles("audio", ev.target.files);
    } catch (e) {
      $("sites-status").textContent = String(e?.message || e);
    }
    ev.target.value = "";
  });
  $("sites-save")?.addEventListener("click", async () => {
    const base = brainBaseUrl();
    const body = {
      brand: $("sites-brand")?.value || "ava",
      title: $("sites-title")?.value || "",
      body: $("sites-body")?.value || "",
      teaser: $("sites-teaser")?.value || "",
      category: "ops",
      audio: [...sitesMedia.audio],
      images: [...sitesMedia.images],
    };
    const fanout = $("sites-fanout")?.value === "all";
    const url = fanout ? `${base}/api/ops/sites-fanout` : `${base}/api/ops/blog`;
    const payload = fanout
      ? { ...body, brands: ["ava", "rootrecord", "rootmc"] }
      : body;
    const j = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
    $("sites-status").textContent = JSON.stringify(j, null, 2);
    if (j?.ok) {
      sitesMedia.images = [];
      sitesMedia.audio = [];
      renderSitesMediaChips();
    }
    await refreshSitesPage();
  });
  $("sites-publish-rootmc")?.addEventListener("click", async () => {
    const j = await fetch(`${brainBaseUrl()}/api/ops/publish-rootmc`, { method: "POST" }).then((r) => r.json());
    $("sites-status").textContent = JSON.stringify(j, null, 2);
  });
  $("sites-goals-generate")?.addEventListener("click", async () => {
    const j = await fetch(`${brainBaseUrl()}/api/ops/goal-drafts/generate`, { method: "POST" }).then((r) => r.json());
    $("sites-goals-out").textContent = JSON.stringify(j, null, 2);
  });
  $("sites-goals-approve")?.addEventListener("click", async () => {
    const j = await fetch(`${brainBaseUrl()}/api/ops/goal-drafts/approve?index=0`, { method: "POST" }).then((r) => r.json());
    $("sites-goals-out").textContent = JSON.stringify(j, null, 2);
  });
}

async function refreshAutomationPage() {
  if (!$("page-automation")?.classList.contains("active")) return;
  const base = brainBaseUrl();
  try {
    const j = await fetch(`${base}/api/ops/python-drop/status`).then((r) => r.json());
    const table = $("auto-table");
    const rows = Object.entries(j.scripts || {}).sort((a, b) => a[0].localeCompare(b[0]));
    if ($("auto-dir")) $("auto-dir").textContent = `Folder: ${j.drop_dir || "—"}`;
    if (table) {
      table.innerHTML = rows
        .map(([name, meta]) => {
          const run = j.running?.[name];
          const running = run?.alive ? `running (pid ${run.pid})` : "stopped";
          const reason = meta.disabled_reason ? ` · ${meta.disabled_reason}` : "";
          return `<div class="cron-row">
            <div class="cron-main">
              <div class="cron-title">${escapeHtml(name)}</div>
              <div class="cron-sub">${running}${reason}</div>
            </div>
            <div class="row wrap">
              <label class="mc-follow"><input type="checkbox" data-auto-toggle="enabled" data-auto-name="${escapeHtml(name)}" ${meta.enabled ? "checked" : ""}/> enabled</label>
              <label class="mc-follow"><input type="checkbox" data-auto-toggle="autostart" data-auto-name="${escapeHtml(name)}" ${meta.autostart ? "checked" : ""}/> autostart</label>
              <label class="mc-follow"><input type="checkbox" data-auto-toggle="restart_on_exit" data-auto-name="${escapeHtml(name)}" ${meta.restart_on_exit ? "checked" : ""}/> restart</label>
            </div>
          </div>`;
        })
        .join("") || '<div class="hint-inline">No .py files discovered in drop folder.</div>';
      table.querySelectorAll("input[data-auto-toggle]").forEach((el) => {
        el.addEventListener("change", async () => {
          const name = el.dataset.autoName;
          const field = el.dataset.autoToggle;
          const body = { name, [field]: el.checked };
          const out = await fetch(`${base}/api/ops/python-drop/toggle`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }).then((r) => r.json());
          $("auto-status").textContent = JSON.stringify(out, null, 2);
          await refreshAutomationPage();
        });
      });
    }
    $("auto-status").textContent = JSON.stringify(j, null, 2);
  } catch (e) {
    $("auto-status").textContent = String(e);
  }
}

async function bootAutomationPage() {
  if (!$("page-automation")) return;
  $("auto-refresh")?.addEventListener("click", refreshAutomationPage);
  $("auto-rescan")?.addEventListener("click", async () => {
    const j = await fetch(`${brainBaseUrl()}/api/ops/python-drop/rescan`, { method: "POST" }).then((r) => r.json());
    $("auto-status").textContent = JSON.stringify(j, null, 2);
    await refreshAutomationPage();
  });
}

let lastBrainUrl = "http://127.0.0.1:8787";
let connectionPresets = null;

function connFormValues() {
  const mode = $("conn-mode-headless")?.checked ? "headless" : "local";
  let via = "loopback";
  if ($("conn-via-public")?.checked) via = "public";
  else if ($("conn-via-lan")?.checked) via = "lan";
  else if ($("conn-via-loopback")?.checked) via = "loopback";
  if (mode === "headless" && via === "loopback") via = "lan";
  if (mode === "local") via = "loopback";
  return {
    mode,
    via,
    brainUrl: $("conn-brain")?.value?.trim() || "",
    localApiUrl: $("conn-local-api")?.value?.trim() || "",
    ollamaUrl: $("conn-ollama")?.value?.trim() || "",
    publicUrl: $("conn-public")?.value?.trim() || "",
    operatorKey: $("conn-operator-key")?.value?.trim() || "",
    workstationKey: $("conn-workstation-key")?.value?.trim() || "",
  };
}

function fillConnectionForm(conn) {
  if (!conn) return;
  const local = $("conn-mode-local");
  const headless = $("conn-mode-headless");
  if (local) local.checked = conn.mode !== "headless";
  if (headless) headless.checked = conn.mode === "headless";
  const via = conn.via || (conn.mode === "headless" ? "lan" : "loopback");
  if ($("conn-via-lan")) $("conn-via-lan").checked = via === "lan";
  if ($("conn-via-public")) $("conn-via-public").checked = via === "public";
  if ($("conn-via-loopback")) $("conn-via-loopback").checked = via === "loopback";
  if ($("conn-brain")) $("conn-brain").value = conn.brainUrl || "";
  if ($("conn-local-api")) $("conn-local-api").value = conn.localApiUrl || "";
  if ($("conn-ollama")) $("conn-ollama").value = conn.ollamaUrl || "";
  if ($("conn-public")) $("conn-public").value = conn.publicUrl || "";
  if ($("conn-operator-key")) $("conn-operator-key").value = conn.operatorKey || "";
  if ($("conn-workstation-key")) $("conn-workstation-key").value = conn.workstationKey || "";
  syncConnViaVisibility();
}

function syncConnViaVisibility() {
  const headless = $("conn-mode-headless")?.checked;
  const row = $("conn-via-row");
  if (row) row.style.display = headless ? "flex" : "none";
  if ($("conn-via-loopback")?.parentElement) {
    $("conn-via-loopback").parentElement.style.display = headless ? "none" : "";
  }
  const note = $("conn-note");
  if (note) {
    note.textContent = headless
      ? "Headless: rewrite, core, crons, reports, Minecraft, and HTTP ops run on Ava-linux. Terminal script buttons still need Ava core on this disk."
      : "Local: this machine’s :8787 / Ollama. Same box as Ava-linux is the usual OptiPlex desktop mode.";
  }
}

function applyConnectionPreset() {
  if (!connectionPresets) return;
  const headless = $("conn-mode-headless")?.checked;
  const viaPublic = $("conn-via-public")?.checked;
  const preset = !headless
    ? connectionPresets.local
    : viaPublic
      ? connectionPresets.headlessPublic
      : connectionPresets.headlessLan;
  fillConnectionForm(preset);
}

function setConnPill(view, testOk) {
  const pill = $("conn-pill");
  if (!pill) return;
  const mode = view?.mode === "headless" ? "Headless" : "Local";
  const url = String(view?.brainUrl || lastBrainUrl || "").replace(/^https?:\/\//, "");
  const behind = Number(lastGitSync?.behind || 0);
  const gitBit = behind > 0 ? ` · git↓${behind}` : "";
  pill.textContent = `${mode} · ${url || "?"}${gitBit}`;
  pill.classList.remove("ok", "remote", "warn", "git-behind");
  if (testOk === false) pill.classList.add("warn");
  else if (view?.mode === "headless") pill.classList.add("remote");
  else pill.classList.add("ok");
  if (behind > 0) pill.classList.add("git-behind");
}

let lastGitSync = null;

function formatGitSync(result) {
  if (!result) return "No check yet.";
  const lines = [
    `repo: ${result.repo || "core"}`,
    `branch: ${result.branch || "?"} → ${result.upstream || "?"}`,
    `ahead ${result.ahead || 0} · behind ${result.behind || 0}`,
    `dirty: ${result.dirty ? "yes" : "no"} · pulled: ${result.pulled ? "yes" : "no"}`,
    `detail: ${result.detail || "?"}`,
  ];
  if (result.at) lines.push(`at: ${result.at}`);
  if (result.changed_desktop) lines.push("note: desktop files changed — restart Ava desktop");
  if (result.changed_core) lines.push("note: core files changed — restart Ava core / origin");
  if (result.changed_web) lines.push("note: web packages changed — Vercel/GitHub deploy picks those up from GitHub");
  if (result.detail === "dirty_tree") {
    lines.push("Working tree dirty — auto-push or commit first, then pull.");
  }
  return lines.join("\n");
}

function applyGitSyncResult(result) {
  lastGitSync = result || null;
  const pre = $("git-sync-status");
  if (pre) pre.textContent = formatGitSync(result);
  const hint = $("git-sync-hint");
  if (hint) {
    if (result?.pulled) {
      hint.textContent = "Live tree updated from GitHub.";
    } else if (result?.behind > 0 && result?.dirty) {
      hint.textContent = "Behind GitHub but dirty locally — use Pull after the tree is clean, or rely on auto-push first.";
    } else if (result?.behind > 0) {
      hint.textContent = "Behind GitHub — auto-pull will try when clean, or press Pull now.";
    } else if (result?.detail === "already_up_to_date" || result?.detail === "up_to_date") {
      hint.textContent = "Live tree matches GitHub.";
    } else {
      hint.textContent = "";
    }
  }
  // Refresh pill git badge without wiping connection mode.
  const pill = $("conn-pill");
  if (pill && lastBrainUrl) {
    setConnPill(
      { mode: pill.textContent.startsWith("Headless") ? "headless" : "local", brainUrl: lastBrainUrl },
      !pill.classList.contains("warn"),
    );
  }
}

async function refreshGitSyncPrefs() {
  if (!window.avaDesktop?.gitSyncPrefs) return null;
  try {
    const r = await window.avaDesktop.gitSyncPrefs();
    if (r?.prefs) {
      if ($("git-auto-check")) $("git-auto-check").checked = r.prefs.autoCheck !== false;
      if ($("git-auto-pull")) $("git-auto-pull").checked = r.prefs.autoPull !== false;
    }
    if (r?.last) applyGitSyncResult(r.last);
    else if (r?.repo && $("git-sync-status") && !$("git-sync-status").textContent) {
      $("git-sync-status").textContent = `repo: ${r.repo}\n(waiting for first auto-check)`;
    }
    return r;
  } catch (err) {
    if ($("git-sync-status")) $("git-sync-status").textContent = String(err.message || err);
    return null;
  }
}

async function saveGitSyncPrefsForm() {
  const out = $("git-sync-status");
  try {
    const r = await window.avaDesktop.gitSyncPrefsSave({
      autoCheck: Boolean($("git-auto-check")?.checked),
      autoPull: Boolean($("git-auto-pull")?.checked),
    });
    if (out) out.textContent = `prefs saved\n${JSON.stringify(r.prefs, null, 2)}`;
  } catch (err) {
    if (out) out.textContent = String(err.message || err);
  }
}

let deskFeatSeq = 0;

function paintDeskFeatures(radio, gate) {
  if (radio && radio.ok === true) {
    if ($("feat-hurricane-radio") && typeof radio.hurricane_on_radio === "boolean") {
      $("feat-hurricane-radio").checked = radio.hurricane_on_radio;
    }
    if ($("feat-voice-inserts") && typeof radio.voice_inserts === "boolean") {
      $("feat-voice-inserts").checked = radio.voice_inserts;
    }
    if ($("feat-feedback-popup") && typeof radio.feedback_popup === "boolean") {
      $("feat-feedback-popup").checked = radio.feedback_popup;
    }
  }
  if (gate && gate.ok === true) {
    const gateEl = $("feat-ecoflow-gate");
    const socEl = $("feat-ecoflow-soc");
    if (gateEl && typeof gate.enabled === "boolean" && document.activeElement !== gateEl) {
      gateEl.checked = gate.enabled;
    }
    if (socEl && typeof gate.soc_keep_ac_on === "boolean" && document.activeElement !== socEl) {
      socEl.checked = gate.soc_keep_ac_on;
    }
  }
}

function featBit(on, unknown, onLabel, offLabel) {
  if (unknown) return `${offLabel.replace(/ off$/, "")} unknown`;
  return on ? onLabel : offLabel;
}

async function refreshDeskFeatures() {
  const out = $("feat-status");
  const seq = ++deskFeatSeq;
  try {
    const [radioRes, gateRes] = await Promise.all([
      fetch(`${brainBaseUrl()}/api/radio/status`, {
        cache: "no-store",
        headers: operatorHeaders(),
      }),
      fetch(`${brainBaseUrl()}/api/ecoflow/ac-gate`, {
        cache: "no-store",
        headers: operatorHeaders(),
      }),
    ]);
    if (seq !== deskFeatSeq) return;
    const radio = await radioRes.json().catch(() => ({}));
    const gate = await gateRes.json().catch(() => ({}));
    if (seq !== deskFeatSeq) return;
    paintDeskFeatures(radio, gate);
    if (out) {
      out.textContent = [
        featBit(radio.hurricane_on_radio !== false, radio.ok !== true, "hurricane radio on", "hurricane radio off"),
        featBit(radio.voice_inserts !== false, radio.ok !== true, "inserts on", "inserts off"),
        featBit(radio.feedback_popup !== false, radio.ok !== true, "feedback on", "feedback off"),
        featBit(gate.enabled === true, gate.ok !== true || typeof gate.enabled !== "boolean", "AC gate on", "AC gate off"),
        featBit(
          gate.soc_keep_ac_on === true,
          gate.ok !== true || typeof gate.soc_keep_ac_on !== "boolean",
          "SOC keep-AC on",
          "SOC keep-AC off",
        ),
      ].join(" · ");
    }
  } catch (err) {
    if (seq !== deskFeatSeq) return;
    if (out) out.textContent = String(err.message || err);
  }
}

async function saveDeskFeatures() {
  const out = $("feat-status");
  const seq = ++deskFeatSeq;
  if (out) out.textContent = "saving…";
  try {
    const gateRes = await fetch(`${brainBaseUrl()}/api/ecoflow/ac-gate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...operatorHeaders() },
      body: JSON.stringify({
        enabled: !!$("feat-ecoflow-gate")?.checked,
        soc_keep_ac_on: !!$("feat-ecoflow-soc")?.checked,
      }),
    });
    const gate = await gateRes.json().catch(() => ({}));
    if (seq !== deskFeatSeq) return;
    if (!gateRes.ok || gate.ok !== true) {
      if (out) out.textContent = gate.detail || `AC gate save failed (${gateRes.status})`;
      return;
    }
    const radio = await patchRadio({
      hurricane_on_radio: !!$("feat-hurricane-radio")?.checked,
      voice_inserts: !!$("feat-voice-inserts")?.checked,
      feedback_popup: !!$("feat-feedback-popup")?.checked,
    });
    if (seq !== deskFeatSeq) return;
    paintDeskFeatures(radio, gate);
    if (out) {
      out.textContent = [
        "Saved.",
        gate.enabled ? "AC gate on" : "AC gate off",
        gate.soc_keep_ac_on ? "SOC keep-AC on" : "SOC keep-AC off",
      ].join(" · ");
    }
  } catch (err) {
    if (seq !== deskFeatSeq) return;
    if (out) out.textContent = String(err.message || err);
  }
}

async function runGitCheckBtn() {
  const out = $("git-sync-status");
  if (out) out.textContent = "checking…";
  try {
    const r = await window.avaDesktop.gitCheck();
    applyGitSyncResult(r);
  } catch (err) {
    if (out) out.textContent = String(err.message || err);
  }
}

async function runGitPullBtn() {
  if (!confirm("Pull latest GitHub commits into the live tree now?")) return;
  const out = $("git-sync-status");
  if (out) out.textContent = "pulling…";
  try {
    const r = await window.avaDesktop.gitPull();
    applyGitSyncResult(r);
  } catch (err) {
    if (out) out.textContent = String(err.message || err);
  }
}

async function refreshConnectionForm() {
  try {
    const payload = await window.avaDesktop.connectionGet();
    connectionPresets = payload?.presets || null;
    const lan = payload?.server?.lanHost;
    if (lan && $("conn-lan-label")) $("conn-lan-label").textContent = lan;
    fillConnectionForm(payload?.current);
    lastBrainUrl = payload?.current?.brainUrl || lastBrainUrl;
    setConnPill(payload?.view || payload?.current);
    return payload;
  } catch (err) {
    if ($("conn-test-out")) $("conn-test-out").textContent = String(err.message || err);
    return null;
  }
}

async function testConnectionForm() {
  const out = $("conn-test-out");
  if (out) out.textContent = "testing…";
  try {
    const r = await window.avaDesktop.connectionTest(connFormValues());
    if (out) out.textContent = JSON.stringify(r, null, 2);
    setConnPill({ mode: r.mode, brainUrl: r.brainUrl }, Boolean(r.ok));
    return r;
  } catch (err) {
    if (out) out.textContent = String(err.message || err);
    return null;
  }
}

async function saveConnectionForm() {
  const out = $("conn-test-out");
  if (out) out.textContent = "saving…";
  try {
    const saved = await window.avaDesktop.connectionSave(connFormValues());
    if (!saved?.ok) {
      if (out) out.textContent = saved?.detail || "save failed";
      return;
    }
    lastBrainUrl = saved.connection?.brainUrl || lastBrainUrl;
    setConnPill(saved.connection);
    const test = await window.avaDesktop.connectionTest();
    if (out) {
      out.textContent = JSON.stringify({ saved: saved.written, test }, null, 2);
    }
    setConnPill(saved.connection, Boolean(test?.ok));
    const st = await window.avaDesktop.envStatus();
    $("settings-status").textContent = JSON.stringify(st, null, 2);
    refreshCoreStatus().catch(() => {});
  } catch (err) {
    if (out) out.textContent = String(err.message || err);
  }
}

async function boot() {
  await refreshConnectionForm();
  const st = await window.avaDesktop.envStatus();
  $("settings-status").textContent = JSON.stringify(st, null, 2);

  const prov = await window.avaDesktop.rewriteProviders();
  providers = prov.providers || [];
  $("settings-providers").textContent = JSON.stringify(providers, null, 2);
  renderProviders("discord-providers", "discord");
  renderProviders("slack-providers", "slack");
  renderProviders("telegram-providers", "telegram");
  renderProviders("post-providers", "post");
  renderProviders("feedback-providers", "feedback");
  try {
    const ft = await window.avaDesktop.feedbackTargets();
    fillFeedbackTemplates(ft?.templates || []);
    if (ft?.targets?.discordDevelopment?.id) {
      feedbackState.targets.discord = ft.targets.discordDevelopment.id;
    }
    if (ft?.targets?.slackFeedback?.id) {
      feedbackState.targets.slack = ft.targets.slackFeedback.id;
    }
  } catch {
    fillFeedbackTemplates([]);
  }
  {
    const prev = providers;
    providers = (providers || []).filter((p) => !["exact", "ollama"].includes(p.id));
    if (!providers.length) {
      providers = [
        { id: "dream", label: "Dream / Grok" },
        { id: "cursor", label: "Cursor" },
        { id: "google", label: "Google / Gemini" },
      ];
    }
    if (!providerSel.core || providerSel.core === "ollama") providerSel.core = "dream";
    renderProviders("core-providers", "core");
    providers = prev;
  }
  renderCoreHistory();
  refreshCoreStatus().catch(() => {});
  for (const s of RESPONSE_LOG_SURFACES) renderResponseLog(s);
  document.querySelectorAll("[data-log-clear]").forEach((btn) => {
    btn.addEventListener("click", () => clearResponseLog(btn.dataset.logClear));
  });
  for (const id of [
    "discord-draft",
    "slack-draft",
    "telegram-draft",
    "post-draft",
    "core-draft",
    "feedback-draft",
  ]) {
    wireDraftAutosize(id);
  }

  await bootTerminal();
  await bootMinecraft();
  await bootStreamOps();
  await bootAutomationPage();
  await bootSitesPage();
  ensureBizTimer();
  window.avaDesktop.earlyLogin?.().catch(() => {});
  await refreshGitSyncPrefs();
  window.avaDesktop.onGitSync?.((payload) => applyGitSyncResult(payload));
  window.avaDesktop.onDeskLifecycle?.((payload) => paintDeskLifecycleStatus(payload));
  await applyDeskUiRestore();
  $("git-check-btn")?.addEventListener("click", () => runGitCheckBtn().catch(() => {}));
  $("git-pull-btn")?.addEventListener("click", () => runGitPullBtn().catch(() => {}));
  $("header-git-pull")?.addEventListener("click", () => runGitPullBtn().catch(() => {}));
  $("feat-save")?.addEventListener("click", () => saveDeskFeatures().catch(() => {}));
  $("feat-refresh")?.addEventListener("click", () => refreshDeskFeatures().catch(() => {}));
  $("feat-ecoflow-gate")?.addEventListener("change", () => saveDeskFeatures().catch(() => {}));
  $("feat-ecoflow-soc")?.addEventListener("change", () => saveDeskFeatures().catch(() => {}));
  $("git-prefs-save")?.addEventListener("click", () => saveGitSyncPrefsForm().catch(() => {}));

  const presetRes = await window.avaDesktop.listPresets();
  presets = presetRes.presets || [];
  fillPresets($("post-surface").value);
  const updates = presets.find((p) => p.key === "updates");
  if (updates) {
    $("post-surface").value = "discord";
    fillPresets("discord");
    $("post-preset").value = updates.id;
    $("post-channel").value = updates.id;
  }

  const guild = await window.avaDesktop.listDiscordChannels();
  fillSelect($("discord-channel"), guild.channels || [], {
    nameFn: (c) => `#${c.name}`,
  });
  const priv = await window.avaDesktop.listDiscordPrivate();
  fillSelect($("discord-private"), priv.channels || [], {
    placeholder: "(none — use guild)",
    nameFn: (c) => c.name,
  });
  const prefer = (guild.channels || []).find((c) =>
    /development|admins|updates|general/i.test(c.name),
  );
  if (prefer) $("discord-channel").value = prefer.id;

  const slack = await window.avaDesktop.listSlackChannels();
  fillSelect($("slack-channel"), slack.channels || [], {
    nameFn: (c) => `${c.private ? "🔒" : "#"}${c.name}`,
  });

  const tg = await window.avaDesktop.listTelegramChats();
  fillSelect($("telegram-chat"), tg.channels || [], {
    nameFn: (c) => c.name,
  });

  await refreshDiscord();
  await refreshSlack();
  await refreshTelegram();
  await refreshCrons();
  refreshPostAllMeta().catch(() => {});
}

async function refreshPostAllMeta() {
  const el = $("post-all-meta");
  if (!el || !window.avaDesktop.listAllPostTargets) return;
  try {
    const listed = await window.avaDesktop.listAllPostTargets();
    const c = listed?.counts || {};
    const total = Number(c.total || 0);
    el.textContent = total
      ? `${total} known · Discord ${c.discord || 0} + ${c.discordDm || 0} DMs · Slack ${c.slack || 0} + ${c.slackDm || 0} DMs · Telegram ${c.telegram || 0}`
      : listed?.detail || "Every Discord channel + DM, Slack channel + DM, and Telegram chat Ava knows.";
  } catch {
    /* keep default hint */
  }
}

/* bindings */
$("discord-channel").onchange = () => {
  $("discord-private").value = "";
  refreshDiscord();
};
$("discord-private").onchange = () => refreshDiscord();
$("discord-refresh").onclick = () => refreshDiscord();
$("discord-reply-clear").onclick = () => setReplyBar("discord", null);
$("discord-edit-load").onclick = () => loadDiscordEdit();
$("discord-delete").onclick = () => deleteDiscordSelected();
$("discord-save-edit").onclick = () => saveDiscordEdit();
$("discord-cancel-edit").onclick = () => cancelDiscordEdit();
$("discord-preview").onclick = () =>
  previewRewrite("discord", "discord-draft", discordChannelId(), "discord-status", "discord-compare");
$("discord-compare").onclick = () =>
  previewRewrite("discord", "discord-draft", discordChannelId(), "discord-status", "discord-compare", true);
$("discord-summarize").onclick = () =>
  summarizeSurface("discord", discordChannelId(), "discord-draft", "discord-status");
$("discord-send").onclick = () =>
  sendSurface("discord", "discord-draft", discordChannelId(), "discord-status");

$("slack-channel").onchange = () => refreshSlack();
$("slack-refresh").onclick = () => refreshSlack();
$("slack-reply-clear").onclick = () => setReplyBar("slack", null);
$("slack-preview").onclick = () =>
  previewRewrite("slack", "slack-draft", $("slack-channel").value, "slack-status", "slack-compare");
$("slack-compare").onclick = () =>
  previewRewrite("slack", "slack-draft", $("slack-channel").value, "slack-status", "slack-compare", true);
$("slack-summarize").onclick = () =>
  summarizeSurface("slack", $("slack-channel").value, "slack-draft", "slack-status");
$("slack-send").onclick = () =>
  sendSurface("slack", "slack-draft", $("slack-channel").value, "slack-status");

$("telegram-chat").onchange = () => refreshTelegram();
$("telegram-refresh").onclick = () => refreshTelegram();
$("telegram-reply-clear").onclick = () => setReplyBar("telegram", null);
$("telegram-preview").onclick = () =>
  previewRewrite(
    "telegram",
    "telegram-draft",
    $("telegram-chat").value,
    "telegram-status",
    "telegram-compare",
  );
$("telegram-compare").onclick = () =>
  previewRewrite(
    "telegram",
    "telegram-draft",
    $("telegram-chat").value,
    "telegram-status",
    "telegram-compare",
    true,
  );
$("telegram-summarize").onclick = () =>
  summarizeSurface("telegram", $("telegram-chat").value, "telegram-draft", "telegram-status");
$("telegram-send").onclick = () =>
  sendSurface("telegram", "telegram-draft", $("telegram-chat").value, "telegram-status");

$("post-surface").onchange = () => {
  fillPresets($("post-surface").value);
  $("post-channel").value = "";
  $("post-history").innerHTML = "";
  $("post-history-meta").textContent = "";
};
$("post-preset").onchange = () => {
  if ($("post-preset").value) $("post-channel").value = $("post-preset").value;
  refreshPostHistory();
};
$("post-channel").onchange = () => refreshPostHistory();
$("post-refresh-history").onclick = () => refreshPostHistory();
$("post-clear").onclick = () => {
  $("post-draft").value = "";
  $("post-ref").value = "";
  $("post-status").textContent = "";
};
$("post-preview").onclick = () =>
  previewRewrite("post", "post-draft", $("post-channel").value, "post-status", "post-compare");
$("post-compare").onclick = () =>
  previewRewrite("post", "post-draft", $("post-channel").value, "post-status", "post-compare", true);
if (typeof window.avaDesktop.onPostAllProgress === "function") {
  window.avaDesktop.onPostAllProgress((p) => {
    if (!$("page-post")?.classList.contains("active")) return;
    if (!p?.total) return;
    $("post-status").textContent = `posting to all ${p.i}/${p.total} · ${p.label || ""}`;
  });
}

$("post-all").onclick = async () => {
  const text = $("post-draft").value.trim();
  if (!text) {
    $("post-status").textContent = "Need a message.";
    return;
  }
  if (surfaceBusy.post) {
    $("post-status").textContent = "already posting — ignored double click";
    return;
  }
  $("post-status").textContent = "listing every known channel + DM…";
  let listed;
  try {
    listed = await window.avaDesktop.listAllPostTargets();
  } catch (err) {
    $("post-status").textContent = String(err.message || err);
    return;
  }
  const counts = listed?.counts || {};
  const total = Number(counts.total || (listed?.targets || []).length || 0);
  if (!total) {
    $("post-status").textContent = listed?.detail || "no known destinations";
    return;
  }
  const summary = [
    `${counts.discord || 0} Discord channels`,
    `${counts.discordDm || 0} Discord DMs`,
    `${counts.slack || 0} Slack channels`,
    `${counts.slackDm || 0} Slack DMs`,
    `${counts.telegram || 0} Telegram chats`,
  ].join(", ");
  if (
    !confirm(
      `Post this message to ALL ${total} known pages?\n\n${summary}\n\nThis goes to every DM and every channel Ava knows. Cannot be undone.`,
    )
  ) {
    $("post-status").textContent = "cancelled";
    return;
  }
  const provider = providerSel.post;
  const rewrite = provider !== "exact" && !draftReadyExact.post;
  surfaceBusy.post = true;
  $("post-status").textContent = `posting to all ${total}…`;
  try {
    const r = await window.avaDesktop.postAll({
      text,
      rewrite,
      provider: rewrite ? provider : "exact",
    });
    draftReadyExact.post = false;
    const failed = r.results?.filter((x) => !x.ok) || [];
    $("post-status").textContent = [
      r.ok ? `posted ${r.posted}/${r.total || total}` : `failed · ${r.detail || ""}`,
      r.failed ? `${r.failed} failed` : null,
      r.provider || provider,
      r.via || "",
    ]
      .filter(Boolean)
      .join(" · ");
    if ($("post-all-meta")) {
      $("post-all-meta").textContent = `Last fan-out: ${r.posted || 0} sent · ${r.failed || 0} failed · ${total} known`;
    }
    appendResponseLog("post", {
      kind: "send",
      text: r.text || text,
      provider: r.provider || (rewrite ? provider : "exact"),
      via: r.via || "all-pages",
      meta: `all pages ${r.posted || 0}/${r.total || total}${
        failed.length
          ? ` · fail ${failed
              .slice(0, 6)
              .map((f) => f.label || f.channelId)
              .join(", ")}`
          : ""
      }`,
    });
  } catch (err) {
    $("post-status").textContent = String(err.message || err);
  } finally {
    surfaceBusy.post = false;
  }
};

$("post-send").onclick = async () => {
  let channelId = $("post-channel").value.trim();
  const text = $("post-draft").value.trim();
  const asPreset = presets.find(
    (p) => p.key === channelId.toLowerCase() || p.id === channelId,
  );
  if (asPreset) {
    channelId = asPreset.id;
    $("post-surface").value = asPreset.surface;
  }
  if (!channelId || !text) {
    $("post-status").textContent = "Need channel + message.";
    return;
  }
  if (surfaceBusy.post) {
    $("post-status").textContent = "already posting — ignored double click";
    return;
  }
  const provider = providerSel.post;
  const rewrite = provider !== "exact" && !draftReadyExact.post;
  surfaceBusy.post = true;
  $("post-status").textContent = rewrite
    ? `posting via ${provider}…`
    : draftReadyExact.post
      ? "posting exact (already rewritten)…"
      : "posting…";
  try {
    const r = await window.avaDesktop.post({
      surface: $("post-surface").value,
      channelId,
      text,
      refId: $("post-ref").value.trim() || undefined,
      rewrite,
      provider: rewrite ? provider : "exact",
    });
    draftReadyExact.post = false;
    $("post-status").textContent = `sent · ${r.provider || provider} · ${r.via || ""} · ${r.id || ""}`;
    appendResponseLog("post", {
      kind: "send",
      text: r.text || text,
      provider: r.provider || (rewrite ? provider : "exact"),
      via: r.via || "",
      meta: r.id ? `id ${r.id}` : "",
    });
    await refreshPostHistory();
  } catch (err) {
    $("post-status").textContent = String(err.message || err);
  } finally {
    surfaceBusy.post = false;
  }
};

$("cron-refresh").onclick = () => refreshCrons();
$("cron-catchup").onclick = () => runOpsCommand("cron-catchup");
if ($("reports-refresh")) $("reports-refresh").onclick = () => refreshReports();
if ($("reports-readiness-run")) {
  $("reports-readiness-run").onclick = async () => {
    const status = $("reports-readiness-meta");
    if (status) status.textContent = "Running readiness poll…";
    try {
      const result = await window.avaDesktop.cronRun("report-readiness");
      if (status) status.textContent = result?.ok ? `Readiness ran · ${result.slot || "no slot"}` : JSON.stringify(result);
      await refreshReports();
    } catch (err) {
      if (status) status.textContent = String(err?.message || err);
    }
  };
}
if ($("reports-load-current")) {
  $("reports-load-current").onclick = async () => {
    const st = $("reports-status");
    try {
      const res = await fetch(`${brainBaseUrl()}/api/reports/current`, {
        cache: "no-store",
        headers: operatorHeaders(),
      });
      const d = await res.json();
      if (!d?.exists) {
        if (st) st.textContent = "No current report on disk yet.";
        return;
      }
      $("reports-manual-draft").value = d.text || "";
      if (st) st.textContent = `Loaded ${d.name || "current"}`;
    } catch (err) {
      if (st) st.textContent = String(err.message || err);
    }
  };
}
if ($("reports-clear-draft")) {
  $("reports-clear-draft").onclick = () => {
    $("reports-manual-draft").value = "";
    $("reports-status").textContent = "";
  };
}
if ($("reports-submit-manual")) {
  $("reports-submit-manual").onclick = async () => {
    const draft = $("reports-manual-draft")?.value?.trim() || "";
    const st = $("reports-status");
    if (!draft) {
      if (st) st.textContent = "Paste the written daily report first.";
      return;
    }
    const post = Boolean($("reports-post")?.checked);
    const kind = $("reports-kind")?.value || "summary";
    const dest = kind === "morning" ? "#automations" : "#updates";
    const ok = confirm(
      post
        ? `Replace the current daily report and post to ${dest} + subscribers?\n\nDoes not call Grok or Cursor.`
        : "Replace the current daily report on disk only (no Discord post)?",
    );
    if (!ok) return;
    if (st) st.textContent = "Submitting current report…";
    try {
      const res = await fetch(`${brainBaseUrl()}/api/reports/manual`, {
        method: "POST",
        headers: operatorHeaders(),
        body: JSON.stringify({ text: draft, kind, post }),
      });
      const d = await res.json().catch(() => null);
      if (!res.ok || !d?.ok) {
        if (st) st.textContent = d?.detail || `http_${res.status}`;
        return;
      }
      const posted = d.posted || {};
      if (st) {
        st.textContent = [
          `Current updated: ${d.current || d.dated || "ok"}`,
          post
            ? `posted ${posted.channel ? "channel" : "no channel"} · DMs ${posted.dms || 0}`
            : "disk only",
        ].join("\n");
      }
      await refreshReports();
    } catch (err) {
      if (st) st.textContent = String(err.message || err);
    }
  };
}
if ($("reports-open-reports")) {
  $("reports-open-reports").onclick = () => window.avaDesktop.openFolder("reports");
}
if ($("reports-open-days")) $("reports-open-days").onclick = () => window.avaDesktop.openFolder("solarDays");
if ($("reports-open-dumps")) $("reports-open-dumps").onclick = () => window.avaDesktop.openFolder("dumps");
if ($("reports-open-data")) $("reports-open-data").onclick = () => window.avaDesktop.openFolder("data");
if ($("wg-refresh")) $("wg-refresh").onclick = () => refreshWeatherGifsPage();
if ($("wg-open-folder")) {
  $("wg-open-folder").onclick = () => window.avaDesktop.openFolder("weatherGifs");
}
if ($("wg-open-collector")) {
  $("wg-open-collector").onclick = () => window.avaDesktop.openFolder("weatherGifsCollector");
}
if ($("wg-open-board")) {
  $("wg-open-board").onclick = () => {
    const url = `${brainBaseUrl()}/weather/gifs`;
    window.avaDesktop.openLink(url);
  };
}

if ($("biz-refresh")) $("biz-refresh").onclick = () => refreshBiz();
if ($("biz-clock-in")) {
  $("biz-clock-in").onclick = () =>
    runBizAction({
      action: "clock-in",
      personId: "alex",
      projectId: $("biz-project")?.value || "proj-ava",
      categoryId: $("biz-category")?.value || "cat-dev",
      description: $("biz-note")?.value?.trim() || "",
    });
}
if ($("biz-clock-out")) {
  $("biz-clock-out").onclick = () =>
    runBizAction({
      action: "clock-out",
      personId: "alex",
      description: $("biz-note")?.value?.trim() || "",
    });
}
if ($("biz-clock-form")) {
  $("biz-clock-form").onsubmit = async (e) => {
    e.preventDefault();
    await runBizAction({
      action: "clock-in",
      personId: "alex",
      projectId: $("biz-project")?.value || "proj-ava",
      categoryId: $("biz-category")?.value || "cat-dev",
      description: $("biz-note")?.value?.trim() || "",
    });
    if ($("biz-note")) $("biz-note").value = "";
  };
}
if ($("biz-project-form")) {
  $("biz-project-form").onsubmit = async (e) => {
    e.preventDefault();
    await runBizAction({
      action: "add-project",
      name: $("biz-new-project")?.value?.trim(),
      note: $("biz-new-note")?.value?.trim() || "",
    });
    if ($("biz-new-project")) $("biz-new-project").value = "";
    if ($("biz-new-note")) $("biz-new-note").value = "";
  };
}

if ($("finance-refresh")) $("finance-refresh").onclick = () => refreshFinance();
if ($("finance-stripe")) $("finance-stripe").onclick = () => refreshFinance({ refreshStripe: true });
if ($("finance-pnl-txns")) {
  $("finance-pnl-txns").addEventListener("change", async (e) => {
    const sel = e.target.closest(".fin-venmo-cat");
    if (!sel?.dataset.venmoId) return;
    await runFinanceAction({
      action: "update-venmo-txn",
      id: sel.dataset.venmoId,
      category: sel.value,
    });
  });
}
if ($("finance-review")) $("finance-review").onclick = () => runFinanceAction({ action: "review" });
if ($("finance-notify")) {
  $("finance-notify").onclick = () => {
    if (!confirm("Send finance review to Telegram Alex?")) return;
    runFinanceAction({ action: "notify" });
  };
}
if ($("finance-optimal-form")) {
  $("finance-optimal-form").onsubmit = async (e) => {
    e.preventDefault();
    await runFinanceAction({
      action: "upsert-optimal",
      label: $("fin-opt-label").value.trim(),
      amountUsd: Number($("fin-opt-amount").value),
      period: $("fin-opt-period")?.value || "month",
      category: $("fin-opt-category")?.value || "ops",
      note: $("fin-opt-note")?.value?.trim() || "",
    });
    $("fin-opt-label").value = "";
    $("fin-opt-amount").value = "";
    if ($("fin-opt-note")) $("fin-opt-note").value = "";
  };
}
if ($("finance-optimal")) {
  $("finance-optimal").addEventListener("submit", async (e) => {
    const form = e.target.closest(".fin-opt-edit");
    if (!form) return;
    e.preventDefault();
    await runFinanceAction({
      action: "upsert-optimal",
      id: form.dataset.id,
      label: form.label.value.trim(),
      amountUsd: Number(form.amount.value),
      period: form.period.value,
      category: form.category.value,
      note: form.note.value.trim(),
    });
  });
  $("finance-optimal").addEventListener("click", async (e) => {
    const btn = e.target.closest(".fin-opt-del");
    if (!btn) return;
    const form = btn.closest(".fin-opt-edit");
    if (!form?.dataset.id) return;
    if (!confirm("Remove this optimal budget line?")) return;
    await runFinanceAction({ action: "delete-optimal", id: form.dataset.id });
  });
}
if ($("finance-add-form")) {
  $("finance-add-form").onsubmit = async (e) => {
    e.preventDefault();
    await runFinanceAction({
      action: "upsert-line",
      kind: $("fin-kind").value,
      label: $("fin-label").value.trim(),
      amountUsd: Number($("fin-amount").value),
      period: $("fin-period").value,
      category: $("fin-category")?.value || "ops",
      projectId: $("fin-project").value.trim() || ($("fin-kind").value === "debt" ? "ava" : "rootmc-ops"),
      account: $("fin-account").value.trim() || ($("fin-kind").value === "debt" ? "debts" : "default"),
    });
    $("fin-label").value = "";
    $("fin-amount").value = "";
  };
}
if ($("finance-wishlist-form")) {
  $("finance-wishlist-form").onsubmit = async (e) => {
    e.preventDefault();
    await runFinanceAction({
      action: "add-wishlist",
      name: $("fin-wl-name").value.trim(),
      note: $("fin-wl-note")?.value.trim() || "",
    });
    $("fin-wl-name").value = "";
    if ($("fin-wl-note")) $("fin-wl-note").value = "";
  };
}
if ($("finance-acct-form")) {
  $("finance-acct-form").onsubmit = async (e) => {
    e.preventDefault();
    await runFinanceAction({
      action: "add-account",
      name: $("fin-acct-name").value.trim(),
      kind: $("fin-acct-kind").value,
      balanceUsd: Number($("fin-acct-balance").value) || 0,
      projectId: $("fin-acct-project").value.trim() || "ava",
    });
    $("fin-acct-name").value = "";
    $("fin-acct-balance").value = "";
  };
}

let releaseKind = "plugins";

function fmtSize(n) {
  const x = Number(n) || 0;
  if (x < 1024) return `${x} B`;
  if (x < 1024 * 1024) return `${(x / 1024).toFixed(1)} KB`;
  return `${(x / 1024 / 1024).toFixed(1)} MB`;
}

function selectedReleaseTargets() {
  return [...document.querySelectorAll("#release-targets input[type=checkbox]:checked")].map(
    (el) => el.value,
  );
}

function setReleaseKind(kind) {
  releaseKind = kind === "apps" ? "apps" : "plugins";
  $("release-kind-plugins")?.classList.toggle("primary", releaseKind === "plugins");
  $("release-kind-apps")?.classList.toggle("primary", releaseKind === "apps");
  refreshRelease();
}

async function refreshRelease() {
  const meta = $("release-meta");
  const log = $("release-log");
  const targetsEl = $("release-targets");
  const artsEl = $("release-arts");
  if (!meta || !targetsEl) return;
  meta.textContent = `Loading ${releaseKind}…`;
  try {
    const data = await window.avaDesktop.releaseStatus(releaseKind);
    if (!data?.ok) {
      meta.textContent = data?.detail || "failed";
      log.textContent = data?.hint || data?.detail || "Private API unreachable — is Ava :8787 up?";
      return;
    }
    const s = data.status || {};
    const busy = !!data.busy;
    meta.textContent =
      `${releaseKind} · ${busy ? "running" : s.state || "idle"}` +
      (s.action ? ` · ${s.action}` : "") +
      (data.javaReady ? " · JDK ok" : " · JDK missing") +
      (data.sync?.copied != null ? ` · synced ${data.sync.copied}` : "");
    const prev = new Set(selectedReleaseTargets());
    targetsEl.innerHTML =
      (data.targets || [])
        .map((t) => {
          const ver = t.version
            ? escapeHtml(t.version)
            : t.versionCode != null
              ? `code ${t.versionCode}`
              : "—";
          const checked = prev.has(t.id) ? " checked" : "";
          return `<label><input type="checkbox" value="${escapeHtml(t.id)}"${checked}/><span><div>${escapeHtml(t.label || t.id)}</div><div class="ver">${ver}</div></span></label>`;
        })
        .join("") || `<div class="hint-inline">No targets on disk.</div>`;
    artsEl.innerHTML =
      (data.artifacts || [])
        .map((a) => {
          const href = a.url || (data.public?.public ? `${data.public.public}${a.publicRel || ""}` : "");
          const name = href
            ? `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">${escapeHtml(a.name)}</a>`
            : escapeHtml(a.name);
          return `<div class="row"><span>${name}</span><span class="meta">${escapeHtml(fmtSize(a.size))}</span></div>`;
        })
        .join("") || `<div class="hint-inline">No artifacts yet — build or sync publicfiles.</div>`;
    log.textContent = (s.logTail && s.logTail.trim()) || (busy ? "Running…" : "Idle.");
    ["release-bump", "release-build", "release-release"].forEach((id) => {
      if ($(id)) $(id).disabled = busy;
    });
  } catch (err) {
    meta.textContent = String(err.message || err);
  }
}

async function runRelease(action) {
  const log = $("release-log");
  ["release-bump", "release-build", "release-release"].forEach((id) => {
    if ($(id)) $(id).disabled = true;
  });
  log.textContent = `Starting ${action}…`;
  try {
    const r = await window.avaDesktop.releaseAction(releaseKind, action, selectedReleaseTargets());
    if (!r?.ok && !r?.accepted) {
      log.textContent = r?.detail || r?.error || "request failed";
    }
  } catch (err) {
    log.textContent = String(err.message || err);
  }
  refreshRelease();
}

$("release-kind-plugins")?.addEventListener("click", () => setReleaseKind("plugins"));
$("release-kind-apps")?.addEventListener("click", () => setReleaseKind("apps"));
$("release-refresh")?.addEventListener("click", () => refreshRelease());
$("release-bump")?.addEventListener("click", () => runRelease("bump"));
$("release-build")?.addEventListener("click", () => runRelease("build"));
$("release-release")?.addEventListener("click", () => runRelease("release"));
$("release-files-link")?.addEventListener("click", (ev) => {
  ev.preventDefault();
  window.avaDesktop.openLink("https://ava.rootmc.net/publicfiles/");
});

async function renderLinks() {
  const host = $("links-catalog");
  const status = $("links-status");
  if (!host) return;
  host.innerHTML = "";
  status.textContent = "loading…";
  try {
    const data = await window.avaDesktop.listLinks();
    if (!data?.ok) {
      status.textContent = data?.detail || "failed to load links";
      return;
    }
    for (const group of data.groups || []) {
      const section = document.createElement("section");
      section.className = "links-group";
      const h3 = document.createElement("h3");
      h3.textContent = group.label || group.id;
      section.appendChild(h3);
      const grid = document.createElement("div");
      grid.className = "links-grid";
      for (const link of group.links || []) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "link-card";
        btn.innerHTML =
          `<span class="title">${escapeHtml(link.title || "Link")}</span>` +
          `<span class="url">${escapeHtml(link.url || "")}</span>` +
          (link.note ? `<span class="note">${escapeHtml(link.note)}</span>` : "");
        btn.onclick = async () => {
          status.textContent = `opening ${link.url}…`;
          const r = await window.avaDesktop.openLink(link.url);
          status.textContent = r?.ok ? `opened · ${link.title}` : `open failed · ${r?.detail || "?"}`;
        };
        grid.appendChild(btn);
      }
      section.appendChild(grid);
      host.appendChild(section);
    }
    const count = (data.groups || []).reduce((n, g) => n + (g.links?.length || 0), 0);
    status.textContent = `${count} links · ${data.groups?.length || 0} groups`;
  } catch (err) {
    status.textContent = String(err.message || err);
  }
}

$("links-refresh").onclick = () => renderLinks();

function renderCoreHistory() {
  const el = $("core-history");
  if (!el) return;
  if (!coreState.messages.length && !coreState.pending) {
    el.innerHTML = "<div class='msg meta'>Start a 1:1 turn — replies train Ava core on this host.</div>";
    return;
  }
  const rows = coreState.messages.map((m) => {
    const role = m.role === "assistant" ? "ava" : "you";
    const who = m.role === "assistant" ? "Ava" : "You";
    return `<div class="msg ${role}"><span class="who">${who}</span>: ${escapeHtml(m.content || "")}</div>`;
  });
  if (coreState.pending) {
    rows.push(
      `<div class="msg ava typing" aria-live="polite"><span class="who">Ava</span>: <span class="typing-label">is typing</span><span class="typing-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="typing-elapsed">${escapeHtml(coreState.pendingLabel || "")}</span></div>`,
    );
  }
  el.innerHTML = rows.join("");
  el.scrollTop = el.scrollHeight;
}

function coreContextForEnhance() {
  return coreState.messages.slice(-12).map((m) => ({
    who: m.role === "assistant" ? "Ava" : "You",
    text: m.content || "",
  }));
}

let coreTick = null;

function stopCoreTick() {
  if (coreTick) {
    clearInterval(coreTick);
    coreTick = null;
  }
  coreState.pending = false;
  coreState.pendingLabel = "";
  const cancel = $("core-cancel");
  if (cancel) cancel.disabled = true;
}

function setCoreBusy(busy, label) {
  coreState.busy = Boolean(busy);
  const send = $("core-send");
  const enh = $("core-enhance");
  const cancel = $("core-cancel");
  if (send) send.disabled = coreState.busy;
  if (enh) enh.disabled = coreState.busy;
  if (cancel) cancel.disabled = !coreState.busy;
  if (label) $("core-status").textContent = label;
}

async function refreshCoreStatus() {
  const meta = $("core-meta");
  const status = $("core-status");
  try {
    const st = await window.avaDesktop.coreStatus();
    if (Array.isArray(st.providers) && st.providers.length) {
      providers = [
        ...providers.filter((p) => !st.providers.some((x) => x.id === p.id)),
        ...st.providers,
      ];
      const enhanceList = (st.providers || []).filter((p) => p.id !== "ollama");
      if (enhanceList.length) {
        const host = $("core-providers");
        if (host) {
          const prev = providers;
          providers = enhanceList;
          renderProviders("core-providers", "core");
          providers = prev;
        }
      }
    } else {
      renderProviders("core-providers", "core");
    }
    const sid = coreState.sessionId
      ? ` · session ${coreState.sessionId.slice(0, 8)}…`
      : "";
    if (meta) {
      if (st.remote) {
        meta.textContent = st.ok
          ? `Core via Ava-linux · ${st.model || "ava-ivy"} @ ${st.baseUrl || lastBrainUrl}${sid}`
          : `Ava-linux core unreachable · ${st.detail || "down"} — check Settings → Connection`;
      } else if (st.persona || !st.direct) {
        meta.textContent = st.ok
          ? `Ava ready · ${st.model || "llama3.2"} @ ${st.baseUrl || "http://127.0.0.1:8787"} (persona)${sid}`
          : `Ava origin unreachable · ${st.detail || "down"}`;
      } else {
        meta.textContent = st.ok
          ? `Ollama ready · ${st.model || "llama3.2"} @ ${st.baseUrl || "local"} (direct)${sid}`
          : `Ollama down · ${st.detail || "unreachable"} — start ollama`;
      }
    }
    if (status && !coreState.busy) {
      status.textContent = st.ok
        ? `ready · ${st.model || "?"} · ${st.persona ? "persona" : "direct"}`
        : `status · ${st.detail || "fail"}`;
    }
  } catch (err) {
    if (meta) meta.textContent = String(err.message || err);
  }
}

async function sendCoreChat() {
  const draft = ($("core-draft").value || "").trim();
  if (!draft) {
    $("core-status").textContent = "type a message first";
    return;
  }
  if (coreState.busy) return;

  const prior = coreState.messages.slice();
  coreState.messages = [...prior, { role: "user", content: draft }];
  coreState.pending = true;
  coreState.pendingLabel = "0s";
  $("core-draft").value = "";
  renderCoreHistory();

  const started = Date.now();
  stopCoreTick();
  coreState.pending = true;
  setCoreBusy(true, "Ava is typing…");
  coreTick = setInterval(() => {
    const sec = Math.round((Date.now() - started) / 1000);
    coreState.pendingLabel = `${sec}s`;
    $("core-status").textContent = `Ava is typing… ${sec}s`;
    renderCoreHistory();
  }, 1000);

  try {
    const res = await window.avaDesktop.coreChat({
      text: draft,
      messages: prior,
      sessionId: coreState.sessionId,
      save: true,
    });
    stopCoreTick();
    if (!res?.ok) {
      // keep the user message; show failure
      coreState.messages = prior.concat([{ role: "user", content: draft }]);
      renderCoreHistory();
      $("core-status").textContent = `fail · ${res?.detail || "unknown"} · ${res?.ms ? `${res.ms}ms` : ""}`;
      return;
    }
    coreState.sessionId = res.sessionId || coreState.sessionId;
    coreState.lastQuestion = draft;
    coreState.lastAnswer = res.reply || "";
    coreState.messages = Array.isArray(res.messages)
      ? res.messages
      : [
          ...prior,
          { role: "user", content: draft },
          { role: "assistant", content: res.reply || "" },
        ];
    renderCoreHistory();
    appendResponseLog("core", {
      kind: "core",
      text: `You: ${draft}\n\nAva: ${res.reply || ""}`,
      provider: res.model || "ollama",
      via: res.direct ? "ollama-persona" : "origin",
      meta: res.ms ? `${res.ms}ms` : "",
    });
    $("core-status").textContent = `ok · ${res.model || "ollama"} · ${res.ms || "?"}ms · ${res.saved ? "saved" : "unsaved"} · ${res.direct ? "persona-fallback" : "persona"}`;
    refreshCoreStatus();
  } catch (err) {
    stopCoreTick();
    coreState.messages = prior.concat([{ role: "user", content: draft }]);
    renderCoreHistory();
    $("core-status").textContent = String(err.message || err);
  } finally {
    stopCoreTick();
    setCoreBusy(false);
    renderCoreHistory();
  }
}

async function cancelCoreChat() {
  $("core-status").textContent = "cancelling…";
  try {
    await window.avaDesktop.coreCancel();
  } catch {
    /* ignore */
  }
}

$("core-cancel")?.addEventListener("click", () => cancelCoreChat());

async function enhanceCoreReply() {
  if (!coreState.lastAnswer) {
    $("core-status").textContent = "send a turn first — nothing to enhance";
    return;
  }
  if (coreState.busy) return;
  const provider = providerSel.core || "dream";
  setCoreBusy(true, `enhancing via ${provider}…`);
  $("core-enhance-out").classList.remove("show");
  try {
    const res = await window.avaDesktop.coreEnhance({
      draft: coreState.lastAnswer,
      context: coreContextForEnhance(),
      provider,
      sessionId: coreState.sessionId,
      save: true,
    });
    if (!res?.ok) {
      $("core-status").textContent = `enhance fail · ${res?.detail || "?"}`;
      return;
    }
    coreState.enhanceText = res.text || "";
    coreState.enhanceProvider = res.provider || provider;
    const out = $("core-enhance-out");
    out.classList.add("show");
    out.textContent = `── ${res.provider || provider} · ${res.via || ""}\n${res.text || ""}`;
    appendResponseLog("core", {
      kind: "enhance",
      text: res.text || "",
      provider: res.provider || provider,
      via: res.via || "",
    });
    $("core-status").textContent = `enhanced · ${res.provider || provider}`;
  } catch (err) {
    $("core-status").textContent = String(err.message || err);
  } finally {
    setCoreBusy(false);
  }
}

function applyCoreEnhance() {
  if (!coreState.enhanceText) {
    $("core-status").textContent = "run Enhance first";
    return;
  }
  // Replace last assistant message with enhanced text
  for (let i = coreState.messages.length - 1; i >= 0; i--) {
    if (coreState.messages[i].role === "assistant") {
      coreState.messages[i] = {
        role: "assistant",
        content: coreState.enhanceText,
      };
      break;
    }
  }
  coreState.lastAnswer = coreState.enhanceText;
  renderCoreHistory();
  $("core-status").textContent = `applied · ${coreState.enhanceProvider || "enhance"} as Ava reply (local view)`;
}

async function markCoreGold(useEnhance) {
  const question = coreState.lastQuestion;
  const answer = useEnhance && coreState.enhanceText
    ? coreState.enhanceText
    : coreState.lastAnswer;
  if (!question || !answer) {
    $("core-status").textContent = "need a completed turn to mark gold";
    return;
  }
  try {
    const res = await window.avaDesktop.coreGold({
      question,
      answer,
      sessionId: coreState.sessionId,
      provider: useEnhance ? coreState.enhanceProvider || "enhance" : "ollama",
    });
    $("core-status").textContent = res?.ok
      ? `gold saved · ${useEnhance ? "enhance pair" : "last turn"}`
      : `gold fail · ${res?.detail || "?"}`;
  } catch (err) {
    $("core-status").textContent = String(err.message || err);
  }
}

function clearCoreChat() {
  coreState.messages = [];
  coreState.lastQuestion = "";
  coreState.lastAnswer = "";
  coreState.enhanceText = "";
  coreState.enhanceProvider = "";
  $("core-enhance-out").classList.remove("show");
  $("core-enhance-out").textContent = "";
  renderCoreHistory();
  $("core-status").textContent = "cleared (session kept)";
}

function newCoreSession() {
  coreState.sessionId = null;
  clearCoreChat();
  $("core-status").textContent = "new session";
  refreshCoreStatus();
}

$("core-send")?.addEventListener("click", () => sendCoreChat());
$("core-draft")?.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
    ev.preventDefault();
    sendCoreChat();
  }
});
$("core-refresh-status")?.addEventListener("click", () => refreshCoreStatus());
$("core-clear")?.addEventListener("click", () => clearCoreChat());
$("core-new-session")?.addEventListener("click", () => newCoreSession());
$("core-enhance")?.addEventListener("click", () => enhanceCoreReply());
$("core-enhance-apply")?.addEventListener("click", () => applyCoreEnhance());
$("core-mark-gold")?.addEventListener("click", () => markCoreGold(false));
$("core-enhance-gold")?.addEventListener("click", () => markCoreGold(true));

function feedbackSelected() {
  return (feedbackState.items || []).find(
    (x) => String(x.id) === String(feedbackState.selectedId),
  );
}

function feedbackProcessedStamp(elapsedSec = 0) {
  const when = new Date().toLocaleString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
  return `Feedback was fully processed on ${when} ${elapsedSec} Seconds ago`;
}

function updateFeedbackSelMeta() {
  const el = $("feedback-sel-meta");
  if (!el) return;
  const d = feedbackState.discordSel;
  const s = feedbackState.slackSel;
  const bits = [];
  if (d?.id) bits.push(`Discord ${d.self ? "ava" : "msg"} …${String(d.id).slice(-6)}`);
  if (s?.id) bits.push(`Slack ${s.self ? "ava" : "msg"} ${s.id}`);
  el.textContent = bits.length ? bits.join(" · ") : "No message selected";
}

function renderFeedbackQueue() {
  const host = $("feedback-queue");
  if (!host) return;
  const rows = feedbackState.items || [];
  if (!rows.length) {
    host.innerHTML = "<div class='msg meta'>(queue empty or unavailable)</div>";
    return;
  }
  host.innerHTML = rows
    .map((fb) => {
      const id = String(fb.id || "");
      const who = escapeHtml(fb.minecraft_username || fb.player || fb.author || "?");
      const hostName = escapeHtml(fb.server_name || fb.server_id || "");
      const st = escapeHtml(fb.status || "");
      const msg = escapeHtml(String(fb.message || fb.body || "").slice(0, 500));
      const active = id && id === String(feedbackState.selectedId) ? " active" : "";
      return `<button type="button" class="feedback-item${active}" data-id="${escapeHtml(id)}"><div class="who">${who}</div><div class="meta">${hostName}${st ? ` · ${st}` : ""} · ${escapeHtml(id.slice(0, 8))}…</div><div class="body">${msg}</div></button>`;
    })
    .join("");
  host.querySelectorAll(".feedback-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      feedbackState.selectedId = btn.dataset.id;
      renderFeedbackQueue();
      $("feedback-status").textContent = `selected ${btn.dataset.id}`;
    });
  });
}

function fillFeedbackTemplates(templates) {
  const sel = $("feedback-template");
  if (!sel) return;
  feedbackState.templates = templates || [];
  sel.innerHTML = "";
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = "(pick a template)";
  sel.appendChild(blank);
  for (const t of feedbackState.templates) {
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = t.label || t.id;
    sel.appendChild(opt);
  }
  const quick = $("feedback-quick-templates");
  if (quick) {
    quick.innerHTML = (feedbackState.templates || [])
      .map(
        (t) =>
          `<button type="button" data-fb-tpl="${escapeHtml(t.id)}">${escapeHtml(t.label || t.id)}</button>`,
      )
      .join("");
    quick.querySelectorAll("button[data-fb-tpl]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const t = (feedbackState.templates || []).find((x) => x.id === btn.dataset.fbTpl);
        if (!t?.text) return;
        $("feedback-draft").value = t.text;
        autosizeDraft($("feedback-draft"));
        draftReadyExact.feedback = false;
        if ($("feedback-template")) $("feedback-template").value = t.id;
        $("feedback-status").textContent = `template · ${t.label}`;
      });
    });
  }
}

async function refreshFeedbackQueue() {
  const status = $("feedback-status-filter")?.value || "queued";
  $("feedback-status").textContent = `loading ${status}…`;
  try {
    const data = await window.avaDesktop.feedbackList({ status, limit: 50 });
    if (!data?.ok) {
      feedbackState.items = [];
      renderFeedbackQueue();
      $("feedback-meta").textContent = data?.detail || "queue unavailable";
      $("feedback-status").textContent = data?.detail || "fail";
      return;
    }
    feedbackState.items = data.feedback || [];
    renderFeedbackQueue();
    $("feedback-meta").textContent = `${feedbackState.items.length} ${status} · dual post → Discord #development + Slack #feedback`;
    $("feedback-status").textContent = `queue · ${feedbackState.items.length} ${status}`;
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

async function refreshFeedbackChannels() {
  $("feedback-status").textContent = "loading channel peeks…";
  try {
    const [d, s] = await Promise.all([
      window.avaDesktop.history({
        surface: "discord",
        channelId: feedbackState.targets.discord,
        limit: 40,
      }),
      window.avaDesktop.history({
        surface: "slack",
        channelId: feedbackState.targets.slack,
        limit: 40,
      }),
    ]);
    feedbackState._discordMsgs = d.messages || [];
    feedbackState._slackMsgs = s.messages || [];
    bindFeedbackDiscordHist();
    bindFeedbackSlackHist();
    updateFeedbackSelMeta();
    $("feedback-status").textContent = `channels · discord ${d.messages?.length || 0} · slack ${s.messages?.length || 0}`;
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

function bindFeedbackDiscordHist() {
  renderHistory($("feedback-discord-hist"), feedbackState._discordMsgs || [], {
    replyId: feedbackState.discordSel?.id || null,
    surface: "feedback-discord",
    onPick: (pick) => {
      feedbackState.discordSel = pick;
      updateFeedbackSelMeta();
      bindFeedbackDiscordHist();
      $("feedback-status").textContent = `discord sel · …${String(pick.id).slice(-6)}${pick.self ? " (ava)" : ""}`;
    },
  });
}

function bindFeedbackSlackHist() {
  renderHistory($("feedback-slack-hist"), feedbackState._slackMsgs || [], {
    replyId: feedbackState.slackSel?.id || null,
    surface: "feedback-slack",
    onPick: (pick) => {
      feedbackState.slackSel = pick;
      updateFeedbackSelMeta();
      bindFeedbackSlackHist();
      $("feedback-status").textContent = `slack sel · ${pick.id}${pick.self ? " (ava)" : ""}`;
    },
  });
}

async function refreshFeedbackPage() {
  await refreshFeedbackQueue();
  await refreshFeedbackChannels();
}

function loadFeedbackSelectedToDraft({ staffReply = false } = {}) {
  const fb = feedbackSelected();
  if (!fb) {
    $("feedback-status").textContent = "select a queue item first";
    return;
  }
  const who = fb.minecraft_username || fb.player || "?";
  const msg = String(fb.message || fb.body || "").trim();
  const body = staffReply
    ? `**Feedback reply** — ${who}\n\n> ${msg.replace(/\n/g, "\n> ")}\n\n`
    : `**Feedback** from **${who}** (${fb.server_name || fb.server_id || "server"})\n${msg}\n\n_id ${fb.id}_`;
  $("feedback-draft").value = body;
  autosizeDraft($("feedback-draft"));
  draftReadyExact.feedback = true;
  $("feedback-status").textContent = staffReply
    ? `draft staff reply · ${who}`
    : `loaded ${who} into draft`;
}

async function ackFeedbackSelected() {
  const fb = feedbackSelected();
  if (!fb?.id) {
    $("feedback-status").textContent = "select a queue item to ack";
    return;
  }
  const note = ($("feedback-draft").value || "").trim().slice(0, 500) ||
    `Acked from Ava Ivy Feedback page`;
  $("feedback-status").textContent = "acking…";
  try {
    const r = await window.avaDesktop.feedbackAck({ id: fb.id, note });
    appendResponseLog("feedback", {
      kind: "ack",
      text: note,
      provider: "exact",
      via: "governance",
      meta: `id ${fb.id}`,
    });
    $("feedback-status").textContent = r?.ok
      ? `acked · ${fb.id}`
      : `ack fail · ${r?.detail || "?"}`;
    await refreshFeedbackQueue();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

async function ackAllVisibleFeedback() {
  const rows = (feedbackState.items || []).filter((x) => x?.id);
  if (!rows.length) {
    $("feedback-status").textContent = "nothing to ack";
    return;
  }
  if (!confirm(`Ack all ${rows.length} visible queue items?`)) return;
  $("feedback-status").textContent = `acking ${rows.length}…`;
  let ok = 0;
  for (const fb of rows) {
    try {
      const r = await window.avaDesktop.feedbackAck({
        id: fb.id,
        note: "Bulk ack from Ava Ivy Feedback",
      });
      if (r?.ok) ok += 1;
    } catch {
      /* continue */
    }
  }
  appendResponseLog("feedback", {
    kind: "ack-all",
    text: `Acked ${ok}/${rows.length}`,
    provider: "exact",
    via: "bulk",
    meta: `${ok} ok`,
  });
  $("feedback-status").textContent = `acked ${ok}/${rows.length}`;
  await refreshFeedbackQueue();
}

async function processFeedbackNextItem() {
  if (feedbackState.busy) return;
  feedbackState.busy = true;
  $("feedback-status").textContent = "processing next…";
  try {
    const r = await window.avaDesktop.feedbackProcessNext();
    if (r?.empty) {
      $("feedback-status").textContent = "queue empty";
      return;
    }
    if (!r?.ok) {
      $("feedback-status").textContent = `process fail · ${r?.detail || "?"}`;
      return;
    }
    const fb = r.feedback || r.item || null;
    if (fb) {
      feedbackState.selectedId = fb.id;
      const who = fb.minecraft_username || "?";
      const msg = String(fb.message || "").trim();
      $("feedback-draft").value = `**Feedback** from **${who}**\n${msg}\n\n_id ${fb.id}_`;
      autosizeDraft($("feedback-draft"));
      draftReadyExact.feedback = true;
      appendResponseLog("feedback", {
        kind: "process",
        text: $("feedback-draft").value,
        provider: "exact",
        via: "process-next",
        meta: `id ${fb.id}`,
      });
    }
    $("feedback-status").textContent = fb
      ? `processed · ${fb.id} — review draft, then dual post or ack`
      : "processed";
    await refreshFeedbackQueue();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  } finally {
    feedbackState.busy = false;
  }
}

async function drainFeedbackQueue(times = 5) {
  for (let i = 0; i < times; i++) {
    await processFeedbackNextItem();
    if (($("feedback-status").textContent || "").includes("queue empty")) break;
  }
}

async function dualPostFeedbackDraft() {
  const text = ($("feedback-draft").value || "").trim();
  if (!text) {
    $("feedback-status").textContent = "type a message first";
    return;
  }
  if (surfaceBusy.feedback) {
    $("feedback-status").textContent = "already posting";
    return;
  }
  const provider = providerSel.feedback || "exact";
  const rewrite = provider !== "exact" && !draftReadyExact.feedback;
  surfaceBusy.feedback = true;
  $("feedback-status").textContent = rewrite
    ? `dual posting via ${provider}…`
    : "dual posting exact → Discord #development + Slack #feedback…";
  try {
    const r = await window.avaDesktop.feedbackDualPost({
      text,
      rewrite,
      provider: rewrite ? provider : "exact",
      includeDevFeed: Boolean($("feedback-also-devfeed")?.checked),
    });
    draftReadyExact.feedback = false;
    const lines = (r.results || [])
      .map((x) => `${x.ok ? "ok" : "fail"} · ${x.label}${x.id ? ` · ${x.id}` : ""}${x.detail ? ` · ${x.detail}` : ""}`)
      .join("\n");
    appendResponseLog("feedback", {
      kind: "dual-post",
      text,
      provider: rewrite ? provider : "exact",
      via: "dual",
      meta: `${r.posted || 0} posted`,
    });
    $("feedback-status").textContent = r?.ok
      ? `posted ${r.posted}/${(r.results || []).length}\n${lines}`
      : `dual post fail\n${lines || r?.detail || "?"}`;
    await refreshFeedbackChannels();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  } finally {
    surfaceBusy.feedback = false;
  }
}

async function deleteFeedbackDiscordSelected() {
  const pick = feedbackState.discordSel;
  if (!pick?.id) {
    $("feedback-status").textContent = "select a Discord message first";
    return;
  }
  if (!confirm(`Delete Discord message …${String(pick.id).slice(-6)}?`)) return;
  $("feedback-status").textContent = "deleting discord…";
  try {
    const r = await window.avaDesktop.feedbackDeleteDiscord({ messageId: pick.id });
    appendResponseLog("feedback", {
      kind: "delete",
      text: pick.text || "",
      provider: "exact",
      via: "discord-delete",
      meta: r?.ok ? `ok ${pick.id}` : r?.detail || "fail",
    });
    feedbackState.discordSel = null;
    updateFeedbackSelMeta();
    $("feedback-status").textContent = r?.ok ? `deleted discord · ${pick.id}` : `delete fail · ${r?.detail || "?"}`;
    await refreshFeedbackChannels();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

async function deleteFeedbackSlackSelected() {
  const pick = feedbackState.slackSel;
  if (!pick?.id) {
    $("feedback-status").textContent = "select a Slack message first";
    return;
  }
  if (!confirm(`Delete Slack message ${pick.id}?`)) return;
  $("feedback-status").textContent = "deleting slack…";
  try {
    const r = await window.avaDesktop.feedbackDeleteSlack({ messageTs: pick.id });
    appendResponseLog("feedback", {
      kind: "delete",
      text: pick.text || "",
      provider: "exact",
      via: "slack-delete",
      meta: r?.ok ? `ok ${pick.id}` : r?.detail || "fail",
    });
    feedbackState.slackSel = null;
    updateFeedbackSelMeta();
    $("feedback-status").textContent = r?.ok ? `deleted slack · ${pick.id}` : `delete fail · ${r?.detail || "?"}`;
    await refreshFeedbackChannels();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

async function clearFeedbackDiscordOwn() {
  if (!confirm("Delete Ava's own messages in Discord #development (capped)? This cannot be undone.")) return;
  $("feedback-status").textContent = "clearing discord ava msgs…";
  try {
    const r = await window.avaDesktop.feedbackClearDiscord({});
    appendResponseLog("feedback", {
      kind: "clear",
      text: `Cleared Discord Ava msgs: ${r?.deleted || 0}`,
      provider: "exact",
      via: "clear-discord",
      meta: `deleted ${r?.deleted || 0} failed ${r?.failed || 0}`,
    });
    $("feedback-status").textContent = `discord clear · deleted ${r?.deleted || 0} · failed ${r?.failed || 0}`;
    await refreshFeedbackChannels();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

async function clearFeedbackSlackOwn() {
  if (!confirm("Delete Ava's own messages in Slack #feedback (capped)? This cannot be undone.")) return;
  $("feedback-status").textContent = "clearing slack ava msgs…";
  try {
    const r = await window.avaDesktop.feedbackClearSlack({});
    appendResponseLog("feedback", {
      kind: "clear",
      text: `Cleared Slack Ava msgs: ${r?.deleted || 0}`,
      provider: "exact",
      via: "clear-slack",
      meta: `deleted ${r?.deleted || 0} failed ${r?.failed || 0}`,
    });
    $("feedback-status").textContent = `slack clear · deleted ${r?.deleted || 0} · failed ${r?.failed || 0}`;
    await refreshFeedbackChannels();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  }
}

async function clearAllFeedbackAndStamp() {
  const clearDiscord = Boolean($("feedback-clear-discord-opt")?.checked);
  const clearSlack = Boolean($("feedback-clear-slack-opt")?.checked);
  if (!clearDiscord && !clearSlack) {
    $("feedback-status").textContent = "tick Discord and/or Slack to clear";
    return;
  }
  const bits = [
    clearDiscord ? "Discord #development Ava msgs" : null,
    clearSlack ? "Slack #feedback Ava msgs" : null,
  ]
    .filter(Boolean)
    .join(" + ");
  if (
    !confirm(
      `Clear all (${bits}), then dual-post:\n“Feedback was fully processed on TIMESTAMP Seconds ago”?\n\nCannot be undone.`,
    )
  ) {
    return;
  }
  if (surfaceBusy.feedback) {
    $("feedback-status").textContent = "busy";
    return;
  }
  surfaceBusy.feedback = true;
  $("feedback-status").textContent = "clear all + stamp…";
  try {
    const r = await window.avaDesktop.feedbackClearAll({
      clearDiscord,
      clearSlack,
      alsoDevFeed: Boolean($("feedback-also-devfeed")?.checked),
    });
    const dDel = r?.discord?.deleted ?? 0;
    const sDel = r?.slack?.deleted ?? 0;
    appendResponseLog("feedback", {
      kind: "clear-all",
      text: r?.text || feedbackProcessedStamp(r?.elapsedSec || 0),
      provider: "exact",
      via: "clear-all-stamp",
      meta: `discord −${dDel} · slack −${sDel} · stamp ${r?.ok ? "ok" : "fail"}`,
    });
    $("feedback-draft").value = r?.text || feedbackProcessedStamp(0);
    autosizeDraft($("feedback-draft"));
    draftReadyExact.feedback = true;
    $("feedback-status").textContent = [
      `clear-all · discord −${dDel} · slack −${sDel}`,
      r?.text || "",
      r?.stamp?.ok ? "stamp posted" : `stamp · ${r?.stamp?.detail || r?.detail || "fail"}`,
    ].join("\n");
    await refreshFeedbackChannels();
  } catch (err) {
    $("feedback-status").textContent = String(err.message || err);
  } finally {
    surfaceBusy.feedback = false;
  }
}

async function postFeedbackStampOnly() {
  const text = feedbackProcessedStamp(0);
  $("feedback-draft").value = text;
  autosizeDraft($("feedback-draft"));
  draftReadyExact.feedback = true;
  await dualPostFeedbackDraft();
}

$("feedback-refresh-queue")?.addEventListener("click", () => refreshFeedbackQueue());
$("feedback-refresh-channels")?.addEventListener("click", () => refreshFeedbackChannels());
$("feedback-refresh-all")?.addEventListener("click", () => refreshFeedbackPage());
$("feedback-process-next")?.addEventListener("click", () => processFeedbackNextItem());
$("feedback-process-drain")?.addEventListener("click", () => drainFeedbackQueue(5));
$("feedback-status-filter")?.addEventListener("change", () => refreshFeedbackQueue());
$("feedback-load-selected")?.addEventListener("click", () => loadFeedbackSelectedToDraft());
$("feedback-draft-from-item")?.addEventListener("click", () =>
  loadFeedbackSelectedToDraft({ staffReply: true }),
);
$("feedback-ack-selected")?.addEventListener("click", () => ackFeedbackSelected());
$("feedback-ack-all-queued")?.addEventListener("click", () => ackAllVisibleFeedback());
$("feedback-select-first")?.addEventListener("click", () => {
  const first = feedbackState.items?.[0];
  if (!first?.id) {
    $("feedback-status").textContent = "queue empty";
    return;
  }
  feedbackState.selectedId = first.id;
  renderFeedbackQueue();
  $("feedback-status").textContent = `selected ${first.id}`;
});
$("feedback-deselect")?.addEventListener("click", () => {
  feedbackState.selectedId = null;
  renderFeedbackQueue();
  $("feedback-status").textContent = "deselected";
});
$("feedback-copy-item")?.addEventListener("click", async () => {
  const fb = feedbackSelected();
  if (!fb) {
    $("feedback-status").textContent = "select a queue item first";
    return;
  }
  const text = `${fb.minecraft_username || "?"} · ${fb.message || fb.body || ""}`;
  try {
    await navigator.clipboard.writeText(text);
    $("feedback-status").textContent = "copied item";
  } catch {
    $("feedback-status").textContent = "clipboard failed";
  }
});
$("feedback-delete-discord")?.addEventListener("click", () => deleteFeedbackDiscordSelected());
$("feedback-delete-slack")?.addEventListener("click", () => deleteFeedbackSlackSelected());
$("feedback-clear-discord")?.addEventListener("click", () => clearFeedbackDiscordOwn());
$("feedback-clear-slack")?.addEventListener("click", () => clearFeedbackSlackOwn());
$("feedback-clear-all")?.addEventListener("click", () => clearAllFeedbackAndStamp());
$("feedback-clear-sel")?.addEventListener("click", () => {
  feedbackState.discordSel = null;
  feedbackState.slackSel = null;
  updateFeedbackSelMeta();
  bindFeedbackDiscordHist();
  bindFeedbackSlackHist();
  $("feedback-status").textContent = "selection cleared";
});
$("feedback-load-discord-sel")?.addEventListener("click", () => {
  const p = feedbackState.discordSel;
  if (!p?.id) {
    $("feedback-status").textContent = "select a Discord message";
    return;
  }
  $("feedback-draft").value = p.text || "";
  autosizeDraft($("feedback-draft"));
  draftReadyExact.feedback = true;
  $("feedback-status").textContent = "loaded discord → draft";
});
$("feedback-load-slack-sel")?.addEventListener("click", () => {
  const p = feedbackState.slackSel;
  if (!p?.id) {
    $("feedback-status").textContent = "select a Slack message";
    return;
  }
  $("feedback-draft").value = p.text || "";
  autosizeDraft($("feedback-draft"));
  draftReadyExact.feedback = true;
  $("feedback-status").textContent = "loaded slack → draft";
});
$("feedback-insert-stamp")?.addEventListener("click", () => {
  $("feedback-draft").value = feedbackProcessedStamp(0);
  autosizeDraft($("feedback-draft"));
  draftReadyExact.feedback = true;
  $("feedback-status").textContent = "inserted processed stamp";
});
$("feedback-insert-now")?.addEventListener("click", () => {
  const ta = $("feedback-draft");
  const stamp = new Date().toISOString();
  ta.value = `${ta.value || ""}${ta.value ? "\n" : ""}${stamp}`;
  autosizeDraft(ta);
  $("feedback-status").textContent = "inserted ISO timestamp";
});
$("feedback-insert-triage")?.addEventListener("click", () => {
  const t = (feedbackState.templates || []).find((x) => x.id === "triage");
  if (!t?.text) return;
  $("feedback-draft").value = t.text;
  autosizeDraft($("feedback-draft"));
  $("feedback-status").textContent = "inserted triage header";
});
$("feedback-insert-digest")?.addEventListener("click", () => {
  const t = (feedbackState.templates || []).find((x) => x.id === "digest");
  if (!t?.text) return;
  $("feedback-draft").value = t.text;
  autosizeDraft($("feedback-draft"));
  $("feedback-status").textContent = "inserted digest header";
});
$("feedback-append-nl")?.addEventListener("click", () => {
  const ta = $("feedback-draft");
  ta.value = `${ta.value || ""}\n\n`;
  autosizeDraft(ta);
});
$("feedback-uppercase")?.addEventListener("click", () => {
  const ta = $("feedback-draft");
  ta.value = String(ta.value || "").toUpperCase();
  autosizeDraft(ta);
});
$("feedback-trim")?.addEventListener("click", () => {
  const ta = $("feedback-draft");
  ta.value = String(ta.value || "").trim();
  autosizeDraft(ta);
});
$("feedback-copy-draft")?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("feedback-draft").value || "");
    $("feedback-status").textContent = "draft copied";
  } catch {
    $("feedback-status").textContent = "clipboard failed";
  }
});
$("feedback-post-stamp")?.addEventListener("click", () => postFeedbackStampOnly());
$("feedback-clear")?.addEventListener("click", () => {
  $("feedback-draft").value = "";
  draftReadyExact.feedback = false;
  autosizeDraft($("feedback-draft"));
  $("feedback-status").textContent = "cleared";
});
$("feedback-template")?.addEventListener("change", () => {
  const id = $("feedback-template").value;
  const t = (feedbackState.templates || []).find((x) => x.id === id);
  if (!t?.text) return;
  $("feedback-draft").value = t.text;
  autosizeDraft($("feedback-draft"));
  draftReadyExact.feedback = false;
  $("feedback-status").textContent = `template · ${t.label}`;
});
$("feedback-preview")?.addEventListener("click", () =>
  previewRewrite(
    "feedback",
    "feedback-draft",
    feedbackState.targets.discord,
    "feedback-status",
    null,
  ),
);
$("feedback-dual-post")?.addEventListener("click", () => dualPostFeedbackDraft());

$("conn-pill")?.addEventListener("click", () => {
  document.querySelector('.tab[data-page="settings"]')?.click();
});
$("conn-mode-local")?.addEventListener("change", () => applyConnectionPreset());
$("conn-mode-headless")?.addEventListener("change", () => applyConnectionPreset());
$("conn-via-lan")?.addEventListener("change", () => applyConnectionPreset());
$("conn-via-public")?.addEventListener("change", () => applyConnectionPreset());
$("conn-via-loopback")?.addEventListener("change", () => applyConnectionPreset());
$("conn-show-keys")?.addEventListener("change", () => {
  const show = Boolean($("conn-show-keys")?.checked);
  if ($("conn-operator-key")) $("conn-operator-key").type = show ? "text" : "password";
  if ($("conn-workstation-key")) $("conn-workstation-key").type = show ? "text" : "password";
});
$("conn-reset")?.addEventListener("click", () => applyConnectionPreset());
$("conn-test")?.addEventListener("click", () => testConnectionForm());
$("conn-save")?.addEventListener("click", () => saveConnectionForm());

function brainBaseUrl() {
  return String($("conn-brain")?.value || lastBrainUrl || "http://127.0.0.1:8787").replace(/\/$/, "");
}
function operatorHeaders() {
  const key = String($("conn-operator-key")?.value || "").trim();
  const h = { "Content-Type": "application/json" };
  if (key) {
    h["X-Ava-Operator-Key"] = key;
    h["X-RootMC-Dev-Key"] = key;
  }
  return h;
}
let shutdownAtMs = null;
function pad2(n) { return String(n).padStart(2, "0"); }
function fmtLeft(ms) {
  let s = Math.max(0, Math.floor(Number(ms) / 1000));
  const h = Math.floor(s / 3600); s %= 3600;
  const m = Math.floor(s / 60); const sec = s % 60;
  return `${pad2(h)}:${pad2(m)}:${pad2(sec)}`;
}
function paintShutdownCountdown() {
  const el = $("shutdown-countdown");
  if (!el) return;
  if (!shutdownAtMs) { el.value = "—"; return; }
  el.value = fmtLeft(shutdownAtMs - Date.now());
}
async function refreshShutdownTimer() {
  const st = $("shutdown-status");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/projected-shutdown`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      if (st) st.textContent = d?.detail || "unavailable";
      return;
    }
    shutdownAtMs = Number(d.atMs) || null;
    if ($("shutdown-time") && document.activeElement !== $("shutdown-time")) {
      $("shutdown-time").value = d.timeHst || "";
    }
    paintShutdownCountdown();
    if (st) st.textContent = `Target ${d.label} · next ${d.atIso}` +
      (d.averageLabel ? ` · rolling avg ${d.averageLabel}` : "") +
      (d.sampleDays ? ` · ${d.sampleDays} nights` : "");
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function saveShutdownTimer() {
  const st = $("shutdown-status");
  const time = $("shutdown-time")?.value;
  if (!time) {
    if (st) st.textContent = "pick a time first";
    return;
  }
  if (st) st.textContent = "saving…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/projected-shutdown`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({ time, updatedBy: "desktop-panel" }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || d.hint || `HTTP ${res.status}`;
      return;
    }
    shutdownAtMs = Number(d.atMs) || null;
    paintShutdownCountdown();
    if (st) st.textContent = `Saved ${d.label} · countdown live on status + solar`;
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
$("shutdown-refresh")?.addEventListener("click", () => refreshShutdownTimer());
$("shutdown-save")?.addEventListener("click", () => saveShutdownTimer());
async function useAverageShutdown() {
  const st = $("shutdown-status");
  if (st) st.textContent = "switching to average…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/projected-shutdown`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({ useAverage: true, updatedBy: "desktop-panel" }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || `HTTP ${res.status}`;
      return;
    }
    await refreshShutdownTimer();
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
$("shutdown-use-avg")?.addEventListener("click", () => useAverageShutdown());
setInterval(paintShutdownCountdown, 1000);

async function refreshStartTimer() {
  const st = $("start-status");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/projected-start`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      if (st) st.textContent = d?.detail || "unavailable";
      return;
    }
    if ($("start-time") && document.activeElement !== $("start-time")) {
      $("start-time").value = d.timeHst || "";
    }
    if ($("start-source")) {
      $("start-source").value =
        d.source === "manual"
          ? "manual override"
          : d.source === "average"
            ? `average (${d.sampleDays || 0} days)`
            : "default 10:00";
    }
    if (st) {
      st.textContent = `${d.label} · ${d.note || d.source}` +
        (d.averageLabel ? ` · rolling avg ${d.averageLabel}` : "");
    }
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function saveStartTimer() {
  const st = $("start-status");
  const time = $("start-time")?.value;
  if (!time) {
    if (st) st.textContent = "pick a time first";
    return;
  }
  if (st) st.textContent = "saving…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/projected-start`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({ time, updatedBy: "desktop-panel" }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || d.hint || `HTTP ${res.status}`;
      return;
    }
    await refreshStartTimer();
    if (st) st.textContent = `Locked to ${d.label} (manual) · solar + status updated`;
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function useAverageStart() {
  const st = $("start-status");
  if (st) st.textContent = "switching to average…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/projected-start`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({ useAverage: true, updatedBy: "desktop-panel" }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || `HTTP ${res.status}`;
      return;
    }
    await refreshStartTimer();
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
$("start-refresh")?.addEventListener("click", () => refreshStartTimer());
$("start-save")?.addEventListener("click", () => saveStartTimer());
$("start-use-avg")?.addEventListener("click", () => useAverageStart());

async function refreshOpsBanner() {
  const st = $("ops-banner-status");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/ops-schedule-banner`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      if (st) st.textContent = d?.detail || "unavailable";
      return;
    }
    if ($("ops-enabled")) $("ops-enabled").checked = Boolean(d.enabled);
    if ($("ops-auto-low")) $("ops-auto-low").checked = d.autoLowBank !== false;
    if ($("ops-show-start")) $("ops-show-start").checked = d.showStart !== false;
    if ($("ops-show-stop")) $("ops-show-stop").checked = d.showShutdown !== false;
    if (st) {
      st.textContent = d.show
        ? `${d.title || "showing"} · ${d.detail || ""}`
        : "banner off";
    }
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function saveOpsBanner() {
  const st = $("ops-banner-status");
  if (st) st.textContent = "saving…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/ops-schedule-banner`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({
        enabled: Boolean($("ops-enabled")?.checked),
        autoLowBank: Boolean($("ops-auto-low")?.checked),
        showStart: Boolean($("ops-show-start")?.checked),
        showShutdown: Boolean($("ops-show-stop")?.checked),
      }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || `HTTP ${res.status}`;
      return;
    }
    await refreshOpsBanner();
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
$("ops-banner-refresh")?.addEventListener("click", () => refreshOpsBanner());
$("ops-banner-save")?.addEventListener("click", () => saveOpsBanner());

async function refreshGovernance() {
  const st = $("gov-status");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/governance`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      if (st) st.textContent = d?.detail || "unavailable";
      return;
    }
    if ($("gov-community")) $("gov-community").checked = Boolean(d.community_governance);
    if ($("gov-self-update")) $("gov-self-update").checked = Boolean(d.self_update);
    if ($("gov-min-free") && document.activeElement !== $("gov-min-free")) {
      $("gov-min-free").value = String(d.cursor_min_free_pct ?? 25);
    }
    if ($("gov-free-now") && document.activeElement !== $("gov-free-now")) {
      $("gov-free-now").value = d.cursor_context_free_pct == null ? "" : String(d.cursor_context_free_pct);
    }
    const last = d.last || {};
    const passed = Array.isArray(last.passed) ? last.passed.length : 0;
    const people = last.people ?? 0;
    if (st) {
      st.textContent = [
        d.community_governance ? "governance on" : "governance off",
        d.self_update ? "self-update on" : "self-update off",
        `cursor ${d.cursor_gate || "?"}`,
        last.source ? `last ${last.source}: ${people} people, ${passed} passed` : "no tally yet",
      ].join(" · ");
    }
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function saveGovernance(runNow) {
  const st = $("gov-status");
  if (st) st.textContent = runNow ? "tally…" : "saving…";
  const freeRaw = String($("gov-free-now")?.value || "").trim();
  const body = {
    community_governance: Boolean($("gov-community")?.checked),
    self_update: Boolean($("gov-self-update")?.checked),
    cursor_min_free_pct: Number($("gov-min-free")?.value || 25),
    cursor_context_free_pct: freeRaw === "" ? null : Number(freeRaw),
    run_now: Boolean(runNow),
  };
  try {
    const res = await fetch(`${brainBaseUrl()}/api/governance`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify(body),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || `HTTP ${res.status}`;
      return;
    }
    await refreshGovernance();
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
$("gov-refresh")?.addEventListener("click", () => refreshGovernance());
$("gov-save")?.addEventListener("click", () => saveGovernance(false));
$("gov-run")?.addEventListener("click", () => saveGovernance(true));

function ledgerUsdField(id, value) {
  const el = $(id);
  if (!el || document.activeElement === el) return;
  el.value = value == null || value === "" ? "" : String(value);
}
function ledgerLine(bal) {
  if (!bal) return "";
  const bits = [bal.label || "?"];
  if (bal.kind === "percent_pool") {
    bits.push(bal.used_pct == null ? "used unknown" : `${bal.used_pct}% used`);
    bits.push(bal.remaining_pct == null ? "remaining unknown" : `${bal.remaining_pct}% left`);
  } else {
    bits.push(bal.starting_usd == null ? "no seed" : `seed $${Number(bal.starting_usd).toFixed(2)}`);
    bits.push(bal.remaining_usd == null ? "remaining unknown" : `~$${Number(bal.remaining_usd).toFixed(2)} left`);
  }
  bits.push(bal.key_present ? "key on disk" : "no key");
  bits.push(bal.spend_allowed ? "spend on" : "spend off");
  return bits.join(" · ");
}
async function refreshLedger() {
  const st = $("ledger-status");
  const prices = $("ledger-prices");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/ledger`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      if (st) st.textContent = d?.detail || "unavailable";
      return;
    }
    if ($("ledger-capture")) $("ledger-capture").checked = Boolean(d.capture_enabled);
    if ($("ledger-spend-master")) $("ledger-spend-master").checked = Boolean(d.spend_master);
    const acc = d.accounts || {};
    const bal = d.balances || {};
    const paintSpend = (id, on) => {
      const el = $(id);
      if (!el || document.activeElement === el) return;
      el.checked = Boolean(on);
    };
    paintSpend("ledger-cursor-spend", acc.cursor?.spend_allowed);
    paintSpend("ledger-xai-spend", acc.xai?.spend_allowed);
    paintSpend("ledger-openai-spend", acc.openai?.spend_allowed);
    paintSpend("ledger-gemini-spend", acc.gemini?.spend_allowed);
    ledgerUsdField("ledger-cursor-used", acc.cursor?.used_pct);
    ledgerUsdField("ledger-xai-usd", acc.xai?.starting_usd);
    ledgerUsdField("ledger-openai-usd", acc.openai?.starting_usd);
    ledgerUsdField("ledger-gemini-usd", acc.gemini?.starting_usd);
    const auto = d.auto || {};
    const last = d.last || {};
    if (st) {
      st.textContent = [
        d.capture_enabled ? "price capture on" : "price capture off",
        d.spend_master ? "spend master on" : "spend master off",
        ledgerLine(bal.cursor),
        ledgerLine(bal.xai),
        ledgerLine(bal.openai),
        ledgerLine(bal.gemini),
        auto.typical_range_usd
          ? `Auto turn on Grok 4.6 ~$${auto.typical_range_usd[0]}–$${auto.typical_range_usd[1]}`
          : "",
        d.defaults?.xai ? `default grok ${d.defaults.xai}` : "",
        last.source ? `last ${last.source}` : "no fetch yet",
      ].filter(Boolean).join("\n");
    }
    if (prices) {
      const rows = Array.isArray(d.prices) ? d.prices.slice(0, 24) : [];
      prices.textContent = rows
        .map((r) => {
          const inn = r.input_per_m == null ? "—" : `$${r.input_per_m}`;
          const out = r.output_per_m == null ? "—" : `$${r.output_per_m}`;
          return `${r.vendor} ${r.model}  in ${inn} / out ${out}  per 1M`;
        })
        .join("\n");
    }
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function saveLedger(refreshNow) {
  const st = $("ledger-status");
  if (st) st.textContent = refreshNow ? "fetching prices…" : "saving…";
  const numOrNull = (id) => {
    const raw = String($(id)?.value || "").trim();
    if (raw === "") return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  };
  const body = {
    capture_enabled: Boolean($("ledger-capture")?.checked),
    spend_master: Boolean($("ledger-spend-master")?.checked),
    accounts: {
      cursor: { spend_allowed: Boolean($("ledger-cursor-spend")?.checked), used_pct: numOrNull("ledger-cursor-used") },
      xai: { spend_allowed: Boolean($("ledger-xai-spend")?.checked), starting_usd: numOrNull("ledger-xai-usd") },
      openai: { spend_allowed: Boolean($("ledger-openai-spend")?.checked), starting_usd: numOrNull("ledger-openai-usd") },
      gemini: { spend_allowed: Boolean($("ledger-gemini-spend")?.checked), starting_usd: numOrNull("ledger-gemini-usd") },
    },
    refresh: Boolean(refreshNow),
  };
  try {
    const res = await fetch(`${brainBaseUrl()}/api/ledger`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify(body),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || `HTTP ${res.status}`;
      return;
    }
    await refreshLedger();
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
$("ledger-save")?.addEventListener("click", () => saveLedger(false));
$("ledger-refresh")?.addEventListener("click", () => saveLedger(true));

async function refreshDisruptionBanner() {
  const st = $("disrupt-status");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/disruption-banner`, { cache: "no-store" });
    const d = await res.json();
    if (!d?.ok) {
      if (st) st.textContent = d?.detail || "unavailable";
      return;
    }
    if ($("disrupt-enabled")) $("disrupt-enabled").checked = Boolean(d.enabled);
    if ($("disrupt-category") && document.activeElement !== $("disrupt-category")) {
      $("disrupt-category").value = d.category || "weather";
    }
    if ($("disrupt-title") && document.activeElement !== $("disrupt-title")) {
      $("disrupt-title").value = d.title || "";
    }
    if ($("disrupt-detail") && document.activeElement !== $("disrupt-detail")) {
      $("disrupt-detail").value = d.detail || "";
    }
    if ($("disrupt-until-date") && document.activeElement !== $("disrupt-until-date")) {
      $("disrupt-until-date").value = d.untilDate || "";
    }
    if ($("disrupt-until-time") && document.activeElement !== $("disrupt-until-time")) {
      $("disrupt-until-time").value = d.untilTimeHst || (d.untilDate ? "10:00" : "");
    }
    if ($("disrupt-until-label")) $("disrupt-until-label").value = d.untilLabel || "—";
    disruptionUntilMs = Number(d.untilMs) || null;
    paintDisruptionCountdown();
    if (st) {
      const untilBit = d.untilLabel
        ? (d.ended ? ` · window passed (${d.untilLabel})` : ` · until ${d.untilLabel}`)
        : "";
      st.textContent = d.show
        ? `Live on status · ${d.categoryLabel || d.category}${untilBit}`
        : d.enabled
          ? "Enabled, but empty — add a title or details"
          : "Off · status page will not show a banner";
    }
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
async function saveDisruptionBanner() {
  const st = $("disrupt-status");
  if (st) st.textContent = "saving…";
  try {
    const untilDate = String($("disrupt-until-date")?.value || "").trim();
    const untilTime = String($("disrupt-until-time")?.value || "").trim() || (untilDate ? "10:00" : "");
    const res = await fetch(`${brainBaseUrl()}/api/disruption-banner`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({
        enabled: Boolean($("disrupt-enabled")?.checked),
        category: $("disrupt-category")?.value || "weather",
        title: $("disrupt-title")?.value || "",
        detail: $("disrupt-detail")?.value || "",
        untilDate: untilDate || "",
        untilTimeHst: untilTime,
        updatedBy: "desktop-panel",
      }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (st) st.textContent = d.detail || d.hint || `HTTP ${res.status}`;
      return;
    }
    await refreshDisruptionBanner();
  } catch (err) {
    if (st) st.textContent = String(err.message || err);
  }
}
let disruptionUntilMs = null;
function paintDisruptionCountdown() {
  const el = $("disrupt-countdown");
  if (!el) return;
  if (!disruptionUntilMs) {
    el.value = "—";
    return;
  }
  const left = disruptionUntilMs - Date.now();
  el.value = left <= 0 ? "ended" : fmtLeft(left);
}
$("disrupt-refresh")?.addEventListener("click", () => refreshDisruptionBanner());
$("disrupt-save")?.addEventListener("click", () => saveDisruptionBanner());
setInterval(paintDisruptionCountdown, 1000);

let lastGfsSunny = null;
async function refreshGfsOutlook() {
  const label = $("disrupt-gfs-label");
  const note = $("disrupt-gfs-note");
  try {
    const res = await fetch(`${brainBaseUrl()}/api/gfs`, { cache: "no-store" });
    const d = await res.json();
    lastGfsSunny = d?.nextSunny || null;
    if (label) {
      label.value = lastGfsSunny?.label || (d?.configured === false ? "GFS token missing" : "No GFS outlook yet");
    }
    if (note) {
      if (d?.error) note.value = String(d.error).slice(0, 80);
      else if (lastGfsSunny) {
        const bits = [
          lastGfsSunny.kind === "clear" ? "meets sunny thresholds" : "clearest in 16-day GFS",
          lastGfsSunny.cloudPct != null ? `cloud ${lastGfsSunny.cloudPct}%` : null,
          lastGfsSunny.dswrf != null ? `${lastGfsSunny.dswrf} W/m²` : null,
        ].filter(Boolean);
        note.value = bits.join(" · ");
      } else note.value = d?.configured ? "Waiting for first collect" : "—";
    }
  } catch (err) {
    lastGfsSunny = null;
    if (label) label.value = "GFS unavailable";
    if (note) note.value = String(err.message || err);
  }
}
function useGfsSunnyDay() {
  if (!lastGfsSunny?.date) {
    const st = $("disrupt-status");
    if (st) st.textContent = "no GFS sunny date yet — refresh GFS first";
    return;
  }
  if ($("disrupt-until-date")) $("disrupt-until-date").value = lastGfsSunny.date;
  if ($("disrupt-until-time")) $("disrupt-until-time").value = lastGfsSunny.timeHst || "10:00";
  if ($("disrupt-category")) $("disrupt-category").value = "weather";
  const st = $("disrupt-status");
  if (st) st.textContent = `Filled ${lastGfsSunny.label} — save to publish the countdown`;
}
async function forceGfsRefresh() {
  const note = $("disrupt-gfs-note");
  if (note) note.value = "refreshing GFS…";
  try {
    const res = await fetch(`${brainBaseUrl()}/api/gfs/refresh`, {
      method: "POST",
      headers: operatorHeaders(),
      body: JSON.stringify({ updatedBy: "desktop-panel" }),
    });
    const d = await res.json();
    if (!res.ok) {
      if (note) note.value = d.detail || `HTTP ${res.status}`;
      return;
    }
    await refreshGfsOutlook();
  } catch (err) {
    if (note) note.value = String(err.message || err);
  }
}
$("disrupt-use-gfs")?.addEventListener("click", () => useGfsSunnyDay());
$("disrupt-gfs-refresh")?.addEventListener("click", () => forceGfsRefresh());

boot().catch((err) => {
  $("settings-status").textContent = String(err.message || err);
});
refreshShutdownTimer().catch(() => {});
refreshStartTimer().catch(() => {});
refreshDisruptionBanner().catch(() => {});
refreshOpsBanner().catch(() => {});
refreshGovernance().catch(() => {});
refreshLedger().catch(() => {});
refreshGfsOutlook().catch(() => {});
