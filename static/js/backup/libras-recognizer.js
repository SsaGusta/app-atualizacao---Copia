/**
 * Libras Letter Recognition using MediaPipe
 * Reconhecimento de letras em Libras usando landmarks da mão
 */

class LibrasLetterRecognizer {
    constructor() {
        this.landmarks = null;
        this.lastRecognizedLetter = '';
        this.confidenceThreshold = 0.7;
        this.stabilityFrames = 5; // Número de frames para confirmar reconhecimento
        this.frameCounter = {};
        
        // Inicializar padrões de letras
        this.initializeLetterPatterns();
    }
    
    /**
     * Inicializar padrões básicos das letras em Libras
     * Baseado nas posições dos landmarks da mão do MediaPipe
     */
    initializeLetterPatterns() {
        // Landmarks importantes da mão MediaPipe:
        // 0: Pulso, 4: Polegar, 8: Indicador, 12: Médio, 16: Anelar, 20: Mindinho
        
        this.letterPatterns = {
            'A': {
                description: 'Punho fechado com polegar para o lado',
                check: (landmarks) => this.checkLetterA(landmarks)
            },
            'B': {
                description: 'Mão aberta, dedos estendidos e juntos',
                check: (landmarks) => this.checkLetterB(landmarks)
            },
            'C': {
                description: 'Mão em formato de C',
                check: (landmarks) => this.checkLetterC(landmarks)
            },
            'D': {
                description: 'Só o indicador estendido',
                check: (landmarks) => this.checkLetterD(landmarks)
            },
            'E': {
                description: 'Dedos curvados',
                check: (landmarks) => this.checkLetterE(landmarks)
            },
            'F': {
                description: 'Indicador e polegar se tocam, outros dedos estendidos',
                check: (landmarks) => this.checkLetterF(landmarks)
            },
            'G': {
                description: 'Indicador apontando horizontalmente',
                check: (landmarks) => this.checkLetterG(landmarks)
            },
            'H': {
                description: 'Indicador e médio estendidos horizontalmente',
                check: (landmarks) => this.checkLetterH(landmarks)
            },
            'I': {
                description: 'Só o mindinho estendido',
                check: (landmarks) => this.checkLetterI(landmarks)
            },
            'L': {
                description: 'Polegar e indicador em L',
                check: (landmarks) => this.checkLetterL(landmarks)
            },
            'O': {
                description: 'Mão em formato de O',
                check: (landmarks) => this.checkLetterO(landmarks)
            },
            'U': {
                description: 'Indicador e médio estendidos juntos',
                check: (landmarks) => this.checkLetterU(landmarks)
            },
            'V': {
                description: 'Indicador e médio estendidos separados',
                check: (landmarks) => this.checkLetterV(landmarks)
            }
        };
    }
    
    /**
     * Processar landmarks da mão e reconhecer letra
     */
    recognizeLetter(landmarks) {
        if (!landmarks || landmarks.length < 21) {
            return null;
        }
        
        this.landmarks = landmarks;
        let bestMatch = null;
        let highestConfidence = 0;
        
        // Testar cada padrão de letra
        for (const [letter, pattern] of Object.entries(this.letterPatterns)) {
            const confidence = pattern.check(landmarks);
            
            if (confidence > highestConfidence && confidence > this.confidenceThreshold) {
                highestConfidence = confidence;
                bestMatch = {
                    letter: letter,
                    confidence: confidence
                };
            }
        }
        
        // Sistema de estabilidade - confirmar reconhecimento
        if (bestMatch) {
            return this.confirmRecognition(bestMatch.letter, bestMatch.confidence);
        }
        
        return null;
    }
    
    /**
     * Confirmar reconhecimento através de múltiplos frames
     */
    confirmRecognition(letter, confidence) {
        if (!this.frameCounter[letter]) {
            this.frameCounter[letter] = 0;
        }
        
        this.frameCounter[letter]++;
        
        // Resetar contadores de outras letras
        for (const otherLetter in this.frameCounter) {
            if (otherLetter !== letter) {
                this.frameCounter[otherLetter] = Math.max(0, this.frameCounter[otherLetter] - 1);
            }
        }
        
        // Se a letra foi detectada por frames suficientes
        if (this.frameCounter[letter] >= this.stabilityFrames) {
            this.lastRecognizedLetter = letter;
            return {
                letter: letter,
                confidence: confidence,
                stable: true
            };
        }
        
        return {
            letter: letter,
            confidence: confidence,
            stable: false
        };
    }
    
    /**
     * Utilitários para cálculo de distâncias e ângulos
     */
    distance(point1, point2) {
        return Math.sqrt(
            Math.pow(point1.x - point2.x, 2) + 
            Math.pow(point1.y - point2.y, 2)
        );
    }
    
    isFingerExtended(landmarks, fingerTip, fingerDip) {
        return landmarks[fingerTip].y < landmarks[fingerDip].y;
    }
    
    isFingerCurved(landmarks, fingerTip, fingerDip, fingerPip) {
        return landmarks[fingerTip].y > landmarks[fingerDip].y && 
               landmarks[fingerDip].y > landmarks[fingerPip].y;
    }
    
    /**
     * Reconhecimento específico das letras
     */
    
    checkLetterA(landmarks) {
        // A: Punho fechado com polegar para o lado
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const middleTip = landmarks[12];
        const ringTip = landmarks[16];
        const pinkyTip = landmarks[20];
        
        // Verificar se dedos estão fechados (exceto polegar)
        const fingersClosed = !this.isFingerExtended(landmarks, 8, 6) &&
                             !this.isFingerExtended(landmarks, 12, 10) &&
                             !this.isFingerExtended(landmarks, 16, 14) &&
                             !this.isFingerExtended(landmarks, 20, 18);
        
        // Polegar deve estar ao lado
        const thumbPosition = thumbTip.x > landmarks[3].x;
        
        return fingersClosed && thumbPosition ? 0.85 : 0.3;
    }
    
    checkLetterB(landmarks) {
        // B: Mão aberta, dedos estendidos e juntos
        const fingersExtended = this.isFingerExtended(landmarks, 8, 6) &&
                               this.isFingerExtended(landmarks, 12, 10) &&
                               this.isFingerExtended(landmarks, 16, 14) &&
                               this.isFingerExtended(landmarks, 20, 18);
        
        // Verificar se dedos estão juntos
        const fingersTogether = this.distance(landmarks[8], landmarks[12]) < 0.05 &&
                               this.distance(landmarks[12], landmarks[16]) < 0.05 &&
                               this.distance(landmarks[16], landmarks[20]) < 0.05;
        
        // Polegar fechado
        const thumbClosed = landmarks[4].y > landmarks[3].y;
        
        return fingersExtended && fingersTogether && thumbClosed ? 0.9 : 0.4;
    }
    
    checkLetterC(landmarks) {
        // C: Mão em formato de C
        const curvature = this.isFingerCurved(landmarks, 8, 6, 5) &&
                         this.isFingerCurved(landmarks, 12, 10, 9) &&
                         this.isFingerCurved(landmarks, 16, 14, 13) &&
                         this.isFingerCurved(landmarks, 20, 18, 17);
        
        // Polegar e indicador formando C
        const cShape = this.distance(landmarks[4], landmarks[8]) > 0.1 &&
                      this.distance(landmarks[4], landmarks[8]) < 0.2;
        
        return curvature && cShape ? 0.8 : 0.3;
    }
    
    checkLetterD(landmarks) {
        // D: Só o indicador estendido
        const indexExtended = this.isFingerExtended(landmarks, 8, 6);
        const othersClosed = !this.isFingerExtended(landmarks, 12, 10) &&
                            !this.isFingerExtended(landmarks, 16, 14) &&
                            !this.isFingerExtended(landmarks, 20, 18);
        
        // Polegar pode estar em várias posições
        return indexExtended && othersClosed ? 0.85 : 0.4;
    }
    
    checkLetterE(landmarks) {
        // E: Dedos curvados
        const allCurved = this.isFingerCurved(landmarks, 8, 6, 5) &&
                         this.isFingerCurved(landmarks, 12, 10, 9) &&
                         this.isFingerCurved(landmarks, 16, 14, 13) &&
                         this.isFingerCurved(landmarks, 20, 18, 17);
        
        const thumbCurved = landmarks[4].y > landmarks[2].y;
        
        return allCurved && thumbCurved ? 0.8 : 0.3;
    }
    
    checkLetterF(landmarks) {
        // F: Indicador e polegar se tocam, outros estendidos
        const thumbIndexClose = this.distance(landmarks[4], landmarks[8]) < 0.05;
        
        const othersExtended = this.isFingerExtended(landmarks, 12, 10) &&
                              this.isFingerExtended(landmarks, 16, 14) &&
                              this.isFingerExtended(landmarks, 20, 18);
        
        return thumbIndexClose && othersExtended ? 0.85 : 0.4;
    }
    
    checkLetterG(landmarks) {
        // G: Indicador apontando horizontalmente
        const indexExtended = this.isFingerExtended(landmarks, 8, 6);
        const indexHorizontal = Math.abs(landmarks[8].y - landmarks[5].y) < 0.03;
        
        const othersClosed = !this.isFingerExtended(landmarks, 12, 10) &&
                            !this.isFingerExtended(landmarks, 16, 14) &&
                            !this.isFingerExtended(landmarks, 20, 18);
        
        return indexExtended && indexHorizontal && othersClosed ? 0.8 : 0.3;
    }
    
    checkLetterH(landmarks) {
        // H: Indicador e médio estendidos horizontalmente
        const indexExtended = this.isFingerExtended(landmarks, 8, 6);
        const middleExtended = this.isFingerExtended(landmarks, 12, 10);
        
        const horizontal = Math.abs(landmarks[8].y - landmarks[12].y) < 0.03;
        
        const othersClosed = !this.isFingerExtended(landmarks, 16, 14) &&
                            !this.isFingerExtended(landmarks, 20, 18);
        
        return indexExtended && middleExtended && horizontal && othersClosed ? 0.85 : 0.4;
    }
    
    checkLetterI(landmarks) {
        // I: Só o mindinho estendido
        const pinkyExtended = this.isFingerExtended(landmarks, 20, 18);
        
        const othersClosed = !this.isFingerExtended(landmarks, 8, 6) &&
                            !this.isFingerExtended(landmarks, 12, 10) &&
                            !this.isFingerExtended(landmarks, 16, 14);
        
        return pinkyExtended && othersClosed ? 0.85 : 0.4;
    }
    
    checkLetterL(landmarks) {
        // L: Polegar e indicador em L
        const thumbExtended = landmarks[4].x > landmarks[3].x;
        const indexExtended = this.isFingerExtended(landmarks, 8, 6);
        
        // Ângulo aproximado de 90 graus
        const angle = Math.abs(landmarks[4].x - landmarks[8].x) > 0.05 &&
                     Math.abs(landmarks[4].y - landmarks[8].y) > 0.05;
        
        const othersClosed = !this.isFingerExtended(landmarks, 12, 10) &&
                            !this.isFingerExtended(landmarks, 16, 14) &&
                            !this.isFingerExtended(landmarks, 20, 18);
        
        return thumbExtended && indexExtended && angle && othersClosed ? 0.85 : 0.4;
    }
    
    checkLetterO(landmarks) {
        // O: Mão em formato de O
        const thumbIndexClose = this.distance(landmarks[4], landmarks[8]) < 0.08;
        
        // Outros dedos curvados formando O
        const othersCurved = this.isFingerCurved(landmarks, 12, 10, 9) &&
                            this.isFingerCurved(landmarks, 16, 14, 13) &&
                            this.isFingerCurved(landmarks, 20, 18, 17);
        
        return thumbIndexClose && othersCurved ? 0.8 : 0.3;
    }
    
    checkLetterU(landmarks) {
        // U: Indicador e médio estendidos juntos
        const indexExtended = this.isFingerExtended(landmarks, 8, 6);
        const middleExtended = this.isFingerExtended(landmarks, 12, 10);
        
        const together = this.distance(landmarks[8], landmarks[12]) < 0.04;
        
        const othersClosed = !this.isFingerExtended(landmarks, 16, 14) &&
                            !this.isFingerExtended(landmarks, 20, 18);
        
        return indexExtended && middleExtended && together && othersClosed ? 0.85 : 0.4;
    }
    
    checkLetterV(landmarks) {
        // V: Indicador e médio estendidos separados
        const indexExtended = this.isFingerExtended(landmarks, 8, 6);
        const middleExtended = this.isFingerExtended(landmarks, 12, 10);
        
        const separated = this.distance(landmarks[8], landmarks[12]) > 0.06;
        
        const othersClosed = !this.isFingerExtended(landmarks, 16, 14) &&
                            !this.isFingerExtended(landmarks, 20, 18);
        
        return indexExtended && middleExtended && separated && othersClosed ? 0.85 : 0.4;
    }
    
    /**
     * Obter estatísticas do reconhecimento
     */
    getRecognitionStats() {
        return {
            lastLetter: this.lastRecognizedLetter,
            frameCounters: { ...this.frameCounter },
            availableLetters: Object.keys(this.letterPatterns)
        };
    }
    
    /**
     * Resetar contadores
     */
    reset() {
        this.frameCounter = {};
        this.lastRecognizedLetter = '';
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.LibrasLetterRecognizer = LibrasLetterRecognizer;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LibrasLetterRecognizer;
}