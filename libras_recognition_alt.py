"""
Sistema de Reconhecimento LIBRAS Alternativo
Usando OpenCV + TensorFlow Lite para melhor compatibilidade
"""

import os
import pandas as pd
import numpy as np
import cv2
import base64
import io
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import logging
import json

logger = logging.getLogger(__name__)

class LibrasRecognizerAlternative:
    def __init__(self, csv_path="dados_libras.csv", model_path="libras_model_alt.pkl"):
        """
        Reconhecedor LIBRAS alternativo sem MediaPipe
        """
        self.csv_path = csv_path
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        
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
            return X, y
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            return None, None
    
    def preprocess_data(self, X, y):
        """Preprocessar dados"""
        try:
            unique_labels = sorted(y.unique())
            self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
            self.reverse_label_encoder = {idx: label for label, idx in self.label_encoder.items()}
            
            y_encoded = [self.label_encoder[label] for label in y]
            
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            logger.info(f"Dados preprocessados: {X_scaled.shape[0]} amostras, {X_scaled.shape[1]} features")
            return X_scaled, y_encoded
            
        except Exception as e:
            logger.error(f"Erro no preprocessamento: {e}")
            return None, None
    
    def train_model(self, X, y):
        """Treinar modelo"""
        try:
            logger.info("Treinando modelo KNN...")
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            self.model = KNeighborsClassifier(n_neighbors=5, weights='distance')
            self.model.fit(X_train, y_train)
            
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Modelo treinado com acurácia: {accuracy:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Erro no treinamento: {e}")
            return False
    
    def save_model(self):
        """Salvar modelo"""
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
        """Carregar modelo"""
        try:
            if not os.path.exists(self.model_path):
                return False
            
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoder = model_data['label_encoder']
            self.reverse_label_encoder = model_data['reverse_label_encoder']
            
            logger.info(f"Modelo alternativo carregado de {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False
    
    def load_or_train_model(self):
        """Carregar ou treinar modelo"""
        if self.load_model():
            logger.info("Modelo alternativo carregado com sucesso")
            return
        
        logger.info("Treinando novo modelo alternativo...")
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
            logger.info("Modelo alternativo treinado e salvo")
        else:
            logger.error("Falha no treinamento")
    
    def extract_hand_features_simple(self, image_data):
        """
        Extração simples de features usando OpenCV
        Simula landmarks com features básicas da imagem
        """
        try:
            # Decodificar imagem
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Falha ao decodificar imagem")
                return None
            
            # Converter para HSV para melhor detecção de pele
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detectar pele (faixa HSV aproximada)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Aplicar operações morfológicas para limpar máscara
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                logger.info("Nenhum contorno de pele detectado")
                return None
            
            # Pegar maior contorno (provavelmente a mão)
            largest_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(largest_contour) < 1000:  # Muito pequeno
                logger.info("Área da mão muito pequena")
                return None
            
            # Extrair features do contorno
            features = self.extract_contour_features(largest_contour, image.shape)
            
            logger.info(f"Features extraídas: {len(features)} valores")
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Erro na extração de features: {e}")
            return None
    
    def extract_contour_features(self, contour, image_shape):
        """
        Extrair 63 features do contorno para simular landmarks MediaPipe
        """
        features = []
        
        try:
            h, w = image_shape[:2]
            
            # 1. Centro de massa
            M = cv2.moments(contour)
            if M['m00'] != 0:
                cx = M['m10'] / M['m00'] / w  # Normalizado
                cy = M['m01'] / M['m00'] / h
            else:
                cx = cy = 0.5
            
            # 2. Bounding box
            x, y, w_box, h_box = cv2.boundingRect(contour)
            x_norm = x / w
            y_norm = y / h
            w_norm = w_box / w
            h_norm = h_box / h
            
            # 3. Área e perímetro
            area = cv2.contourArea(contour) / (w * h)  # Normalizado
            perimeter = cv2.arcLength(contour, True) / (w + h)  # Normalizado
            
            # 4. Aspectos geométricos
            if len(contour) >= 5:
                ellipse = cv2.fitEllipse(contour)
                angle = ellipse[2] / 180.0  # Normalizado
                major_axis = max(ellipse[1]) / max(w, h)
                minor_axis = min(ellipse[1]) / max(w, h)
            else:
                angle = major_axis = minor_axis = 0
            
            # 5. Hull e defeitos de convexidade
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull) / (w * h)
            solidity = area / hull_area if hull_area > 0 else 0
            
            # 6. Pontos extremos (simular landmarks)
            leftmost = tuple(contour[contour[:,:,0].argmin()][0])
            rightmost = tuple(contour[contour[:,:,0].argmax()][0])
            topmost = tuple(contour[contour[:,:,1].argmin()][0])
            bottommost = tuple(contour[contour[:,:,1].argmax()][0])
            
            # Normalizar pontos extremos
            extreme_points = [
                leftmost[0]/w, leftmost[1]/h,
                rightmost[0]/w, rightmost[1]/h,
                topmost[0]/w, topmost[1]/h,
                bottommost[0]/w, bottommost[1]/h
            ]
            
            # 7. Distribuir pontos ao longo do contorno para simular 21 landmarks
            contour_points = []
            if len(contour) > 0:
                # Interpolar 17 pontos adicionais (21 total - 4 extremos já temos)
                indices = np.linspace(0, len(contour)-1, 17, dtype=int)
                for idx in indices:
                    pt = contour[idx][0]
                    contour_points.extend([pt[0]/w, pt[1]/h, 0.0])  # z=0 (sem profundidade)
            else:
                contour_points = [0.0] * 51  # 17 pontos * 3 coordenadas
            
            # Montar features finais (63 valores para simular 21 landmarks x,y,z)
            features = [
                # Centro de massa (3D)
                cx, cy, 0.0,
                # Bounding box cantos (12 valores = 4 cantos * 3 coordenadas)
                x_norm, y_norm, 0.0,
                (x_norm + w_norm), y_norm, 0.0,
                x_norm, (y_norm + h_norm), 0.0,
                (x_norm + w_norm), (y_norm + h_norm), 0.0,
                # Pontos extremos (12 valores = 4 pontos * 3 coordenadas)
                extreme_points[0], extreme_points[1], 0.0,
                extreme_points[2], extreme_points[3], 0.0,
                extreme_points[4], extreme_points[5], 0.0,
                extreme_points[6], extreme_points[7], 0.0,
                # Features geométricas como coordenadas (9 valores = 3 pontos * 3 coordenadas)
                area, perimeter, solidity,
                angle, major_axis, minor_axis,
                hull_area, w_norm, h_norm
            ]
            
            # Completar com pontos do contorno até 63 valores
            features.extend(contour_points)
            
            # Garantir exatamente 63 features
            if len(features) > 63:
                features = features[:63]
            elif len(features) < 63:
                features.extend([0.0] * (63 - len(features)))
            
            return features
            
        except Exception as e:
            logger.error(f"Erro na extração de features do contorno: {e}")
            return [0.0] * 63
    
    def predict_letter(self, image_data):
        """
        Prever letra usando features simples
        """
        try:
            if self.model is None or self.scaler is None:
                logger.error("Modelo não carregado")
                return None, 0
            
            logger.info("Extraindo features da imagem...")
            
            # Extrair features simples
            features = self.extract_hand_features_simple(image_data)
            
            if features is None:
                logger.info("Nenhuma mão detectada")
                return None, 0
            
            if len(features) != 63:
                logger.error(f"Número incorreto de features: {len(features)} != 63")
                return None, 0
            
            logger.info("Features extraídas com sucesso")
            
            # Preprocessar
            features_scaled = self.scaler.transform([features])
            
            # Prever
            prediction = self.model.predict(features_scaled)[0]
            
            # Calcular confiança
            try:
                probabilities = self.model.predict_proba(features_scaled)[0]
                confidence = float(np.max(probabilities))
            except:
                distances, _ = self.model.kneighbors(features_scaled)
                avg_distance = np.mean(distances[0])
                confidence = max(0.1, 1.0 - min(avg_distance, 1.0))
            
            # Decodificar label
            letter = self.reverse_label_encoder.get(prediction, None)
            
            logger.info(f"Predição: {letter} (confiança: {confidence:.3f})")
            
            return letter, float(confidence)
            
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None, 0

# Instância global do reconhecedor alternativo
recognizer_alt = None

def initialize_recognizer_alternative(csv_path="dados_libras.csv"):
    """Inicializar reconhecedor alternativo"""
    global recognizer_alt
    try:
        recognizer_alt = LibrasRecognizerAlternative(csv_path=csv_path)
        logger.info("Reconhecedor LIBRAS alternativo inicializado")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar reconhecedor alternativo: {e}")
        return False

def recognize_letter_alternative(image_data):
    """Função principal para reconhecimento alternativo"""
    global recognizer_alt
    
    if recognizer_alt is None:
        logger.error("Reconhecedor alternativo não inicializado")
        return None, 0
    
    return recognizer_alt.predict_letter(image_data)