#!/usr/bin/env python3
# ==============================================================================
# internet_gate.py — optional shared TCP internet check (stdlib only)
# ------------------------------------------------------------------------------
# Preferred implementation lives in rootserver_poller.py; this module is a
# reusable helper for other skills that need the same gate.
# Layout style (standing): keep SECTION banners.
# ==============================================================================
"""Internet connectivity gate (TCP to public endpoints — not local DNS stub)."""  # info: """Internet connectivity gate (TCP to public endpoints — not local DNS stub)."""
from __future__ import annotations  # info: from __future__ import annotations

import socket  # info: import socket

# ====================================================
# SECTION: CHECK
# ====================================================

def internet_ok(timeout: float = 2.5) -> bool:  # info: def internet_ok
    """True when TCP can reach 1.1.1.1:443 or 8.8.8.8:53."""  # info: """True when TCP can reach 1.1.1.1:443 or 8.8.8.8:53."""
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53), ("1.0.0.1", 443)):  # info: for host , port in ( ( "1.1.1.1"
        try:  # info: try :
            with socket.create_connection((host, port), timeout=timeout):  # info: with socket . create_connection ( ( host ,
                return True  # info: return True
        except OSError:  # info: except OSError :
            continue  # info: continue
    return False  # info: return False
