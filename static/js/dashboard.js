document.addEventListener('DOMContentLoaded', () => {
    const createBoardBtns = document.querySelectorAll('.create-board-btn, .new-board');

    createBoardBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/boards/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: 'Untitled Board',
                        content: '',
                        thumbnail: ''
                    })
                });

                const data = await response.json();

                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    console.error('Error creating board:', data.error);
                    alert('Failed to create board. Please try again.');
                }
            } catch (error) {
                console.error('Error creating board:', error);
                alert('Failed to create board. Please try again.');
            }
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

async function deleteBoard(boardId, boardTitle) {
    if (!confirm(`Are you sure you want to delete "${boardTitle}"?\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/boards/${boardId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            // Remove the board card from the DOM
            const boardCard = document.querySelector(`[data-board-id="${boardId}"]`);
            if (boardCard) {
                boardCard.style.opacity = '0';
                boardCard.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    boardCard.remove();
                }, 300);
            }
        } else {
            console.error('Error deleting board:', data.error);
            alert('Failed to delete board. Please try again.');
        }
    } catch (error) {
        console.error('Error deleting board:', error);
        alert('Failed to delete board. Please try again.');
    }
}
