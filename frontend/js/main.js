/* AgriThermal AI Main Global Script */

const API_BASE_URL = '/api';

function getCurrentUser() {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch (e) {
    return null;
  }
}

function setCurrentUser(user) {
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
  } else {
    localStorage.removeItem('user');
  }
  renderNavbar();
}

function logout() {
  localStorage.removeItem('user');
  window.location.href = '/login.html';
}

function renderNavbar() {
  const navContainer = document.getElementById('mainNav');
  if (!navContainer) return;

  const user = getCurrentUser();
  const currentPath = window.location.pathname;

  let authSectionHtml = '';
  if (user) {
    authSectionHtml = `
      <span class="user-badge">👤 ${user.name || user.email}</span>
      <button onclick="logout()" class="btn btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">Logout</button>
    `;
  } else {
    authSectionHtml = `
      <a href="/login.html" class="nav-link ${currentPath.includes('login') ? 'active' : ''}">Login</a>
      <a href="/register.html" class="btn btn-primary" style="padding: 0.4rem 1rem; font-size: 0.85rem;">Register</a>
    `;
  }

  navContainer.innerHTML = `
    <div class="nav-container">
      <a href="/index.html" class="logo">
        <div class="logo-icon">🌾</div>
        <span>AgriThermal <span style="color: var(--primary);">AI</span></span>
      </a>
      <ul class="nav-links">
        <li><a href="/index.html" class="nav-link ${currentPath === '/' || currentPath.includes('index') ? 'active' : ''}">Home</a></li>
        <li><a href="/predict.html" class="nav-link ${currentPath.includes('predict') ? 'active' : ''}">Analyze Scan</a></li>
        <li><a href="/history.html" class="nav-link ${currentPath.includes('history') ? 'active' : ''}">History</a></li>
        <li><a href="/dashboard.html" class="nav-link ${currentPath.includes('dashboard') ? 'active' : ''}">Dashboard</a></li>
        <li><a href="/performance.html" class="nav-link ${currentPath.includes('performance') ? 'active' : ''}">Model Specs</a></li>
      </ul>
      <div class="nav-auth">
        ${authSectionHtml}
      </div>
    </div>
  `;
}

document.addEventListener('DOMContentLoaded', () => {
  renderNavbar();
});
