/* Predict Page JavaScript - Batch Thermal Image Support */

document.addEventListener('DOMContentLoaded', () => {
  const MAX_BATCH_SIZE = 10;
  let selectedFiles = []; // Array of File objects

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const previewArea = document.getElementById('previewArea');
  const previewGrid = document.getElementById('previewGrid');
  const fileCountBadge = document.getElementById('fileCountBadge');

  const uploadCard = document.getElementById('uploadCard');
  const resultCard = document.getElementById('resultCard');
  const predictAlert = document.getElementById('predictAlert');

  const analyzeBtn = document.getElementById('analyzeBtn');
  const addMoreBtn = document.getElementById('addMoreBtn');
  const clearAllBtn = document.getElementById('clearAllBtn');
  const scanAnotherBtn = document.getElementById('scanAnotherBtn');

  const btnIcon = document.getElementById('btnIcon');
  const btnText = document.getElementById('btnText');

  // Trigger file dialog on dropzone click
  dropzone.addEventListener('click', () => fileInput.click());
  addMoreBtn.addEventListener('click', () => fileInput.click());

  // Drag and drop handlers
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
      fileInput.value = ''; // Reset input so same files can be re-selected if needed
    }
  });

  function addFiles(files) {
    hideAlert();
    const validImages = [];

    for (const file of files) {
      if (!file.type.startsWith('image/')) {
        showAlert(`File '${file.name}' is not a valid image format. (JPG, PNG, BMP, WebP supported)`);
        continue;
      }
      validImages.push(file);
    }

    if (selectedFiles.length + validImages.length > MAX_BATCH_SIZE) {
      showAlert(`Maximum batch limit reached (${MAX_BATCH_SIZE} images max). Adding first ${MAX_BATCH_SIZE - selectedFiles.length} files.`);
      const remainingSlots = MAX_BATCH_SIZE - selectedFiles.length;
      selectedFiles.push(...validImages.slice(0, remainingSlots));
    } else {
      selectedFiles.push(...validImages);
    }

    renderPreviews();
  }

  function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderPreviews();
  }

  clearAllBtn.addEventListener('click', () => {
    selectedFiles = [];
    renderPreviews();
  });

  function renderPreviews() {
    if (selectedFiles.length === 0) {
      previewArea.style.display = 'none';
      dropzone.style.display = 'block';
      return;
    }

    dropzone.style.display = 'none';
    previewArea.style.display = 'block';

    fileCountBadge.textContent = `${selectedFiles.length} / ${MAX_BATCH_SIZE}`;

    previewGrid.innerHTML = selectedFiles.map((file, idx) => {
      const url = URL.createObjectURL(file);
      return `
        <div class="preview-item">
          <button type="button" class="remove-btn" data-index="${idx}" title="Remove image">&times;</button>
          <img src="${url}" alt="${escapeHtml(file.name)}">
          <div style="font-size: 0.8rem; font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
            ${escapeHtml(file.name)}
          </div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">
            ${(file.size / 1024).toFixed(0)} KB
          </div>
        </div>
      `;
    }).join('');

    // Attach click listeners to remove buttons
    previewGrid.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.currentTarget.getAttribute('data-index'));
        removeFile(idx);
      });
    });
  }

  scanAnotherBtn.addEventListener('click', () => {
    resultCard.style.display = 'none';
    uploadCard.style.display = 'block';
    selectedFiles = [];
    renderPreviews();
  });

  analyzeBtn.addEventListener('click', async () => {
    if (selectedFiles.length === 0) {
      showAlert('Please select or drop at least one thermal image file.');
      return;
    }

    const user = getCurrentUser();
    const userId = user ? user.id : 1;

    analyzeBtn.disabled = true;
    btnIcon.textContent = '⚙️';
    btnIcon.className = 'animate-spin';
    btnText.textContent = `Processing ${selectedFiles.length} Image(s) with PyTorch...`;
    hideAlert();

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('userId', userId);

      const response = await fetch('/api/predictions', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Failed to process thermal images.');
      }

      displayResults(data);
    } catch (err) {
      showAlert(err.message);
    } finally {
      analyzeBtn.disabled = false;
      btnIcon.textContent = '🔥';
      btnIcon.className = '';
      btnText.textContent = 'Analyze All Thermal Images';
    }
  });

  function displayResults(data) {
    uploadCard.style.display = 'none';
    resultCard.style.display = 'block';

    const now = new Date().toLocaleString();
    document.getElementById('batchTimestamp').textContent = `Executed: ${now}`;

    // Handle single result response format or batch response format
    const results = data.results ? data.results : [data];
    const total = data.totalUploaded !== undefined ? data.totalUploaded : (data.totalImages !== undefined ? data.totalImages : results.length);
    const validCount = data.validPredictions !== undefined ? data.validPredictions : results.filter(r => r.validImage !== false && !r.error).length;
    const rejectedCount = data.rejectedImages !== undefined ? data.rejectedImages : results.filter(r => r.validImage === false || r.error).length;
    const diseased = data.diseasedCount !== undefined ? data.diseasedCount : results.filter(r => r.validImage !== false && r.disease && r.disease !== 'Healthy').length;

    document.getElementById('sumTotal').textContent = total;
    document.getElementById('sumValid').textContent = validCount;
    document.getElementById('sumRejected').textContent = rejectedCount;
    document.getElementById('sumDiseased').textContent = diseased;

    const resultsGrid = document.getElementById('resultsGrid');
    resultsGrid.innerHTML = results.map(r => {
      if (r.error || r.validImage === false) {
        return `
          <div class="card" style="padding: 1.25rem; border: 1px solid rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.06);">
            <div style="display: flex; gap: 1rem; align-items: flex-start;">
              <div style="width: 80px; height: 80px; background: #000; border-radius: var(--radius-sm); border: 1px solid rgba(239,68,68,0.3); display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0;">
                <img src="${r.imageUrl || ''}" alt="" style="width: 100%; height: 100%; object-fit: contain;" onerror="this.style.display='none'">
              </div>
              <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                  <h4 style="color: #f87171; font-size: 1.05rem; font-weight: 800; margin-bottom: 0.2rem;">
                    ⚠️ Invalid Thermal Paddy Leaf Image
                  </h4>
                  <span class="badge badge-danger" style="font-size: 0.7rem;">${escapeHtml(r.status || 'REJECTED')}</span>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 0.5rem; word-break: break-all;">
                  ${escapeHtml(r.imageName)}
                </div>
                <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.4; margin-bottom: 0.5rem;">
                  ${escapeHtml(r.message || 'The uploaded image could not be recognized as a valid thermal paddy leaf image.')}
                </p>
                <div style="font-size: 0.8rem; color: #fca5a5; font-weight: 500;">
                  💡 Please upload a thermal image of a paddy leaf.
                </div>
              </div>
            </div>
          </div>
        `;
      }

      const isHealthy = r.disease === 'Healthy';
      const color = isHealthy ? '#34d399' : '#fbbf24';
      const badgeClass = isHealthy ? 'badge-success' : (r.status === 'HIGH_CONFIDENCE' ? 'badge-success' : 'badge-warning');

      return `
        <div class="card" style="padding: 1.25rem;">
          <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
            <img src="${r.imageUrl}" alt="" style="width: 100px; height: 100px; object-fit: contain; background: #000; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
            <div style="flex: 1;">
              <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 0.2rem; word-break: break-all;">
                ${escapeHtml(r.imageName)}
              </div>
              <div style="font-size: 1.3rem; font-weight: 800; color: ${color}; margin-bottom: 0.3rem;">
                ${escapeHtml(r.disease)}
              </div>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.1rem; font-weight: 800; font-family: var(--font-mono);">${escapeHtml(r.confidencePercentage)}</span>
                <span class="badge ${badgeClass}">${escapeHtml(r.status.replace('_', ' '))}</span>
              </div>
            </div>
          </div>
          <div style="background: rgba(0,0,0,0.25); padding: 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color); font-size: 0.82rem; color: var(--text-muted); line-height: 1.4;">
            ℹ️ ${escapeHtml(r.generalInfo || 'Thermal scan completed.')}
          </div>
        </div>
      `;
    }).join('');
  }

  function showAlert(msg) {
    predictAlert.textContent = msg;
    predictAlert.style.display = 'flex';
  }

  function hideAlert() {
    predictAlert.style.display = 'none';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
