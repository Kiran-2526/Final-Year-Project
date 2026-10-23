/* Dashboard Page JavaScript */

document.addEventListener('DOMContentLoaded', () => {
  const loadingDash = document.getElementById('loadingDash');
  const dashContent = document.getElementById('dashContent');
  const dashAlert = document.getElementById('dashAlert');

  const statTotal = document.getElementById('statTotal');
  const statHealthy = document.getElementById('statHealthy');
  const statDiseased = document.getElementById('statDiseased');
  const distContainer = document.getElementById('distContainer');
  const recentContainer = document.getElementById('recentContainer');

  fetchStats();

  async function fetchStats() {
    const user = getCurrentUser();
    const userId = user ? user.id : 1;

    try {
      const response = await fetch(`/api/dashboard/stats?userId=${userId}`);
      if (!response.ok) {
        throw new Error('Failed to load dashboard statistics.');
      }
      const data = await response.json();
      renderDashboard(data);
    } catch (err) {
      loadingDash.style.display = 'none';
      dashAlert.textContent = err.message;
      dashAlert.style.display = 'flex';
    }
  }

  function renderDashboard(data) {
    loadingDash.style.display = 'none';
    dashContent.style.display = 'block';

    statTotal.textContent = data.totalPredictions || 0;
    statHealthy.textContent = data.healthyPredictions || 0;
    statDiseased.textContent = data.diseasedPredictions || 0;

    // Render Disease Distribution
    const dist = data.diseaseDistribution || {};
    const total = data.totalPredictions || 1;
    const entries = Object.entries(dist);

    if (entries.length === 0) {
      distContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No scan data collected yet.</p>';
    } else {
      distContainer.innerHTML = entries.map(([disease, count]) => {
        const pct = Math.round((count / total) * 100);
        const isHealthy = disease === 'Healthy';
        const color = isHealthy ? '#34d399' : '#fbbf24';

        return `
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.3rem;">
              <span>${escapeHtml(disease)}</span>
              <span style="color: ${color}; font-family: var(--font-mono);">${count} (${pct}%)</span>
            </div>
            <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
              <div style="width: ${pct}%; height: 100%; background: ${color}; border-radius: 4px;"></div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render Recent Scans
    const recents = data.recentPredictions || [];
    if (recents.length === 0) {
      recentContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No recent scans recorded.</p>';
    } else {
      recentContainer.innerHTML = recents.map(r => {
        const isHealthy = r.disease === 'Healthy';
        return `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem; background: rgba(0,0,0,0.25); border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
              <img src="${r.imageUrl}" alt="" style="width: 38px; height: 38px; object-fit: cover; border-radius: 6px; background: #000;" onerror="this.style.display='none'">
              <div>
                <div style="font-weight: 600; font-size: 0.88rem; color: ${isHealthy ? '#34d399' : '#fbbf24'};">${escapeHtml(r.disease)}</div>
                <div style="font-size: 0.78rem; color: var(--text-dim);">${escapeHtml(r.imageName)}</div>
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-family: var(--font-mono); font-size: 0.85rem; font-weight: 600;">${escapeHtml(r.confidencePercentage)}</div>
              <div style="font-size: 0.75rem; color: var(--text-dim);">${new Date(r.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            </div>
          </div>
        `;
      }).join('');
    }
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
