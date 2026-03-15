import logging
import os
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_from_directory

from config import Config
from generate import OUTPUT_DIR
from pipeline import PosterPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app_web")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

progress_store: dict = {}
store_lock = threading.Lock()

# Progress weights: 3 steps -> 30%, 60%, 100%
PROGRESS_STEPS = [30, 60, 100]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_pipeline(task_id: str, image_path: str, comment: str | None) -> None:
    started_at = time.perf_counter()
    with store_lock:
        progress_store[task_id] = {
            "status": "running",
            "messages": [],
            "progress": None,
            "result_path": None,
            "description": None,
            "error": None,
            "started_at": started_at,
            "elapsed_sec": None,
        }

    step_index = [0]

    def progress_callback(msg: str) -> None:
        with store_lock:
            if task_id not in progress_store:
                return
            progress_store[task_id]["messages"].append(msg)
            idx = min(step_index[0], len(PROGRESS_STEPS) - 1)
            progress_store[task_id]["progress"] = PROGRESS_STEPS[idx]
            step_index[0] += 1

    try:
        logger.info("Pipeline started task_id=%s", task_id)
        config = Config()
        pipeline = PosterPipeline(config)
        filepath, description_text = pipeline.run(image_path, comment, progress_callback)
        elapsed = time.perf_counter() - started_at
        with store_lock:
            if task_id in progress_store:
                progress_store[task_id]["status"] = "done"
                progress_store[task_id]["progress"] = 100
                progress_store[task_id]["result_path"] = os.path.basename(filepath)
                progress_store[task_id]["description"] = description_text
                progress_store[task_id]["elapsed_sec"] = round(elapsed, 1)
        logger.info("Pipeline done task_id=%s elapsed=%.1fs", task_id, elapsed)
    except Exception as e:
        elapsed = time.perf_counter() - started_at
        logger.exception("Pipeline error task_id=%s: %s", task_id, e)
        with store_lock:
            if task_id in progress_store:
                progress_store[task_id]["status"] = "error"
                progress_store[task_id]["error"] = str(e)
                progress_store[task_id]["elapsed_sec"] = round(elapsed, 1)
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass


INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Туристическая открытка</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f0f7ff;
      --surface: #ffffff;
      --border: #c5d9f0;
      --text: #1e3a5f;
      --muted: #5a7a9e;
      --accent: #0ea5e9;
      --accent-hover: #0284c7;
      --accent-light: #e0f2fe;
      --success: #0d9488;
      --error: #dc2626;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'DM Sans', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem 1rem;
    }
    .container { max-width: 480px; margin: 0 auto; }
    h1 {
      font-size: 1.75rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      letter-spacing: -0.02em;
      color: var(--text);
    }
    .subtitle { color: var(--muted); font-size: 0.95rem; margin-bottom: 2rem; }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.75rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 3px rgba(14, 165, 233, 0.08);
    }
    .form-group {
      margin-bottom: 1.25rem;
    }
    .form-group:last-of-type { margin-bottom: 0; }
    label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 500;
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
      color: var(--text);
    }
    label svg { flex-shrink: 0; opacity: 0.9; }
    input[type="file"] {
      width: 100%;
      padding: 0.75rem 1rem;
      background: var(--accent-light);
      border: 1px solid var(--border);
      border-radius: 10px;
      color: var(--text);
      font-size: 0.9rem;
      cursor: pointer;
    }
    input[type="file"]::file-selector-button {
      margin-right: 0.75rem;
      padding: 0.35rem 0.75rem;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 0.85rem;
      cursor: pointer;
    }
    input[type="text"] {
      width: 100%;
      padding: 0.75rem 1rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      color: var(--text);
      font-size: 0.95rem;
    }
    input[type="text"]::placeholder { color: var(--muted); }
    input:focus { outline: none; border-color: var(--accent); }
    button[type="submit"] {
      width: 100%;
      margin-top: 0.5rem;
      padding: 0.875rem 1.5rem;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 10px;
      font-size: 1rem;
      font-weight: 500;
      font-family: inherit;
      cursor: pointer;
      transition: background 0.2s;
    }
    button[type="submit"]:hover:not(:disabled) { background: var(--accent-hover); }
    button[type="submit"]:disabled { opacity: 0.6; cursor: not-allowed; }
    .progress-section { display: none; margin-top: 1.5rem; }
    .progress-section.visible { display: block; }
    .uploaded-preview {
      margin-bottom: 1rem;
      text-align: center;
    }
    .uploaded-preview img {
      max-width: 100%;
      max-height: 200px;
      border-radius: 12px;
      border: 1px solid var(--border);
      object-fit: contain;
    }
    .uploaded-preview .label { font-size: 0.85rem; color: var(--muted); margin-bottom: 0.5rem; }
    .progress-bar-wrap {
      height: 8px;
      background: var(--border);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 0.75rem;
    }
    .progress-bar {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--accent), #38bdf8);
      border-radius: 4px;
      transition: width 0.4s ease;
    }
    .progress-label { font-size: 0.85rem; color: var(--muted); }
    .progress-time { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }
    #result { margin-top: 1.5rem; }
    #result .card { margin-bottom: 1rem; }
    #result .description {
      white-space: pre-wrap;
      font-size: 0.9rem;
      line-height: 1.55;
      color: var(--text);
    }
    #result img {
      width: 100%;
      border-radius: 12px;
      border: 1px solid var(--border);
      display: block;
    }
    #result .meta { font-size: 0.85rem; color: var(--success); margin-top: 0.75rem; }
    .error-msg { color: var(--error); font-size: 0.9rem; margin-top: 0.5rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Туристическая открытка</h1>
    <p class="subtitle">Загрузите фото места — получите описание и открытку.</p>

    <div class="card">
      <form id="form">
        <div class="form-group">
          <label for="image">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <path d="M21 15l-5-5L5 21"/>
            </svg>
            Изображение *
          </label>
          <input type="file" id="image" name="image" accept=".jpg,.jpeg,.png,.webp" required>
        </div>
        <div class="form-group">
          <label for="comment">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Комментарий (необязательно)
          </label>
          <input type="text" id="comment" name="comment" placeholder="Например: Шанхай, район Пудун">
        </div>
        <button type="submit" id="submit">Создать открытку</button>
      </form>
    </div>

    <div class="progress-section" id="progressSection">
      <div class="uploaded-preview" id="uploadedPreview">
        <div class="label">Загруженное изображение</div>
        <img id="uploadedImage" src="" alt="Загруженное фото" style="display:none;">
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar" id="progressBar"></div>
      </div>
      <div class="progress-label" id="progressLabel">Загрузка...</div>
      <div class="progress-time" id="progressTime"></div>
    </div>

    <div id="result"></div>
  </div>

  <script>
    const form = document.getElementById('form');
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressBar');
    const progressLabel = document.getElementById('progressLabel');
    const progressTime = document.getElementById('progressTime');
    const result = document.getElementById('result');
    const submitBtn = document.getElementById('submit');

    var uploadedImageUrl = null;

    function showProgress(visible) {
      progressSection.classList.toggle('visible', !!visible);
      if (!visible) {
        progressBar.style.width = '0%';
        progressLabel.textContent = '';
        progressTime.textContent = '';
        var img = document.getElementById('uploadedImage');
        if (img) { img.style.display = 'none'; img.removeAttribute('src'); }
      }
    }

    function setProgress(percent, label) {
      progressBar.style.width = Math.max(0, Math.min(100, percent)) + '%';
      progressLabel.textContent = label || '';
    }

    function formatTime(sec) {
      if (sec == null) return '—';
      sec = Math.round(Number(sec));
      if (sec >= 60) {
        var m = Math.floor(sec / 60);
        var s = sec % 60;
        return m + ' мин ' + s + ' с';
      }
      return sec + ' с';
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const file = document.getElementById('image').files[0];
      const comment = document.getElementById('comment').value.trim() || null;
      if (!file) return;

      if (uploadedImageUrl) URL.revokeObjectURL(uploadedImageUrl);
      uploadedImageUrl = URL.createObjectURL(file);
      var previewImg = document.getElementById('uploadedImage');
      previewImg.src = uploadedImageUrl;
      previewImg.style.display = 'block';

      submitBtn.disabled = true;
      result.innerHTML = '';
      showProgress(true);
      setProgress(8, 'Загрузка...');
      progressTime.textContent = '';

      const fd = new FormData();
      fd.append('image', file);
      if (comment) fd.append('comment', comment);

      const r = await fetch('/run', { method: 'POST', body: fd });
      const data = await r.json();
      if (!r.ok) {
        showProgress(false);
        submitBtn.disabled = false;
        result.innerHTML = '<div class="card"><span class="error-msg">' + (data.error || 'Ошибка загрузки').replace(/</g, '&lt;') + '</span></div>';
        return;
      }

      const taskId = data.task_id;
      var lastPct = 8;
      setProgress(8, 'Запуск...');

      const poll = setInterval(async () => {
        const s = await fetch('/status/' + taskId);
        const st = await s.json();
        var pct = lastPct;
        if (st.status === 'done') {
          pct = 100;
        } else if (st.progress != null && st.progress > 0) {
          pct = st.progress;
          lastPct = pct;
        }
        setProgress(pct, (st.messages && st.messages.length) ? st.messages[st.messages.length - 1] : 'Запуск...');
        if (st.elapsed_sec != null) progressTime.textContent = 'Время: ' + formatTime(st.elapsed_sec);

        if (st.status === 'done') {
          clearInterval(poll);
          submitBtn.disabled = false;
          setProgress(100, 'Готово');
          progressTime.textContent = 'Общее время обработки: ' + formatTime(st.elapsed_sec);
          result.innerHTML =
            '<div class="card"><p style="margin-bottom:0.5rem;font-weight:500;">Загруженное изображение</p><img src="' + uploadedImageUrl + '" alt="Загруженное фото" style="max-width:100%;border-radius:12px;border:1px solid var(--border);"></div>' +
            '<div class="card"><p style="margin-bottom:0.5rem;font-weight:500;">Описание</p><pre class="description">' + (st.description || '').replace(/</g, '&lt;') + '</pre></div>' +
            '<div class="card"><p style="margin-bottom:0.5rem;font-weight:500;">Открытка</p><img src="/output/' + (st.result_path || '') + '" alt="Poster"><p class="meta">Время обработки: ' + formatTime(st.elapsed_sec) + '</p></div>';
        } else if (st.status === 'error') {
          clearInterval(poll);
          submitBtn.disabled = false;
          progressLabel.textContent = 'Ошибка';
          progressBar.style.width = '0%';
          result.innerHTML = '<div class="card"><span class="error-msg">' + (st.error || 'Ошибка').replace(/</g, '&lt;') + '</span></div>';
        }
      }, 800);
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/run", methods=["POST"])
def run():
    if "image" not in request.files:
        logger.warning("POST /run: no image in request")
        return jsonify({"error": "Нет файла"}), 400
    file = request.files["image"]
    if not file or file.filename == "":
        return jsonify({"error": "Файл не выбран"}), 400
    if not allowed_file(file.filename):
        logger.warning("POST /run: invalid file type %s", file.filename)
        return jsonify({"error": "Разрешены только jpg, png, webp"}), 400

    comment = request.form.get("comment") or None
    task_id = str(uuid.uuid4())
    ext = file.filename.rsplit(".", 1)[1].lower()
    save_path = UPLOAD_DIR / f"{task_id}.{ext}"
    file.save(save_path)
    logger.info("Task created task_id=%s", task_id)

    thread = threading.Thread(
        target=run_pipeline,
        args=(task_id, str(save_path), comment),
    )
    thread.start()

    return jsonify({"task_id": task_id})


@app.route("/status/<task_id>")
def status(task_id):
    with store_lock:
        data = progress_store.get(task_id, {})
    return jsonify(data)


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    logger.info("Starting app_web on port 5000")
    app.run(debug=True, port=5000)
