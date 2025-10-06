// Game Logic for Libras Learning

class LibrasGame {
    constructor() {
        this.gameState = {
            mode: 'normal',
            currentWord: '',
            currentLetterIndex: 0,
            currentWordIndex: 0,
            totalWords: 10,
            isPlaying: false,
            score: 0,
            totalLetters: 0,
            correctLetters: 0,
            timeRemaining: 0,
            gameTimer: null,
            difficulty: 'iniciante'
        };

        this.elements = {};
        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        // Game control elements
        this.elements.modeSelect = document.getElementById('modeSelect');
        this.elements.difficultySelect = document.getElementById('difficultySelect');
        this.elements.startGameBtn = document.getElementById('startGameBtn');
        this.elements.stopGameBtn = document.getElementById('stopGameBtn');
        
        // Mode-specific containers
        this.elements.normalModeContent = document.getElementById('normalModeContent');
        this.elements.soletracaoModeContent = document.getElementById('soletracaoModeContent');
        this.elements.desafioModeContent = document.getElementById('desafioModeContent');
        
        // Word and letter displays
        this.elements.currentWord = document.getElementById('currentWord');
        this.elements.challengeWord = document.getElementById('challengeWord');
        this.elements.letterBoxes = document.getElementById('letterBoxes');
        this.elements.challengeLetterBoxes = document.getElementById('challengeLetterBoxes');
        
        // Progress displays
        this.elements.letterPosition = document.getElementById('letterPosition');
        this.elements.totalLetters = document.getElementById('totalLetters');
        this.elements.challengeLetterPosition = document.getElementById('challengeLetterPosition');
        this.elements.challengeTotalLetters = document.getElementById('challengeTotalLetters');
        this.elements.challengeWordCount = document.getElementById('challengeWordCount');
        this.elements.totalChallengeWords = document.getElementById('totalChallengeWords');
        
        // Custom word input
        this.elements.customWordInput = document.getElementById('customWordInput');
        this.elements.validateWordBtn = document.getElementById('validateWordBtn');
        this.elements.customWordContainer = document.getElementById('customWordContainer');
        
        // Game content
        this.elements.gameContent = document.getElementById('gameContent');
    }

    setupEventListeners() {
        // Mode selection
        if (this.elements.modeSelect) {
            this.elements.modeSelect.addEventListener('change', () => {
                this.changeMode(this.elements.modeSelect.value);
            });
        }

        // Start/Stop game buttons
        if (this.elements.startGameBtn) {
            this.elements.startGameBtn.addEventListener('click', () => {
                this.startGame();
            });
        }

        if (this.elements.stopGameBtn) {
            this.elements.stopGameBtn.addEventListener('click', () => {
                this.stopGame();
            });
        }

        // Custom word validation
        if (this.elements.validateWordBtn) {
            this.elements.validateWordBtn.addEventListener('click', () => {
                this.validateCustomWord();
            });
        }

        // Enter key on custom word input
        if (this.elements.customWordInput) {
            this.elements.customWordInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.validateCustomWord();
                }
            });
        }

        // Setup demo button callbacks
        this.setupDemoCallbacks();
    }

    setupDemoCallbacks() {
        // Set callback for when practice starts after demo
        if (window.VideoDemoManager) {
            window.VideoDemoManager.setPracticeStartCallback(() => {
                // Resume game after demo
                console.log('Practice started after demo');
            });
        }
    }

    changeMode(mode) {
        this.gameState.mode = mode;
        
        // Hide all mode content
        this.elements.normalModeContent.classList.add('d-none');
        this.elements.soletracaoModeContent.classList.add('d-none');
        this.elements.desafioModeContent.classList.add('d-none');
        this.elements.customWordContainer.classList.add('d-none');

        // Show appropriate content based on mode
        switch (mode) {
            case 'normal':
                this.elements.normalModeContent.classList.remove('d-none');
                break;
            case 'soletracao':
                this.elements.soletracaoModeContent.classList.remove('d-none');
                this.elements.customWordContainer.classList.remove('d-none');
                break;
            case 'desafio':
                this.elements.desafioModeContent.classList.remove('d-none');
                break;
        }

        console.log('Mode changed to:', mode);
    }

    async validateCustomWord() {
        const word = this.elements.customWordInput.value.trim().toUpperCase();
        
        if (!word) {
            showAlert('Por favor, digite uma palavra', 'warning');
            return;
        }

        if (!/^[A-Z]+$/.test(word)) {
            showAlert('Use apenas letras de A-Z', 'warning');
            return;
        }

        if (word.length > 20) {
            showAlert('Palavra muito longa (máximo 20 letras)', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/validate_word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ word: word })
            });

            const result = await response.json();
            
            if (result.success) {
                this.gameState.currentWord = word;
                this.setupWordDisplay();
                showAlert('Palavra validada! Clique em "Iniciar Jogo"', 'success');
            } else {
                showAlert(result.message || 'Erro ao validar palavra', 'danger');
            }
        } catch (error) {
            console.error('Error validating word:', error);
            showAlert('Erro ao validar palavra', 'danger');
        }
    }

    async startGame() {
        this.gameState.isPlaying = true;
        
        // Update button states
        this.elements.startGameBtn.classList.add('d-none');
        this.elements.stopGameBtn.classList.remove('d-none');
        
        // Show game content
        this.elements.gameContent.style.display = 'block';

        try {
            // Start appropriate game mode
            switch (this.gameState.mode) {
                case 'normal':
                    await this.startNormalMode();
                    break;
                case 'soletracao':
                    await this.startSoletracaoMode();
                    break;
                case 'desafio':
                    await this.startDesafioMode();
                    break;
            }

            // Initialize camera
            if (window.CameraManager) {
                await window.CameraManager.init();
                await window.CameraManager.start();
            }

        } catch (error) {
            console.error('Error starting game:', error);
            showAlert('Erro ao iniciar jogo: ' + error.message, 'danger');
            this.stopGame();
        }
    }

    async startNormalMode() {
        console.log('Starting normal mode');
        showAlert('Modo normal iniciado! Faça sinais com as mãos', 'success');
    }

    async startSoletracaoMode() {
        if (!this.gameState.currentWord) {
            throw new Error('Palavra não definida. Valide uma palavra primeiro.');
        }

        console.log('Starting soletração mode with word:', this.gameState.currentWord);
        this.gameState.currentLetterIndex = 0;
        this.setupWordDisplay();
        this.updateCurrentLetter();
        
        showAlert(`Soletração iniciada! Comece com a letra "${this.getCurrentLetter()}"`, 'success');
    }

    async startDesafioMode() {
        console.log('Starting desafio mode');
        
        try {
            // Get random word from server
            const response = await fetch('/api/start_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: 'desafio',
                    difficulty: this.gameState.difficulty
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.gameState.currentWord = result.word;
                this.gameState.currentLetterIndex = 0;
                this.gameState.currentWordIndex = 1;
                this.setupChallengeWordDisplay();
                this.updateCurrentLetter();
                
                showAlert(`Desafio iniciado! Palavra: ${this.gameState.currentWord}`, 'success');
            } else {
                throw new Error(result.message || 'Erro ao iniciar desafio');
            }
        } catch (error) {
            console.error('Error starting challenge:', error);
            throw error;
        }
    }

    stopGame() {
        this.gameState.isPlaying = false;
        
        // Update button states
        this.elements.startGameBtn.classList.remove('d-none');
        this.elements.stopGameBtn.classList.add('d-none');
        
        // Stop camera
        if (window.CameraManager) {
            window.CameraManager.stop();
        }

        // Clear timers
        if (this.gameState.gameTimer) {
            clearInterval(this.gameState.gameTimer);
            this.gameState.gameTimer = null;
        }

        showAlert('Jogo parado', 'info');
        console.log('Game stopped');
    }

    setupWordDisplay() {
        if (this.gameState.mode === 'soletracao') {
            this.elements.currentWord.textContent = this.gameState.currentWord;
            this.elements.totalLetters.textContent = this.gameState.currentWord.length;
            this.createLetterBoxes(this.elements.letterBoxes);
        }
    }

    setupChallengeWordDisplay() {
        if (this.gameState.mode === 'desafio') {
            this.elements.challengeWord.textContent = this.gameState.currentWord;
            this.elements.challengeTotalLetters.textContent = this.gameState.currentWord.length;
            this.elements.challengeWordCount.textContent = this.gameState.currentWordIndex;
            this.elements.totalChallengeWords.textContent = this.gameState.totalWords;
            this.createLetterBoxes(this.elements.challengeLetterBoxes);
        }
    }

    createLetterBoxes(container) {
        if (!container) return;
        
        container.innerHTML = '';
        
        for (let i = 0; i < this.gameState.currentWord.length; i++) {
            const letterBox = document.createElement('div');
            letterBox.className = 'letter-box';
            letterBox.textContent = this.gameState.currentWord[i];
            letterBox.id = `letter-${i}`;
            
            if (i === this.gameState.currentLetterIndex) {
                letterBox.classList.add('current');
            }
            
            container.appendChild(letterBox);
        }
    }

    getCurrentLetter() {
        if (this.gameState.currentWord && this.gameState.currentLetterIndex < this.gameState.currentWord.length) {
            return this.gameState.currentWord[this.gameState.currentLetterIndex];
        }
        return null;
    }

    updateCurrentLetter() {
        const currentLetter = this.getCurrentLetter();
        console.log('updateCurrentLetter called. Current letter:', currentLetter);
        
        if (currentLetter && window.VideoDemoManager) {
            console.log('Setting current letter in VideoDemoManager:', currentLetter);
            window.VideoDemoManager.setCurrentLetter(currentLetter);
        } else {
            console.log('VideoDemoManager not available or no current letter');
        }

        // Update progress displays
        if (this.gameState.mode === 'soletracao') {
            this.elements.letterPosition.textContent = this.gameState.currentLetterIndex + 1;
        } else if (this.gameState.mode === 'desafio') {
            this.elements.challengeLetterPosition.textContent = this.gameState.currentLetterIndex + 1;
        }

        console.log('Current letter update complete:', currentLetter);
    }

    onLetterRecognized(letter) {
        const expectedLetter = this.getCurrentLetter();
        
        if (!expectedLetter) {
            console.log('No expected letter');
            return;
        }

        if (letter === expectedLetter) {
            // Correct letter
            this.markLetterCompleted();
            this.gameState.currentLetterIndex++;
            this.gameState.correctLetters++;

            if (this.gameState.currentLetterIndex >= this.gameState.currentWord.length) {
                // Word completed
                this.onWordCompleted();
            } else {
                // Move to next letter
                this.updateCurrentLetter();
                this.updateLetterBoxes();
            }
        }

        this.gameState.totalLetters++;
    }

    markLetterCompleted() {
        const letterBox = document.getElementById(`letter-${this.gameState.currentLetterIndex}`);
        if (letterBox) {
            letterBox.classList.remove('current');
            letterBox.classList.add('completed');
        }
    }

    updateLetterBoxes() {
        // Remove current class from all boxes
        const letterBoxes = document.querySelectorAll('.letter-box');
        letterBoxes.forEach(box => box.classList.remove('current'));

        // Add current class to current letter
        const currentBox = document.getElementById(`letter-${this.gameState.currentLetterIndex}`);
        if (currentBox) {
            currentBox.classList.add('current');
        }
    }

    onWordCompleted() {
        if (this.gameState.mode === 'desafio') {
            this.gameState.currentWordIndex++;
            
            if (this.gameState.currentWordIndex <= this.gameState.totalWords) {
                // Get next word
                this.getNextChallengeWord();
            } else {
                // Challenge completed
                this.onChallengeCompleted();
            }
        } else {
            // Soletração completed
            showAlert('Palavra completada com sucesso!', 'success');
            this.stopGame();
        }
    }

    async getNextChallengeWord() {
        try {
            const response = await fetch('/api/start_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: 'desafio',
                    difficulty: this.gameState.difficulty
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.gameState.currentWord = result.word;
                this.gameState.currentLetterIndex = 0;
                this.setupChallengeWordDisplay();
                this.updateCurrentLetter();
                
                showAlert(`Nova palavra: ${this.gameState.currentWord}`, 'info');
            }
        } catch (error) {
            console.error('Error getting next word:', error);
            showAlert('Erro ao obter próxima palavra', 'danger');
        }
    }

    onChallengeCompleted() {
        const accuracy = this.gameState.totalLetters > 0 ? 
            Math.round((this.gameState.correctLetters / this.gameState.totalLetters) * 100) : 0;
        
        showAlert(`Desafio completado! Precisão: ${accuracy}%`, 'success');
        this.stopGame();
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing LibrasGame...');
    window.LibrasGame = new LibrasGame();
    console.log('LibrasGame initialized:', window.LibrasGame);
    
    // Export for global use
    window.onLetterRecognized = function(letter) {
        if (window.LibrasGame) {
            window.LibrasGame.onLetterRecognized(letter);
        }
    };
    
    console.log('LibrasGame setup complete');
});