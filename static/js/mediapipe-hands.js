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
        
        // Sistema de reconhecimento de gestos
        this.savedGestures = {};
        this.lastRecognitionTime = 0;
        this.recognitionDelay = 500; // Reconhecer a cada 500ms para evitar spam
        this.lastDetailedAnalysis = null; // Armazenar análise detalhada
        
        // Configurar canvas
        this.canvasElement.width = 640;
        this.canvasElement.height = 480;
        
        this.initializeMediaPipe();
        this.setupEventListeners();
        this.loadSavedGestures();
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
    
    async loadSavedGestures() {
        try {
            console.log('📥 Carregando gestos salvos...');
            
            // Primeiro verificar informações de sincronização
            await this.checkGestureSync();
            
            const response = await fetch('/api/get_gestures');
            
            if (response.ok) {
                this.savedGestures = await response.json();
                const gestureCount = Object.keys(this.savedGestures).length;
                console.log('✅ Gestos carregados:', gestureCount, 'letras disponíveis');
                
                if (gestureCount > 0) {
                    console.log('📚 Letras disponíveis:', Object.keys(this.savedGestures).join(', '));
                    
                    // Mostrar informações na interface
                    const statusElement = document.getElementById('gestureStatus');
                    if (statusElement) {
                        statusElement.innerHTML = `<strong style="color: #28a745;">Gestos carregados:</strong> ${gestureCount} letras (${Object.keys(this.savedGestures).join(', ')})`;
                    }
                    
                    // Verificar se há gestos de qualidade baixa
                    this.checkGestureQuality();
                } else {
                    console.log('⚠️ Nenhum gesto salvo encontrado. Vá para /admin para capturar gestos.');
                    const statusElement = document.getElementById('gestureStatus');
                    if (statusElement) {
                        statusElement.innerHTML = '<strong style="color: #dc3545;">Atenção:</strong> Nenhum gesto salvo encontrado. <a href="/admin">Capture gestos aqui</a>';
                    }
                }
            } else {
                console.warn('⚠️ Não foi possível carregar gestos salvos');
                this.savedGestures = {};
                const statusElement = document.getElementById('gestureStatus');
                if (statusElement) {
                    statusElement.innerHTML = '<strong style="color: #dc3545;">Erro:</strong> Não foi possível carregar gestos salvos';
                }
            }
        } catch (error) {
            console.error('❌ Erro ao carregar gestos:', error);
            this.savedGestures = {};
            const statusElement = document.getElementById('gestureStatus');
            if (statusElement) {
                statusElement.innerHTML = '<strong style="color: #dc3545;">Erro:</strong> Falha na conexão com o servidor';
            }
        }
    }
    
    async checkGestureSync() {
        // Verifica informações de sincronização dos gestos
        try {
            const response = await fetch('/api/gesture_sync_info');
            if (response.ok) {
                const syncInfo = await response.json();
                console.log('📊 Info de sincronização:', syncInfo);
                
                // Log estatísticas
                console.log(`📈 Progresso: ${syncInfo.completion_percentage?.toFixed(1)}% do alfabeto capturado`);
                console.log(`🎯 Qualidade: ${syncInfo.quality_distribution?.high_quality || 0} alta, ${syncInfo.quality_distribution?.medium_quality || 0} média, ${syncInfo.quality_distribution?.low_quality || 0} baixa`);
                
                // Mostrar letras faltantes
                if (syncInfo.letters_without_gestures && syncInfo.letters_without_gestures.length > 0) {
                    console.log('⚠️ Letras não capturadas:', syncInfo.letters_without_gestures.join(', '));
                }
            }
        } catch (error) {
            console.warn('⚠️ Não foi possível verificar sincronização:', error);
        }
    }
    
    checkGestureQuality() {
        // Verifica e alerta sobre gestos de baixa qualidade
        let lowQualityGestures = [];
        
        for (const [letter, gestureData] of Object.entries(this.savedGestures)) {
            if (gestureData.quality < 70) {
                lowQualityGestures.push(`${letter} (${gestureData.quality}%)`);
            }
        }
        
        if (lowQualityGestures.length > 0) {
            console.warn('⚠️ Gestos de baixa qualidade encontrados:', lowQualityGestures.join(', '));
            console.warn('💡 Considere recapturar estes gestos na área de admin para melhor reconhecimento');
        }
    }
    
    async refreshGestures() {
        // Força o recarregamento dos gestos
        try {
            console.log('🔄 Recarregando gestos...');
            const response = await fetch('/api/refresh_gestures', { method: 'POST' });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Gestos recarregados:', result);
                
                // Recarregar gestos na interface
                await this.loadSavedGestures();
                
                return true;
            } else {
                console.error('❌ Erro ao recarregar gestos');
                return false;
            }
        } catch (error) {
            console.error('❌ Erro ao recarregar gestos:', error);
            return false;
        }
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
        this.updateFPS('-');
    }
    
    onResults(results) {
        if (!this.isRunning) return;
        
        // Limpar canvas
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        
        // Desenhar imagem da câmera (sem espelhamento)
        this.canvasCtx.drawImage(results.image, 0, 0, this.canvasElement.width, this.canvasElement.height);
        
        // Processar mãos detectadas
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            this.updateHandCount(results.multiHandLandmarks.length);
            
            for (let i = 0; i < results.multiHandLandmarks.length; i++) {
                const landmarks = results.multiHandLandmarks[i];
                
                // Desenhar conexões
                drawConnectors(this.canvasCtx, landmarks, HAND_CONNECTIONS, {
                    color: '#00FF00',
                    lineWidth: 3
                });
                
                // Desenhar pontos com cores baseadas na análise (se disponível)
                this.drawLandmarksWithAnalysis(landmarks, this.lastDetailedAnalysis);
                
                // Reconhecer letra (apenas para a primeira mão, com throttling)
                if (i === 0) {
                    this.recognizeGesture(landmarks);
                }
            }
            
            this.updateHandLandmarks(results.multiHandLandmarks);
            
        } else {
            this.updateHandCount(0);
            this.updateHandLandmarks([]);
            this.updateDetectedLetter('-');
        }
        
        this.canvasCtx.restore();
        this.updateFPSCounter();
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

    updateFPS(fps) {
        const fpsElement = document.getElementById('fps_counter');
        if (fpsElement) {
            fpsElement.innerHTML = `<strong>FPS:</strong> ${fps}`;
        }
    }
    
    async recognizeGesture(landmarks) {
        // Throttling para evitar muitas requisições
        const currentTime = Date.now();
        if (currentTime - this.lastRecognitionTime < this.recognitionDelay) {
            return;
        }
        
        this.lastRecognitionTime = currentTime;
        
        try {
            // Verificar se temos gestos salvos
            if (Object.keys(this.savedGestures).length === 0) {
                console.log('⚠️ Nenhum gesto salvo disponível para reconhecimento');
                this.updateDetectedLetter('-', null);
                return;
            }
            
            console.log('🔍 Enviando landmarks para reconhecimento...', {
                numLandmarks: landmarks.length,
                gesturesSalvos: Object.keys(this.savedGestures).length
            });
            
            const response = await fetch('/api/recognize_gesture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    landmarks: landmarks
                })
            });
            
            console.log('📡 Resposta da API:', response.status, response.statusText);
            
            if (response.ok) {
                const data = await response.json();
                console.log('📦 Dados recebidos:', data);
                
                if (data.success && data.result) {
                    const result = data.result;
                    
                    // Log detalhado do reconhecimento
                    console.log('🎯 Reconhecimento detalhado:');
                    console.log(`📝 Letra: ${result.letter}`);
                    console.log(`📊 Similaridade: ${(result.similarity * 100).toFixed(1)}%`);
                    console.log(`🔧 Método: ${result.method || 'traditional'}`);
                    
                    // Se houver análise detalhada, mostrar estatísticas
                    if (result.detailed_analysis && result.detailed_analysis.statistics) {
                        const stats = result.detailed_analysis.statistics;
                        console.log('📈 Análise dos pontos:');
                        console.log(`  ✅ Excelentes: ${stats.excellent_points}/21`);
                        console.log(`  ✔️ Bons: ${stats.good_points}/21`);
                        console.log(`  ⚠️ Aceitáveis: ${stats.acceptable_points}/21`);
                        console.log(`  ❌ Ruins: ${stats.bad_points}/21`);
                        console.log(`  🎯 Taxa de match: ${stats.match_percentage.toFixed(1)}%`);
                        
                        // Mostrar pontos problemáticos
                        if (result.detailed_analysis.point_analysis) {
                            const badPoints = result.detailed_analysis.point_analysis
                                .filter(p => p.quality === 'ruim')
                                .map(p => p.point_id);
                            
                            if (badPoints.length > 0) {
                                console.log(`⚠️ Pontos com problemas: ${badPoints.join(', ')}`);
                            }
                        }
                    }
                    
                    this.updateDetectedLetter(result.letter, result);
                    
                    // Armazenar análise detalhada para visualização
                    this.lastDetailedAnalysis = result.detailed_analysis;
                } else {
                    console.log('❌ API retornou sem resultado de reconhecimento');
                    this.updateDetectedLetter('-');
                }
            } else {
                console.error(`❌ Erro HTTP ${response.status}:`, response.statusText);
                try {
                    const errorData = await response.text();
                    console.error('Detalhes do erro:', errorData);
                } catch (e) {
                    console.error('Não foi possível ler detalhes do erro');
                }
                this.updateDetectedLetter('-');
                
                // Mostrar erro na interface temporariamente
                const statusElement = document.getElementById('gestureStatus');
                if (statusElement) {
                    const originalContent = statusElement.innerHTML;
                    statusElement.innerHTML = `<strong style="color: #dc3545;">Erro na API:</strong> HTTP ${response.status}`;
                    setTimeout(() => {
                        statusElement.innerHTML = originalContent;
                    }, 3000);
                }
            }
        } catch (error) {
            console.error('❌ Erro na conexão com API:', error);
            
            // Verificar tipo de erro
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                console.error('💡 Possível causa: Servidor não está rodando ou problema de CORS');
            }
            
            this.updateDetectedLetter('-');
            
            // Mostrar erro na interface temporariamente
            const statusElement = document.getElementById('gestureStatus');
            if (statusElement) {
                const originalContent = statusElement.innerHTML;
                statusElement.innerHTML = `<strong style="color: #dc3545;">Erro de conexão:</strong> ${error.message}`;
                setTimeout(() => {
                    statusElement.innerHTML = originalContent;
                }, 5000);
            }
        }
    }
    
    updateDetectedLetter(letter, detailedResult = null) {
        const letterElement = document.getElementById('detectedLetter');
        const detailsElement = document.getElementById('recognitionDetails');
        const analysisElement = document.getElementById('analysisInfo');
        const legendElement = document.getElementById('pointLegend');
        
        if (letterElement) {
            letterElement.textContent = letter;
            
            if (letter !== '-') {
                letterElement.style.color = '#28a745';
                letterElement.style.fontWeight = 'bold';
                letterElement.style.fontSize = '1.5em';
                
                // Efeito visual de reconhecimento
                letterElement.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    letterElement.style.transform = 'scale(1.0)';
                }, 200);
                
                // Mostrar informações detalhadas
                if (detailedResult && detailedResult.detailed_analysis) {
                    const stats = detailedResult.detailed_analysis.statistics;
                    
                    // Tooltip detalhado
                    letterElement.title = `Similaridade: ${(detailedResult.similarity * 100).toFixed(1)}%\n` +
                                         `Pontos excelentes: ${stats.excellent_points}/21\n` +
                                         `Pontos bons: ${stats.good_points}/21\n` +
                                         `Taxa de match: ${stats.match_percentage.toFixed(1)}%`;
                    
                    // Informações na interface
                    if (analysisElement && detailsElement) {
                        analysisElement.innerHTML = `Similaridade: ${(detailedResult.similarity * 100).toFixed(1)}% | ` +
                                                   `Match: ${stats.match_percentage.toFixed(1)}% | ` +
                                                   `Pontos OK: ${stats.excellent_points + stats.good_points}/21`;
                        detailsElement.style.display = 'block';
                    }
                    
                    // Mostrar legenda quando há análise detalhada
                    if (legendElement) {
                        legendElement.style.display = 'block';
                    }
                } else {
                    letterElement.title = `Similaridade: ${detailedResult ? (detailedResult.similarity * 100).toFixed(1) + '%' : 'N/A'}`;
                    
                    if (analysisElement && detailsElement) {
                        analysisElement.textContent = detailedResult ? 
                            `Similaridade: ${(detailedResult.similarity * 100).toFixed(1)}%` : 
                            'Análise básica';
                        detailsElement.style.display = 'block';
                    }
                    
                    // Esconder legenda para análise básica
                    if (legendElement) {
                        legendElement.style.display = 'none';
                    }
                }
                
                console.log('✅ Letra reconhecida:', letter);
            } else {
                letterElement.style.color = '#6c757d';
                letterElement.style.fontWeight = 'normal';
                letterElement.style.fontSize = '1.2em';
                letterElement.title = 'Nenhuma letra detectada';
                
                // Esconder detalhes e legenda
                if (detailsElement) {
                    detailsElement.style.display = 'none';
                }
                if (legendElement) {
                    legendElement.style.display = 'none';
                }
            }
        }
    }
    
    drawLandmarksWithAnalysis(landmarks, detailedAnalysis) {
        if (!landmarks) return;
        
        // Se não há análise detalhada, desenhar normalmente
        if (!detailedAnalysis || !detailedAnalysis.point_analysis) {
            drawLandmarks(this.canvasCtx, landmarks, {
                color: '#FF0000',
                lineWidth: 2,
                radius: 4
            });
            return;
        }
        
        // Desenhar cada ponto com cor baseada na qualidade
        const pointAnalysis = detailedAnalysis.point_analysis;
        
        landmarks.forEach((landmark, index) => {
            const analysis = pointAnalysis.find(p => p.point_id === index);
            let color = '#FF0000'; // Padrão vermelho
            let radius = 4;
            
            if (analysis) {
                switch (analysis.quality) {
                    case 'excelente':
                        color = '#00FF00'; // Verde
                        radius = 5;
                        break;
                    case 'bom':
                        color = '#90EE90'; // Verde claro
                        radius = 4;
                        break;
                    case 'aceitável':
                        color = '#FFA500'; // Laranja
                        radius = 4;
                        break;
                    case 'ruim':
                        color = '#FF4444'; // Vermelho forte
                        radius = 6;
                        break;
                }
            }
            
            // Desenhar o ponto
            this.canvasCtx.fillStyle = color;
            this.canvasCtx.beginPath();
            this.canvasCtx.arc(
                landmark.x * this.canvasElement.width,
                landmark.y * this.canvasElement.height,
                radius,
                0,
                2 * Math.PI
            );
            this.canvasCtx.fill();
            
            // Adicionar contorno para pontos ruins
            if (analysis && analysis.quality === 'ruim') {
                this.canvasCtx.strokeStyle = '#FFFFFF';
                this.canvasCtx.lineWidth = 2;
                this.canvasCtx.stroke();
            }
        });
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