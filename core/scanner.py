import ssl
import asyncio
import subprocess
import os
from datetime import datetime, timedelta

from utils.constants import CDN_PORTS, OUTPUT_FILE
from utils.file_utils import read_ips_from_file


class FastAsyncScanner:
    def __init__(self, stop_event, ping_timeout=13.5, tls_check=True):
        self.stop_event   = stop_event
        self.existing_ips = set(read_ips_from_file(OUTPUT_FILE))
        self.ping_cache   = {}
        self.tls_cache    = {}
        self.CACHE_TTL    = 40
        self.PING_TIMEOUT = ping_timeout
        self.TLS_CHECK    = tls_check
        self.TLS_TIMEOUT  = 6.0

    # ─── Cache helpers ────────────────────────────────────
    def _is_cache_valid(self, cache, ip):
        if ip not in cache:
            return False
        return (datetime.now() - cache[ip][1] < timedelta(seconds=self.CACHE_TTL))

    def _evict_expired(self, cache):
        """Remove expired entries to prevent unbounded cache growth."""
        now    = datetime.now()
        cutoff = timedelta(seconds=self.CACHE_TTL)
        expired = [k for k, v in cache.items() if now - v[1] >= cutoff]
        for k in expired:
            del cache[k]
        # Hard cap: evict oldest entries if cache is still too large
        MAX_CACHE_ENTRIES = 5000
        if len(cache) > MAX_CACHE_ENTRIES:
            sorted_keys = sorted(cache, key=lambda k: cache[k][1])
            for k in sorted_keys[:len(cache) - MAX_CACHE_ENTRIES]:
                del cache[k]

    # ─── TLS handshake ────────────────────────────────────
    async def tls_handshake(self, ip):
        if self.stop_event.is_set():
            return False, None, None
        if self._is_cache_valid(self.tls_cache, ip):
            return self.tls_cache[ip][0]

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode    = ssl.CERT_NONE
        try:
            context.set_alpn_protocols(["h2", "http/1.1", "acme-tls/1"])
        except Exception:
            pass

        best_result = (False, None, None)
        best_rtt    = float('inf')
        detection_keywords = ["edge", "cdn", "proxy", "nginx", "cloudfront", "front", "akamai", "fastly", "cache"]

        for port in CDN_PORTS:
            if self.stop_event.is_set():
                return False, None, None
            try:
                tls_start      = __import__('time').time()
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port, ssl=context, server_hostname=None),
                    timeout=self.TLS_TIMEOUT,
                )
                tls_rtt   = (__import__('time').time() - tls_start) * 1000
                transport = writer.get_extra_info('ssl_object') or writer.get_extra_info('ssl_obj')

                selected_alpn = None
                try:
                    selected_alpn = transport.selected_alpn_protocol() if transport else None
                except Exception:
                    selected_alpn = None

                request = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
                writer.write(request.encode())
                await writer.drain()
                try:
                    response = (await asyncio.wait_for(reader.read(2048), timeout=2.2)).decode(errors="ignore")
                except Exception:
                    response = ""
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

                cdn_name      = "Unknown Edge"
                server_header = ""
                for line in response.splitlines():
                    if line.lower().startswith("server:"):
                        server_header = line.split(":", 1)[1].strip()
                        cdn_name      = server_header
                        break
                    if line.lower().startswith("via:") and not server_header:
                        server_header = line.split(":", 1)[1].strip()
                        cdn_name      = server_header

                server_lower = server_header.lower()
                is_clean     = any(kw in server_lower for kw in detection_keywords) or (len(server_header) > 8)

                result = (True, port, {
                    "alpn":  selected_alpn,
                    "rtt":   tls_rtt,
                    "cdn":   cdn_name,
                    "clean": is_clean,
                })

                if is_clean and tls_rtt < best_rtt:
                    best_result = result
                    best_rtt    = tls_rtt

                self.tls_cache[ip] = (result, datetime.now())
                if is_clean:
                    self._evict_expired(self.tls_cache)
                    return result
            except Exception:
                continue

        self.tls_cache[ip] = (best_result, datetime.now())
        self._evict_expired(self.tls_cache)
        return best_result

    # ─── Ping / TCP probe ─────────────────────────────────
    async def ping_host(self, ip):
        if self.stop_event.is_set():
            return False
        if self._is_cache_valid(self.ping_cache, ip):
            return self.ping_cache[ip][0]

        alive = False
        cmd   = (
            ['ping', '-n', '1', '-w', str(int(self.PING_TIMEOUT * 1000)), ip]
            if os.name == 'nt'
            else ['ping', '-c', '1', '-W', str(int(self.PING_TIMEOUT)), ip]
        )
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=(__import__('subprocess').CREATE_NO_WINDOW if os.name == 'nt' else 0),
            )
            await asyncio.wait_for(proc.communicate(), timeout=self.PING_TIMEOUT + 1.0)
            if proc.returncode == 0:
                alive = True
        except Exception:
            pass

        if not alive:
            for port in [443, 8443, 2083, 2053]:
                if self.stop_event.is_set():
                    break
                try:
                    _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2.0)
                    writer.close()
                    await writer.wait_closed()
                    alive = True
                    break
                except Exception:
                    continue

        self.ping_cache[ip] = (alive, datetime.now())
        self._evict_expired(self.ping_cache)
        return alive
