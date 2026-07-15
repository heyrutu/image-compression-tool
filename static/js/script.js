// ---------------------------------------------------------------------
// Hero block-grid animation
// An 8x8 grid (the same block size JPEG uses for its DCT encoding)
// starts "noisy" with many distinct tones, then periodically collapses
// into fewer, flatter tones — a visual stand-in for quantization.
// ---------------------------------------------------------------------
(function initBlockGrid() {
  const grid = document.getElementById('blockGrid');
  if (!grid) return;

  const SIZE = 8;
  const cells = [];
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const teal = [79, 209, 197];
  const amber = [240, 168, 104];
  const base = [27, 35, 48]; // surface-alt

  function mix(a, b, t) {
    return a.map((v, i) => Math.round(v + (b[i] - v) * t));
  }

  function toRgb(arr) {
    return `rgb(${arr[0]}, ${arr[1]}, ${arr[2]})`;
  }

  for (let i = 0; i < SIZE * SIZE; i++) {
    const cell = document.createElement('div');
    cell.className = 'blk';
    grid.appendChild(cell);
    cells.push(cell);
  }

  function randomNoisy() {
    cells.forEach((cell) => {
      const t = Math.random() * 0.5;
      const tint = Math.random() > 0.5 ? teal : amber;
      cell.style.background = toRgb(mix(base, tint, t));
    });
  }

  function compress() {
    // Group cells into 2x2 macro-blocks and flatten each to one tone,
    // mimicking how JPEG averages detail within a block at low quality.
    for (let r = 0; r < SIZE; r += 2) {
      for (let c = 0; c < SIZE; c += 2) {
        const t = 0.15 + Math.random() * 0.25;
        const tint = (r / 2 + c / 2) % 2 === 0 ? teal : amber;
        const color = toRgb(mix(base, tint, t));
        [
          r * SIZE + c, r * SIZE + c + 1,
          (r + 1) * SIZE + c, (r + 1) * SIZE + c + 1,
        ].forEach((idx) => {
          if (cells[idx]) cells[idx].style.background = color;
        });
      }
    }
  }

  randomNoisy();

  if (!prefersReducedMotion) {
    setTimeout(compress, 700);
    setInterval(() => {
      randomNoisy();
      setTimeout(compress, 700);
    }, 4200);
  } else {
    compress();
  }
})();

// ---------------------------------------------------------------------
// Dashboard: dropzone + live filename / quality feedback
// ---------------------------------------------------------------------
(function initDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const fileNameEl = document.getElementById('fileName');
  if (!dropzone || !fileInput) return;

  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function showFile(file) {
    if (!file) return;
    fileNameEl.textContent = `${file.name} — ${formatSize(file.size)}`;
  }

  fileInput.addEventListener('change', () => showFile(fileInput.files[0]));

  ['dragenter', 'dragover'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      fileInput.files = e.dataTransfer.files;
      showFile(file);
    }
  });
})();

// Disable the submit button after click to avoid duplicate uploads
(function initUploadForm() {
  const form = document.getElementById('uploadForm');
  const btn = document.getElementById('uploadBtn');
  if (!form || !btn) return;
  form.addEventListener('submit', () => {
    btn.disabled = true;
    btn.textContent = 'Compressing…';
  });
})();
