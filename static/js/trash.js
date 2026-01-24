document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const boardCards = document.querySelectorAll('.board-card.trash-card');

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

async function restoreBoard(boardId, boardTitle) {
    if (!confirm(`Restore "${boardTitle}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/boards/${boardId}/restore`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            const boardCard = document.querySelector(`[data-board-id="${boardId}"]`);
            if (boardCard) {
                boardCard.style.opacity = '0';
                boardCard.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    boardCard.remove();

                    const remainingBoards = document.querySelectorAll('.board-card.trash-card');
                    if (remainingBoards.length === 0) {
                        location.reload();
                    }
                }, 300);
            }

            alert(`"${boardTitle}" has been restored!`);
        } else {
            console.error('Error restoring board:', data.error);
            alert('Failed to restore board. Please try again.');
        }
    } catch (error) {
        console.error('Error restoring board:', error);
        alert('Failed to restore board. Please try again.');
    }
}

async function permanentDelete(boardId, boardTitle) {
    if (!confirm(`Permanently delete "${boardTitle}"?\n\nThis action CANNOT be undone!`)) {
        return;
    }

    if (!confirm(`Are you absolutely sure?\n\n"${boardTitle}" will be deleted forever!`)) {
        return;
    }

    try {
        const response = await fetch(`/api/boards/${boardId}/permanent-delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            const boardCard = document.querySelector(`[data-board-id="${boardId}"]`);
            if (boardCard) {
                boardCard.style.opacity = '0';
                boardCard.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    boardCard.remove();

                    const remainingBoards = document.querySelectorAll('.board-card.trash-card');
                    if (remainingBoards.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
        } else {
            console.error('Error deleting board:', data.error);
            alert('Failed to delete board permanently. Please try again.');
        }
    } catch (error) {
        console.error('Error deleting board:', error);
        alert('Failed to delete board permanently. Please try again.');
    }
}
