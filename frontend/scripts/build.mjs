// Copies the static site to dist/ and writes config.js from RUDRIX_API_URL (used by Vercel).
import { cpSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });
for (const f of ["index.html", "styles.css", "app.js", "utils.js", "i18n.js", "favicon.svg"]) cpSync(join(root, f), join(dist, f));

const api = (process.env.RUDRIX_API_URL || "").trim().replace(/\/+$/, "");
if (!api) console.warn("[rudrix] RUDRIX_API_URL is not set; falling back to http://localhost:8000");
if (api && !/^https?:\/\//i.test(api)) { console.error("[rudrix] RUDRIX_API_URL must start with http:// or https://"); process.exit(1); }
writeFileSync(join(dist, "config.js"), `window.RUDRIX_CONFIG = { API_BASE_URL: ${JSON.stringify(api || "http://localhost:8000")} };\n`);
console.log(`[rudrix] built dist/ with API_BASE_URL=${api || "http://localhost:8000"}`);
