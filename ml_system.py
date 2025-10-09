import sqlite3
import numpy as np
import json
import pickle
import os
from datetime import datetime
import logging

# Tentar importar sklearn, mas continuar sem ML se não disponível
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Aviso: scikit-learn não disponível - ML desabilitado")

logger = logging.getLogger(__name__)

class LibrasMLSystem:
    """Sistema de Machine Learning para melhorar reconhecimento de gestos LIBRAS"""
    
    def __init__(self, db_path="libras_ml.db", models_path="ml_models"):
        self.db_path = db_path
        self.models_path = models_path
        self.models = {}
        self.scalers = {}
        self.sklearn_available = SKLEARN_AVAILABLE
        
        if not self.sklearn_available:
            print("⚠️ ML System inicializado sem scikit-learn - apenas coleta de dados")
            return
        
        # Criar diretório para modelos
        os.makedirs(models_path, exist_ok=True)
        
        self.init_ml_database()
        self.load_existing_models()
    
    def init_ml_database(self):
        """Inicializa banco de dados para Machine Learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela para armazenar exemplos de gestos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gesture_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                letter TEXT NOT NULL,
                landmarks TEXT NOT NULL,
                user_id INTEGER,
                confidence REAL,
                feedback TEXT,
                source TEXT DEFAULT 'game',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela para histórico de treinamento dos modelos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                letter TEXT NOT NULL,
                examples_count INTEGER,
                accuracy REAL,
                model_version INTEGER DEFAULT 1,
                training_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela para feedback dos usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                predicted_letter TEXT,
                actual_letter TEXT,
                confidence REAL,
                landmarks TEXT,
                feedback_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Banco de dados ML inicializado: {self.db_path}")
    
    def collect_gesture_example(self, letter, landmarks, user_id=None, confidence=None, source="game"):
        """Coleta exemplo de gesto durante o uso"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Converter landmarks para JSON
            landmarks_json = json.dumps(landmarks)
            
            cursor.execute('''
                INSERT INTO gesture_examples 
                (letter, landmarks, user_id, confidence, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (letter, landmarks_json, user_id, confidence, source))
            
            example_id = cursor.lastrowid
            conn.commit()
            
            print(f"Exemplo coletado: {letter} (ID: {example_id})")
            
            # Verificar se há exemplos suficientes para retreinar
            self._check_retrain_needed(letter)
            
            return example_id
            
        except Exception as e:
            print(f"Erro ao coletar exemplo: {e}")
            return None
        finally:
            conn.close()
    
    def add_user_feedback(self, user_id, predicted_letter, actual_letter, confidence, landmarks, feedback_type="correction"):
        """Adiciona feedback do usuário para melhorar o modelo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            landmarks_json = json.dumps(landmarks)
            
            cursor.execute('''
                INSERT INTO user_feedback 
                (user_id, predicted_letter, actual_letter, confidence, landmarks, feedback_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, predicted_letter, actual_letter, confidence, landmarks_json, feedback_type))
            
            feedback_id = cursor.lastrowid
            conn.commit()
            
            # Se o feedback é uma correção, adicionar como exemplo positivo
            if feedback_type == "correction" and actual_letter:
                self.collect_gesture_example(
                    actual_letter, landmarks, user_id, confidence, "user_correction"
                )
            
            print(f"Feedback registrado: {predicted_letter} -> {actual_letter}")
            return feedback_id
            
        except Exception as e:
            print(f"Erro ao registrar feedback: {e}")
            return None
        finally:
            conn.close()
    
    def _check_retrain_needed(self, letter, min_examples=10):
        """Verifica se há exemplos suficientes para retreinar o modelo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Contar exemplos para a letra
        cursor.execute('''
            SELECT COUNT(*) FROM gesture_examples 
            WHERE letter = ? AND created_at > datetime('now', '-7 days')
        ''', (letter,))
        
        recent_count = cursor.fetchone()[0]
        conn.close()
        
        if recent_count >= min_examples:
            print(f"Retreinamento necessário para letra {letter}: {recent_count} novos exemplos")
            self.train_letter_model(letter)
    
    def prepare_training_data(self, letter):
        """Prepara dados de treinamento para uma letra específica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar exemplos positivos (letra correta)
        cursor.execute('''
            SELECT landmarks FROM gesture_examples 
            WHERE letter = ?
        ''', (letter,))
        
        positive_examples = []
        for row in cursor.fetchall():
            landmarks = json.loads(row[0])
            # Converter para array flat de 63 features (21 pontos x 3 coordenadas)
            features = self._landmarks_to_features(landmarks)
            if features is not None:
                positive_examples.append(features)
        
        # Buscar exemplos negativos (outras letras)
        cursor.execute('''
            SELECT landmarks FROM gesture_examples 
            WHERE letter != ? 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (letter, len(positive_examples) * 2))  # 2x mais exemplos negativos
        
        negative_examples = []
        for row in cursor.fetchall():
            landmarks = json.loads(row[0])
            features = self._landmarks_to_features(landmarks)
            if features is not None:
                negative_examples.append(features)
        
        conn.close()
        
        if len(positive_examples) < 5:
            print(f"Exemplos insuficientes para {letter}: {len(positive_examples)}")
            return None, None
        
        # Preparar datasets
        X_positive = np.array(positive_examples)
        y_positive = np.ones(len(positive_examples))
        
        X_negative = np.array(negative_examples)
        y_negative = np.zeros(len(negative_examples))
        
        # Combinar dados
        X = np.vstack([X_positive, X_negative])
        y = np.hstack([y_positive, y_negative])
        
        print(f"Dados preparados para {letter}: {len(positive_examples)} positivos, {len(negative_examples)} negativos")
        return X, y
    
    def _landmarks_to_features(self, landmarks):
        """Converte landmarks para features de ML"""
        try:
            if len(landmarks) != 21:
                return None
            
            features = []
            for point in landmarks:
                features.extend([point['x'], point['y'], point['z']])
            
            return np.array(features)
        except Exception as e:
            print(f"Erro ao converter landmarks: {e}")
            return None
    
    def train_letter_model(self, letter):
        """Treina modelo específico para uma letra"""
        if not self.sklearn_available:
            print("❌ Sklearn não disponível - não é possível treinar modelos")
            return False
            
        print(f"Iniciando treinamento para letra {letter}...")
        
        start_time = datetime.now()
        
        # Preparar dados
        X, y = self.prepare_training_data(letter)
        if X is None:
            return False
        
        try:
            # Dividir dados
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Normalizar dados
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Treinar modelo
            model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            model.fit(X_train_scaled, y_train)
            
            # Avaliar modelo
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Salvar modelo e scaler
            model_path = os.path.join(self.models_path, f"model_{letter}.pkl")
            scaler_path = os.path.join(self.models_path, f"scaler_{letter}.pkl")
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            # Carregar modelo em memória
            self.models[letter] = model
            self.scalers[letter] = scaler
            
            # Salvar histórico de treinamento
            training_time = (datetime.now() - start_time).total_seconds()
            self._save_training_history(letter, len(X), accuracy, training_time)
            
            print(f"✅ Modelo {letter} treinado com sucesso! Accuracy: {accuracy:.3f}")
            return True
            
        except Exception as e:
            print(f"❌ Erro no treinamento do modelo {letter}: {e}")
            return False
    
    def _save_training_history(self, letter, examples_count, accuracy, training_time):
        """Salva histórico de treinamento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO model_training_history 
            (letter, examples_count, accuracy, training_time)
            VALUES (?, ?, ?, ?)
        ''', (letter, examples_count, accuracy, training_time))
        
        conn.commit()
        conn.close()
    
    def load_existing_models(self):
        """Carrega modelos existentes"""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            model_path = os.path.join(self.models_path, f"model_{letter}.pkl")
            scaler_path = os.path.join(self.models_path, f"scaler_{letter}.pkl")
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    with open(model_path, 'rb') as f:
                        self.models[letter] = pickle.load(f)
                    
                    with open(scaler_path, 'rb') as f:
                        self.scalers[letter] = pickle.load(f)
                    
                    print(f"Modelo {letter} carregado")
                except Exception as e:
                    print(f"Erro ao carregar modelo {letter}: {e}")
    
    def predict_letter(self, landmarks, return_probabilities=False):
        """Prediz letra usando modelos ML"""
        if not self.sklearn_available:
            return None, 0.0
            
        features = self._landmarks_to_features(landmarks)
        if features is None:
            return None, 0.0
        
        predictions = {}
        
        for letter, model in self.models.items():
            try:
                # Normalizar features
                scaler = self.scalers[letter]
                features_scaled = scaler.transform([features])
                
                # Fazer predição
                prob = model.predict_proba(features_scaled)[0]
                positive_prob = prob[1] if len(prob) > 1 else prob[0]
                
                predictions[letter] = positive_prob
                
            except Exception as e:
                print(f"Erro na predição para {letter}: {e}")
                continue
        
        if not predictions:
            return None, 0.0
        
        # Encontrar melhor predição
        best_letter = max(predictions, key=predictions.get)
        best_confidence = predictions[best_letter]
        
        if return_probabilities:
            return best_letter, best_confidence, predictions
        
        return best_letter, best_confidence
    
    def get_model_stats(self):
        """Retorna estatísticas dos modelos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Contar exemplos por letra
        cursor.execute('''
            SELECT letter, COUNT(*) as count
            FROM gesture_examples
            GROUP BY letter
            ORDER BY letter
        ''')
        
        for row in cursor.fetchall():
            letter, count = row
            stats[letter] = {
                'examples': count,
                'has_model': letter in self.models,
                'last_training': None,
                'accuracy': None
            }
        
        # Buscar últimos treinamentos
        cursor.execute('''
            SELECT letter, accuracy, created_at
            FROM model_training_history
            WHERE id IN (
                SELECT MAX(id) FROM model_training_history GROUP BY letter
            )
        ''')
        
        for row in cursor.fetchall():
            letter, accuracy, created_at = row
            if letter in stats:
                stats[letter]['last_training'] = created_at
                stats[letter]['accuracy'] = accuracy
        
        conn.close()
        return stats
    
    def train_all_models(self, min_examples=10):
        """Treina modelos para todas as letras com exemplos suficientes"""
        stats = self.get_model_stats()
        trained = 0
        
        for letter, info in stats.items():
            if info['examples'] >= min_examples:
                if self.train_letter_model(letter):
                    trained += 1
        
        print(f"✅ Treinamento concluído: {trained} modelos atualizados")
        return trained