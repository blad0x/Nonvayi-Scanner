import os
from utils.constants import MAX_FILE_SIZE_BYTES


def get_rotated_filename(base_path):
    """Return base_path if under size limit, otherwise return the next available rotated filename."""
    if not os.path.exists(base_path):
        return base_path
    if os.path.getsize(base_path) < MAX_FILE_SIZE_BYTES:
        return base_path
    name, ext = os.path.splitext(base_path)
    counter = 1
    while True:
        new_path = f"{name}_{counter}{ext}"
        if not os.path.exists(new_path) or os.path.getsize(new_path) < MAX_FILE_SIZE_BYTES:
            return new_path
        counter += 1


def append_to_file_with_rotation(base_path, content_line):
    """Append a line to base_path, rotating to a new numbered file when the size limit is hit."""
    target_path = get_rotated_filename(base_path)
    with open(target_path, "a", encoding="utf-8") as f:
        f.write(content_line + "\n")


def read_ips_from_file(file_path):
    """Read IPs from base file and all its rotated siblings (e.g. output_1.txt, output_2.txt…)."""
    ips = []
    base, ext = os.path.splitext(file_path)

    def extract_ip(line):
        line = line.strip()
        return line.split(" | ")[0].strip() if " | " in line else line

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            ips.extend([extract_ip(line) for line in f if line.strip()])

    counter = 1
    while True:
        part_path = f"{base}_{counter}{ext}"
        if os.path.exists(part_path):
            with open(part_path, "r", encoding="utf-8") as f:
                ips.extend([extract_ip(line) for line in f if line.strip()])
            counter += 1
        else:
            break

    return ips
