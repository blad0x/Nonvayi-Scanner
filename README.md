# 🥖 NONVAYI Scanner

اسکنر پیشرفته CDN Fronting و TLS Edge ساخته‌شده با Python + PyQt6

## ویژگی‌ها

- اسکن سریع IP به‌صورت Async
- اعتبارسنجی TLS/SSL
- تشخیص CDN Fronting
- بررسی ICMP + TCP Fallback
- پشتیبانی از CIDR Expansion
- لاگ زنده و لحظه‌ای اسکن
- سیستم خودکار مدیریت و چرخش خروجی‌ها

## ساخته‌شده با

- Python
- PyQt6
- asyncio
- SSL/TLS Sockets
- موتور اختصاصی UI و انیمیشن

## توسعه با کمک هوش مصنوعی

این پروژه به‌صورت کامل با کمک هوش مصنوعی نوشته، بهینه‌سازی و دیباگ شده است.

انیمیشن‌های رابط کاربری، منطق اعتبارسنجی TLS، سیستم Async Networking و بهینه‌سازی‌های اسکنر با کمک توسعه مبتنی بر AI بهبود داده شده‌اند.

با این حال، ایده اصلی پروژه، منطق کلی اسکن و مفهوم پایه پروژه توسط صاحب پروژه طراحی و ساخته شده است.

## نحوه استفاده

### 1. نصب پیش‌نیازها

```bash
pip install PyQt6
2. اجرای فایل اصلی
python main.py
3. شروع اسکن
لیست IP یا رنج‌های CIDR را بارگذاری کنید
پروفایل عملکرد را انتخاب کنید
موتور TLS را فعال یا غیرفعال کنید
اسکن را شروع کنید

نتایج به‌صورت خودکار در مسیرهای زیر ذخیره می‌شوند:

output.txt
پوشه reportlogs
نسخه کامپایل‌شده

یک نسخه اجرایی (EXE) آماده نیز برای کاربرانی که نمی‌خواهند Python را به‌صورت دستی نصب کنند ارائه شده است.

نکات
برای دقت بیشتر اسکن، VPN را غیرفعال کنید
اسکن‌های بزرگ ممکن است به اینترنت پایدار و منابع سخت‌افزاری بیشتری نیاز داشته باشند




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
2. Run main.py
python main.py
3. Start Scanning
Load IP list or CIDR ranges
Select performance preset
Enable/Disable TLS engine
Start scan

Results will be saved automatically into:

output.txt
reportlogs folder
Compiled Version

A precompiled executable version is also included for users who don't want to install Python manually.

Notes
Disable VPNs before scanning for accurate results
Large scans may require stable internet and higher system resources
