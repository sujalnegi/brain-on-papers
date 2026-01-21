class Whiteboard {
    constructor() {
        this.canvas = document.getElementById('whiteboard-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.isDrawing = false;
        this.currentTool = 'pen';
        this.currentColor = '#6C7D47';
        this.brushSize = 3;
        this.history = [];
        this.historyStep = -1;

        this.initCanvas();
        this.initTools();
        this.initEvents();
    }

    initCanvas() {
        const wrapper = document.querySelector('.canvas-wrapper');
        const padding = 40;
        this.canvas.width = wrapper.clientWidth - padding;
        this.canvas.height = wrapper.clientHeight - padding;

        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.saveState();
    }

    initTools() {
        const toolButtons = document.querySelectorAll('.tool-btn[data-tool]');
        toolButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                toolButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentTool = btn.dataset.tool;
                this.updateCursor();
            });
        });

        const colorPicker = document.getElementById('color-picker');
        colorPicker.addEventListener('input', (e) => {
            this.currentColor = e.target.value;
        });

        const brushSize = document.getElementById('brush-size');
        const brushSizeLabel = document.querySelector('.brush-size-label');
        brushSize.addEventListener('input', (e) => {
            this.brushSize = e.target.value;
            brushSizeLabel.textContent = `${this.brushSize}px`;
        });

        document.getElementById('undo-btn').addEventListener('click', () => this.undo());
        document.getElementById('redo-btn').addEventListener('click', () => this.redo());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearCanvas());
        document.getElementById('save-btn').addEventListener('click', () => this.save());
        document.getElementById('export-btn').addEventListener('click', () => this.export());

        document.getElementById('zoom-in').addEventListener('click', () => this.zoom(1.1));
        document.getElementById('zoom-out').addEventListener('click', () => this.zoom(0.9));
    }

    initEvents() {
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', () => this.stopDrawing());
        this.canvas.addEventListener('mouseout', () => this.stopDrawing());

        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.canvas.dispatchEvent(mouseEvent);
        });

        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.canvas.dispatchEvent(mouseEvent);
        });

        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            const mouseEvent = new MouseEvent('mouseup', {});
            this.canvas.dispatchEvent(mouseEvent);
        });

        window.addEventListener('resize', () => this.initCanvas());
    }

    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    startDrawing(e) {
        this.isDrawing = true;
        const pos = this.getMousePos(e);

        this.ctx.beginPath();
        this.ctx.moveTo(pos.x, pos.y);

        if (this.currentTool === 'eraser') {
            this.ctx.globalCompositeOperation = 'destination-out';
            this.ctx.lineWidth = this.brushSize * 3;
        } else {
            this.ctx.globalCompositeOperation = 'source-over';
            this.ctx.strokeStyle = this.currentColor;
            this.ctx.lineWidth = this.brushSize;
        }
    }

    draw(e) {
        if (!this.isDrawing) return;

        const pos = this.getMousePos(e);

        this.ctx.lineTo(pos.x, pos.y);
        this.ctx.stroke();
    }

    stopDrawing() {
        if (!this.isDrawing) return;
        this.isDrawing = false;
        this.ctx.closePath();
        this.saveState();
    }

    updateCursor() {
        if (this.currentTool === 'eraser') {
            this.canvas.style.cursor = 'grab';
        } else {
            this.canvas.style.cursor = 'crosshair';
        }
    }

    saveState() {
        this.historyStep++;
        if (this.historyStep < this.history.length) {
            this.history.length = this.historyStep;
        }
        this.history.push(this.canvas.toDataURL());
    }

    undo() {
        if (this.historyStep > 0) {
            this.historyStep--;
            this.restoreState();
        }
    }

    redo() {
        if (this.historyStep < this.history.length - 1) {
            this.historyStep++;
            this.restoreState();
        }
    }

    restoreState() {
        const img = new Image();
        img.src = this.history[this.historyStep];
        img.onload = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.drawImage(img, 0, 0);
        };
    }

    clearCanvas() {
        if (confirm('Are you sure you want to clear the entire canvas?')) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.saveState();
        }
    }

    save() {
        const boardName = document.querySelector('.board-name-input').value || 'Untitled Board';
        const imageData = this.canvas.toDataURL();

        localStorage.setItem(`whiteboard_${Date.now()}`, JSON.stringify({
            name: boardName,
            data: imageData,
            timestamp: new Date().toISOString()
        }));

        const statusText = document.querySelector('#auto-save-status span:last-child');
        statusText.textContent = 'Saved successfully!';

        setTimeout(() => {
            statusText.textContent = 'All changes saved';
        }, 2000);
    }

    export() {
        const boardName = document.querySelector('.board-name-input').value || 'Untitled Board';
        const link = document.createElement('a');
        link.download = `${boardName}.png`;
        link.href = this.canvas.toDataURL();
        link.click();
    }

    zoom(factor) {
        const currentZoom = parseFloat(document.querySelector('.zoom-level').textContent) / 100;
        const newZoom = Math.max(0.5, Math.min(2, currentZoom * factor));

        this.canvas.style.transform = `scale(${newZoom})`;
        document.querySelector('.zoom-level').textContent = `${Math.round(newZoom * 100)}%`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Whiteboard();
});
