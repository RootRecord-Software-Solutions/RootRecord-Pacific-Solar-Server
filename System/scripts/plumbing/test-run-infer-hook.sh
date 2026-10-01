#!/usr/bin/env bash
# ==============================================================================
# # INFO — test-run-infer-hook.sh: model-free test of the run-infer.sh specialist hook
# Usage: test-run-infer-hook.sh <reference-run-infer.sh>   (e.g. the pre-hook backup)
# Runs the reference and the current run-infer.sh in a temp dir against a FAKE FLM server (127.0.0.1:52999) and a STUB
# run-ollama.sh, with a private lock/state/JSONL. No model, no real lock, no Database writes (RR_ROUTE_LOG=0).
#  1. Flag OFF (8 cases incl. injected RR_SPEC_* env, FLM fail -> Ollama path, DESK_LIVE_FILE): stdout+stderr, FLM request
#     body, JSONL line (ts/latency/mem normalised) and the Ollama model must be BYTE-IDENTICAL to the reference.
#  2. Flag ON: routed/forced/generic/explicit-model cases; checks system message, temperature, max_tokens, Ollama model and
#     the JSONL "specialist" / "route_confidence" fields.   Exit 0 = all pass.
# Created 2026-09-29 HST (g3-specialists hook pass). Bak snapshots: 2 - RootRecord-Database/Archive/Github-desk-backups/
# ==============================================================================
set -u  # info: set
REF="${1:?reference run-infer.sh}"  # info: set REF
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE
CFG="${RR_SPECIALIST_ROUTES:-$HERE/../../config/specialist-routes.json}"  # info: set CFG
T=$(mktemp -d /tmp/rrhook-test.XXXXXX); PORT="${HOOKTEST_PORT:-52999}"  # info: set T
trap '[[ -n "${FAKE:-}" ]] && kill "$FAKE" 2>/dev/null; rm -rf "$T"' EXIT  # info: trap
mkdir -p "$T/old" "$T/new" "$T/state" "$T/out"  # info: mkdir
cp "$REF" "$T/old/run-infer.sh"; cp "$HERE/run-infer.sh" "$T/new/run-infer.sh"  # info: cp
for d in old new; do  # info: for
  cp "$HERE/single-flight.sh" "$HERE/route-specialist.py" "$T/$d/"  # info: cp
  printf '#!/usr/bin/env bash\nprintf "STUB-OLLAMA model=%%s prompt_chars=%%s\\n" "$1" "${#2}"\nprintf "%%s\\n" "$1" >> "$(dirname "$0")/ollama-calls.txt"\n' > "$T/$d/run-ollama.sh"
  chmod +x "$T/$d/"*.sh "$T/$d/"*.py  # info: chmod
done  # info: done
cat > "$T/fake.py" <<'PY'  # info: cat
import http.server, json, os, sys
LOG, FAIL = sys.argv[2], sys.argv[3]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"data":[]}')
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        open(LOG, "ab").write(body + b"\n")
        if os.path.exists(FAIL):
            self.send_response(500); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"choices": [{"message": {"content": "FAKE-REPLY"}}]}).encode())
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PY
python3 "$T/fake.py" "$PORT" "$T/bodies.jsonl" "$T/FAIL" >/dev/null 2>&1 & FAKE=$!  # info: python3
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -sf -m 1 "http://127.0.0.1:$PORT/v1/models" >/dev/null && break; sleep 0.3; done  # info: for
printf 'soc_delta2=41\n# comment\nload1=2.1\n' > "$T/desk.txt"

# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
run() { # <old|new> <name> <fail 0|1> <target> <prompt> [VAR=VAL...]
  local ver=$1 name=$2 fail=$3 tgt=$4 prompt=$5; shift 5  # info: local
  local o="$T/out/$ver"; mkdir -p "$o"; rm -f "$T/bodies.jsonl" "$T/$ver/ollama-calls.txt" "$T/$ver/infer.jsonl"  # info: local
  if [[ $fail == 1 ]]; then touch "$T/FAIL"; else rm -f "$T/FAIL"; fi  # info: if
  env -u RR_SPECIALIST_ROUTING -u RR_SPECIALIST -u DESK_LIVE_FILE FLM_URL="http://127.0.0.1:$PORT" FLM_ON_DEMAND=0 \
    RR_INFERENCE_LOCK="$T/lock" RR_PLUMBING_STATE="$T/state" RR_INFER_LOG_FILE="$T/$ver/infer.jsonl" RR_CALLER=hooktest RR_ROUTE_LOG=0 \
    RR_SPECIALIST_ROUTES="$CFG" "$@" bash "$T/$ver/run-infer.sh" "$tgt" "$prompt" > "$o/$name.out" 2>&1  # info: set RR_SPECIALIST_ROUTES
  echo "rc=$?" >> "$o/$name.out"  # info: echo
  sed -i -E 's/[0-9]{8}-[0-9]{6}/<JOBTS>/g; s/pid [0-9]+/pid <N>/g' "$o/$name.out"  # info: sed
  cp "$T/bodies.jsonl" "$o/$name.body" 2>/dev/null || : > "$o/$name.body"  # info: cp
  cp "$T/$ver/ollama-calls.txt" "$o/$name.ollama" 2>/dev/null || : > "$o/$name.ollama"  # info: cp
  sed -E 's/"ts":"[^"]*"/"ts":"<TS>"/; s/"latency_ms":[0-9]+/"latency_ms":0/; s/"mem_avail_mb_(before|after)":[0-9]+/"mem_avail_mb_\1":0/g' \
    "$T/$ver/infer.jsonl" > "$o/$name.jsonl" 2>/dev/null || : > "$o/$name.jsonl"  # info: command
}  # info: command
fails=0  # info: set fails
echo "== 1. flag OFF: current vs reference (byte-identical)"  # info: echo
OFF=(  # info: set OFF
 "A_off_flm|0|bruce|What is the battery SOC on the Delta 2 right now?|"  # info: command
 "B_off_ollama|1|bruce|What is the battery SOC on the Delta 2 right now?|"  # info: command
 "C_off_injected_env|0|bruce|What is the battery SOC on the Delta 2 right now?|RR_SPECIALIST=rr-exec RR_SPEC_SYS=INJECTED RR_SPEC_SYSTEM=INJECTED RR_SPEC_TEMP=0.9"  # info: command
 "D_flag_0|0|bruce|What is the battery SOC?|RR_SPECIALIST_ROUTING=0"  # info: command
 "E_off_rr_target|0|rr-exec|Draft PURPOSE: line|"  # info: command
 "F_off_rr_target_ollama|1|rr-exec|Draft PURPOSE: line|"  # info: command
 "G_off_generic|0|carly|Tell me a joke about coconuts.|"  # info: command
 "H_off_desk_file|0|ava|Status?|DESK_LIVE_FILE=$T/desk.txt"  # info: command
)  # info: command
for c in "${OFF[@]}"; do  # info: for
  IFS='|' read -r n f t p e <<<"$c"; read -r -a ex <<<"$e"  # info: set IFS
  for v in old new; do run "$v" "$n" "$f" "$t" "$p" "${ex[@]}"; done  # info: for
  if cmp -s <(cd "$T/out/old" && cat "$n".out "$n".body "$n".jsonl "$n".ollama) <(cd "$T/out/new" && cat "$n".out "$n".body "$n".jsonl "$n".ollama); then  # info: if
    echo "  PASS $n (identical)"; else echo "  FAIL $n (differs)"; fails=$((fails+1)); fi  # info: echo
done  # info: done
echo "== 2. flag ON: expected routing"  # info: echo
ON=(  # info: set ON
 "I_on_routed_flm|0|bruce|What is the battery SOC on the Delta 2 right now?||You are RootRecord Energy|0.2|256|-|rr-energy"  # info: command
 "J_on_routed_ollama|1|bruce|What is the battery SOC on the Delta 2 right now?||You are RootRecord Energy|0.2|256|rr-energy|rr-energy"  # info: command
 "K_on_generic|0|carly|Tell me a joke about coconuts.||You are RootRecord carly. Be brief|0.3|180|-|generic"  # info: command
 "L_on_forced_env|0|rr-exec|Draft PURPOSE: line|RR_SPECIALIST=rr-exec|You are RootRecord Exec|0.1|320|-|rr-exec"  # info: command
 "M_on_rr_target_ollama|1|rr-exec|Draft PURPOSE: line||You are RootRecord Exec|0.1|320|rr-exec|rr-exec"  # info: command
 "N_on_explicit_model|0|qwen2.5:1.5b-instruct-q8_0|hello||You are RootRecord qwen2.5|0.3|180|-|<absent>"  # info: command
 "O_on_forced_unknown|0|bruce|hello there|RR_SPECIALIST=rr-nope|You are RootRecord bruce. Be brief|0.3|180|-|generic"  # info: command
)  # info: command
for c in "${ON[@]}"; do  # info: for
  IFS='|' read -r n f t p e sysw tw mw ow specw <<<"$c"; read -r -a ex <<<"$e"  # info: set IFS
  run new "$n" "$f" "$t" "$p" RR_SPECIALIST_ROUTING=1 "${ex[@]}"  # info: run
  if python3 - "$T/out/new/$n" "$sysw" "$tw" "$mw" "$ow" "$specw" <<'PY'  # info: if
import json, sys
b, sysw, tw, mw, ow, specw = sys.argv[1:7]
d = json.loads(open(b + ".body").read().splitlines()[0])
j = json.loads(open(b + ".jsonl").read().replace('"<TS>"', '""'))
got = (d["messages"][0]["content"].startswith(sysw), str(d["temperature"]) == tw, str(d["max_tokens"]) == mw,
       (open(b + ".ollama").read().strip() or "-") == ow, j.get("specialist", "<absent>") == specw,
       ("route_confidence" in j) == (specw != "<absent>"))
sys.exit(0 if all(got) else 1)
PY
  then echo "  PASS $n"; else echo "  FAIL $n"; fails=$((fails+1)); fi  # info: then
done  # info: done
echo "== result: $fails failure(s)"; exit $(( fails > 0 ))  # info: echo
