# 🥖 NONVAYI Scanner

Advanced CDN Fronting / TLS Edge Scanner built with Python + PyQt6.

## Features

- Async high-speed IP scanning
- TLS/SSL edge validation
- CDN fronting detection
- ICMP + TCP fallback checking
- CIDR expansion support
- Realtime scan logs
- Auto output rotation system

## Built With

- Python
- PyQt6
- asyncio
- SSL/TLS sockets
- Custom animated UI engine

## AI Development

This project was fully written, optimized, and debugged with AI assistance.

The UI animations, TLS validation logic, async networking system, and scanner optimizations were refined using AI-assisted development.

However, the original idea, scanning logic direction, and the core project concept were created and designed by the project owner.

## Usage

### 1. Install Requirements

```bash
pip install PyQt6
```

### 2. Run main.py

```bash
python main.py
```

### 3. Start Scanning

- Load IP list or CIDR ranges
- Select performance preset
- Enable/Disable TLS engine
- Start scan

Results will be saved automatically into:

- `output.txt`
- `reportlogs`

## Compiled Version

A precompiled executable version is also included for users who don't want to install Python manually.

## Notes

- Disable VPNs before scanning for accurate results
- Large scans may require stable internet and higher system resources
