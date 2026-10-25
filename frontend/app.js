import { buildUrl, errorMessage, formatBytes, languageValue, normalizeBaseUrl, validateFile } from "./utils.js";
import { t } from "./i18n.js";

const API = normalizeBaseUrl(window.RUDRIX_CONFIG && window.RUDRIX_CONFIG.API_BASE_URL);
const $ = (id) => document.getElementById(id);
const state = { lang: localStorage.getItem("rudrix_lang") || "en", file: null, caps: null, busy: false, job: null, maxMb: 25 };
const tr = (k, p) => t(state.lang, k, p);

function applyLang() {
  document.documentElement.lang = state.lang === "bn" ? "bn" : "en";
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = tr(el.dataset.i18n, { mb: state.maxMb }); });
  document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang)));
  renderServerPill(); renderOcrNote();
  if (state.job) renderResult(state.job);
}

function showBanner(msg, info = false) {
  const b = $("banner"); b.textContent = msg || ""; b.hidden = !msg; b.classList.toggle("info", info);
}

function renderServerPill() {
  const p = $("serverPill");
  const key = state.caps ? "serverOk" : state.caps === false ? "serverBad" : "serverWait";
  p.textContent = tr(key);
  p.className = "pill " + (state.caps ? "pill-ok" : state.caps === false ? "pill-bad" : "pill-wait");
}

function renderOcrNote() {
  const note = $("ocrNote"), sel = $("ocrLang"), toggle = $("ocrToggle");
  if (!state.caps) { note.textContent = ""; return; }
  const o = state.caps.ocr, has = o.available;
  toggle.disabled = !has; sel.disabled = !has;
  if (!has) { toggle.checked = false; note.textContent = tr("ocrUnavailable"); return; }
  const codes = o.languages.map((l) => l.code);
  note.textContent = tr("ocrReady", { langs: o.languages.map((l) => l.label).join(", ") }) + (codes.includes("ben") ? "" : tr("ocrNoBangla"));
}

function buildOcrSelect() {
  const sel = $("ocrLang"); sel.replaceChildren();
  const langs = state.caps.ocr.languages;
  const add = (v, label) => { const o = document.createElement("option"); o.value = v; o.textContent = label; sel.append(o); };
  langs.forEach((l) => add(l.code, l.label));
  if (langs.length > 1) add(langs.map((l) => l.code).join("+"), langs.map((l) => l.label.split(" ")[0]).join(" + "));
}

async function loadCaps() {
  if (!API) { showBanner(tr("configMissing")); state.caps = false; renderServerPill(); return; }
  try {
    const r = await fetch(buildUrl(API, "/api/capabilities"));
    if (!r.ok) throw new Error(String(r.status));
    state.caps = await r.json();
    state.maxMb = state.caps.limits.max_upload_mb;
    buildOcrSelect();
  } catch {
    state.caps = false; showBanner(tr("errNetwork"));
  }
  applyLang(); updateButton();
}

function updateButton() { $("convertBtn").disabled = !state.file || state.busy || !API; }

function setFile(file) {
  showBanner("");
  const v = validateFile(file, state.maxMb);
  if (!v.ok) { showBanner(tr(v.key, v.params || {})); return; }
  state.file = file; resetResult();
  $("fileName").textContent = file.name; $("fileSize").textContent = formatBytes(file.size);
  $("fileRow").hidden = false; updateButton();
}

function clearFile() { state.file = null; $("fileInput").value = ""; $("fileRow").hidden = true; updateButton(); }

function resetResult() { state.job = null; $("result").hidden = true; $("progress").hidden = true; }

function setProgress(text, pct) {
  const bar = $("progress").querySelector(".bar");
  $("progress").hidden = false; $("progressText").textContent = text;
  bar.classList.toggle("indet", pct == null);
  $("barFill").style.width = pct == null ? "" : `${pct}%`;
}

function convert() {
  if (!state.file || state.busy) return;
  state.busy = true; updateButton(); showBanner(""); resetResult();
  const fd = new FormData();
  fd.append("file", state.file);
  fd.append("mode", document.querySelector('input[name="mode"]:checked').value);
  fd.append("ocr", String($("ocrToggle").checked && !$("ocrToggle").disabled));
  fd.append("ocr_lang", languageValue($("ocrLang").value));
  const xhr = new XMLHttpRequest();
  xhr.open("POST", buildUrl(API, "/api/convert"));
  xhr.timeout = 6 * 60 * 1000;
  xhr.upload.onprogress = (e) => { if (e.lengthComputable) setProgress(tr("uploading", { pct: Math.round((e.loaded / e.total) * 100) }), (e.loaded / e.total) * 100); };
  xhr.upload.onload = () => setProgress(tr("processing"), null);
  const done = () => { state.busy = false; updateButton(); };
  xhr.onerror = () => { done(); $("progress").hidden = true; showBanner(tr("errNetwork")); };
  xhr.ontimeout = () => { done(); $("progress").hidden = true; showBanner(tr("errTimeout")); };
  xhr.onload = () => {
    done(); $("progress").hidden = true;
    let data = null; try { data = JSON.parse(xhr.responseText); } catch { /* not JSON */ }
    if (xhr.status === 200 && data && data.job_id) { state.job = data; renderResult(data); }
    else showBanner(errorMessage(data, tr("errGeneric")));
  };
  setProgress(tr("uploading", { pct: 0 }), 0);
  xhr.send(fd);
}

function renderResult(job) {
  const r = job.report;
  $("levelBadge").textContent = tr("level" + r.level); $("levelBadge").className = "badge " + r.level;
  $("levelMsg").textContent = r.message;
  $("downloadBtn").href = buildUrl(API, job.download_url);
  $("downloadBtn").textContent = `${tr("download")} (${formatBytes(job.size_bytes)})`;
  const ul = $("checks"); ul.replaceChildren();
  r.checks.forEach((c) => {
    const li = document.createElement("li");
    const name = document.createElement("span"); name.textContent = tr("c_" + c.name) === "c_" + c.name ? c.name : tr("c_" + c.name);
    const st = document.createElement("span"); st.className = "st " + c.status;
    st.textContent = `${tr("st_" + c.status)}${c.value != null ? " · " + c.value + (c.unit || "") : ""}`;
    const d = document.createElement("span"); d.className = "detail"; d.textContent = c.detail;
    li.append(name, st, d); ul.append(li);
  });
  const w = $("warns"); w.replaceChildren();
  r.warnings.forEach((x) => { const li = document.createElement("li"); li.textContent = x; w.append(li); });
  $("warnWrap").hidden = r.warnings.length === 0;
  $("disclaimer").textContent = `${r.disclaimer} ${tr("expires", { min: Math.round(job.expires_in_seconds / 60) })}`;
  $("result").hidden = false;
  $("result").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function deleteJob() {
  if (!state.job) return;
  try { await fetch(buildUrl(API, `/api/jobs/${state.job.job_id}`), { method: "DELETE" }); } catch { /* ignore */ }
  resetResult(); showBanner(tr("deleted"), true);
}

// ---- wiring ----
const drop = $("drop"), input = $("fileInput");
drop.addEventListener("click", () => input.click());
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
input.addEventListener("change", () => input.files[0] && setFile(input.files[0]));
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) setFile(f); });
$("clearFile").addEventListener("click", () => { clearFile(); resetResult(); });
$("convertBtn").addEventListener("click", convert);
$("againBtn").addEventListener("click", () => { clearFile(); resetResult(); showBanner(""); window.scrollTo({ top: 0, behavior: "smooth" }); });
$("deleteBtn").addEventListener("click", deleteJob);
document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
  state.lang = b.dataset.lang; localStorage.setItem("rudrix_lang", state.lang); applyLang();
}));
$("year").textContent = new Date().getFullYear();
applyLang(); loadCaps();
