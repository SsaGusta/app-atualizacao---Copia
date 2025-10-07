console.log('Game JS básico carregado');

function startGame() {
    alert('Jogo iniciado! Use "Testar Reconhecimento" para detectar letras.');
    
    const startBtn = document.getElementById('startGameBtn');
    const stopBtn = document.getElementById('stopGameBtn');
    
    if (startBtn) startBtn.classList.add('d-none');
    if (stopBtn) stopBtn.classList.remove('d-none');
}

function stopGame() {
    alert('Jogo finalizado!');
    
    const startBtn = document.getElementById('startGameBtn');
    const stopBtn = document.getElementById('stopGameBtn');
    
    if (startBtn) startBtn.classList.remove('d-none');
    if (stopBtn) stopBtn.classList.add('d-none');
}

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startGameBtn');
    const stopBtn = document.getElementById('stopGameBtn');
    
    if (startBtn) {
        startBtn.addEventListener('click', startGame);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopGame);
    }
});