// Camera Management for Libras Learning
class CameraManager {
    constructor() {
        this.stream = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.context = null;
        this.isActive = false;
        this.lastFrameTime = 0;
        this.frameCount = 0;
        this.fpsInterval = null;
        this.processingInterval = null;
    }

    init() {
        this.videoElement = document.getElementById('videoElement');
        this.canvasElement = document.getElementById('canvasElement');
        
        if (this.canvasElement) {
            this.context = this.canvasElement.getContext('2d');
        }
        
        this.setupFPSCounter();
    }

    async start() {
        try {
            // Request camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15 }
                },
                audio: false
            });

            this.videoElement.srcObject = this.stream;
            this.isActive = true;

            // Update camera status
            this.updateCameraStatus('Conectada', 'success');

            // Wait for video to be ready
            await new Promise((resolve) => {
                this.videoElement.addEventListener('loadedmetadata', resolve, { once: true });
            });

            // Setup canvas dimensions
            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;

            // Start processing frames
            this.startFrameProcessing();

            console.log('Câmera iniciada com sucesso');

        } catch (error) {
            console.error('Erro ao acessar câmera:', error);
            this.updateCameraStatus('Erro', 'danger');
            
            let errorMessage = 'Erro ao acessar a câmera. ';
            if (error.name === 'NotAllowedError') {
                errorMessage += 'Permissão negada. Permita o acesso à câmera.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'Nenhuma câmera encontrada.';
            } else {
                errorMessage += 'Verifique se a câmera está disponível.';
            }
            
            showAlert(errorMessage, 'danger');
            throw error;
        }
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.videoElement) {
            this.videoElement.srcObject = null;
        }

        this.isActive = false;
        this.updateCameraStatus('Desconectada', 'secondary');

        // Stop processing
        if (this.processingInterval) {
            clearInterval(this.processingInterval);
            this.processingInterval = null;
        }

        console.log('Câmera parada');
    }

    updateCameraStatus(text, type) {
        const statusElement = document.getElementById('cameraStatus');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.className = `badge bg-${type} ms-2`;
        }
    }

    setupFPSCounter() {
        this.fpsInterval = setInterval(() => {
            const fpsElement = document.getElementById('fpsCounter');
            if (fpsElement) {
                fpsElement.textContent = this.frameCount;
            }
            this.frameCount = 0;
        }, 1000);
    }

    startFrameProcessing() {
        // Process frames at 10 FPS to reduce load
        this.processingInterval = setInterval(() => {
            if (this.isActive && this.videoElement && this.context) {
                this.processFrame();
            }
        }, 100); // 10 FPS
    }

    async processFrame() {
        try {
            // Draw current frame to canvas
            this.context.drawImage(
                this.videoElement,
                0, 0,
                this.canvasElement.width,
                this.canvasElement.height
            );

            // Convert canvas to base64
            const imageData = this.canvasElement.toDataURL('image/jpeg', 0.7);

            // Send to backend for processing
            await this.sendFrameForProcessing(imageData);

            this.frameCount++;

        } catch (error) {
            console.error('Erro ao processar frame:', error);
        }
    }

    async sendFrameForProcessing(imageData) {
        try {
            // Only process if game is active
            if (!window.gameState || !window.gameState.isActive) {
                return;
            }

            const response = await fetch('/api/process_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageData
                })
            });

            const data = await response.json();

            if (data.success) {
                this.handleRecognitionResult(data);
            }

        } catch (error) {
            console.error('Erro ao enviar frame:', error);
        }
    }

    handleRecognitionResult(data) {
        // Update confidence display
        const confidenceElement = document.getElementById('confidenceDisplay');
        if (confidenceElement) {
            const confidence = Math.round(data.confidence * 100);
            confidenceElement.textContent = `${confidence}%`;
        }

        // Update recognition result display
        const resultElement = document.getElementById('recognitionResult');
        if (resultElement && window.gameState && window.gameState.isActive) {
            const mode = window.gameState.mode;
            
            if (mode === 'normal') {
                this.handleNormalModeRecognition(data, resultElement);
            } else if (mode === 'soletracao' || mode === 'desafio') {
                this.handleWordModeRecognition(data, resultElement);
            }
        }
    }
    
    handleNormalModeRecognition(data, resultElement) {
        const recognizedLetter = data.letter;
        const confidence = data.confidence;
        
        let resultHTML = '';
        
        if (data.has_hand) {
            if (recognizedLetter && confidence > 0.6) {
                resultHTML = `
                    <div class="text-success">
                        <i class="fas fa-hand-paper fa-2x mb-2"></i>
                        <h4>Letra Reconhecida: "${recognizedLetter}"</h4>
                        <p>Confiança: ${Math.round(confidence * 100)}%</p>
                    </div>
                `;
            } else {
                resultHTML = `
                    <div class="text-info">
                        <i class="fas fa-hand-paper fa-2x mb-2"></i>
                        <h4>Processando sinal...</h4>
                        ${recognizedLetter ? `<p>Detectado: "${recognizedLetter}"</p>` : ''}
                        <small>Confiança: ${Math.round(confidence * 100)}%</small>
                    </div>
                `;
            }
        } else {
            resultHTML = `
                <div class="text-muted">
                    <i class="fas fa-hand-paper fa-2x mb-2"></i>
                    <h4>Mostre sua mão</h4>
                    <p>Faça um sinal para reconhecimento</p>
                </div>
            `;
        }
        
        resultElement.innerHTML = resultHTML;
    }
    
    handleWordModeRecognition(data, resultElement) {
        const currentWord = window.gameState.currentWord;
        const currentLetterIndex = window.gameState.currentLetterIndex;
        
        if (currentWord && currentLetterIndex < currentWord.length) {
            const expectedLetter = currentWord[currentLetterIndex];
            const recognizedLetter = data.letter;
            const confidence = data.confidence;

            let resultHTML = '';

            if (data.has_hand) {
                if (recognizedLetter && confidence > 0.6) {
                    if (recognizedLetter === expectedLetter) {
                        resultHTML = `
                            <div class="text-success">
                                <i class="fas fa-check-circle fa-2x mb-2"></i>
                                <h4>Correto! "${recognizedLetter}"</h4>
                                <p>Confiança: ${Math.round(confidence * 100)}%</p>
                            </div>
                        `;
                        
                        // Update game progress
                        if (window.updateLetterProgress) {
                            window.updateLetterProgress(true);
                        }
                    } else {
                        resultHTML = `
                            <div class="text-warning">
                                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                                <h4>Detectado: "${recognizedLetter}"</h4>
                                <p>Esperado: "${expectedLetter}"</p>
                                <small>Confiança: ${Math.round(confidence * 100)}%</small>
                            </div>
                        `;
                    }
                } else {
                    resultHTML = `
                        <div class="text-info">
                            <i class="fas fa-hand-paper fa-2x mb-2"></i>
                            <h4>Fazendo sinal...</h4>
                            <p>Esperando: "${expectedLetter}"</p>
                            <small>Confiança baixa: ${Math.round(confidence * 100)}%</small>
                        </div>
                    `;
                }
            } else {
                resultHTML = `
                    <div class="text-muted">
                        <i class="fas fa-hand-paper fa-2x mb-2"></i>
                        <h4>Mostre sua mão</h4>
                        <p>Esperando: "${expectedLetter}"</p>
                    </div>
                `;
            }

            resultElement.innerHTML = resultHTML;
        }
    }

    pauseProcessing() {
        if (this.processingInterval) {
            clearInterval(this.processingInterval);
            this.processingInterval = null;
            console.log('Camera processing paused');
        }
    }

    resumeProcessing() {
        if (this.isActive && !this.processingInterval) {
            this.startFrameProcessing();
            console.log('Camera processing resumed');
        }
    }

    // Cleanup when page unloads
    cleanup() {
        this.stop();
        if (this.fpsInterval) {
            clearInterval(this.fpsInterval);
        }
    }
}

// ===== VIDEO DEMONSTRATION MANAGER =====
class VideoDemonstrationManager {
    constructor() {
        this.demoCard = null;
        this.demoVideo = null;
        this.demoLetterTitle = null;
        this.closeDemoBtn = null;
        this.startPracticeBtn = null;
        this.showDemoBtn = null;
        this.showChallengeDemoBtn = null;
        this.currentLetter = null;
        this.onPracticeStart = null;
    }

    init() {
        console.log('VideoDemoManager.init() called');
        
        this.demoCard = document.getElementById('videoDemonstrationCard');
        this.demoVideo = document.getElementById('demoVideoElement');
        this.demoLetterTitle = document.getElementById('demoLetterTitle');
        this.closeDemoBtn = document.getElementById('closeDemoBtn');
        this.startPracticeBtn = document.getElementById('startPracticeBtn');
        this.showDemoBtn = document.getElementById('showDemoBtn');
        this.showChallengeDemoBtn = document.getElementById('showChallengeDemoBtn');

        console.log('Elements found:', {
            demoCard: !!this.demoCard,
            demoVideo: !!this.demoVideo,
            demoLetterTitle: !!this.demoLetterTitle,
            closeDemoBtn: !!this.closeDemoBtn,
            startPracticeBtn: !!this.startPracticeBtn,
            showDemoBtn: !!this.showDemoBtn,
            showChallengeDemoBtn: !!this.showChallengeDemoBtn
        });

        this.setupEventListeners();
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Close demo button
        if (this.closeDemoBtn) {
            this.closeDemoBtn.addEventListener('click', () => {
                console.log('Close demo button clicked');
                this.hideDemo();
            });
            console.log('Close demo button listener added');
        }

        // Start practice button
        if (this.startPracticeBtn) {
            this.startPracticeBtn.addEventListener('click', () => {
                console.log('Start practice button clicked');
                this.hideDemo();
                if (this.onPracticeStart) {
                    this.onPracticeStart();
                }
            });
            console.log('Start practice button listener added');
        }

        // Show demo buttons
        if (this.showDemoBtn) {
            this.showDemoBtn.addEventListener('click', () => {
                console.log('Show demo button clicked');
                this.showCurrentLetterDemo();
            });
            console.log('Show demo button listener added');
        }

        if (this.showChallengeDemoBtn) {
            this.showChallengeDemoBtn.addEventListener('click', () => {
                console.log('Show challenge demo button clicked');
                this.showCurrentLetterDemo();
            });
            console.log('Show challenge demo button listener added');
        }

        // Video ended event
        if (this.demoVideo) {
            this.demoVideo.addEventListener('ended', () => {
                console.log('Demo video ended');
            });
            console.log('Video ended listener added');
        }
        
        console.log('Event listeners setup complete');
    }

    async showCurrentLetterDemo() {
        if (!this.currentLetter) {
            console.warn('No current letter set for demonstration');
            // Try to get current letter from game state
            if (window.LibrasGame && window.LibrasGame.getCurrentLetter()) {
                this.currentLetter = window.LibrasGame.getCurrentLetter();
                console.log('Got current letter from game:', this.currentLetter);
            } else {
                // For testing, use 'A' as default
                this.currentLetter = 'A';
                console.log('Using default letter A for demonstration');
            }
        }

        await this.showDemo(this.currentLetter);
    }

    async showDemo(letter) {
        try {
            console.log('showDemo called with letter:', letter);
            this.currentLetter = letter.toUpperCase();

            // Get video information from API
            console.log('Fetching video info from API...');
            const response = await fetch(`/api/get_video_demo/${this.currentLetter}`);
            const data = await response.json();

            console.log('API response:', data);

            if (!data.success) {
                throw new Error(data.message || 'Erro ao obter informações do vídeo');
            }

            if (!data.video_available) {
                console.warn('Video not available for letter:', this.currentLetter);
                alert(`Vídeo não disponível para a letra ${this.currentLetter}`);
                return;
            }

            // Update UI
            console.log('Updating UI elements...');
            this.demoLetterTitle.textContent = this.currentLetter;
            this.demoVideo.src = data.video_url;

            // Show the demo card
            console.log('Showing demo card...');
            this.demoCard.classList.remove('d-none');

            // Pause camera processing if active
            if (window.CameraManager && window.CameraManager.isActive) {
                console.log('Pausing camera processing...');
                window.CameraManager.pauseProcessing();
            }

            console.log(`Demo shown successfully for letter: ${this.currentLetter}`);

        } catch (error) {
            console.error('Error showing demo:', error);
            alert('Erro ao carregar vídeo de demonstração: ' + error.message);
        }
    }

    hideDemo() {
        this.demoCard.classList.add('d-none');
        this.demoVideo.pause();
        this.demoVideo.src = '';

        // Resume camera processing if it was active
        if (window.CameraManager && window.CameraManager.isActive) {
            window.CameraManager.resumeProcessing();
        }

        console.log('Demo hidden');
    }

    setCurrentLetter(letter) {
        this.currentLetter = letter ? letter.toUpperCase() : null;
        console.log('Current letter set to:', this.currentLetter);
    }

    setPracticeStartCallback(callback) {
        this.onPracticeStart = callback;
    }
}

// Create global instance
const VideoDemoManager = new VideoDemonstrationManager();

// Create global instance
const CameraManager = new CameraManager();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    CameraManager.cleanup();
});

// Export for use in other scripts
window.CameraManager = CameraManager;
window.VideoDemoManager = VideoDemoManager;