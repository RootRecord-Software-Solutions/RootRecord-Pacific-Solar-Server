# ==============================================================================
# flm-log-redact.awk — privacy filter for FastFlowLM server output (flm.log).
# Used by run-infer.sh on-demand start (FLM_LOG_REDACT=1 default; 0 = raw log).
# Drops request bodies ("[LOG]  Body:" + following JSON lines) and model output
# ("Model RAW Output:" until NPU Lock Release / ==== / next [FLM] line).
# Keeps status, timing, target and error lines. Added 2026-09-29 (g3-voice-ailog).
# ==============================================================================
skip == "body" {
  if ($0 == "" || $0 ~ /^[{}[:space:]]/) { n++; next }
  print "[LOG]  Body: [redacted " n " lines]"; fflush(); skip = ""
}
skip == "raw" {
  if ($0 ~ /NPU Lock Release|^=====|^\[FLM\]/) { print "[FLM]  Model RAW Output: [redacted " n " lines]"; fflush(); skip = "" }
  else { n++; next }
}
/Body:/ { skip = "body"; n = 0; next }
/RAW Output/ { skip = "raw"; n = 0; next }
{ print; fflush() }
END { if (skip != "") { print "[redacted " n " lines]"; fflush() } }
