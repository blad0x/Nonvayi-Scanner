import os
import asyncio
import subprocess

from PyQt6.QtCore import QThread, pyqtSignal

from utils.constants import CDN_PORTS, OUTPUT_FILE, file_lock
from utils.file_utils import read_ips_from_file, append_to_file_with_rotation
from core.scanner import FastAsyncScanner


class ScanWorker(QThread):
    log_signal      = pyqtSignal(str, str)
    stat_signal     = pyqtSignal(bool)
    targets_signal  = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, workers, file_path, ping_timeout, tls_enabled, stop_event, log_file):
        super().__init__()
        self.workers      = workers
        self.file_path    = file_path
        self.ping_timeout = ping_timeout
        self.tls_enabled  = tls_enabled
        self.stop_event   = stop_event
        self.log_file     = log_file
        self.loop         = None

    def run(self):
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Strip proxy env vars to avoid routing scan traffic through a proxy
        for v in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
            os.environ.pop(v, None)

        self.log_signal.emit("⚠  Disable any active VPN before scanning for accurate results.", "#f59e0b")
        self.log_signal.emit(f"  Engine  ›  {'TLS Validation' if self.tls_enabled else 'Ping / TCP'}", "#71717a")

        try:
            self.loop.run_until_complete(self.run_logic_async())
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                self.loop.close()
            except Exception:
                pass

            self.finished_signal.emit(not self.stop_event.is_set())

    async def run_logic_async(self):
        sc  = FastAsyncScanner(self.stop_event, self.ping_timeout, self.tls_enabled)
        raw = read_ips_from_file(self.file_path)

        seen, targets = set(), []
        dup_count = 0
        for ip in raw:
            if ip in sc.existing_ips:
                dup_count += 1
            elif ip not in seen:
                seen.add(ip)
                targets.append(ip)

        if dup_count:
            self.log_signal.emit(
                f"  {dup_count} node(s) already in output database — skipped.",
                "#f59e0b",
            )

        self.targets_signal.emit(len(targets))
        sem   = asyncio.Semaphore(self.workers)
        tasks = [self.verify_node_async(ip, sem, sc, self.ping_timeout) for ip in targets]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def verify_node_async(self, ip, sem, sc, t):
        async with sem:
            if self.stop_event.is_set():
                return

            if sc.TLS_CHECK:
                self.log_signal.emit(f"  {ip}  ›  negotiating TLS...", "#71717a")
                ok, port, info = await sc.tls_handshake(ip)
                if ok and info.get("clean", False):
                    msg = (
                        f"{ip} → TLS SECURED [{port}] | "
                        f"RTT: {info.get('rtt', 0):.0f}ms | CDN Edge: {info.get('cdn')}"
                    )
                    self.log_signal.emit(msg, "#10b981")
                    with file_lock:
                        if ip not in sc.existing_ips:
                            sc.existing_ips.add(ip)
                            append_to_file_with_rotation(OUTPUT_FILE, ip)
                    self.stat_signal.emit(True)
                else:
                    self.log_signal.emit(f"  {ip}  ›  dropped  (TLS / fronting quality fail)", "#ef4444")
                    self.stat_signal.emit(False)
                return

            self.log_signal.emit(f"  {ip}  ›  probing...", "#71717a")
            p_ok = await sc.ping_host(ip)
            if not p_ok:
                self.log_signal.emit(f"  {ip}  ›  ICMP silent — trying TCP fallback...", "#f59e0b")

            alive, f_port = False, None
            for p in CDN_PORTS:
                if self.stop_event.is_set():
                    return
                try:
                    _, wr = await asyncio.wait_for(asyncio.open_connection(ip, p), timeout=t)
                    wr.close()
                    await wr.wait_closed()
                    alive, f_port = True, p
                    break
                except Exception:
                    continue

            if alive:
                self.log_signal.emit(f"{ip} → EDGE MATRIX VALIDATED [{f_port}]", "#10b981")
                with file_lock:
                    if ip not in sc.existing_ips:
                        sc.existing_ips.add(ip)
                        append_to_file_with_rotation(OUTPUT_FILE, ip)
                self.stat_signal.emit(True)
            else:
                self.log_signal.emit(f"  {ip}  ›  unreachable", "#ef4444")
                self.stat_signal.emit(False)
