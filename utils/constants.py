import os
import threading

# ─── File paths ───────────────────────────────────────────
OUTPUT_FILE       = "output.txt"
EXPANDED_IPS_FILE = "expanded_ips.txt"
LOG_DIR           = "reportlogs"

# ─── Size limits ──────────────────────────────────────────
MAX_FILE_SIZE_BYTES     = 20 * 1024 * 1024   # output.txt rotation threshold (20 MB)
MAX_EXPANDED_FILE_SIZE  = 30 * 1024 * 1024   # expanded_ips hard cap (30 MB)
MAX_LOG_FILE_SIZE_BYTES = 10 * 1024 * 1024   # per-session log file cap (10 MB)

# ─── Network ──────────────────────────────────────────────
CDN_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

# ─── Thread safety ────────────────────────────────────────
file_lock = threading.Lock()

# ─── Display (overwritten at startup after QApplication) ──
DISPLAY_HZ = 60
DISPLAY_MS = 16

# ─── Bootstrap: ensure required paths exist ───────────────
if not os.path.exists(OUTPUT_FILE):
    open(OUTPUT_FILE, 'w', encoding='utf-8').close()
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
