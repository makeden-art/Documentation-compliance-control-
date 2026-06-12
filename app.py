"""Сервис нормоконтроля (Documentation-compliance-control)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

import normocontrol_engine

router = APIRouter()

app = FastAPI(title="Нормоконтроль")


@router.get("/norm", response_class=HTMLResponse)
async def norm_page() -> str:
    html = """
    <!DOCTYPE html>
    <html lang="ru">
      <head>
        <meta charset="utf-8" />
        <title>Нормоконтроль</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          :root {
            color-scheme: light dark;
            --bg: #0f172a;
            --bg-card: #111827;
            --accent: #38bdf8;
            --text: #e5e7eb;
            --text-soft: #9ca3af;
          }
          body {
            margin: 0; min-height: 100vh;
            font-family: system-ui, -apple-system, sans-serif;
            background: radial-gradient(circle at top left, #1e293b, #020617);
            color: var(--text);
            display: flex; flex-direction: column; align-items: center; padding: 40px 20px;
          }
          .container { max-width: 800px; width: 100%; }
          .card {
            background: var(--bg-card); border: 1px solid rgba(148, 163, 184, 0.3);
            border-radius: 20px; padding: 40px; text-align: center;
          }
          .title { margin-bottom: 30px; text-align: center; }
          .title h1 { margin: 0 0 10px 0; }
          .title p { color: var(--text-soft); margin: 0; }
          .back-link { display: inline-block; margin-bottom: 20px; color: var(--accent); text-decoration: none; font-size: 14px; font-weight: 500; }
          
          /* Form styles (similar to calc) */
          .card {
            background: var(--bg-card); border: 1px solid rgba(148, 163, 184, 0.3);
            border-radius: 20px; padding: 24px; width: 100%;
          }
          .drop-zone {
            border: 2px dashed rgba(148, 163, 184, 0.3); border-radius: 12px;
            padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.2s ease;
            background: rgba(15, 23, 42, 0.5); margin-bottom: 24px;
          }
          .drop-zone:hover, .drop-zone.drag-over {
            border-color: var(--accent); background: var(--accent-soft);
          }
          .primary-btn {
            background: var(--accent); color: #000; border: none; padding: 12px 24px;
            border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;
            display: flex; align-items: center; justify-content: center; gap: 8px;
            font-size: 15px; margin-top: 10px;
          }
          .primary-btn:hover { background: #7dd3fc; }
          .file-chip {
            display: none; background: rgba(148, 163, 184, 0.1); padding: 8px 12px;
            border-radius: 8px; font-size: 13px; color: var(--accent); margin-top: 12px;
          }
          
          /* Results styles */
          .results-container { display: none; margin-top: 24px; text-align: left; }
          .result-box { padding: 16px; border-radius: 12px; margin-bottom: 16px; background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border); }
          .result-box.passed { border-color: rgba(34, 197, 94, 0.5); background: rgba(34, 197, 94, 0.05); }
          .result-box.failed { border-color: rgba(249, 115, 115, 0.5); background: rgba(249, 115, 115, 0.05); }
          .result-title { font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
          .error-list { margin: 0; padding-left: 20px; font-size: 14px; color: var(--danger); line-height: 1.6; }
          .warning-list { margin: 0; padding-left: 20px; font-size: 14px; color: #fbbf24; line-height: 1.6; }
          .loader { display: none; text-align: center; color: var(--accent); margin-top: 20px; }
        </style>
      </head>
      <body>
        <div class="container">
          <a href="/" class="back-link">← На главную</a>
          <div class="title">
            <h1>Нормоконтроль (Beta)</h1>
            <p>Проверка оформления чертежей и документов по ГОСТ (DXF, DWG, PDF, DOCX, XLSX, ZIP)</p>
          </div>
          <div class="card">
            <form id="norm-form">
              <div class="drop-zone" id="drop-zone">
                <div>Перетащите файлы или ZIP-архив сюда<br>или нажмите, чтобы выбрать с диска</div>
                <div class="file-chip" id="file-chip">Файл: <b class="name"></b></div>
                <input type="file" id="file-input" accept=".zip,.dxf,.dwg,.docx,.xlsx,.pdf" style="display:none" />
              </div>
              <button type="submit" class="primary-btn" id="submit-btn">Проверить чертеж</button>
            </form>
            
            <div class="loader" id="loader">Анализ файла... ⏳</div>
            
            <div class="results-container" id="results">
              <div class="result-box" id="result-status"></div>
            </div>
          </div>
        </div>
        
        <script>
          const dropZone = document.getElementById("drop-zone");
          const fileInput = document.getElementById("file-input");
          const fileChip = document.getElementById("file-chip");
          const fileChipName = fileChip.querySelector(".name");
          const form = document.getElementById("norm-form");
          const submitBtn = document.getElementById("submit-btn");
          const loader = document.getElementById("loader");
          const results = document.getElementById("results");
          const resultStatus = document.getElementById("result-status");

          dropZone.onclick = () => fileInput.click();
          
          fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
              fileChipName.textContent = file.name;
              fileChip.style.display = "inline-block";
              results.style.display = "none";
            }
          };

          dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); };
          dropZone.ondragleave = (e) => { dropZone.classList.remove("drag-over"); };
          dropZone.ondrop = (e) => {
            e.preventDefault(); dropZone.classList.remove("drag-over");
            if (e.dataTransfer.files.length) {
              fileInput.files = e.dataTransfer.files;
              fileInput.dispatchEvent(new Event("change"));
            }
          };

          form.onsubmit = async (e) => {
            e.preventDefault();
            if (!fileInput.files.length) return alert("Выберите файл!");
            
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            
            submitBtn.disabled = true;
            loader.style.display = "block";
            results.style.display = "none";
            
            try {
              const res = await fetch("/process_norm", { method: "POST", body: formData });
              const data = await res.json();
              
              if (!res.ok) throw new Error(data.error || "Ошибка сервера");
              
              results.style.display = "block";
              
              let html = "";
              
              if (data.batch_summary) {
                // Batch processing mode
                const summary = data.batch_summary;
                html += `<div class="result-title">📊 Результаты проверки (${summary.total} файлов)</div>`;
                html += `<p style="font-size:14px; margin-bottom:16px;">✅ Прошло: ${summary.passed} | ❌ Ошибок: ${summary.failed}</p>`;
                
                for (const [filename, report] of Object.entries(data.files)) {
                    if (report.passed) {
                        html += `<div class="result-box passed">
                            <div class="result-title">📄 ${filename} - ✅ ГОСТ</div>`;
                        if (report.stamp) {
                            html += `<div style="font-size:12px; color:var(--text-soft);">🛡️ Наложен крипто-штамп: ${report.stamp.hash.substring(0,16)}...</div>`;
                        }
                        html += `</div>`;
                    } else {
                        html += `<div class="result-box failed">
                            <div class="result-title">📄 ${filename} - ❌ ОШИБКИ</div>`;
                        if (report.error) {
                            html += `<p style="color:var(--danger); font-size:14px;">${report.error}</p>`;
                        } else if (report.errors) {
                            html += `<ul class="error-list">` + report.errors.map(e => `<li>${e}</li>`).join('') + `</ul>`;
                        }
                        html += `</div>`;
                    }
                }
              } else {
                 // Fallback for single file (if normocontrol_engine returned single result directly, though it wraps in batch now)
                 if (data.passed) {
                   resultStatus.className = "result-box passed";
                   html += `<div class="result-title">✅ Нормоконтроль пройден!</div>`;
                   if (data.stamp) {
                       html += `<div style="font-size:12px; color:var(--text-soft);">🛡️ Наложен крипто-штамп: ${data.stamp.hash.substring(0,16)}...</div>`;
                   }
                 } else {
                   resultStatus.className = "result-box failed";
                   html += `<div class="result-title">❌ Найдены ошибки (${data.total_errors})</div>`;
                 }
                 if (data.errors && data.errors.length) {
                   html += `<ul class="error-list">` + data.errors.map(e => `<li>${e}</li>`).join('') + `</ul>`;
                 }
                 if (data.warnings && data.warnings.length) {
                   html += `<div style="margin-top:16px;" class="result-title">⚠️ Предупреждения (${data.total_warnings})</div>`;
                   html += `<ul class="warning-list">` + data.warnings.map(e => `<li>${e}</li>`).join('') + `</ul>`;
                 }
              }
              
              resultStatus.className = ""; // clear old classes
              resultStatus.innerHTML = html;
              
            } catch (err) {
              alert(err.message);
            } finally {
              submitBtn.disabled = false;
              loader.style.display = "none";
            }
          };
        </script>
      </body>
    </html>
    """
    return html

@router.post("/process_norm")
async def process_norm(file: UploadFile = File(...)):
    tmp_dir = Path(tempfile.mkdtemp(prefix="norm_control_"))
    in_path = tmp_dir / file.filename
    data = await file.read()
    in_path.write_bytes(data)
    
    try:
        report = normocontrol_engine.process_batch(str(in_path))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Внутренняя ошибка сервера: {str(e)}"})
        
    return JSONResponse(report)

app.include_router(router)
