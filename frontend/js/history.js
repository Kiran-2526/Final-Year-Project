/* History Page JavaScript */

document.addEventListener('DOMContentLoaded', () => {
  let allPredictions = [];

  const loadingState = document.getElementById('loadingState');
  const historyCard = document.getElementById('historyCard');
  const emptyState = document.getElementById('emptyState');
  const historyTbody = document.getElementById('historyTbody');
  const searchInput = document.getElementById('searchInput');
  const historyAlert = document.getElementById('historyAlert');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');

  fetchHistory();

  async function fetchHistory() {
    const user = getCurrentUser();
    const userId = user ? user.id : 1;

    try {
      const response = await fetch(`/api/predictions?userId=${userId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch prediction history.');
      }
      allPredictions = await response.json();
      renderTable(allPredictions);
    } catch (err) {
      loadingState.style.display = 'none';
      historyAlert.className = 'alert alert-error';
      historyAlert.textContent = err.message;
      historyAlert.style.display = 'flex';
      if (clearHistoryBtn) clearHistoryBtn.disabled = true;
    }
  }

  function renderTable(predictions) {
    loadingState.style.display = 'none';

    if (clearHistoryBtn) {
      clearHistoryBtn.disabled = (!allPredictions || allPredictions.length === 0);
    }

    if (!predictions || predictions.length === 0) {
      historyCard.style.display = 'none';
      emptyState.style.display = 'block';
      return;
    }

    emptyState.style.display = 'none';
    historyCard.style.display = 'block';

    historyTbody.innerHTML = predictions.map(pred => {
      const isHealthy = pred.disease === 'Healthy';
      const badgeClass = isHealthy ? 'badge-success' : (pred.status === 'HIGH_CONFIDENCE' ? 'badge-success' : 'badge-warning');
      const dateStr = new Date(pred.timestamp).toLocaleString();

      return `
        <tr>
          <td>
            <img
              src="${pred.imageUrl}"
              alt="Scan thumbnail"
              style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border-color); background: #000;"
              onerror="this.style.display='none'"
            />
          </td>
          <td style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(pred.imageName)}</td>
          <td style="color: ${isHealthy ? '#34d399' : '#fbbf24'}; font-weight: 700;">
            ${escapeHtml(pred.disease)}
          </td>
          <td style="font-family: var(--font-mono); font-weight: 600;">
            ${escapeHtml(pred.confidencePercentage)}
          </td>
          <td>
            <span class="badge ${badgeClass}">
              ${escapeHtml(pred.status.replace('_', ' '))}
            </span>
          </td>
          <td style="font-size: 0.85rem; color: var(--text-dim);">
            ${dateStr}
          </td>
        </tr>
      `;
    }).join('');
  }

  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', async () => {
      if (!allPredictions || allPredictions.length === 0) return;

      const confirmed = confirm(
        "Are you sure you want to clear your prediction history?\nThis action cannot be undone."
      );

      if (!confirmed) {
        return; // Cancel pressed, do nothing
      }

      const user = getCurrentUser();
      const userId = user ? user.id : 1;

      try {
        const response = await fetch(`/api/predictions?userId=${userId}`, {
          method: 'DELETE'
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || data.message || 'Failed to clear prediction history.');
        }

        allPredictions = [];
        renderTable([]);

        historyAlert.className = 'alert alert-success';
        historyAlert.textContent = 'Prediction history cleared successfully.';
        historyAlert.style.display = 'flex';

      } catch (err) {
        historyAlert.className = 'alert alert-error';
        historyAlert.textContent = err.message || 'An error occurred while clearing history.';
        historyAlert.style.display = 'flex';
      }
    });
  }

  searchInput.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allPredictions.filter(p => 
      p.disease.toLowerCase().includes(term) || 
      p.imageName.toLowerCase().includes(term)
    );
    renderTable(filtered);
  });

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
