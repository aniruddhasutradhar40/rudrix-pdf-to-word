import test from "node:test";
import assert from "node:assert/strict";
import { buildUrl, errorMessage, formatBytes, languageValue, normalizeBaseUrl, validateFile } from "../utils.js";
import { STRINGS, t } from "../i18n.js";

const f = (name, size, type = "application/pdf") => ({ name, size, type });

test("validateFile accepts a normal PDF", () => assert.equal(validateFile(f("a.pdf", 1000), 25).ok, true));
test("validateFile rejects non-PDF, empty and oversize", () => {
  assert.equal(validateFile(f("a.docx", 10, "application/msword"), 25).key, "errNotPdf");
  assert.equal(validateFile(f("a.pdf", 0), 25).key, "errEmpty");
  assert.equal(validateFile(f("a.pdf", 26 * 1024 * 1024), 25).key, "errTooLarge");
  assert.equal(validateFile(null, 25).key, "errNoFile");
});
test("formatBytes", () => { assert.equal(formatBytes(512), "512 B"); assert.equal(formatBytes(2048), "2.0 KB"); assert.equal(formatBytes(5 * 1024 * 1024), "5.0 MB"); });
test("URL helpers", () => {
  assert.equal(normalizeBaseUrl("https://api.example.com/"), "https://api.example.com");
  assert.equal(normalizeBaseUrl("javascript:alert(1)"), "");
  assert.equal(buildUrl("https://x.io/", "/api/convert"), "https://x.io/api/convert");
});
test("languageValue only allows known codes", () => { assert.equal(languageValue("ben"), "ben"); assert.equal(languageValue("; rm -rf"), "eng"); });
test("errorMessage falls back", () => {
  assert.equal(errorMessage({ error: { message: "bad" } }, "x"), "bad");
  assert.equal(errorMessage(null, "fallback"), "fallback");
});
test("i18n: every English key exists in Bangla and params interpolate", () => {
  for (const k of Object.keys(STRINGS.en)) assert.ok(k in STRINGS.bn, `missing bn key ${k}`);
  assert.equal(t("en", "errTooLarge", { mb: 25 }), "File is larger than 25 MB.");
});
