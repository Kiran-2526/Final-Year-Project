/* Login Page JavaScript */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const alertDiv = document.getElementById('loginAlert');
  const submitBtn = document.getElementById('submitBtn');

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showAlert('Please enter both email and password.', 'error');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in...';
    hideAlert();

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Failed to authenticate user.');
      }

      // Save user in session
      setCurrentUser(data);

      showAlert('Login successful! Redirecting...', 'success');
      setTimeout(() => {
        window.location.href = '/predict.html';
      }, 700);
    } catch (err) {
      showAlert(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  });

  function showAlert(msg, type) {
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = msg;
    alertDiv.style.display = 'block';
  }

  function hideAlert() {
    alertDiv.style.display = 'none';
  }
});
