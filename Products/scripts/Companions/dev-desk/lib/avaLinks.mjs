/**
 * Canonical Ava / Root Record / RootMC links for the Ava Ivy console.
 */
export const AVA_LINK_GROUPS = [
  {
    id: "live",
    label: "Live boards",
    links: [
      {
        title: "Status desk",
        url: "https://rootrecord.cloud/status",
        note: "Public status on rootrecord.cloud",
      },
      {
        title: "Origin (tunnel)",
        url: "https://origin.avaivy.cloud/",
        note: "Cloudflare tunnel → this PC :8787",
      },
      {
        title: "Origin health",
        url: "https://origin.avaivy.cloud/health",
        note: "JSON liveness",
      },
      {
        title: "Kīlauea",
        url: "https://kilauea.cloud/",
        note: "Public Kīlauea app",
      },
      {
        title: "Weather product",
        url: "https://rootrecord.cloud/weather",
        note: "Public product page",
      },
      {
        title: "Ava wiki",
        url: "https://avaivy.cloud/",
        note: "Wiki / context — not an iframe of the desk",
      },
    ],
  },
  {
    id: "local",
    label: "Local AVA-CORE",
    links: [
      {
        title: "Local origin",
        url: "http://127.0.0.1:8787/",
        note: "HTTP home on this host",
      },
      {
        title: "Local status",
        url: "http://127.0.0.1:8787/status",
      },
      {
        title: "Local weather",
        url: "http://127.0.0.1:8787/weather",
      },
      {
        title: "Local Kīlauea",
        url: "http://127.0.0.1:8787/kilauea",
      },
      {
        title: "Local account",
        url: "http://127.0.0.1:8787/account.html",
      },
      {
        title: "Local site-config",
        url: "http://127.0.0.1:8787/api/site-config",
      },
      {
        title: "Local health",
        url: "http://127.0.0.1:8787/health",
        note: "JSON liveness",
      },
    ],
  },
  {
    id: "wiki",
    label: "Wiki & context",
    links: [
      {
        title: "Ava Ivy home",
        url: "https://avaivy.cloud/",
        note: "Public wiki / context",
      },
      {
        title: "Chat",
        url: "https://rootrecord.cloud/chat",
      },
    ],
  },
  {
    id: "products",
    label: "Root Record · RootMC",
    links: [
      {
        title: "Root Record",
        url: "https://rootrecord.cloud/",
        note: "Public home",
      },
      {
        title: "Account / sign in",
        url: "https://rootrecord.cloud/account",
      },
      {
        title: "Discord verify",
        url: "https://rootrecord.cloud/discord-verify",
      },
      {
        title: "RootMC",
        url: "https://rootmc.net/",
        note: "Minecraft network site",
      },
      {
        title: "Play",
        url: "https://play.rootmc.net/",
        note: "Production join address",
      },
      {
        title: "RootMC wiki",
        url: "https://rootmc.net/wiki/",
      },
      {
        title: "RootMC API",
        url: "https://api.rootmc.net/",
      },
    ],
  },
  {
    id: "api",
    label: "APIs",
    links: [
      {
        title: "Origin status",
        url: "https://origin.avaivy.cloud/api/status",
      },
      {
        title: "Site config",
        url: "https://origin.avaivy.cloud/api/site-config",
      },
      {
        title: "Account Worker",
        url: "https://rootrecord-api-account.rootrecord.workers.dev/",
      },
      {
        title: "RootMC API",
        url: "https://api.rootmc.net/",
        note: "Minecraft API only — not Ava origin",
      },
    ],
  },
  {
    id: "community",
    label: "Community & code",
    links: [
      {
        title: "RootMC Discord invite",
        url: "https://discord.gg/rFFQYrNaqS",
      },
      {
        title: "RootRecord on GitHub",
        url: "https://github.com/RootRecord",
        note: "Public org",
      },
    ],
  },
];

export function listAvaLinks() {
  return {
    ok: true,
    title: "Ava links",
    updatedAt: Date.now(),
    groups: AVA_LINK_GROUPS,
  };
}
