// Bring server-side validation into view, including collapsed groups.
document.addEventListener('DOMContentLoaded', () => {
    const summary = document.getElementById('encar-errors');
    if (!summary) return;
    summary.focus({preventScroll: true});
    summary.scrollIntoView({block: 'start'});
    summary.addEventListener('click', (event) => {
        const link = event.target.closest('a[href^="#"]');
        if (!link) return;
        const target = document.getElementById(link.getAttribute('href').slice(1));
        if (!target) return;
        event.preventDefault();
        target.querySelectorAll('details').forEach((details) => { details.open = true; });
        target.focus({preventScroll: true});
        target.scrollIntoView({block: 'start', behavior: 'smooth'});
    });
});
