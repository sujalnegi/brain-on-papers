document.addEventListener('DOMContentLoaded', () => {
    const createBoardBtns = document.querySelectorAll('.create-board-btn, .new-board');

    createBoardBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            window.location.href = '/whiteboard';
        });
    });

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });

    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const boardCards = document.querySelectorAll('.board-card:not(.new-board)');

            boardCards.forEach(card => {
                const title = card.querySelector('.board-title')?.textContent.toLowerCase();
                if (title && title.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});
