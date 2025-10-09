/**
 * Sistema Administrativo de Captura de Gestos Libras
 * Permite ao administrador capturar e salvar gestos para cada letra
 */

class AdminGestureCapture {
    constructor() {
        console.log('🎯 Inicializando AdminGestureCapture...');
        
        this.videoElement = document.getElementById('videoElement');
        this.landmarksCanvas = document.getElementById('landmarksCanvas');
        this.canvasCtx = this.landmarksCanvas.getContext('2d');
        this.camera = null;
        this.hands = null;
        this.isCapturing = false;
        this.currentLandmarks = null;
        this.savedGestures = {};
        
        // Elementos da interface
        this.letterSelect = document.getElementById('letterSelect');
        this.startCameraBtn = document.getElementById('startCameraBtn');
        this.captureGestureBtn = document.getElementById('captureGestureBtn');
        this.clearGestureBtn = document.getElementById('clearGestureBtn');
        this.cameraStatus = document.getElementById('cameraStatus');
        this.handDetection = document.getElementById('handDetection');
        this.captureStatus = document.getElementById('captureStatus');
        this.feedbackArea = document.getElementById('feedbackArea');
        this.gestureList = document.getElementById('gestureList');
        this.countdown = document.getElementById('countdown');
        
        this.initializeInterface();
        this.setupEventListeners();
        this.loadSavedGestures();
    }
    
    initializeInterface() {
        // Preencher seletor de letras
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
        alphabet.forEach(letter => {
            const option = document.createElement('option');
            option.value = letter;
            option.textContent = `Letra ${letter}`;
            this.letterSelect.appendChild(option);
        });
        
        this.updateSystemStatus('inactive', 'Sistema inicializado - Câmera desconectada');
        this.updateCaptureStatus('Selecione uma letra e inicie a câmera');
    }
    
    setupEventListeners() {
        this.startCameraBtn.addEventListener('click', () => this.toggleCamera());
        this.captureGestureBtn.addEventListener('click', () => this.captureCurrentGesture());
        this.clearGestureBtn.addEventListener('click', () => this.clearSelectedGesture());
        
        document.getElementById('refreshGesturesBtn').addEventListener('click', () => this.loadSavedGestures());
        document.getElementById('exportGesturesBtn').addEventListener('click', () => this.exportGestures());
        
        this.letterSelect.addEventListener('change', () => this.onLetterSelectionChange());
    }
    
    async toggleCamera() {
        if (!this.camera) {
            await this.startCamera();
        } else {
            this.stopCamera();
        }
    }
    
    async startCamera() {
        try {
            this.updateSystemStatus('loading', 'Inicializando câmera...');
            this.showFeedback('Iniciando câmera e MediaPipe...', 'info');
            
            // Configurar MediaPipe Hands
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                }
            });
            
            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.8,
                minTrackingConfidence: 0.8
            });
            
            this.hands.onResults(this.onHandResults.bind(this));
            
            // Inicializar câmera
            this.camera = new Camera(this.videoElement, {
                onFrame: async () => {
                    if (this.hands) {
                        await this.hands.send({ image: this.videoElement });
                    }
                },
                width: 640,
                height: 480
            });
            
            // Configurar canvas quando o vídeo carregar
            this.videoElement.addEventListener('loadedmetadata', () => {
                this.resizeCanvas();
            });
            
            this.videoElement.addEventListener('play', () => {
                this.resizeCanvas();
            });
            
            await this.camera.start();
            
            this.updateSystemStatus('active', 'Câmera ativa - Pronto para capturar');
            this.updateCameraStatus('Conectada');
            this.startCameraBtn.textContent = '📹 Parar Câmera';
            this.startCameraBtn.style.background = '#dc3545';
            
            this.showFeedback('Câmera iniciada com sucesso! Posicione sua mão na frente da câmera.', 'success');
            
        } catch (error) {
            console.error('Erro ao iniciar câmera:', error);
            this.updateSystemStatus('inactive', 'Erro na câmera');
            this.showFeedback(`Erro ao iniciar câmera: ${error.message}`, 'error');
        }
    }
    
    stopCamera() {
        if (this.camera) {
            this.camera.stop();
            this.camera = null;
        }
        
        if (this.hands) {
            this.hands.close();
            this.hands = null;
        }
        
        this.currentLandmarks = null;
        this.updateSystemStatus('inactive', 'Câmera desconectada');
        this.updateCameraStatus('Desconectada');
        this.updateHandDetection('Nenhuma mão detectada');
        this.startCameraBtn.textContent = '📷 Iniciar Câmera';
        this.startCameraBtn.style.background = '#28a745';
        this.captureGestureBtn.disabled = true;
        
        this.showFeedback('Câmera desconectada.', 'info');
    }
    
    onHandResults(results) {
        // Ajustar tamanho do canvas para corresponder ao vídeo
        if (this.videoElement.videoWidth > 0 && this.videoElement.videoHeight > 0) {
            if (this.landmarksCanvas.width !== this.videoElement.videoWidth || 
                this.landmarksCanvas.height !== this.videoElement.videoHeight) {
                this.resizeCanvas();
            }
        }
        
        // Limpar canvas anterior
        this.canvasCtx.clearRect(0, 0, this.landmarksCanvas.width, this.landmarksCanvas.height);
        
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            this.currentLandmarks = results.multiHandLandmarks[0];
            
            // Desenhar landmarks no canvas
            this.drawHandLandmarks(this.currentLandmarks);
            
            // Calcular qualidade da detecção
            const quality = this.calculateHandQuality(this.currentLandmarks);
            this.updateHandDetection(`Mão detectada - Qualidade: ${quality}%`);
            
            // Habilitar captura se tiver letra selecionada e boa qualidade
            const canCapture = this.letterSelect.value && quality >= 70 && !this.isCapturing;
            this.captureGestureBtn.disabled = !canCapture;
            
            if (quality >= 70) {
                document.getElementById('qualityIndicator').textContent = `${quality}% - Boa`;
                document.getElementById('qualityIndicator').style.color = '#28a745';
            } else {
                document.getElementById('qualityIndicator').textContent = `${quality}% - Ruim`;
                document.getElementById('qualityIndicator').style.color = '#dc3545';
            }
            
        } else {
            this.currentLandmarks = null;
            this.updateHandDetection('Nenhuma mão detectada');
            this.captureGestureBtn.disabled = true;
            document.getElementById('qualityIndicator').textContent = '-';
        }
    }
    
    calculateHandQuality(landmarks) {
        if (!landmarks || landmarks.length < 21) return 0;
        
        // Verificar se todos os pontos estão dentro da tela
        let validPoints = 0;
        landmarks.forEach(point => {
            if (point.x >= 0 && point.x <= 1 && point.y >= 0 && point.y <= 1) {
                validPoints++;
            }
        });
        
        // Calcular estabilidade (baseado na variação das coordenadas)
        const avgX = landmarks.reduce((sum, p) => sum + p.x, 0) / landmarks.length;
        const avgY = landmarks.reduce((sum, p) => sum + p.y, 0) / landmarks.length;
        
        let stability = 0;
        landmarks.forEach(point => {
            const distance = Math.sqrt(Math.pow(point.x - avgX, 2) + Math.pow(point.y - avgY, 2));
            stability += Math.max(0, 1 - distance * 5); // Penalizar pontos muito espalhados
        });
        
        const stabilityScore = (stability / landmarks.length) * 100;
        const validityScore = (validPoints / 21) * 100;
        
        return Math.round((stabilityScore + validityScore) / 2);
    }
    
    resizeCanvas() {
        if (this.videoElement.videoWidth > 0 && this.videoElement.videoHeight > 0) {
            this.landmarksCanvas.width = this.videoElement.videoWidth;
            this.landmarksCanvas.height = this.videoElement.videoHeight;
            console.log('📐 Canvas redimensionado:', this.landmarksCanvas.width, 'x', this.landmarksCanvas.height);
        }
    }
    
    drawHandLandmarks(landmarks) {
        if (!landmarks || landmarks.length === 0) return;
        
        console.log('🎯 Desenhando landmarks:', landmarks.length, 'pontos');
        
        const ctx = this.canvasCtx;
        const canvas = this.landmarksCanvas;
        
        // Desenhar conexões entre os pontos
        const connections = [
            // Polegar
            [0, 1], [1, 2], [2, 3], [3, 4],
            // Indicador
            [0, 5], [5, 6], [6, 7], [7, 8],
            // Médio
            [0, 9], [9, 10], [10, 11], [11, 12],
            // Anelar
            [0, 13], [13, 14], [14, 15], [15, 16],
            // Mindinho
            [0, 17], [17, 18], [18, 19], [19, 20],
            // Conexões entre dedos
            [5, 9], [9, 13], [13, 17]
        ];
        
        // Desenhar linhas das conexões
        ctx.strokeStyle = '#00FF00';
        ctx.lineWidth = 3;
        connections.forEach(([start, end]) => {
            const startPoint = landmarks[start];
            const endPoint = landmarks[end];
            
            ctx.beginPath();
            ctx.moveTo(startPoint.x * canvas.width, startPoint.y * canvas.height);
            ctx.lineTo(endPoint.x * canvas.width, endPoint.y * canvas.height);
            ctx.stroke();
        });
        
        // Desenhar pontos dos landmarks
        ctx.fillStyle = '#FF0000';
        landmarks.forEach((point, index) => {
            const x = point.x * canvas.width;
            const y = point.y * canvas.height;
            
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, 2 * Math.PI);
            ctx.fill();
            
            // Desenhar número do ponto (opcional para debug)
            if (false) { // Mude para true se quiser ver os números
                ctx.fillStyle = '#FFFFFF';
                ctx.font = '12px Arial';
                ctx.fillText(index.toString(), x + 8, y - 8);
                ctx.fillStyle = '#FF0000';
            }
        });
    }

    async captureCurrentGesture() {
        if (!this.currentLandmarks || !this.letterSelect.value) {
            this.showFeedback('Selecione uma letra e certifique-se de que sua mão está sendo detectada.', 'error');
            return;
        }
        
        const selectedLetter = this.letterSelect.value;
        
        try {
            this.isCapturing = true;
            this.captureGestureBtn.disabled = true;
            
            // Mostrar countdown
            await this.showCountdown();
            
            // Capturar landmarks atuais
            const gestureData = {
                letter: selectedLetter,
                landmarks: this.currentLandmarks.map(point => ({
                    x: point.x,
                    y: point.y,
                    z: point.z
                })),
                timestamp: new Date().toISOString(),
                quality: this.calculateHandQuality(this.currentLandmarks)
            };
            
            // Salvar no servidor
            const response = await fetch('/api/save_gesture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(gestureData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showFeedback(`✅ Gesto para letra ${selectedLetter} salvo com sucesso!`, 'success');
                this.savedGestures[selectedLetter] = gestureData;
                this.updateGestureDisplay();
                this.clearGestureBtn.disabled = false;
            } else {
                throw new Error('Erro ao salvar no servidor');
            }
            
        } catch (error) {
            console.error('Erro ao capturar gesto:', error);
            this.showFeedback(`❌ Erro ao salvar gesto: ${error.message}`, 'error');
        } finally {
            this.isCapturing = false;
            this.captureGestureBtn.disabled = false;
        }
    }
    
    async showCountdown() {
        return new Promise(resolve => {
            let count = 3;
            this.countdown.style.display = 'block';
            this.countdown.textContent = count;
            
            const timer = setInterval(() => {
                count--;
                if (count > 0) {
                    this.countdown.textContent = count;
                } else {
                    this.countdown.textContent = '📸 CAPTURAR!';
                    setTimeout(() => {
                        this.countdown.style.display = 'none';
                        clearInterval(timer);
                        resolve();
                    }, 500);
                }
            }, 1000);
        });
    }
    
    async clearSelectedGesture() {
        const selectedLetter = this.letterSelect.value;
        if (!selectedLetter) {
            this.showFeedback('Selecione uma letra para limpar.', 'error');
            return;
        }
        
        if (!confirm(`Tem certeza que deseja remover o gesto da letra ${selectedLetter}?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/delete_gesture/${selectedLetter}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                delete this.savedGestures[selectedLetter];
                this.updateGestureDisplay();
                this.clearGestureBtn.disabled = true;
                this.showFeedback(`Gesto da letra ${selectedLetter} removido.`, 'info');
            } else {
                throw new Error('Erro ao remover do servidor');
            }
        } catch (error) {
            this.showFeedback(`Erro ao remover gesto: ${error.message}`, 'error');
        }
    }
    
    async loadSavedGestures() {
        try {
            const response = await fetch('/api/get_gestures');
            if (response.ok) {
                const gestures = await response.json();
                this.savedGestures = gestures;
                this.updateGestureDisplay();
            }
        } catch (error) {
            console.error('Erro ao carregar gestos:', error);
            this.showFeedback('Erro ao carregar gestos salvos.', 'error');
        }
    }
    
    updateGestureDisplay() {
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
        this.gestureList.innerHTML = '';
        
        alphabet.forEach(letter => {
            const gestureItem = document.createElement('div');
            gestureItem.className = 'gesture-item';
            
            if (this.savedGestures[letter]) {
                gestureItem.classList.add('has-gesture');
                const gesture = this.savedGestures[letter];
                gestureItem.innerHTML = `
                    <div class="letter">${letter}</div>
                    <div class="info">
                        Qualidade: ${gesture.quality}%<br>
                        ${new Date(gesture.timestamp).toLocaleString()}
                    </div>
                    <button class="delete-gesture" onclick="adminSystem.deleteGesture('${letter}')">
                        🗑️ Remover
                    </button>
                `;
            } else {
                gestureItem.innerHTML = `
                    <div class="letter">${letter}</div>
                    <div class="info">Não capturado</div>
                `;
            }
            
            this.gestureList.appendChild(gestureItem);
        });
        
        document.getElementById('totalGestures').textContent = Object.keys(this.savedGestures).length;
    }
    
    async deleteGesture(letter) {
        try {
            const response = await fetch(`/api/delete_gesture/${letter}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                delete this.savedGestures[letter];
                this.updateGestureDisplay();
                this.showFeedback(`Gesto da letra ${letter} removido.`, 'info');
            }
        } catch (error) {
            this.showFeedback(`Erro ao remover gesto: ${error.message}`, 'error');
        }
    }
    
    async exportGestures() {
        try {
            const response = await fetch('/api/export_gestures');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `libras_gestures_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
                this.showFeedback('Backup exportado com sucesso!', 'success');
            }
        } catch (error) {
            this.showFeedback(`Erro ao exportar: ${error.message}`, 'error');
        }
    }
    
    onLetterSelectionChange() {
        const selectedLetter = this.letterSelect.value;
        if (selectedLetter) {
            this.updateCaptureStatus(`Pronto para capturar letra ${selectedLetter}`);
            this.clearGestureBtn.disabled = !this.savedGestures[selectedLetter];
        } else {
            this.updateCaptureStatus('Selecione uma letra');
            this.clearGestureBtn.disabled = true;
        }
    }
    
    // Métodos de atualização da interface
    updateSystemStatus(status, message) {
        const statusElement = document.getElementById('systemStatus');
        const indicator = status === 'active' ? 'active' : status === 'loading' ? 'loading' : 'inactive';
        statusElement.innerHTML = `
            <div><span class="status-indicator ${indicator}"></span> ${message}</div>
        `;
    }
    
    updateCameraStatus(status) {
        this.cameraStatus.textContent = status;
    }
    
    updateHandDetection(text) {
        this.handDetection.textContent = text;
    }
    
    updateCaptureStatus(text) {
        this.captureStatus.textContent = text;
    }
    
    showFeedback(message, type) {
        this.feedbackArea.innerHTML = `
            <div class="feedback ${type}">
                ${message}
            </div>
        `;
        
        // Auto-hide depois de 5 segundos
        setTimeout(() => {
            if (this.feedbackArea.innerHTML.includes(message)) {
                this.feedbackArea.innerHTML = '';
            }
        }, 5000);
    }
}

// Disponibilizar globalmente
window.AdminGestureCapture = AdminGestureCapture;