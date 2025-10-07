"""
Teste do Sistema de Reconhecimento LIBRAS Alternativo
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_alternative_recognition():
    """Testar o sistema alternativo de reconhecimento"""
    
    try:
        logger.info("=== TESTE DO SISTEMA ALTERNATIVO ===")
        
        # Importar o sistema alternativo
        from libras_recognition_alt import LibrasRecognizerAlternative
        
        logger.info("1. Importação bem-sucedida")
        
        # Verificar se o arquivo CSV existe
        csv_path = "dados_libras.csv"
        if os.path.exists(csv_path):
            logger.info(f"2. Arquivo CSV encontrado: {csv_path}")
        else:
            logger.error(f"2. Arquivo CSV NÃO encontrado: {csv_path}")
            return False
        
        # Inicializar reconhecedor
        recognizer = LibrasRecognizerAlternative(csv_path=csv_path)
        
        if recognizer.model is not None:
            logger.info("3. Modelo carregado/treinado com sucesso")
        else:
            logger.error("3. Falha ao carregar/treinar modelo")
            return False
        
        # Testar predição com dados simulados
        logger.info("4. Testando predição com features simuladas...")
        
        # Criar features simuladas (63 valores)
        import numpy as np
        fake_features = np.random.rand(63).tolist()
        
        # Converter para "imagem" base64 simulada para teste
        import base64
        fake_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        try:
            letter, confidence = recognizer.predict_letter(fake_image)
            logger.info(f"5. Teste de predição: letra={letter}, confiança={confidence}")
            
            if letter is None:
                logger.info("5. Resultado: Nenhuma mão detectada (esperado para imagem vazia)")
            else:
                logger.info(f"5. Resultado: Letra detectada {letter} com {confidence:.2%} de confiança")
            
        except Exception as e:
            logger.error(f"5. Erro na predição: {e}")
            return False
        
        logger.info("=== TESTE CONCLUÍDO COM SUCESSO ===")
        return True
        
    except ImportError as e:
        logger.error(f"Erro de importação: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro geral: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_opencv_availability():
    """Testar disponibilidade do OpenCV"""
    try:
        import cv2
        logger.info(f"OpenCV disponível: versão {cv2.__version__}")
        return True
    except ImportError:
        logger.error("OpenCV NÃO disponível")
        return False

def test_dependencies():
    """Testar todas as dependências"""
    logger.info("=== TESTE DE DEPENDÊNCIAS ===")
    
    dependencies = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('cv2', 'cv2'),
        ('sklearn', 'sklearn'),
        ('pickle', 'pickle')
    ]
    
    all_ok = True
    
    for dep_name, import_name in dependencies:
        try:
            __import__(import_name)
            logger.info(f"OK {dep_name}")
        except ImportError:
            logger.error(f"FALHA {dep_name} NAO disponivel")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    logger.info("Iniciando testes do sistema alternativo...")
    
    # Teste 1: Dependências
    if not test_dependencies():
        logger.error("Falha nas dependências")
        sys.exit(1)
    
    # Teste 2: OpenCV
    if not test_opencv_availability():
        logger.error("OpenCV não disponível")
        sys.exit(1)
    
    # Teste 3: Sistema alternativo
    if test_alternative_recognition():
        logger.info("TODOS OS TESTES PASSARAM!")
    else:
        logger.error("FALHA NOS TESTES")
        sys.exit(1)