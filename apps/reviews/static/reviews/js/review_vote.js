// apps/reviews/static/reviews/js/review_vote.js
function initVoteButtons() {
    const voteButtons = document.querySelectorAll('.vote-btn');
    voteButtons.forEach(btn => {
        // Убираем старые обработчики
        btn.removeEventListener('click', handleVoteClick);
        btn.addEventListener('click', handleVoteClick);
    });
}

function handleVoteClick(e) {
    const btn = this;
    const reviewId = btn.dataset.reviewId;
    const isHelpful = btn.dataset.helpful === 'true';
    const url = `/reviews/vote/${reviewId}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `is_helpful=${isHelpful}`
    })
    .then(response => response.json())
    .then(data => {
        const helpfulSpan = document.querySelector(`.vote-btn[data-review-id="${reviewId}"][data-helpful="true"] .helpful-count`);
        const unhelpfulSpan = document.querySelector(`.vote-btn[data-review-id="${reviewId}"][data-helpful="false"] .unhelpful-count`);
        if (helpfulSpan) helpfulSpan.textContent = data.helpful;
        if (unhelpfulSpan) unhelpfulSpan.textContent = data.unhelpful;

        const btnHelpful = document.querySelector(`.vote-btn[data-review-id="${reviewId}"][data-helpful="true"]`);
        const btnUnhelpful = document.querySelector(`.vote-btn[data-review-id="${reviewId}"][data-helpful="false"]`);
        btnHelpful.classList.toggle('voted', data.user_vote === true);
        btnUnhelpful.classList.toggle('voted', data.user_vote === false);
    })
    .catch(error => console.error('Ошибка голосования:', error));
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', initVoteButtons);

// Делаем функцию доступной глобально для переинициализации
window.initVoteButtons = initVoteButtons;