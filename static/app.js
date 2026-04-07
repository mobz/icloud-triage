// Global app.js — minimal shared utilities.
// Page-specific logic lives inline in templates.

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('visible');
  }
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.visible').forEach(m => m.classList.remove('visible'));
  }
});
