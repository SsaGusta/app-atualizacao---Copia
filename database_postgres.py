import psycopg2
import psycopg2.extras
import json
from datetime import datetime
import os
from urllib.parse import urlparse

class LibrasPostgresDatabase:
    def __init__(self):
        # URL do PostgreSQL do Railway (será fornecida como variável de ambiente)
        self.database_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/libras_dev')
        self.init_database()
    
    def get_connection(self):
        """Cria conexão com PostgreSQL"""
        try:
            # Parse da URL do banco
            url = urlparse(self.database_url)
            
            conn = psycopg2.connect(
                database=url.path[1:],  # Remove a barra inicial
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return conn
        except Exception as e:
            print(f"Erro ao conectar com PostgreSQL: {e}")
            return None
    
    def init_database(self):
        """Cria as tabelas se não existirem"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de sessões de jogo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    game_mode VARCHAR(50) NOT NULL,
                    difficulty VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    total_duration INTEGER,
                    words_completed INTEGER DEFAULT 0,
                    total_letters INTEGER DEFAULT 0,
                    correct_letters INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de palavras praticadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS practiced_words (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES game_sessions(id),
                    word VARCHAR(255) NOT NULL,
                    completion_time INTEGER,
                    letters_attempted INTEGER DEFAULT 0,
                    letters_correct INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    attempts INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de gestos (equivalente ao gestures.db)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gestures (
                    id SERIAL PRIMARY KEY,
                    letter VARCHAR(1) UNIQUE NOT NULL,
                    landmarks_json TEXT NOT NULL,
                    quality INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de analytics de gestos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gesture_analytics (
                    id SERIAL PRIMARY KEY,
                    letter VARCHAR(1) NOT NULL,
                    recognition_count INTEGER DEFAULT 0,
                    last_recognized TIMESTAMP
                )
            ''')
            
            # Tabela de dados ML
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_training_data (
                    id SERIAL PRIMARY KEY,
                    letter VARCHAR(1) NOT NULL,
                    landmarks_json TEXT NOT NULL,
                    user_id INTEGER REFERENCES users(id),
                    quality_score REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de resultados do desafio
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS challenge_results (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    difficulty VARCHAR(50) NOT NULL,
                    score INTEGER DEFAULT 0,
                    time_used INTEGER DEFAULT 0,
                    time_limit INTEGER DEFAULT 0,
                    words_completed INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("Tabelas PostgreSQL criadas com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_user(self, username: str):
        """Adiciona um novo usuário"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username) VALUES (%s) ON CONFLICT (username) DO NOTHING RETURNING id",
                (username,)
            )
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                return result['id']
            else:
                # Usuário já existe, buscar ID
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                return result['id'] if result else None
                
        except Exception as e:
            print(f"Erro ao adicionar usuário: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def save_gesture(self, letter: str, landmarks: list, quality: int):
        """Salva um gesto no PostgreSQL"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            landmarks_json = json.dumps(landmarks)
            
            cursor.execute('''
                INSERT INTO gestures (letter, landmarks_json, quality, updated_at) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (letter) 
                DO UPDATE SET 
                    landmarks_json = EXCLUDED.landmarks_json,
                    quality = EXCLUDED.quality,
                    updated_at = EXCLUDED.updated_at
            ''', (letter, landmarks_json, quality, datetime.now()))
            
            # Inicializar analytics se não existir
            cursor.execute('''
                INSERT INTO gesture_analytics (letter, recognition_count) 
                VALUES (%s, 0)
                ON CONFLICT (letter) DO NOTHING
            ''', (letter,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao salvar gesto: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_all_gestures(self):
        """Recupera todos os gestos salvos"""
        conn = self.get_connection()
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT letter, landmarks_json, quality FROM gestures")
            results = cursor.fetchall()
            
            gestures = {}
            for row in results:
                gestures[row['letter']] = {
                    'landmarks': json.loads(row['landmarks_json']),
                    'quality': row['quality']
                }
            
            return gestures
            
        except Exception as e:
            print(f"Erro ao buscar gestos: {e}")
            return {}
        finally:
            conn.close()
    
    def save_challenge_result(self, user_id: int, difficulty: str, score: int, 
                            time_used: int, time_limit: int, words_completed: int, 
                            total_words: int, accuracy: float):
        """Salva resultado do desafio"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO challenge_results 
                (user_id, difficulty, score, time_used, time_limit, words_completed, total_words, accuracy)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, difficulty, score, time_used, time_limit, words_completed, total_words, accuracy))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao salvar resultado do desafio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()