import os
import random
import ipaddress

from PyQt6.QtCore import QThread, pyqtSignal

from utils.constants import EXPANDED_IPS_FILE
from utils.file_utils import read_ips_from_file, append_to_file_with_rotation


class CIDRWorker(QThread):
    log_signal      = pyqtSignal(str, str)
    finished_signal = pyqtSignal(str)
    error_signal    = pyqtSignal(str)

    def __init__(self, file_path, target_count, overwrite):
        super().__init__()
        self.file_path    = file_path
        self.target_count = target_count
        self.overwrite    = overwrite

    def run(self):
        try:
            ex_ips = set() if self.overwrite else set(read_ips_from_file(EXPANDED_IPS_FILE))

            # Parse networks from file
            nets = []
            with open(self.file_path, "r", encoding="utf-8") as f:
                for l in f:
                    l = l.strip()
                    if not l or l.startswith("#"):
                        continue
                    try:
                        nets.append(ipaddress.ip_network(l, strict=False))
                    except Exception:
                        try:
                            nets.append(ipaddress.ip_network(f"{l}/32", strict=False))
                        except Exception:
                            pass

            if not nets:
                self.error_signal.emit("Zero valid structures compiled.")
                return

            gen_ips = []
            gen_set = set()
            rem     = self.target_count
            used    = [set() for _ in nets]
            exh     = [False] * len(nets)

            random.shuffle(nets)

            while rem > 0 and not all(exh) and not self.isInterruptionRequested():
                active = [i for i, x in enumerate(exh) if not x]
                if not active:
                    break
                share = max(1, rem // len(active))
                for idx in active:
                    if rem <= 0:
                        break
                    net   = nets[idx]
                    avail = net.num_addresses - len(used[idx])
                    take  = min(share, rem, avail)
                    if take <= 0:
                        exh[idx] = True
                        continue
                    takes, streak = 0, 0
                    while takes < take and streak < 40:
                        s_idx = random.randint(0, net.num_addresses - 1)
                        if s_idx not in used[idx]:
                            used[idx].add(s_idx)
                            ip = str(net[s_idx])
                            if ip not in ex_ips and ip not in gen_set:
                                gen_ips.append(ip)
                                gen_set.add(ip)
                                takes  += 1
                                rem    -= 1
                                streak  = 0
                            else:
                                streak += 1
                        else:
                            streak += 1
                    if len(used[idx]) >= net.num_addresses or streak >= 40:
                        exh[idx] = True
                        used[idx].clear()   # free memory: indices no longer needed

            random.shuffle(gen_ips)

            if self.overwrite:
                if os.path.exists(EXPANDED_IPS_FILE):
                    os.remove(EXPANDED_IPS_FILE)
                c = 1
                while os.path.exists(f"expanded_ips_{c}.txt"):
                    os.remove(f"expanded_ips_{c}.txt")
                    c += 1

            for ip in gen_ips:
                append_to_file_with_rotation(EXPANDED_IPS_FILE, ip)

            self.log_signal.emit(
                f"  Expanded  ›  {len(gen_ips):,} targets queued from CIDR ranges.",
                "#10b981",
            )
            self.finished_signal.emit(EXPANDED_IPS_FILE)

        except Exception as e:
            self.error_signal.emit(str(e))
