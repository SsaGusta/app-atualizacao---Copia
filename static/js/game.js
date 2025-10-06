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
        this.elements.modeSelect = document.getElementById('gameModeSelect');
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
        
        // Initialize with default mode
        this.changeMode('normal');
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

        // Update mode description
        const modeDescription = document.getElementById('modeDescription');
        
        // Show appropriate content based on mode
        switch (mode) {
            case 'normal':
                this.elements.normalModeContent.classList.remove('d-none');
                if (modeDescription) {
                    modeDescription.textContent = 'Reconhecimento livre em tempo real - pratique sinais livremente';
                }
                break;
            case 'soletracao':
                this.elements.soletracaoModeContent.classList.remove('d-none');
                this.elements.customWordContainer.classList.remove('d-none');
                if (modeDescription) {
                    modeDescription.textContent = 'Digite uma palavra personalizada para soletrar letra por letra';
                }
                break;
            case 'desafio':
                this.elements.desafioModeContent.classList.remove('d-none');
                if (modeDescription) {
                    modeDescription.textContent = 'Soletração com tempo limite - teste sua velocidade!';
                }
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
                console.log('Word validated and set:', word);
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
        console.log('Iniciando jogo...');
        
        try {
            this.gameState.isPlaying = true;
            
            // Update button states
            if (this.elements.startGameBtn) {
                this.elements.startGameBtn.classList.add('d-none');
            }
            if (this.elements.stopGameBtn) {
                this.elements.stopGameBtn.classList.remove('d-none');
            }
            
            // Show game content
            if (this.elements.gameContent) {
                this.elements.gameContent.style.display = 'block';
            }

            // Get selected mode and difficulty correctly
            const selectedMode = this.elements.modeSelect ? this.elements.modeSelect.value : 'normal';
            const selectedDifficulty = this.elements.difficultySelect ? this.elements.difficultySelect.value : 'iniciante';
            
            this.gameState.mode = selectedMode;
            this.gameState.difficulty = selectedDifficulty;

            console.log('Mode:', selectedMode, 'Difficulty:', selectedDifficulty);
            console.log('Expected timer duration:', this.getDifficultyTime(selectedDifficulty));

            // Handle different modes
            switch (selectedMode) {
                case 'normal':
                    // Normal mode doesn't use timer
                    this.gameState.timeRemaining = 0;
                    this.updateTimerDisplay();
                    await this.startNormalMode();
                    break;
                case 'soletracao':
                    if (!this.gameState.currentWord) {
                        showAlert('Para o modo Soletração, primeiro digite e valide uma palavra personalizada!', 'warning');
                        this.stopGame();
                        return;
                    }
                    await this.startSoletracaoMode();
                    break;
                case 'desafio':
                    // Get a word from API based on difficulty
                    const response = await fetch('/api/start_game', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            mode: selectedDifficulty 
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`Erro HTTP: ${response.status}`);
                    }

                    const data = await response.json();
                    
                    if (data.success) {
                        this.gameState.currentWord = data.word;
                        this.gameState.difficulty = selectedDifficulty;
                        await this.startDesafioMode();
                        showAlert(data.message || `Desafio iniciado! ${this.getDifficultyDescription(selectedDifficulty)}: ${data.word}`, 'success');
                    } else {
                        throw new Error(data.error || 'Erro ao buscar palavra para desafio');
                    }
                    break;
                default:
                    await this.startNormalMode();
            }

            // Initialize camera (opcional)
            this.initializeCamera();
                
        } catch (error) {
            console.error('Error starting game:', error);
            showAlert('Erro ao iniciar jogo: ' + error.message, 'danger');
            this.stopGame();
        }
    }

    initializeCamera() {
        // Tentar inicializar câmera de forma não-bloqueante
        setTimeout(async () => {
            try {
                if (window.cameraManager) {
                    await window.cameraManager.init();
                } else {
                    console.log('CameraManager não disponível');
                }
            } catch (error) {
                console.log('Câmera não disponível:', error.message);
                // Não mostrar erro, pois câmera é opcional
            }
        }, 1000);
    }

    updateWordDisplay() {
        // Atualizar exibição da palavra atual
        if (this.elements.currentWord) {
            this.elements.currentWord.textContent = this.gameState.currentWord;
        }
        if (this.elements.challengeWord) {
            this.elements.challengeWord.textContent = this.gameState.currentWord;
        }
        
        // Criar caixas de letras
        this.createLetterBoxes();
    }

    createLetterBoxes() {
        const word = this.gameState.currentWord;
        if (!word) return;

        // Para modo normal
        if (this.elements.letterBoxes) {
            this.elements.letterBoxes.innerHTML = '';
            for (let i = 0; i < word.length; i++) {
                const box = document.createElement('div');
                box.className = 'letter-box';
                box.style.cssText = `
                    display: inline-block;
                    width: 50px;
                    height: 50px;
                    border: 2px solid #ddd;
                    margin: 0 5px;
                    text-align: center;
                    line-height: 46px;
                    font-size: 24px;
                    font-weight: bold;
                    border-radius: 5px;
                    background: white;
                `;
                box.textContent = '_';
                box.id = `letter-${i}`;
                this.elements.letterBoxes.appendChild(box);
            }
        }

        // Para modo desafio
        if (this.elements.challengeLetterBoxes) {
            this.elements.challengeLetterBoxes.innerHTML = '';
            for (let i = 0; i < word.length; i++) {
                const box = document.createElement('div');
                box.className = 'letter-box';
                box.style.cssText = `
                    display: inline-block;
                    width: 50px;
                    height: 50px;
                    border: 2px solid #ddd;
                    margin: 0 5px;
                    text-align: center;
                    line-height: 46px;
                    font-size: 24px;
                    font-weight: bold;
                    border-radius: 5px;
                    background: white;
                `;
                box.textContent = '_';
                box.id = `challenge-letter-${i}`;
                this.elements.challengeLetterBoxes.appendChild(box);
            }
        }
    }

    async startNormalMode() {
        console.log('Starting normal mode - free letter recognition');
        
        // Show normal mode content
        this.elements.normalModeContent.classList.remove('d-none');
        this.elements.soletracaoModeContent.classList.add('d-none');
        this.elements.desafioModeContent.classList.add('d-none');
        
        // Hide timer card (normal mode doesn't use timer)
        const timerCard = document.getElementById('timerCard');
        if (timerCard) {
            timerCard.style.display = 'none';
        }
        
        // Clear any word-related state since this is free recognition
        this.gameState.currentWord = '';
        this.gameState.currentLetterIndex = 0;
        this.gameState.timeRemaining = 0; // No timer for normal mode
        
        // Update timer display to show no timer
        this.updateTimerDisplay();
        
        // Initialize camera for letter recognition
        this.initializeCamera();
        
        showAlert('Modo Reconhecimento Normal iniciado! Faça sinais com as mãos e veja o reconhecimento em tempo real', 'success');
    }

    async startSoletracaoMode() {
        if (!this.gameState.currentWord) {
            throw new Error('Palavra não definida. Valide uma palavra primeiro.');
        }

        console.log('Starting soletracao mode with word:', this.gameState.currentWord);
        console.log('Current letter index:', this.gameState.currentLetterIndex);
        
        // Show soletracao mode content
        this.elements.normalModeContent.classList.add('d-none');
        this.elements.soletracaoModeContent.classList.remove('d-none');
        this.elements.desafioModeContent.classList.add('d-none');
        
        // Show timer card
        const timerCard = document.getElementById('timerCard');
        if (timerCard) {
            timerCard.style.display = 'block';
        }
        
        // Reset game state for soletracao
        this.gameState.currentLetterIndex = 0;
        this.gameState.correctLetters = 0;
        this.gameState.totalLetters = this.gameState.currentWord.length;
        
        // Set timer based on difficulty
        this.gameState.timeRemaining = this.getDifficultyTime(this.gameState.difficulty);
        this.gameState.startTime = Date.now();
        
        console.log('After reset - Current letter index:', this.gameState.currentLetterIndex);
        console.log('First letter should be:', this.gameState.currentWord[0]);
        console.log('Timer set to:', this.gameState.timeRemaining, 'seconds');
        
        // Update displays
        this.updateWordDisplay();
        this.updateProgressDisplay();
        
        // Start timer
        this.startTimer();
        
        showAlert(`Modo Soletração iniciado! Soletre: ${this.gameState.currentWord} (${this.gameState.timeRemaining}s)`, 'success');
    }

    async startDesafioMode() {
        console.log('Starting desafio mode with word:', this.gameState.currentWord);
        console.log('Current letter index:', this.gameState.currentLetterIndex);
        
        // Show desafio mode content
        this.elements.normalModeContent.classList.add('d-none');
        this.elements.soletracaoModeContent.classList.add('d-none');
        this.elements.desafioModeContent.classList.remove('d-none');
        
        // Show timer card
        const timerCard = document.getElementById('timerCard');
        if (timerCard) {
            timerCard.style.display = 'block';
        }
        
        // Reset game state for challenge (word already set from API call)
        this.gameState.currentLetterIndex = 0;
        this.gameState.currentWordIndex = 1;
        this.gameState.correctLetters = 0;
        this.gameState.totalLetters = this.gameState.currentWord.length;
        
        // Set timer based on difficulty
        this.gameState.timeRemaining = this.getDifficultyTime(this.gameState.difficulty);
        this.gameState.startTime = Date.now();
        
        console.log('After reset - Current letter index:', this.gameState.currentLetterIndex);
        console.log('First letter should be:', this.gameState.currentWord[0]);
        console.log('Timer set to:', this.gameState.timeRemaining, 'seconds');
        
        // Update displays
        this.updateWordDisplay();
        this.updateProgressDisplay();
        
        // Start timer
        this.startTimer();
        
        console.log(`Desafio mode started: ${this.gameState.difficulty} - ${this.gameState.currentWord}`);
    }

    stopGame() {
        this.gameState.isPlaying = false;
        
        // Update button states
        this.elements.startGameBtn.classList.remove('d-none');
        this.elements.stopGameBtn.classList.add('d-none');
        
        // Hide timer card
        const timerCard = document.getElementById('timerCard');
        if (timerCard) {
            timerCard.style.display = 'none';
        }
        
        // Stop camera
        if (window.CameraManager) {
            window.CameraManager.stop();
        }

        // Clear timers
        if (this.gameState.gameTimer) {
            clearInterval(this.gameState.gameTimer);
            this.gameState.gameTimer = null;
        }
        
        // Reset timer display
        const timerElement = document.getElementById('timeRemaining');
        if (timerElement) {
            timerElement.textContent = '--:--';
            timerElement.className = 'h3 mb-0 text-muted';
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

    updateProgressDisplay() {
        // Update progress displays for different modes
        if (this.gameState.mode === 'soletracao') {
            if (this.elements.letterPosition) {
                this.elements.letterPosition.textContent = this.gameState.currentLetterIndex + 1;
            }
            if (this.elements.totalLetters) {
                this.elements.totalLetters.textContent = this.gameState.currentWord.length;
            }
        } else if (this.gameState.mode === 'desafio') {
            if (this.elements.challengeLetterPosition) {
                this.elements.challengeLetterPosition.textContent = this.gameState.currentLetterIndex + 1;
            }
            if (this.elements.challengeTotalLetters) {
                this.elements.challengeTotalLetters.textContent = this.gameState.currentWord.length;
            }
            if (this.elements.challengeWordCount) {
                this.elements.challengeWordCount.textContent = this.gameState.currentWordIndex;
            }
            if (this.elements.totalChallengeWords) {
                this.elements.totalChallengeWords.textContent = this.gameState.totalWords;
            }
        }
    }

    startTimer() {
        if (this.gameState.gameTimer) {
            clearInterval(this.gameState.gameTimer);
        }

        // Update timer display initially
        this.updateTimerDisplay();

        this.gameState.gameTimer = setInterval(() => {
            this.gameState.timeRemaining--;
            
            // Update timer display
            this.updateTimerDisplay();

            if (this.gameState.timeRemaining <= 0) {
                this.onTimeUp();
            }
        }, 1000);
    }

    updateTimerDisplay() {
        console.log('updateTimerDisplay called');
        console.log('timeRemaining:', this.gameState.timeRemaining);
        console.log('game mode:', this.gameState.mode);
        
        const timerElement = document.getElementById('timeRemaining');
        console.log('timerElement found:', !!timerElement);
        
        if (timerElement) {
            if (this.gameState.timeRemaining <= 0 && this.gameState.mode === 'normal') {
                // Normal mode doesn't use timer
                timerElement.textContent = '--:--';
                timerElement.className = 'h3 mb-0 text-muted';
                console.log('Set timer to --:-- for normal mode');
            } else {
                const minutes = Math.floor(this.gameState.timeRemaining / 60);
                const seconds = this.gameState.timeRemaining % 60;
                const timeText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                timerElement.textContent = timeText;
                console.log('Set timer to:', timeText);
                
                // Change color based on time remaining
                if (this.gameState.timeRemaining <= 30) {
                    timerElement.className = 'h3 mb-0 text-danger';
                } else if (this.gameState.timeRemaining <= 60) {
                    timerElement.className = 'h3 mb-0 text-warning';
                } else {
                    timerElement.className = 'h3 mb-0 text-success';
                }
                
                // Update the seconds label
                const secondsLabel = timerElement.nextElementSibling;
                if (secondsLabel && this.gameState.timeRemaining === 1) {
                    secondsLabel.textContent = 'segundo';
                } else if (secondsLabel) {
                    secondsLabel.textContent = 'segundos';
                }
            }
        } else {
            console.error('Timer element not found!');
        }
    }

    onTimeUp() {
        clearInterval(this.gameState.gameTimer);
        
        // Calculate final statistics
        const timeSpent = this.getDifficultyTime(this.gameState.difficulty) - this.gameState.timeRemaining;
        const accuracy = this.gameState.totalLetters > 0 ? 
            Math.round((this.gameState.correctLetters / this.gameState.totalLetters) * 100) : 0;
        
        console.log('Time up! Saving results...');
        
        // Save results to database
        this.saveGameResults(false, timeSpent, accuracy);
        
        showAlert('Tempo esgotado! Resultado salvo.', 'warning');
        
        // End the game
        this.endGame();
    }

    async saveGameResults(completed = false, timeSpent = 0, accuracy = 0) {
        try {
            const gameData = {
                mode: this.gameState.mode,
                difficulty: this.gameState.difficulty,
                word: this.gameState.currentWord,
                completed: completed,
                time_spent: timeSpent,
                total_time: this.getDifficultyTime(this.gameState.difficulty),
                letters_completed: this.gameState.correctLetters,
                total_letters: this.gameState.totalLetters,
                accuracy: accuracy
            };
            
            console.log('Saving game data:', gameData);
            
            const response = await fetch('/api/save_game_result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(gameData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Game result saved successfully:', result.message);
                return true;
            } else {
                console.error('Failed to save game result:', result.error);
                return false;
            }
            
        } catch (error) {
            console.error('Error saving game results:', error);
            return false;
        }
    }

    async nextWord() {
        this.gameState.currentWordIndex++;
        
        if (this.gameState.currentWordIndex > this.gameState.totalWords) {
            this.endGame();
            return;
        }

        // Get next word from API
        try {
            const response = await fetch('/api/start_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    mode: this.gameState.difficulty 
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.gameState.currentWord = data.word;
                this.gameState.currentLetterIndex = 0;
                this.gameState.timeRemaining = 60; // Reset timer
                
                this.updateWordDisplay();
                this.updateProgressDisplay();
                this.startTimer();
                
                showAlert(`Nova palavra: ${data.word}`, 'info');
            }
        } catch (error) {
            console.error('Error getting next word:', error);
            this.endGame();
        }
    }

    endGame() {
        // Calculate final statistics if not already calculated
        if (this.gameState.isPlaying) {
            const timeSpent = this.getDifficultyTime(this.gameState.difficulty) - this.gameState.timeRemaining;
            const accuracy = this.gameState.totalLetters > 0 ? 
                Math.round((this.gameState.correctLetters / this.gameState.totalLetters) * 100) : 0;
            
            // Save results for completed game
            this.saveGameResults(true, timeSpent, accuracy);
        }
        
        this.stopGame();
        showAlert('Jogo finalizado! Resultados salvos com sucesso!', 'success');
        
        // Could show final statistics here
        console.log('Game ended');
    }

    getDifficultyDescription(difficulty) {
        switch (difficulty) {
            case 'iniciante':
                return 'Palavras de 2-5 letras';
            case 'intermediario':
                return 'Palavras sem restrição de tamanho';
            case 'avancado':
                return 'Palavras compostas';
            case 'expert':
                return 'Frases completas';
            default:
                return 'Nível personalizado';
        }
    }

    getDifficultyTime(difficulty) {
        console.log('getDifficultyTime called with:', difficulty);
        let time;
        switch (difficulty) {
            case 'iniciante':
                time = 180; // 3 minutos
                break;
            case 'intermediario':
                time = 160; // 2:40 minutos
                break;
            case 'avancado':
                time = 100; // 1:40 minutos
                break;
            case 'expert':
                time = 60;  // 1 minuto
                break;
            default:
                time = 120; // 2 minutos padrão
        }
        console.log('Returning time:', time, 'for difficulty:', difficulty);
        return time;
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
            // Call start_game API to get a new word
            const response = await fetch('/api/start_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: this.gameState.difficulty
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