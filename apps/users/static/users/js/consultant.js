// static/users/js/consultant.js

document.addEventListener('DOMContentLoaded', function() {
    // Модальное окно для создания записи
    const modal = document.getElementById('slot-form-modal');
    if (!modal) return;
    
    const closeBtn = modal.querySelector('.modal-close');
    const openButtons = document.querySelectorAll('.open-slot-form');

    openButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            document.getElementById('slot-date').value = this.dataset.date;
            document.getElementById('slot-time').value = this.dataset.time;
            modal.style.display = 'flex';
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});