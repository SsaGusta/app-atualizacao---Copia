"""
Módulo de Reconhecimento LIBRAS
Implementa o reconhecimento de letras em LIBRAS usando dados do arquivo CSV
"""

import os
import pandas as pd
import numpy as np
import cv2
import base64
import io
import mediapipe as mp
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import logging

logger = logging.getLogger(__name__)

class LibrasRecognizer:
    def __init__(self, csv_path="dados_libras.csv", model_path="libras_model.pkl"):
        """
        Inicializar o reconhecedor LIBRAS
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados de treinamento
            model_path: Caminho para salvar/carregar o modelo treinado
        """
        self.csv_path = csv_path
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        
        # Configurar MediaPipe
        self.mp_hands = mp.solutions.hands
        # Não inicializar aqui - criar nova instância para cada processamento
        self.hands = None
        
        # Carregar ou treinar modelo
        self.load_or_train_model()
    
    def load_data(self):
        """Carregar dados do CSV"""
        try:
            logger.info(f"Carregando dados de {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            
            # Remover primeira linha se contém headers
            if df.iloc[0]['label'] == 'label':
                df = df.drop(0).reset_index(drop=True)
            
            # Separar features e labels
            feature_columns = [col for col in df.columns if col != 'label']
            X = df[feature_columns].astype(float)
            y = df['label']
            
            logger.info(f"Dados carregados: {len(df)} amostras, {len(feature_columns)} features")
            logger.info(f"Labels únicos: {sorted(y.unique())}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            return None, None
    
    def preprocess_data(self, X, y):
        """Preprocessar dados para treinamento"""
        try:
            # Criar codificação de labels
            unique_labels = sorted(y.unique())
            self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
            self.reverse_label_encoder = {idx: label for label, idx in self.label_encoder.items()}
            
            # Codificar labels
            y_encoded = [self.label_encoder[label] for label in y]
            
            # Escalar features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            logger.info(f"Dados preprocessados: {X_scaled.shape[0]} amostras, {X_scaled.shape[1]} features")
            
            return X_scaled, y_encoded
            
        except Exception as e:
            logger.error(f"Erro no preprocessamento: {e}")
            return None, None
    
    def train_model(self, X, y):
        """Treinar modelo de classificação"""
        try:
            logger.info("Treinando modelo KNN...")
            
            # Dividir dados em treino e teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Treinar modelo KNN
            self.model = KNeighborsClassifier(n_neighbors=5, weights='distance')
            self.model.fit(X_train, y_train)
            
            # Avaliar modelo
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Modelo treinado com acurácia: {accuracy:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro no treinamento: {e}")
            return False
    
    def save_model(self):
        """Salvar modelo e preprocessadores"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
                'reverse_label_encoder': self.reverse_label_encoder
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Modelo salvo em {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar modelo: {e}")
            return False
    
    def load_model(self):
        """Carregar modelo salvo"""
        try:
            if not os.path.exists(self.model_path):
                return False
            
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.reverse_label_encoder = model_data['reverse_label_encoder']
            
            logger.info(f"Modelo carregado de {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False
    
    def load_or_train_model(self):
        """Carregar modelo existente ou treinar novo"""
        # Tentar carregar modelo existente
        if self.load_model():
            logger.info("Modelo carregado com sucesso")
            return
        
        # Treinar novo modelo
        logger.info("Treinando novo modelo...")
        X, y = self.load_data()
        
        if X is None or y is None:
            logger.error("Falha ao carregar dados")
            return
        
        X_processed, y_processed = self.preprocess_data(X, y)
        
        if X_processed is None or y_processed is None:
            logger.error("Falha no preprocessamento")
            return
        
        if self.train_model(X_processed, y_processed):
            self.save_model()
            logger.info("Modelo treinado e salvo com sucesso")
        else:
            logger.error("Falha no treinamento do modelo")
    
    def extract_hand_landmarks(self, image_data):
        """
        Extrair landmarks da mão usando MediaPipe
        
        Args:
            image_data: String base64 da imagem
            
        Returns:
            Array numpy com coordenadas dos landmarks ou None
        """
        try:
            # Decodificar imagem base64
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Falha ao decodificar imagem")
                return None
            
            # Converter BGR para RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Criar nova instância do MediaPipe para cada processamento
            # Isso evita problemas de timestamp
            with self.mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            ) as hands:
                # Processar com MediaPipe
                results = hands.process(image_rgb)
                
                if results.multi_hand_landmarks:
                    # Pegar primeira mão detectada
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    # Extrair coordenadas (x, y, z) para cada landmark
                    landmarks = []
                    for landmark in hand_landmarks.landmark:
                        landmarks.extend([landmark.x, landmark.y, landmark.z])
                    
                    logger.info(f"Mão detectada com {len(landmarks)} coordenadas")
                    return np.array(landmarks)
                
                else:
                    logger.info("Nenhuma mão detectada na imagem")
                    return None
                
        except Exception as e:
            logger.error(f"Erro na extração de landmarks: {e}")
            return None
    
    def predict_letter(self, image_data):
        """
        Prever letra LIBRAS a partir de imagem
        
        Args:
            image_data: String base64 da imagem
            
        Returns:
            Tuple (letra, confiança) ou (None, 0)
        """
        try:
            if self.model is None or self.scaler is None:
                logger.error("Modelo não carregado")
                return None, 0
            
            # Extrair landmarks
            landmarks = self.extract_hand_landmarks(image_data)
            
            if landmarks is None:
                return None, 0
            
            # Verificar se temos o número correto de features
            expected_features = 63  # 21 landmarks * 3 coordenadas
            if len(landmarks) != expected_features:
                logger.error(f"Número incorreto de features: {len(landmarks)} != {expected_features}")
                return None, 0
            
            # Preprocessar
            landmarks_scaled = self.scaler.transform([landmarks])
            
            # Prever
            prediction = self.model.predict(landmarks_scaled)[0]
            
            # Calcular confiança usando probabilidades dos vizinhos
            try:
                probabilities = self.model.predict_proba(landmarks_scaled)[0]
                confidence = float(np.max(probabilities))
            except:
                # Fallback: usar distância dos vizinhos
                distances, indices = self.model.kneighbors(landmarks_scaled)
                # Converter distância em confiança (distância menor = confiança maior)
                avg_distance = np.mean(distances[0])
                confidence = max(0.1, 1.0 - min(avg_distance, 1.0))
            
            # Decodificar label
            letter = self.reverse_label_encoder.get(prediction, None)
            
            logger.info(f"Predição: {letter} (confiança: {confidence:.3f})")
            
            return letter, float(confidence)
            
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            return None, 0

# Instância global do reconhecedor
recognizer = None

def initialize_recognizer(csv_path="dados_libras.csv"):
    """Inicializar reconhecedor global"""
    global recognizer
    try:
        recognizer = LibrasRecognizer(csv_path=csv_path)
        logger.info("Reconhecedor LIBRAS inicializado")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar reconhecedor: {e}")
        return False

def recognize_letter(image_data):
    """
    Função principal para reconhecimento de letra
    
    Args:
        image_data: String base64 da imagem
        
    Returns:
        Tuple (letra, confiança)
    """
    global recognizer
    
    if recognizer is None:
        logger.error("Reconhecedor não inicializado")
        return None, 0
    
    return recognizer.predict_letter(image_data)