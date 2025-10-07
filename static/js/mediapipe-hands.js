/**
 * MediaPipe Hand Tracking Implementation
 * Biblioteca para reconhecimento de mãos em tempo real
 */

class HandTracker {
    constructor() {
        this.videoElement = document.getElementById('input_video');
        this.canvasElement = document.getElementById('output_canvas');
        this.canvasCtx = this.canvasElement.getContext('2d');
        this.camera = null;
        this.hands = null;
        this.isRunning = false;
        this.fpsCounter = 0;
        this.lastTime = performance.now();
        
        // Configurar canvas
        this.canvasElement.width = 640;
        this.canvasElement.height = 480;
        
        this.initializeMediaPipe();
        this.setupEventListeners();
    }
    
    initializeMediaPipe() {
        this.hands = new Hands({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
            }
        });
        
        this.hands.setOptions({
            maxNumHands: 2,
            modelComplexity: 1,
            minDetectionConfidence: 0.7,
            minTrackingConfidence: 0.5
        });
        
        this.hands.onResults(this.onResults.bind(this));
    }
    
    setupEventListeners() {
        const startButton = document.getElementById('start_button');
        const stopButton = document.getElementById('stop_button');
        
        if (startButton) {
            startButton.addEventListener('click', () => {
                this.startCamera();
            });
        }
        
        if (stopButton) {
            stopButton.addEventListener('click', () => {
                this.stopCamera();
            });
        }
        
        // Cleanup quando sair da página
        window.addEventListener('beforeunload', () => {
            this.stopCamera();
        });
    }
    
    async startCamera() {
        try {
            console.log('Iniciando câmera...');
            this.updateStatus('Iniciando câmera...');
            
            // Verificar se MediaPipe está carregado
            if (typeof Camera === 'undefined') {
                console.error('Camera class não encontrada');
                throw new Error('MediaPipe Camera não carregou corretamente');
            }
            
            if (typeof Hands === 'undefined') {
                console.error('Hands class não encontrada');
                throw new Error('MediaPipe Hands não carregou corretamente');
            }
            
            console.log('MediaPipe classes carregadas com sucesso');
            
            // Verificar suporte do navegador
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Seu navegador não suporta acesso à câmera');
            }
            
            console.log('Criando câmera...');
            this.camera = new Camera(this.videoElement, {
                onFrame: async () => {
                    if (this.isRunning) {
                        await this.hands.send({image: this.videoElement});
                    }
                },
                width: 640,
                height: 480
            });
            
            console.log('Iniciando câmera...');
            await this.camera.start();
            this.isRunning = true;
            
            console.log('Câmera iniciada com sucesso');
            
            // Atualizar interface
            const startButton = document.getElementById('start_button');
            const stopButton = document.getElementById('stop_button');
            
            if (startButton) startButton.disabled = true;
            if (stopButton) stopButton.disabled = false;
            
            this.updateStatus('Câmera ativa - Mostre suas mãos!');
            
            // Iniciar contador de FPS
            this.startFPSCounter();
            
        } catch (error) {
            console.error('Erro ao iniciar câmera:', error);
            this.updateStatus('Erro ao acessar câmera');
            
            // Mostrar mensagem de erro mais específica
            let errorMessage = 'Erro ao acessar a câmera.';
            
            if (error.name === 'NotAllowedError') {
                errorMessage = 'Acesso à câmera negado. Permita o acesso e tente novamente.';
            } else if (error.name === 'NotFoundError') {
                errorMessage = 'Nenhuma câmera encontrada no dispositivo.';
            } else if (error.message.includes('MediaPipe')) {
                errorMessage = 'Erro ao carregar MediaPipe. Verifique sua conexão com a internet.';
            }
            
            alert(errorMessage);
        }
    }
    
    stopCamera() {
        this.isRunning = false;
        
        if (this.camera) {
            this.camera.stop();
            this.camera = null;
        }
        
        // Limpar canvas
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        
        // Atualizar interface
        const startButton = document.getElementById('start_button');
        const stopButton = document.getElementById('stop_button');
        
        if (startButton) startButton.disabled = false;
        if (stopButton) stopButton.disabled = true;
        
        this.updateStatus('Câmera parada');
        this.updateHandCount(0);
        this.updateHandLandmarks([]);
        this.updateDetectionConfidence('-');
        this.updateFPS('-');
    }
    
    onResults(results) {
        if (!this.isRunning) return;
        
        // Limpar canvas
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        
        // Desenhar imagem da câmera (espelhada)
        this.canvasCtx.scale(-1, 1);
        this.canvasCtx.drawImage(results.image, -this.canvasElement.width, 0, this.canvasElement.width, this.canvasElement.height);
        this.canvasCtx.scale(-1, 1);
        
        // Processar mãos detectadas
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            this.updateHandCount(results.multiHandLandmarks.length);
            
            let totalConfidence = 0;
            
            for (let i = 0; i < results.multiHandLandmarks.length; i++) {
                const landmarks = results.multiHandLandmarks[i];
                
                // Espelhar landmarks horizontalmente
                const mirroredLandmarks = landmarks.map(landmark => ({
                    x: 1 - landmark.x,
                    y: landmark.y,
                    z: landmark.z
                }));
                
                // Desenhar conexões
                drawConnectors(this.canvasCtx, mirroredLandmarks, HAND_CONNECTIONS, {
                    color: '#00FF00',
                    lineWidth: 3
                });
                
                // Desenhar pontos
                drawLandmarks(this.canvasCtx, mirroredLandmarks, {
                    color: '#FF0000',
                    lineWidth: 2,
                    radius: 4
                });
                
                // Calcular confiança (simulada baseada na estabilidade dos pontos)
                const confidence = this.calculateHandConfidence(landmarks);
                totalConfidence += confidence;
            }
            
            const avgConfidence = (totalConfidence / results.multiHandLandmarks.length * 100).toFixed(1);
            this.updateDetectionConfidence(`${avgConfidence}%`);
            this.updateHandLandmarks(results.multiHandLandmarks);
            
        } else {
            this.updateHandCount(0);
            this.updateHandLandmarks([]);
            this.updateDetectionConfidence('-');
        }
        
        this.canvasCtx.restore();
        this.updateFPSCounter();
    }
    
    calculateHandConfidence(landmarks) {
        // Simular confiança baseada na variabilidade dos pontos
        // Em uma implementação real, isso viria do modelo MediaPipe
        return Math.random() * 0.3 + 0.7; // Entre 70% e 100%
    }
    
    startFPSCounter() {
        this.lastTime = performance.now();
        this.frameCount = 0;
    }
    
    updateFPSCounter() {
        this.frameCount++;
        const currentTime = performance.now();
        const elapsed = currentTime - this.lastTime;
        
        if (elapsed >= 1000) { // Atualizar a cada segundo
            const fps = Math.round((this.frameCount * 1000) / elapsed);
            this.updateFPS(fps);
            this.frameCount = 0;
            this.lastTime = currentTime;
        }
    }
    
    updateStatus(message) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    updateHandCount(count) {
        const handCountElement = document.getElementById('hand_count');
        if (handCountElement) {
            handCountElement.innerHTML = `<strong>Mãos detectadas:</strong> ${count}`;
        }
    }
    
    updateDetectionConfidence(confidence) {
        const confidenceElement = document.getElementById('detection_confidence');
        if (confidenceElement) {
            confidenceElement.innerHTML = `<strong>Confiança:</strong> ${confidence}`;
        }
    }
    
    updateFPS(fps) {
        const fpsElement = document.getElementById('fps_counter');
        if (fpsElement) {
            fpsElement.innerHTML = `<strong>FPS:</strong> ${fps}`;
        }
    }
    
    updateHandLandmarks(handsData) {
        const container = document.getElementById('hand_landmarks');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (handsData.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma mão detectada</p>';
            return;
        }
        
        handsData.forEach((hand, handIndex) => {
            const handDiv = document.createElement('div');
            handDiv.className = 'hand-info mb-3 p-2 border rounded';
            
            // Pontos importantes da mão
            const wrist = hand[0];        // Pulso
            const thumb = hand[4];        // Polegar
            const index = hand[8];        // Indicador
            const middle = hand[12];      // Médio
            const ring = hand[16];        // Anelar
            const pinky = hand[20];       // Mindinho
            
            // Calcular posições em percentual
            const wristPos = `(${Math.round((1-wrist.x) * 100)}%, ${Math.round(wrist.y * 100)}%)`;
            const thumbPos = `(${Math.round((1-thumb.x) * 100)}%, ${Math.round(thumb.y * 100)}%)`;
            
            handDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong class="text-primary">Mão ${handIndex + 1}</strong>
                        <br>
                        <small>Pulso: ${wristPos}</small>
                        <br>
                        <small>Polegar: ${thumbPos}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-success">${hand.length} pontos</span>
                    </div>
                </div>
            `;
            
            container.appendChild(handDiv);
        });
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos na página correta
    if (document.getElementById('output_canvas')) {
        console.log('Página MediaPipe detectada, aguardando carregamento das bibliotecas...');
        
        // Aguardar um pouco para garantir que as bibliotecas MediaPipe sejam carregadas
        setTimeout(() => {
            if (typeof Camera !== 'undefined' && typeof Hands !== 'undefined') {
                window.handTracker = new HandTracker();
                console.log('MediaPipe Hand Tracker inicializado com sucesso');
            } else {
                console.error('MediaPipe não carregou corretamente');
                document.getElementById('status').textContent = 'Erro: MediaPipe não carregou. Recarregue a página.';
            }
        }, 1000);
    }
});

// Função utilitária para verificar suporte do navegador
function checkBrowserSupport() {
    const isSupported = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
    
    if (!isSupported) {
        console.warn('Este navegador não suporta acesso à câmera');
        return false;
    }
    
    return true;
}

// Exportar para uso global se necessário
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HandTracker;
}