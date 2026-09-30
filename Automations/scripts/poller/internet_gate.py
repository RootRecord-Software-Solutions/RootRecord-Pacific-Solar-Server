#!/usr/bin/env python3
# ==============================================================================
# internet_gate.py — TCP internet check for poller net services
# ------------------------------------------------------------------------------
# Used conceptually with tunnel / GitHub / Telegram gates.
# Primary logic is also inlined in rootserver_poller.py for boot reliability.
# Layout style (standing): keep SECTION banners.
# ==============================================================================
"""Internet connectivity gate for poller net services (tunnel, GitHub, Telegram)."""  # info: """Internet connectivity gate for poller net services (tunnel, GitHub, Telegram)."""
from __future__ import annotations  # info: from __future__ import annotations

import socket  # info: import socket

# ====================================================
# SECTION: CHECK
# ====================================================

def internet_ok(timeout: float = 2.5) -> bool:  # info: def internet_ok
    """TCP reachability to public endpoints — does not use local DNS stub."""  # info: """TCP reachability to public endpoints — does not use local DNS stub."""
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53), ("1.0.0.1", 443)):  # info: for host , port in ( ( "1.1.1.1"
        try:  # info: try :
            with socket.create_connection((host, port), timeout=timeout):  # info: with socket . create_connection ( ( host ,
                return True  # info: return True
        except OSError:  # info: except OSError :
            continue  # info: continue
    return False  # info: return False
