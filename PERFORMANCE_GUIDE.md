# Configurações de Performance - Libras Recognition

## 🚀 Otimizações Implementadas

### 1. **Configurações da Webcam**
```python
VIDEO_MIN_SIZE = (800, 600)      # Resolução otimizada
VIDEO_FPS = 15                   # FPS balanceado
FRAME_SKIP = 2                   # Pular frames para acelerar
BUFFER_SIZE = 1                  # Buffer mínimo para reduzir latência
```

### 2. **Modelo Machine Learning**
```python
ML_ESTIMATORS = 20               # Menos árvores = mais velocidade
max_depth = 10                   # Profundidade limitada
min_samples_split = 5            # Menos splits
model_complexity = 0             # MediaPipe mais simples
```

### 3. **Processamento de Frames**
```python
MP_DETECTION_CONFIDENCE = 0.5   # Detecção mais rápida
MP_TRACKING_CONFIDENCE = 0.3     # Tracking mais rápido
Cache de landmarks (100ms)       # Evita reprocessamento
Buffer de predições (3 amostras) # Suavização de resultados
```

### 4. **Renderização Otimizada**
- ✅ Redimensionamento antes da conversão de cor
- ✅ Cache de texto para evitar recálculos
- ✅ Atualização de UI apenas quando necessário
- ✅ Uso de numpy direto ao invés de pandas

## ⚙️ Configurações Ajustáveis

Se quiser mais velocidade (pode reduzir precisão):
```python
VIDEO_FPS = 10                   # Mais rápido
FRAME_SKIP = 3                   # Pular mais frames
ML_ESTIMATORS = 10               # Modelo mais simples
MP_DETECTION_CONFIDENCE = 0.3    # Detecção menos rigorosa
```

Se quiser mais precisão (pode ser mais lento):
```python
VIDEO_FPS = 20                   # Mais suave
FRAME_SKIP = 1                   # Processar todos os frames
ML_ESTIMATORS = 30               # Modelo mais complexo
MP_DETECTION_CONFIDENCE = 0.7    # Detecção mais rigorosa
```

## 📊 Resultados Esperados

### Performance Melhorada:
- ⚡ **Latência reduzida**: ~50% menos delay
- 🎯 **FPS mais estável**: Menos quedas de performance
- 🔄 **Reconhecimento mais fluido**: Buffer de predições
- 💾 **Menos uso de CPU**: Otimizações de processamento

### Recursos Otimizados:
- 📱 **Menor uso de memória**: Cache inteligente
- 🔋 **Menos processamento**: Skip de frames desnecessários
- 🎮 **Resposta mais rápida**: Modelo ML simplificado
- 📺 **Renderização eficiente**: Redimensionamento otimizado

## 🔧 Como Ajustar Performance

### Para computadores mais lentos:
1. Aumente `FRAME_SKIP` para 3 ou 4
2. Reduza `ML_ESTIMATORS` para 10-15
3. Diminua `VIDEO_FPS` para 10-12

### Para computadores mais rápidos:
1. Diminua `FRAME_SKIP` para 1
2. Aumente `ML_ESTIMATORS` para 25-30
3. Aumente `VIDEO_FPS` para 20-25

## 🎛️ Configurações por Hardware

### Hardware Básico (Dual-core, 4GB RAM):
```python
VIDEO_FPS = 10
FRAME_SKIP = 3
ML_ESTIMATORS = 15
VIDEO_MIN_SIZE = (640, 480)
```

### Hardware Médio (Quad-core, 8GB RAM):
```python
VIDEO_FPS = 15
FRAME_SKIP = 2
ML_ESTIMATORS = 20
VIDEO_MIN_SIZE = (800, 600)
```

### Hardware Alto (6+ cores, 16GB+ RAM):
```python
VIDEO_FPS = 20
FRAME_SKIP = 1
ML_ESTIMATORS = 30
VIDEO_MIN_SIZE = (1024, 768)
```

## 🏆 Dicas de Performance

1. **Iluminação**: Boa iluminação melhora detecção
2. **Background**: Fundo contrastante ajuda
3. **Posição**: Mão centralizada na tela
4. **Estabilidade**: Evite movimentos bruscos
5. **Câmera**: Webcam de qualidade faz diferença

## 📈 Monitoramento

Para verificar performance em tempo real:
- Observe a fluidez da imagem
- Verifique se há travamentos
- Monitore uso de CPU/RAM
- Teste reconhecimento de diferentes letras

O sistema foi otimizado para máxima velocidade mantendo boa precisão!