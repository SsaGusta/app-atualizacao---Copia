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
        this.cameraPermissionGranted = false;
        this.cameraErrorMessage = '';
    }

    init() {
        this.videoElement = document.getElementById('videoElement');
        this.canvasElement = document.getElementById('canvasElement');
        
        if (this.canvasElement) {
            this.context = this.canvasElement.getContext('2d');
            // Set canvas size to match video
            this.canvasElement.width = 640;
            this.canvasElement.height = 480;
        }
        
        this.setupFPSCounter();
        this.setupCameraPermissionUI();
    }

    setupCameraPermissionUI() {
        // Criar botão para solicitar câmera se não existir
        if (!document.getElementById('requestCameraBtn')) {
            const cameraContainer = document.querySelector('.camera-container');
            if (cameraContainer) {
                const overlay = document.createElement('div');
                overlay.className = 'camera-permission-overlay';
                overlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.8);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    color: white;
                    text-align: center;
                    padding: 20px;
                    z-index: 10;
                `;
                
                overlay.innerHTML = `
                    <i class="fas fa-video fa-3x mb-3"></i>
                    <h5>Câmera necessária</h5>
                    <p>Para usar o reconhecimento de sinais, precisamos acessar sua câmera.</p>
                    <button id="requestCameraBtn" class="btn btn-primary">
                        <i class="fas fa-camera"></i> Permitir Câmera
                    </button>
                    <button id="skipCameraBtn" class="btn btn-secondary mt-2">
                        <i class="fas fa-eye"></i> Usar apenas vídeos
                    </button>
                    <small class="mt-2 text-muted">Você pode usar apenas os vídeos de demonstração</small>
                `;
                
                cameraContainer.appendChild(overlay);
                
                // Event listeners
                document.getElementById('requestCameraBtn').addEventListener('click', () => this.requestCameraPermission());
                document.getElementById('skipCameraBtn').addEventListener('click', () => this.skipCamera());
            }
        }
    }

    async requestCameraPermission() {
        try {
            showAlert('Solicitando permissão da câmera...', 'info');
            await this.start();
            
            // Remover overlay se sucesso
            const overlay = document.querySelector('.camera-permission-overlay');
            if (overlay) overlay.remove();
            
        } catch (error) {
            this.handleCameraError(error);
        }
    }

    skipCamera() {
        // Remover overlay e mostrar apenas vídeo demo
        const overlay = document.querySelector('.camera-permission-overlay');
        if (overlay) overlay.remove();
        
        // Mostrar mensagem informativa
        const cameraContainer = document.querySelector('.camera-container');
        if (cameraContainer) {
            cameraContainer.innerHTML = `
                <div class="camera-demo-mode" style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                    border-radius: 10px;
                ">
                    <i class="fas fa-play-circle fa-4x mb-3"></i>
                    <h4>Modo Demonstração</h4>
                    <p>Use os vídeos de demonstração para aprender os sinais</p>
                    <small>Câmera não disponível nesta sessão</small>
                </div>
            `;
        }
        
        showAlert('Modo demonstração ativado. Use os vídeos para aprender!', 'info');
    }

    handleCameraError(error) {
        console.error('Erro da câmera:', error);
        let message = 'Erro desconhecido';
        let solution = '';
        
        switch(error.name) {
            case 'NotAllowedError':
            case 'PermissionDeniedError':
                message = 'Permissão da câmera negada';
                solution = 'Por favor, clique no ícone da câmera na barra de endereços e permita o acesso.';
                break;
            case 'NotFoundError':
            case 'DevicesNotFoundError':
                message = 'Nenhuma câmera encontrada';
                solution = 'Verifique se sua câmera está conectada e funcionando.';
                break;
            case 'NotReadableError':
            case 'TrackStartError':
                message = 'Câmera em uso por outro aplicativo';
                solution = 'Feche outros aplicativos que possam estar usando a câmera.';
                break;
            case 'NotSupportedError':
                message = 'Câmera não suportada';
                solution = 'Seu navegador ou dispositivo não suporta acesso à câmera.';
                break;
        }
        
        // Mostrar erro detalhado
        const overlay = document.querySelector('.camera-permission-overlay');
        if (overlay) {
            overlay.innerHTML = `
                <i class="fas fa-exclamation-triangle fa-3x mb-3 text-warning"></i>
                <h5>Problema com a Câmera</h5>
                <p><strong>${message}</strong></p>
                <p class="small">${solution}</p>
                <div class="mt-3">
                    <button id="retryCameraBtn" class="btn btn-warning">
                        <i class="fas fa-redo"></i> Tentar Novamente
                    </button>
                    <button id="skipCameraBtn2" class="btn btn-secondary">
                        <i class="fas fa-eye"></i> Usar apenas vídeos
                    </button>
                </div>
                <div class="mt-3">
                    <small class="text-info">
                        <i class="fas fa-lightbulb"></i> 
                        Dica: Clique no ícone da câmera/cadeado na barra de endereços do navegador
                    </small>
                </div>
            `;
            
            document.getElementById('retryCameraBtn').addEventListener('click', () => this.requestCameraPermission());
            document.getElementById('skipCameraBtn2').addEventListener('click', () => this.skipCamera());
        }
        
        showAlert(`Erro da câmera: ${message}`, 'warning', 8000);
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
            this.cameraPermissionGranted = true;

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
        console.log('Starting frame processing...');
        console.log('isActive:', this.isActive);
        console.log('videoElement:', !!this.videoElement);
        console.log('context:', !!this.context);
        
        // Process frames at 10 FPS to reduce load
        this.processingInterval = setInterval(() => {
            if (this.isActive && this.videoElement && this.context) {
                this.processFrame();
            }
        }, 100); // 10 FPS
        
        console.log('Frame processing interval started');
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
            if (!window.gameInstance || !window.gameInstance.gameState || !window.gameInstance.gameState.isPlaying) {
                console.log('Game not active, skipping frame processing');
                console.log('gameInstance:', !!window.gameInstance);
                if (window.gameInstance) {
                    console.log('gameState:', !!window.gameInstance.gameState);
                    if (window.gameInstance.gameState) {
                        console.log('isPlaying:', window.gameInstance.gameState.isPlaying);
                    }
                }
                return;
            }

            console.log('Sending frame for processing...');

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
            console.log('Recognition response:', data);

            if (data.success) {
                this.handleRecognitionResult(data);
            }

        } catch (error) {
            console.error('Erro ao enviar frame:', error);
        }
    }

    handleRecognitionResult(data) {
        console.log('Resultado do reconhecimento:', data);
        
        // Update confidence display
        const confidenceElement = document.getElementById('confidenceDisplay');
        if (confidenceElement) {
            if (data.success && data.confidence) {
                const confidence = Math.round(data.confidence * 100);
                confidenceElement.textContent = `${confidence}%`;
                confidenceElement.style.color = confidence > 60 ? '#28a745' : '#ffc107';
            } else {
                confidenceElement.textContent = '0%';
                confidenceElement.style.color = '#dc3545';
            }
        }

        // Update recognition status display
        const statusElement = document.getElementById('recognitionStatus');
        if (statusElement) {
            if (data.success) {
                statusElement.textContent = `Reconhecido: ${data.letter}`;
                statusElement.className = 'recognition-status success';
            } else if (data.detected === false) {
                statusElement.textContent = 'Nenhuma mão detectada';
                statusElement.className = 'recognition-status no-hand';
            } else if (data.detected === true && data.confidence < 0.3) {
                statusElement.textContent = 'Mão detectada - forme a letra com mais precisão';
                statusElement.className = 'recognition-status low-confidence';
            } else {
                statusElement.textContent = data.error || 'Erro no reconhecimento';
                statusElement.className = 'recognition-status error';
            }
        }

        // Update recognition result display for game modes
        const resultElement = document.getElementById('recognitionResult');
        if (resultElement && window.gameInstance && window.gameInstance.gameState && window.gameInstance.gameState.isPlaying) {
            const mode = window.gameInstance.gameState.mode;
            
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
        
        // Update the detected letter display
        const detectedLetterElement = document.getElementById('detectedLetter');
        if (detectedLetterElement && recognizedLetter && confidence > 0.6) {
            detectedLetterElement.textContent = recognizedLetter;
        }
        
        // For normal mode, we don't need to show detailed results anymore
        // The letter is shown in the game interface directly
    }
    
    handleWordModeRecognition(data, resultElement) {
        const gameInstance = window.gameInstance;
        if (!gameInstance || !gameInstance.gameState) {
            return;
        }
        
        const currentWord = gameInstance.gameState.currentWord;
        const currentLetterIndex = gameInstance.gameState.currentLetterIndex;
        
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
                        if (gameInstance.checkLetter) {
                            console.log(`Letter ${recognizedLetter} recognized correctly!`);
                            gameInstance.checkLetter(recognizedLetter);
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
            if (window.gameInstance && window.gameInstance.getCurrentLetter) {
                this.currentLetter = window.gameInstance.getCurrentLetter();
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

    // Test recognition function
    testRecognition() {
        console.log('Testando reconhecimento...');
        if (this.isActive && this.videoElement && this.videoElement.videoWidth > 0) {
            // Force capture and send a frame for recognition
            this.sendFrameForProcessing();
        } else {
            console.warn('Câmera não está ativa ou sem vídeo');
            const statusElement = document.getElementById('recognitionStatus');
            if (statusElement) {
                statusElement.textContent = 'Câmera não está ativa';
                statusElement.className = 'recognition-status error';
            }
        }
    }
}

// Create global instance
const VideoDemoManager = new VideoDemonstrationManager();

// Create global instance
const cameraManagerInstance = new CameraManager();

// Initialize camera manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    cameraManagerInstance.init();
    console.log('CameraManager initialized');
    
    // Initialize test button
    const testButton = document.getElementById('testRecognitionBtn');
    if (testButton) {
        testButton.addEventListener('click', () => {
            cameraManagerInstance.testRecognition();
        });
        console.log('Test recognition button initialized');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    cameraManagerInstance.cleanup();
});

// Export for use in other scripts
window.CameraManager = cameraManagerInstance;
window.VideoDemoManager = VideoDemoManager;