# WebToApp — shiaho777/web-to-app

**Research date:** 2026-06-24
**Repo:** https://github.com/shiaho777/web-to-app
**License:** Unlicense (fully open)
**Stack:** Kotlin, Jetpack Compose, Material 3, Koin DI, Room DB

## Ringkasan

WebToApp adalah **on-device APK builder untuk Android** — bisa bikin APK langsung dari HP tanpa Android Studio, tanpa VPS build, tanpa remote service. Web app → APK/AAB tinggal tap.

## Fitur Kunci

### Input yang didukung
| Input | Output | 
|-------|--------|
| URL website | WebView APK |
| HTML/CSS/JS | Localhost APK |
| React/Vue/Vite build | Frontend APK |
| Node.js/PHP/Python/Go | APK + local server |
| WordPress | APK + PHP + SQLite |
| Gambar/video | Gallery/media APK |
| Multi site | Tab/card/feed APK |

### Highlights
- **Binary APK builder**: AXML/ARSC patching, resource injection, V1/V2/V3 signing
- **AAB export**: Rewrite targetSdk ke 35 (Play Store ready), signed locally
- **WebView control**: Custom UA, JS/CSS injection, DNS-over-HTTPS, proxy, desktop mode
- **Engine alternatif**: System WebView + optional GeckoView (Firefox)
- **Local runtimes**: Node.js, PHP 8.4, Python (Flask/Django/FastAPI), Go, WordPress
- **Extensions**: Built-in modules, userscripts (GM_*), MV3 Chrome extensions
- **Security**: PBKDF2+AES-256-GCM encryption, anti-Frida, fingerprint disguise (28 vectors)
- **AI Coding**: 20+ skill prompts built-in — generate HTML apps, modules, userscripts, dll
- **Ad blocking**: 23 built-in filter lists, cosmetic MutationObserver filtering

### Keystore Management
- Create, import, export, delete keystores
- Support PKCS12/PFX/JKS/BKS
- V1/V2/V3 signature scheme controls

## Relevansi untuk Proyek Kita

### 1. ICLIX
- Bisa package ICLIX frontend sebagai native Android app
- WebView-based, bisa custom toolbar, splash screen, notification
- Tidak perlu hosting terpisah

### 3. Development workflow baru
- Build/edit web app di VPS/laptop
- Transfer ke HP
- WebToApp package & sign → APK siap install/share
- Bypass Android Studio/GitHub Actions untuk build

## Arsitektur
- 2 Gradle modules: `app` (builder host) + `shell` (runtime embedded di generated APK)
- `clone-host`: untuk app cloning/repackaging
- `modules/`: community extension marketplace via GitHub PR
- AI skills di `app/src/main/assets/skills/` — 20+ type
- Sample projects di `app/src/main/assets/sample_projects/` — 68 contoh

## Target SDK
- Host: targetSdk 28 (biar bisa fork native binaries — PHP, Node, Go, dll)
- Generated apps: AAB exporter rewrite ke 35 untuk Play Store
- Web/HTML/frontend/media apps: fully Play-publishable
- Native runtime apps: APK-only (Play Store gak izinkan binary forking)

## AI Skills yang Berguna
- `html-app` — Single-page HTML/CSS/JS app
- `react-app` — React/Vite app
- `vue-app` — Vue app
- `gallery-app` — Media gallery
- `nodejs-app`, `php-app`, `python-app`, `go-app` — Backend runtimes
- `module-js`, `module-style`, `module-userscript` — Extensions
- `multi-web-app` — Multi-site aggregator
- `debug`, `refactor`, `optimize`, `explain`, `i18n`, `imagery`

## Kontak Developer
- Telegram: t.me/webtoapp777
- X: @shiaho777
- GitHub: shiaho777
