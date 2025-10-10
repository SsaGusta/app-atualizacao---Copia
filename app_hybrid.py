# ===== APLICAÇÃO WEB FLASK PARA LIBRAS (Versão Deploy) =====
import os
import json
import time
import base64
import io
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, abort
from flask_session import Session
import threading
import logging

# Tentar importar bibliotecas de processamento de imagem
try:
    from PIL import Image
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    print("PIL/numpy não disponível - reconhecimento simulado")

# Tentar importar CORS, mas continuar se falhar
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Flask-CORS não disponível, continuando sem CORS")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detectar ambiente e escolher banco de dados apropriado
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DATABASE_URL')

# Importar módulos locais
try:
    if IS_PRODUCTION and os.environ.get('DATABASE_URL'):
        from database_postgres import LibrasPostgresDatabase as LibrasDatabase
        print("🚀 Usando PostgreSQL (Produção)")
    else:
        from database import LibrasDatabase
        print("🏠 Usando SQLite (Desenvolvimento)")
    DATABASE_AVAILABLE = True
    logger.info("Módulo database importado com sucesso")
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"Aviso: Sistema de banco não disponível: {e}")

try:
    from palavras import palavras, palavras_iniciante, palavras_avancado, palavras_expert
    WORDS_AVAILABLE = True
    logger.info("Módulo palavras importado com sucesso")
except ImportError as e:
    WORDS_AVAILABLE = False
    print(f"Aviso: Sistema de palavras não disponível: {e}")

try:
    from gesture_manager import GestureManager
    
    # Usar PostgreSQL para gestos em produção também
    if IS_PRODUCTION and os.environ.get('DATABASE_URL'):
        # Criar um adapter para o gesture_manager usar PostgreSQL
        gesture_manager = GestureManager(use_postgres=True)
    else:
        gesture_manager = GestureManager()
    
    GESTURE_MANAGER_AVAILABLE = True
    logger.info("Módulo gesture_manager importado com sucesso")
except ImportError as e:
    GESTURE_MANAGER_AVAILABLE = False
    gesture_manager = None
    print(f"Aviso: Sistema de gestos não disponível: {e}")

# Tentar importar sistema de ML
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    import joblib
    import sqlite3
    
    # ML Database class que funciona com PostgreSQL também
    class MLSystem:
        def __init__(self):
            self.use_postgres = IS_PRODUCTION and os.environ.get('DATABASE_URL')
            if self.use_postgres:
                self.db_connection = self._get_postgres_connection
            else:
                self.db_path = "libras_ml.db"
                self._init_sqlite_db()
            
            self.model = None
            self.model_path = "gesture_model.pkl"
            self.load_model()
        
        def _get_postgres_connection(self):
            """Conecta ao PostgreSQL para ML"""
            import psycopg2
            import psycopg2.extras
            from urllib.parse import urlparse
            
            url = urlparse(os.environ.get('DATABASE_URL'))
            return psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        
        def _init_sqlite_db(self):
            """Inicializa banco SQLite para desenvolvimento"""
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ml_training_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        letter TEXT NOT NULL,
                        landmarks_json TEXT NOT NULL,
                        user_id INTEGER,
                        quality_score REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        
        def add_training_example(self, letter: str, landmarks: list, user_id: int = None, quality_score: float = 0.0):
            """Adiciona exemplo de treinamento"""
            try:
                landmarks_json = json.dumps(landmarks)
                
                if self.use_postgres:
                    conn = self._get_postgres_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO ml_training_data (letter, landmarks_json, user_id, quality_score)
                        VALUES (%s, %s, %s, %s)
                    """, (letter, landmarks_json, user_id, quality_score))
                    conn.commit()
                    conn.close()
                else:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            INSERT INTO ml_training_data (letter, landmarks_json, user_id, quality_score)
                            VALUES (?, ?, ?, ?)
                        """, (letter, landmarks_json, user_id, quality_score))
                        conn.commit()
                
                print(f"Exemplo de treinamento adicionado: {letter}")
                return True
                
            except Exception as e:
                print(f"Erro ao adicionar exemplo de treinamento: {e}")
                return False
        
        def get_training_data(self):
            """Recupera dados de treinamento"""
            try:
                if self.use_postgres:
                    conn = self._get_postgres_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT letter, landmarks_json FROM ml_training_data")
                    results = cursor.fetchall()
                    conn.close()
                    
                    data = []
                    for row in results:
                        data.append({
                            'letter': row['letter'],
                            'landmarks': json.loads(row['landmarks_json'])
                        })
                else:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT letter, landmarks_json FROM ml_training_data")
                        results = cursor.fetchall()
                        
                        data = []
                        for row in results:
                            data.append({
                                'letter': row[0],
                                'landmarks': json.loads(row[1])
                            })
                
                return data
                
            except Exception as e:
                print(f"Erro ao recuperar dados de treinamento: {e}")
                return []
        
        def train_model(self):
            """Treina o modelo ML"""
            try:
                data = self.get_training_data()
                if len(data) < 10:
                    print("Dados insuficientes para treinamento (mínimo 10 exemplos)")
                    return False
                
                # Preparar dados
                X = []
                y = []
                for example in data:
                    # Flatten landmarks
                    landmarks_flat = []
                    for point in example['landmarks']:
                        landmarks_flat.extend([point['x'], point['y'], point['z']])
                    X.append(landmarks_flat)
                    y.append(example['letter'])
                
                # Treinar modelo
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
                self.model.fit(X, y)
                
                # Salvar modelo
                joblib.dump(self.model, self.model_path)
                print(f"Modelo treinado com {len(data)} exemplos")
                return True
                
            except Exception as e:
                print(f"Erro ao treinar modelo: {e}")
                return False
        
        def load_model(self):
            """Carrega modelo salvo"""
            try:
                if os.path.exists(self.model_path):
                    self.model = joblib.load(self.model_path)
                    print("Modelo ML carregado com sucesso")
                    return True
                else:
                    print("Nenhum modelo encontrado")
                    return False
            except Exception as e:
                print(f"Erro ao carregar modelo: {e}")
                return False
        
        def predict_letter(self, landmarks: list):
            """Prediz letra usando o modelo"""
            try:
                if not self.model:
                    return None, 0.0
                
                # Flatten landmarks
                landmarks_flat = []
                for point in landmarks:
                    landmarks_flat.extend([point['x'], point['y'], point['z']])
                
                # Fazer predição
                prediction = self.model.predict([landmarks_flat])[0]
                probabilities = self.model.predict_proba([landmarks_flat])[0]
                confidence = max(probabilities)
                
                return prediction, confidence
                
            except Exception as e:
                print(f"Erro na predição: {e}")
                return None, 0.0
    
    ml_system = MLSystem()
    ML_SYSTEM_AVAILABLE = True
    logger.info("Sistema de ML importado com sucesso")
    
    if ml_system.use_postgres:
        print("🚀 Sistema ML usando PostgreSQL")
    else:
        print("🏠 Sistema ML usando SQLite")
        print(f"Banco de dados ML inicializado: {ml_system.db_path}")
    
except ImportError as e:
    ML_SYSTEM_AVAILABLE = False
    ml_system = None
    print(f"Aviso: Sistema de ML não disponível: {e}")

# Restante do código permanece igual...