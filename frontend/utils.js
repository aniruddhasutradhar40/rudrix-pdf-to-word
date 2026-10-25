// Pure helpers (no DOM) so they can be unit-tested with `node --test`.
export function formatBytes(n) {
  if (!Number.isFinite(n) || n < 0) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function validateFile(file, maxMb) {
  if (!file) return { ok: false, key: "errNoFile" };
  const nameOk = /\.pdf$/i.test(file.name || "");
  const typeOk = !file.type || file.type === "application/pdf";
  if (!nameOk || !typeOk) return { ok: false, key: "errNotPdf" };
  if (file.size === 0) return { ok: false, key: "errEmpty" };
  if (file.size > maxMb * 1024 * 1024) return { ok: false, key: "errTooLarge", params: { mb: maxMb } };
  return { ok: true };
}

export function normalizeBaseUrl(url) {
  const u = String(url || "").trim().replace(/\/+$/, "");
  return /^https?:\/\//i.test(u) ? u : "";
}

export function buildUrl(base, path) {
  return `${normalizeBaseUrl(base)}${path.startsWith("/") ? path : "/" + path}`;
}

export function languageValue(selected) {
  const allowed = ["eng", "ben", "eng+ben"];
  return allowed.includes(selected) ? selected : "eng";
}

export function errorMessage(payload, fallback) {
  const m = payload && payload.error && payload.error.message;
  return typeof m === "string" && m ? m : fallback;
}
