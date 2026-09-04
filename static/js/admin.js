/**
 * Anti-Matrix Admin & Application Portal JavaScript
 */
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alert notifications after 6 seconds
  const flashAlerts = document.querySelectorAll('.flash-alert');
  flashAlerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });

  // Client-side quick filter for tables
  const quickSearchInput = document.getElementById('admin-quick-search');
  if (quickSearchInput) {
    quickSearchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('.admin-table tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }
});
