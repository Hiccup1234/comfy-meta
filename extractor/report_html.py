from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_report_html(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    template = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Comfy Metadata Report</title>
  <style>
    :root {
      --bg: #f3f5f8;
      --card: #ffffff;
      --text: #142033;
      --muted: #5a6b85;
      --ok: #117a43;
      --err: #b42318;
      --border: #d9e1eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at 10% 0%, #e8f0ff, var(--bg) 45%);
      color: var(--text);
      font-family: "Segoe UI", Calibri, sans-serif;
    }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
    .hero {
      background: linear-gradient(135deg, #0f6dff, #0c8fcb);
      color: #fff;
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 8px 30px rgba(10, 30, 60, 0.25);
    }
    .hero h1 { margin: 0 0 6px; font-size: 28px; }
    .hero p { margin: 0; opacity: 0.95; }
    .grid {
      margin-top: 18px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
    }
    .stat {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
    }
    .stat .k { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
    .stat .v { margin-top: 4px; font-size: 24px; font-weight: 700; }
    .ok { color: var(--ok); }
    .err { color: var(--err); }
    .toolbar { margin-top: 16px; }
    input[type=\"search\"] {
      width: 100%;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: #fff;
      font-size: 14px;
    }
    .list { margin-top: 16px; display: grid; gap: 10px; }
    .item {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
    }
    .head {
      padding: 12px 14px;
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      cursor: pointer;
    }
    .head.no-toggle { cursor: default; }
    .toggle-btn {
      padding: 5px 10px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: #f4f7ff;
      color: #1f3a64;
      font-size: 12px;
      font-weight: 600;
    }
    .path { font-weight: 600; word-break: break-all; }
    .meta { color: var(--muted); font-size: 12px; }
    .body { border-top: 1px solid var(--border); padding: 12px; display: none; }
    .body.open { display: block; }
    pre {
      margin: 0;
      max-height: 380px;
      overflow: auto;
      background: #101827;
      color: #d9e8ff;
      padding: 12px;
      border-radius: 10px;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
    }
    pre.extracted {
      max-height: 520px;
      font-size: 14px;
      line-height: 1.55;
    }
    pre.raw {
      max-height: 220px;
      font-size: 11px;
      line-height: 1.35;
      opacity: 0.9;
    }
    .section-title { margin: 0 0 8px; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .download-row {
      display: flex;
      gap: 8px;
      margin: 8px 0 12px;
      flex-wrap: wrap;
    }
    .download-btn {
      border: 1px solid #bcd4ff;
      background: #eef4ff;
      color: #163a74;
      padding: 7px 10px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
    }
    .download-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .errbox {
      margin-top: 16px;
      background: #fff;
      border: 1px solid #fecaca;
      border-radius: 12px;
      padding: 12px;
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>Comfy Metadata Report</h1>
      <p id=\"runInfo\"></p>
    </div>

    <div class=\"grid\">
      <div class=\"stat\"><div class=\"k\">Discovered</div><div class=\"v\" id=\"sDiscovered\"></div></div>
      <div class=\"stat\"><div class=\"k\">Processed</div><div class=\"v ok\" id=\"sOk\"></div></div>
      <div class=\"stat\"><div class=\"k\">Failed</div><div class=\"v err\" id=\"sFailed\"></div></div>
      <div class=\"stat\"><div class=\"k\">Skipped Unsupported</div><div class=\"v\" id=\"sSkipped\"></div></div>
    </div>

    <div class=\"toolbar\">
      <input id=\"q\" type=\"search\" placeholder=\"Filter by path / metadata key / value\" />
    </div>

    <div id=\"resultList\" class=\"list\"></div>
    <div id=\"errorBox\" class=\"errbox\" style=\"display:none\"></div>
  </div>

  <script>
    const data = __PAYLOAD_JSON__;

    const runInfo = document.getElementById("runInfo");
    const sDiscovered = document.getElementById("sDiscovered");
    const sOk = document.getElementById("sOk");
    const sFailed = document.getElementById("sFailed");
    const sSkipped = document.getElementById("sSkipped");
    const resultList = document.getElementById("resultList");
    const errorBox = document.getElementById("errorBox");
    const q = document.getElementById("q");

    runInfo.textContent = `Run at ${data.run_at} | Tool v${data.tool_version}`;
    sDiscovered.textContent = data.totals.discovered;
    sOk.textContent = data.totals.processed_ok;
    sFailed.textContent = data.totals.failed;
    sSkipped.textContent = data.totals.skipped_unsupported;

    function esc(str) {
      return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function pretty(obj) {
      return JSON.stringify(obj, null, 2);
    }

    function safeName(text, fallback) {
      const cleaned = String(text || "")
        .replace(/[^A-Za-z0-9._-]+/g, "_")
        .replace(/^_+|_+$/g, "");
      return cleaned ? cleaned.slice(0, 80) : fallback;
    }

    function downloadJson(obj, filename) {
      const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    function render(results) {
      resultList.innerHTML = "";
      const single = results.length <= 1;
      for (const [idx, item] of results.entries()) {
        const metaText = `${item.format} | ${item.dimensions.width}x${item.dimensions.height} | ${item.size_bytes} bytes`;
        const searchable = JSON.stringify(item).toLowerCase();
        const comfy = item.comfyui || {};
        const workflow = comfy.workflow;
        const prompt = comfy.prompt;
        const stem = safeName((item.file_path || "").split(/[\\\\/]/).pop()?.replace(/\\.[^.]+$/, ""), `image_${idx + 1}`);

        const wrapper = document.createElement("div");
        wrapper.className = "item";
        wrapper.dataset.search = searchable;
        const headClass = single ? "head no-toggle" : "head";
        const bodyClass = single ? "body open" : "body";
        const toggle = single ? "" : '<button class="toggle-btn" type="button">Toggle</button>';

        wrapper.innerHTML = `
          <div class=\"${headClass}\">
            <div>
              <div class=\"path\">${esc(item.file_path)}</div>
              <div class=\"meta\">${esc(metaText)}</div>
            </div>
            ${toggle}
          </div>
          <div class=\"${bodyClass}\">
            <p class=\"section-title\">ComfyUI Metadata</p>
            <div class=\"download-row\">
              <button class=\"download-btn dl-workflow\" type=\"button\" ${workflow ? "" : "disabled"}>Download Workflow JSON</button>
              <button class=\"download-btn dl-prompt\" type=\"button\" ${prompt ? "" : "disabled"}>Download Prompt JSON</button>
            </div>
            <pre class=\"extracted\">${esc(pretty(item.comfyui || {}))}</pre>
            <p class=\"section-title\" style=\"margin-top:10px\">EXIF</p>
            <pre class=\"extracted\">${esc(pretty(item.exif || {}))}</pre>
            <p class=\"section-title\" style=\"margin-top:10px\">Raw Metadata</p>
            <pre class=\"raw\">${esc(pretty(item.raw_metadata || {}))}</pre>
          </div>
        `;

        const btn = wrapper.querySelector(".toggle-btn");
        const body = wrapper.querySelector(".body");
        if (!single && btn && body) {
          btn.addEventListener("click", () => body.classList.toggle("open"));
          wrapper.querySelector(".head").addEventListener("click", (e) => {
            if (e.target.tagName !== "BUTTON") body.classList.toggle("open");
          });
        }
        const dlWorkflow = wrapper.querySelector(".dl-workflow");
        const dlPrompt = wrapper.querySelector(".dl-prompt");
        if (dlWorkflow && workflow) {
          dlWorkflow.addEventListener("click", () => downloadJson(workflow, `${stem}_workflow.json`));
        }
        if (dlPrompt && prompt) {
          dlPrompt.addEventListener("click", () => downloadJson(prompt, `${stem}_prompt.json`));
        }
        resultList.appendChild(wrapper);
      }
    }

    function renderErrors(errors) {
      if (!errors || !errors.length) return;
      errorBox.style.display = "block";
      errorBox.innerHTML = `<p class=\"section-title\">Errors (${errors.length})</p><pre>${esc(pretty(errors))}</pre>`;
    }

    render(data.results || []);
    renderErrors(data.errors || []);

    q.addEventListener("input", () => {
      const term = q.value.trim().toLowerCase();
      const rows = [...document.querySelectorAll(".item")];
      for (const row of rows) {
        const ok = !term || row.dataset.search.includes(term);
        row.style.display = ok ? "block" : "none";
      }
    });
  </script>
</body>
</html>
"""
    return template.replace("__PAYLOAD_JSON__", payload_json)


def write_report_html(payload: dict[str, Any], output_path: Path) -> None:
    html = build_report_html(payload)
    output_path.write_text(html, encoding="utf-8")
