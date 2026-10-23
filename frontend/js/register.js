/* Register Page JavaScript */

document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('registerForm');
  const alertDiv = document.getElementById('registerAlert');
  const submitBtn = document.getElementById('submitBtn');

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!name || !email || !password) {
      showAlert('Please fill in all required fields.', 'error');
      return;
    }

    if (password.length < 6) {
      showAlert('Password must be at least 6 characters long.', 'error');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating Account...';
    hideAlert();

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.error || 'Failed to register account.');
      }

      // Save user in session
      setCurrentUser(data);

      showAlert('Account created successfully! Redirecting...', 'success');
      setTimeout(() => {
        window.location.href = '/predict.html';
      }, 700);
    } catch (err) {
      showAlert(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Account';
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
