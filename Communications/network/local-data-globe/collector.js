#!/usr/bin/env node
'use strict';

const { execFile, spawn } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');
const telegramRelay = require('./telegram-relay.js');

const POLL_MS = Number(process.env.POLL_MS || 1000);
const PACKET_WINDOW_MS = Number(process.env.PACKET_WINDOW_MS || 10000);
const SOURCE_NODE = process.env.SOURCE_NODE || 'HawaiiRoot';
const SOURCE_REGION = process.env.SOURCE_REGION || 'local-hawaii';
const AWS_USER = process.env.AWS_USER || 'ubuntu';
const AWS_HOST = process.env.AWS_HOST || '18.118.30.226';
const AWS_PORT = Number(process.env.AWS_PORT || 22);
const AWS_REMOTE_DIR = process.env.AWS_REMOTE_DIR || '/home/ubuntu/network-globe/network-globe';
const SSH_KEY = process.env.SSH_KEY || '/home/rootrecord/.ssh/rootrecordkey.pem';
const SSH_CONNECT_TIMEOUT = Number(process.env.SSH_CONNECT_TIMEOUT || 8);
const ORIGIN_LABEL = process.env.ORIGIN_LABEL || 'Hawaii';
const AWS_FEED_MAX_BYTES = Number(process.env.AWS_FEED_MAX_BYTES || 64 * 1024 * 1024);
const AWS_FEED_TARGET_BYTES = Number(process.env.AWS_FEED_TARGET_BYTES || 48 * 1024 * 1024);
const AWS_FEED_MAINTENANCE_MS = Number(process.env.AWS_FEED_MAINTENANCE_MS || 15 * 60 * 1000);
const AWS_FEED_MAINTENANCE_SCRIPT = process.env.AWS_FEED_MAINTENANCE_SCRIPT || '/home/ubuntu/network-globe/network-globe/scripts/maintain-hawaii-feed.sh';

// NOTE: intentionally no on-disk outbox/ledger and no MAX_BUFFERED cap.
// This collector is a live-state pusher, not a store-and-forward system:
// - SSH reachable -> record streams to AWS immediately.
// - SSH unreachable, general internet up -> record goes to the Telegram
//   insurance channel instead (see telegram-relay.js), batched in memory only.
// - No internet at all -> the record is simply not observed by anything
//   downstream. Nothing is queued to disk for later replay into AWS, by design:
//   AWS must never show a backfilled/caught-up gap, only live state.

let localAddresses = new Set(['127.0.0.1', '::1']);
let flows = new Map();
let packetWindow = [];
let origin = null;
let sshProc = null;
let sshReady = false;
let sshConnecting = false;
let shuttingDown = false;
let maintenanceRunning = false;
let lastFeedMaintenance = 0;

function isPrivateIp(ip) {
  if (!ip) return true;
  if (ip.startsWith('::ffff:')) return isPrivateIp(ip.slice(7));
  const v = net.isIP(ip);
  if (v === 4) {
    const [a,b] = ip.split('.').map(Number);
    return a === 0 || a === 10 || a === 127 || (a === 100 && b >= 64 && b <= 127) ||
      (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) || a >= 224;
  }
  if (v === 6) {
    const x = ip.toLowerCase();
    return x === '::' || x === '::1' || x.startsWith('fc') || x.startsWith('fd') ||
      x.startsWith('fe8') || x.startsWith('fe9') || x.startsWith('fea') || x.startsWith('feb') || x.startsWith('ff');
  }
  return true;
}

function parseEndpoint(value) {
  if (!value || value === '*' || value === '*:*') return null;
  value = value.trim();
  if (value.startsWith('[')) {
    const end = value.lastIndexOf(']');
    if (end > 0) {
      const ip = value.slice(1, end).split('%')[0];
      const port = Number(value.slice(end + 1).replace(/^:/, '')) || 0;
      return { ip, port };
    }
  }
  const i = value.lastIndexOf(':');
  if (i > 0) {
    const ip = value.slice(0, i);
    const port = Number(value.slice(i + 1));
    if (net.isIP(ip) && Number.isFinite(port)) return { ip, port };
  }
  return null;
}

function parseSsLine(line) {
  const cols = line.trim().split(/\s+/);
  if (cols.length < 6) return null;
  const protoRaw = cols[0].toLowerCase();
  const proto = protoRaw.startsWith('tcp') ? 'tcp' : protoRaw.startsWith('udp') ? 'udp' : protoRaw;
  const local = parseEndpoint(cols[4]);
  const peer = parseEndpoint(cols[5]);
  if (!local || !peer || !net.isIP(peer.ip) || isPrivateIp(peer.ip)) return null;
  const m = line.match(/users:\(\("([^"]+)"(?:,pid=(\d+))?/);
  const process = m ? m[1] : 'unknown';
  const pid = m && m[2] ? Number(m[2]) : null;
  const key = `${proto}|${local.ip}:${local.port}|${peer.ip}:${peer.port}`;
  return { key, proto, local, peer, process, pid };
}

function refreshLocalAddresses() {
  return new Promise(resolve => {
    execFile('ip', ['-j', 'addr'], { timeout: 3000, maxBuffer: 2 * 1024 * 1024 }, (err, stdout) => {
      if (!err) {
        try {
          const data = JSON.parse(stdout);
          const next = new Set(['127.0.0.1', '::1']);
          for (const iface of data) for (const a of iface.addr_info || []) if (a.local) next.add(a.local.split('%')[0]);
          localAddresses = next;
        } catch {}
      }
      resolve();
    });
  });
}

function runSs() {
  return new Promise(resolve => {
    execFile('ss', ['-H', '-tun', '-p'], { timeout: 3000, maxBuffer: 8 * 1024 * 1024 }, (err, stdout) => {
      if (err) return resolve([]);
      resolve(stdout.split('\n').map(parseSsLine).filter(Boolean));
    });
  });
}

function parseTcpdumpEndpoint(value) {
  value = value.replace(/^\[|\]$/g, '').trim();
  const i = value.lastIndexOf('.');
  if (i <= 0) return null;
  const ip = value.slice(0, i).replace(/^IP6?\s+/, '').trim();
  const port = Number(value.slice(i + 1));
  if (!net.isIP(ip) || !Number.isFinite(port)) return null;
  return { ip, port };
}

function addPacketEvent(src, dst, proto, bytes) {
  const outbound = localAddresses.has(src.ip);
  const local = outbound ? src : dst;
  const remote = outbound ? dst : src;
  if (!localAddresses.has(local.ip) || isPrivateIp(remote.ip)) return;
  packetWindow.push({ key: `${proto}|${local.ip}:${local.port}|${remote.ip}:${remote.port}`, packets: 1, bytes, ts: Date.now() });
  if (packetWindow.length > 50000) packetWindow.splice(0, packetWindow.length - 50000);
}

function handleTcpdumpLine(line) {
  const cleaned = line.trim().replace(/^\S+\s+IP6?\s+/, '').replace(/^IP6?\s+/, '');
  const parts = cleaned.split(' > ');
  if (parts.length < 2) return;
  const src = parseTcpdumpEndpoint(parts[0].trim());
  const dst = parseTcpdumpEndpoint(parts[1].split(':')[0].trim());
  if (!src || !dst) return;
  const is6 = cleaned.startsWith('IP6 ') || line.includes(' IP6 ');
  const proto = /\btcp\b/i.test(line) ? 'tcp' : /\budp\b/i.test(line) ? 'udp' : (is6 ? 'ip6' : 'ip');
  const len = Number((line.match(/\blength\s+(\d+)/) || [])[1] || 0);
  addPacketEvent(src, dst, proto, len);
}

function startTcpdump() {
  if (!(process.getuid && process.getuid() === 0)) return;
  try {
    const p = spawn('tcpdump', ['-l', '-n', '-q', '-i', 'any', 'ip or ip6'], { stdio: ['ignore', 'pipe', 'ignore'] });
    p.stdout.setEncoding('utf8');
    let buf = '';
    p.stdout.on('data', chunk => {
      buf += chunk;
      const lines = buf.split('\n');
      buf = lines.pop() || '';
      for (const line of lines) handleTcpdumpLine(line);
    });
  } catch {}
}

function packetStats(key) {
  const cutoff = Date.now() - PACKET_WINDOW_MS;
  let packets = 0, bytes = 0;
  const keep = [];
  for (const e of packetWindow) {
    if (e.ts >= cutoff) {
      keep.push(e);
      if (e.key === key) {
        packets += e.packets;
        bytes += e.bytes;
      }
    }
  }
  packetWindow = keep;
  return { packets, bytes };
}

function updateFlows(rows) {
  const now = Date.now();
  const next = new Map();
  for (const row of rows) {
    const prev = flows.get(row.key);
    next.set(row.key, { ...row, firstSeen: prev?.firstSeen || now, lastSeen: now });
  }
  for (const [key, flow] of flows) if (!next.has(key) && now - flow.lastSeen < 12000) next.set(key, flow);
  flows = next;
}

async function discoverOrigin() {
  const lat = Number(process.env.ORIGIN_LAT);
  const lng = Number(process.env.ORIGIN_LNG);
  if (Number.isFinite(lat) && Number.isFinite(lng)) {
    origin = { lat, lng, label: ORIGIN_LABEL };
    return;
  }
  try {
    const r = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(5000) });
    const d = await r.json();
    const dlat = Number(d.latitude), dlng = Number(d.longitude);
    if (Number.isFinite(dlat) && Number.isFinite(dlng)) {
      origin = { lat: dlat, lng: dlng, label: d.city ? `${d.city}, ${d.country_name || ''}`.replace(/, $/, '') : ORIGIN_LABEL, ip: d.ip || null, asn: d.asn || null, org: d.org || null };
      return;
    }
  } catch {}
  origin = { lat: 21.3069, lng: -157.8583, label: ORIGIN_LABEL };
}

function makeRecord(flow) {
  const stats = packetStats(flow.key);
  return {
    type: 'network-globe-telemetry',
    version: 1,
    timestamp: Date.now(),
    sourceNode: SOURCE_NODE,
    sourceRegion: SOURCE_REGION,
    source: {
      latitude: origin?.lat ?? null,
      longitude: origin?.lng ?? null,
      label: origin?.label || ORIGIN_LABEL,
      publicIp: origin?.ip || null,
      asn: origin?.asn || null,
      organization: origin?.org || null
    },
    destination: {
      type: 'public-ip',
      ip: flow.peer.ip,
      port: flow.peer.port
    },
    protocol: flow.proto,
    process: flow.process || 'unknown',
    packets: stats.packets,
    bytes: stats.bytes
  };
}

function queueRecord(record) {
  const line = JSON.stringify(record) + '\n';
  if (sshReady && sshProc?.stdin?.writable) {
    try { sshProc.stdin.write(line); return; } catch { sshReady = false; }
  }
  // SSH isn't up right now: this is a live push, not a store-and-forward
  // system, so we never write this to disk for later replay into AWS.
  // Hand it to the Telegram insurance channel instead -- that's off-box
  // record-keeping only, and it is never drained back into AWS on
  // reconnect (see telegram-relay.js and RATIONALE.md).
  telegramRelay.offer(record);
}

function sshArgs() {
  const remoteFile = AWS_REMOTE_DIR + '/data/hawaii.ndjson';
  const readyMarker = '__NETWORK_GLOBE_SSH_READY__';
  const args = [
    '-T',
    '-o', 'BatchMode=yes',
    '-o', `ConnectTimeout=${SSH_CONNECT_TIMEOUT}`,
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=3',
    '-o', 'StrictHostKeyChecking=accept-new'
  ];
  if (SSH_KEY) args.push('-i', SSH_KEY);
  if (AWS_PORT) args.push('-p', String(AWS_PORT));
  args.push(
    `${AWS_USER}@${AWS_HOST}`,
    `mkdir -p ${shellQuote(AWS_REMOTE_DIR + '/data')} && printf '%s\\n' '${readyMarker}' && exec cat >> ${shellQuote(remoteFile)}`
  );
  return args;
}

function shellQuote(s) { return `'${String(s).replace(/'/g, `'\\''`)}'`; }

function baseSshArgs() {
  const args = [
    '-T',
    '-o', 'BatchMode=yes',
    '-o', `ConnectTimeout=${SSH_CONNECT_TIMEOUT}`,
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=3',
    '-o', 'StrictHostKeyChecking=accept-new'
  ];
  if (SSH_KEY) args.push('-i', SSH_KEY);
  if (AWS_PORT) args.push('-p', String(AWS_PORT));
  return args;
}

function stopSshStream() {
  const p = sshProc;
  sshReady = false;
  sshConnecting = false;
  sshProc = null;
  if (!p) return Promise.resolve();
  return new Promise(resolve => {
    try { p.stdin?.end(); } catch {}
    try { p.kill('SIGTERM'); } catch {}
    const timer = setTimeout(resolve, 1000);
    p.once('close', () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

function maintainAwsFeed() {
  if (shuttingDown || maintenanceRunning) return;
  const now = Date.now();
  if (now - lastFeedMaintenance < AWS_FEED_MAINTENANCE_MS) return;

  maintenanceRunning = true;
  lastFeedMaintenance = now;

  const args = baseSshArgs();
  args.push(
    `${AWS_USER}@${AWS_HOST}`,
    `stat -c '%s' ${shellQuote(AWS_REMOTE_DIR + '/data/hawaii.ndjson')} 2>/dev/null || echo 0`
  );

  const probe = spawn('ssh', args, { stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = '';
  probe.stdout.setEncoding('utf8');
  probe.stderr.setEncoding('utf8');
  probe.stdout.on('data', chunk => { stdout += chunk; });
  probe.stderr.on('data', chunk => {
    const msg = chunk.trim();
    if (msg) console.error(`AWS feed size check: ${msg}`);
  });

  const finish = () => {
    maintenanceRunning = false;
  };

  probe.on('error', err => {
    console.error(`AWS feed size check error: ${err.message}`);
    finish();
  });

  probe.on('close', code => {
    if (code !== 0) {
      console.error(`AWS feed size check exited code=${code}`);
      finish();
      return;
    }

    const size = Number(stdout.trim());
    if (!Number.isFinite(size) || size <= AWS_FEED_MAX_BYTES) {
      finish();
      return;
    }

    console.log(`AWS feed is ${size} bytes; starting bounded-feed maintenance`);

    stopSshStream().then(() => new Promise(resolve => {
      const maintArgs = baseSshArgs();
      maintArgs.push(
        `${AWS_USER}@${AWS_HOST}`,
        `bash ${shellQuote(AWS_FEED_MAINTENANCE_SCRIPT)} ${AWS_FEED_MAX_BYTES} ${AWS_FEED_TARGET_BYTES}`
      );
      const p = spawn('ssh', maintArgs, { stdio: ['ignore', 'pipe', 'pipe'] });
      p.stdout.setEncoding('utf8');
      p.stderr.setEncoding('utf8');
      p.stdout.on('data', chunk => {
        const msg = chunk.trim();
        if (msg) console.log(`AWS feed maintenance: ${msg}`);
      });
      p.stderr.on('data', chunk => {
        const msg = chunk.trim();
        if (msg) console.error(`AWS feed maintenance: ${msg}`);
      });
      p.on('error', err => {
        console.error(`AWS feed maintenance error: ${err.message}`);
        resolve();
      });
      p.on('close', exitCode => {
        if (exitCode !== 0) console.error(`AWS feed maintenance exited code=${exitCode}`);
        resolve();
      });
    })).finally(() => {
      finish();
      if (!shuttingDown) setTimeout(connectSsh, 250);
    });
  });
}

function connectSsh() {
  if (shuttingDown || sshProc || sshConnecting || maintenanceRunning) return;

  sshConnecting = true;
  const p = spawn('ssh', sshArgs(), { stdio: ['pipe', 'pipe', 'pipe'] });
  sshProc = p;

  let stdoutBuffer = '';

  p.stdin.on('error', () => {
    sshReady = false;
  });

  p.stdout.setEncoding('utf8');
  p.stdout.on('data', chunk => {
    stdoutBuffer += chunk;

    if (!sshReady && stdoutBuffer.includes('__NETWORK_GLOBE_SSH_READY__')) {
      sshReady = true;
      stdoutBuffer = '';
      // Deliberately no backlog flush here. Reconnecting resumes live
      // pushes only -- whatever happened during the gap stays a gap on
      // the globe (visually correct: no local data while local was down)
      // and stays only in the Telegram insurance channel, never in AWS.
      console.log('SSH stream ready → AWS');
    }
  });

  p.stderr.setEncoding('utf8');
  p.stderr.on('data', chunk => {
    const msg = chunk.trim();
    if (msg) console.error(`SSH: ${msg}`);
  });

  p.on('spawn', () => {
    sshConnecting = false;
  });

  p.on('error', err => {
    sshReady = false;
    sshConnecting = false;
    console.error(`SSH process error: ${err.message}`);
  });

  p.on('close', (code, signal) => {
    sshReady = false;
    sshConnecting = false;
    if (sshProc === p) sshProc = null;

    if (!shuttingDown) {
      console.error(`SSH stream closed (code=${code}, signal=${signal || 'none'})`);
      setTimeout(connectSsh, 2000);
    }
  });
}

async function collect() {
  await refreshLocalAddresses();
  updateFlows(await runSs());
  for (const flow of flows.values()) queueRecord(makeRecord(flow));
  maintainAwsFeed();
}

async function boot() {
  await refreshLocalAddresses();
  await discoverOrigin();
  startTcpdump();
  telegramRelay.start();
  connectSsh();
  await collect();
  setInterval(() => collect().catch(() => {}), POLL_MS);
  setInterval(() => connectSsh(), 3000);
  console.log(`Hawaii data collector → ${AWS_USER}@${AWS_HOST}:${AWS_PORT}${AWS_REMOTE_DIR}/data/hawaii.ndjson`);
  console.log(`origin: ${origin?.label || ORIGIN_LABEL}`);
}

function shutdown() {
  shuttingDown = true;
  try { sshProc?.stdin?.end(); } catch {}
  try { sshProc?.kill('SIGTERM'); } catch {}
  telegramRelay.stop();
  process.exit(0);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
boot().catch(err => { console.error(err); process.exit(1); });
