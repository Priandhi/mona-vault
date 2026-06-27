# Token Dedup Persistence Fix (Jun9)

## Problem

The `_traded` Set in `token-filter.js` was in-memory only:

```javascript
const _traded = new Set();  // Lost on bot restart!
```

After bot restart, previously traded tokens were sniped again. Observed: LIFE sniped 3x, GO 2x, scooby 2x across restarts.

## Fix

Persist to `data/traded.json` on disk:

```javascript
import fs from "fs";
import path from "path";

const TRADED_FILE = path.resolve("data", "traded.json");
let _traded = new Set();

// Load on startup
try {
  const dir = path.dirname(TRADED_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (fs.existsSync(TRADED_FILE)) {
    const data = JSON.parse(fs.readFileSync(TRADED_FILE, "utf8"));
    _traded = new Set(data || []);
  }
} catch (e) {
  log("filter", `Failed to load traded list: ${e.message}`);
}

function saveTraded() {
  try {
    fs.writeFileSync(TRADED_FILE, JSON.stringify([..._traded]));
  } catch (e) { /* silent */ }
}

export function markTraded(mint) {
  _traded.add(mint);
  saveTraded();  // Persist immediately
}
```

## ES Module Gotcha

The charon-sniper project uses `"type": "module"` in package.json. `__dirname` is NOT available in ES module scope.

**Wrong:** `path.join(__dirname, "..", "data", "traded.json")` → throws `ReferenceError`

**Right:** `path.resolve("data", "traded.json")` — resolves from CWD

Alternative: `import { fileURLToPath } from "url"; const __filename = fileURLToPath(import.meta.url); const __dirname = path.dirname(__filename);`
