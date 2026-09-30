const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("avaDesktop", {
  envStatus: () => ipcRenderer.invoke("ava:env-status"),
  connectionGet: () => ipcRenderer.invoke("ava:connection-get"),
  connectionSave: (patch) => ipcRenderer.invoke("ava:connection-save", patch || {}),
  connectionTest: (patch) => ipcRenderer.invoke("ava:connection-test", patch || {}),
  listDiscordChannels: () => ipcRenderer.invoke("ava:list-discord-channels"),
  listDiscordPrivate: () => ipcRenderer.invoke("ava:list-discord-private"),
  listSlackChannels: () => ipcRenderer.invoke("ava:list-slack-channels"),
  listTelegramChats: () => ipcRenderer.invoke("ava:list-telegram-chats"),
  listPresets: () => ipcRenderer.invoke("ava:list-presets"),
  history: (opts) => ipcRenderer.invoke("ava:history", opts),
  send: (opts) => ipcRenderer.invoke("ava:send", opts),
  post: (opts) => ipcRenderer.invoke("ava:post", opts),
  listAllPostTargets: () => ipcRenderer.invoke("ava:list-all-post-targets"),
  postAll: (opts) => ipcRenderer.invoke("ava:post-all", opts),
  mediaRoot: () => ipcRenderer.invoke("ava:media-root"),
  mediaList: (opts) => ipcRenderer.invoke("ava:media-list", opts),
  mediaPick: (opts) => ipcRenderer.invoke("ava:media-pick", opts),
  mediaImport: (opts) => ipcRenderer.invoke("ava:media-import", opts),
  mediaOpen: () => ipcRenderer.invoke("ava:media-open"),
  rewritePreview: (opts) => ipcRenderer.invoke("ava:rewrite-preview", opts),
  summarize: (opts) => ipcRenderer.invoke("ava:summarize", opts),
  rewriteProviders: () => ipcRenderer.invoke("ava:rewrite-providers"),
  coreStatus: () => ipcRenderer.invoke("ava:core-status"),
  coreChat: (opts) => ipcRenderer.invoke("ava:core-chat", opts),
  coreCancel: () => ipcRenderer.invoke("ava:core-cancel"),
  coreEnhance: (opts) => ipcRenderer.invoke("ava:core-enhance", opts),
  coreGold: (opts) => ipcRenderer.invoke("ava:core-gold", opts),
  discordEdit: (opts) => ipcRenderer.invoke("ava:discord-edit", opts),
  discordDelete: (opts) => ipcRenderer.invoke("ava:discord-delete", opts),
  feedbackTargets: () => ipcRenderer.invoke("ava:feedback-targets"),
  feedbackList: (opts) => ipcRenderer.invoke("ava:feedback-list", opts),
  feedbackProcessNext: () => ipcRenderer.invoke("ava:feedback-process-next"),
  feedbackAck: (opts) => ipcRenderer.invoke("ava:feedback-ack", opts),
  feedbackDualPost: (opts) => ipcRenderer.invoke("ava:feedback-dual-post", opts),
  feedbackDeleteDiscord: (opts) => ipcRenderer.invoke("ava:feedback-delete-discord", opts),
  feedbackDeleteSlack: (opts) => ipcRenderer.invoke("ava:feedback-delete-slack", opts),
  feedbackClearDiscord: (opts) => ipcRenderer.invoke("ava:feedback-clear-discord", opts),
  feedbackClearSlack: (opts) => ipcRenderer.invoke("ava:feedback-clear-slack", opts),
  feedbackClearAll: (opts) => ipcRenderer.invoke("ava:feedback-clear-all", opts),
  cronStatus: () => ipcRenderer.invoke("ava:cron-status"),
  cronRun: (id) => ipcRenderer.invoke("ava:cron-run", { id }),
  cronConfig: (body) => ipcRenderer.invoke("ava:cron-config", body),
  reportsStatus: () => ipcRenderer.invoke("ava:reports-status"),
  finance: (opts) => ipcRenderer.invoke("ava:finance", opts || {}),
  financeAction: (body) => ipcRenderer.invoke("ava:finance-action", body || {}),
  financeReceipt: (opts) => ipcRenderer.invoke("ava:finance-receipt", opts || {}),
  biz: () => ipcRenderer.invoke("ava:biz"),
  bizAction: (body) => ipcRenderer.invoke("ava:biz-action", body || {}),
  earlyLogin: () => ipcRenderer.invoke("ava:early-login"),
  openFolder: (target) => ipcRenderer.invoke("ava:open-folder", { target }),
  openPath: (target) => ipcRenderer.invoke("ava:open-path", { target }),
  revealPath: (target) => ipcRenderer.invoke("ava:reveal-path", { target }),
  opsCatalog: () => ipcRenderer.invoke("ava:ops-catalog"),
  opsRun: (id) => ipcRenderer.invoke("ava:ops-run", { id }),
  opsCancel: () => ipcRenderer.invoke("ava:ops-cancel"),
  activity: (opts) => ipcRenderer.invoke("ava:activity", opts || {}),
  mcStatus: () => ipcRenderer.invoke("ava:mc-status"),
  mcLog: (opts) => ipcRenderer.invoke("ava:mc-log", opts || {}),
  mcControl: (action) => ipcRenderer.invoke("ava:mc-control", { action }),
  mcRcon: (opts) => ipcRenderer.invoke("ava:mc-rcon", opts || {}),
  streamStatus: () => ipcRenderer.invoke("ava:stream-status"),
  streamPreview: () => ipcRenderer.invoke("ava:stream-preview"),
  streamAction: (opts) => ipcRenderer.invoke("ava:stream-action", opts || {}),
  listLinks: () => ipcRenderer.invoke("ava:list-links"),
  openLink: (url) => ipcRenderer.invoke("ava:open-link", { url }),
  releaseStatus: (kind) => ipcRenderer.invoke("ava:release-status", { kind }),
  releaseAction: (kind, action, targets) =>
    ipcRenderer.invoke("ava:release-action", { kind, action, targets }),
  gitSyncPrefs: () => ipcRenderer.invoke("ava:git-sync-prefs"),
  gitSyncPrefsSave: (patch) => ipcRenderer.invoke("ava:git-sync-prefs-save", patch || {}),
  deskUiGet: () => ipcRenderer.invoke("ava:desk-ui-get"),
  deskUiSave: (patch) => ipcRenderer.invoke("ava:desk-ui-save", patch || {}),
  morningReportCheck: () => ipcRenderer.invoke("ava:morning-report-check"),
  operatorPurge: () => ipcRenderer.invoke("ava:operator-purge"),
  gitStatus: () => ipcRenderer.invoke("ava:git-status"),
  gitCheck: () => ipcRenderer.invoke("ava:git-check"),
  gitPull: () => ipcRenderer.invoke("ava:git-pull"),
  onDeskLifecycle: (cb) => {
    const handler = (_e, payload) => cb(payload);
    ipcRenderer.on("ava:desk-lifecycle", handler);
    return () => ipcRenderer.removeListener("ava:desk-lifecycle", handler);
  },
  onGitSync: (cb) => {
    const handler = (_e, payload) => cb(payload);
    ipcRenderer.on("ava:git-sync", handler);
    return () => ipcRenderer.removeListener("ava:git-sync", handler);
  },
  onOpsLine: (cb) => {
    const handler = (_e, payload) => cb(payload);
    ipcRenderer.on("ava:ops-line", handler);
    return () => ipcRenderer.removeListener("ava:ops-line", handler);
  },
  onOpsStart: (cb) => {
    const handler = (_e, payload) => cb(payload);
    ipcRenderer.on("ava:ops-start", handler);
    return () => ipcRenderer.removeListener("ava:ops-start", handler);
  },
  onOpsDone: (cb) => {
    const handler = (_e, payload) => cb(payload);
    ipcRenderer.on("ava:ops-done", handler);
    return () => ipcRenderer.removeListener("ava:ops-done", handler);
  },
  onPostAllProgress: (cb) => {
    const handler = (_e, payload) => cb(payload);
    ipcRenderer.on("ava:post-all-progress", handler);
    return () => ipcRenderer.removeListener("ava:post-all-progress", handler);
  },
});
