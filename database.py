import sqlite3
import json
from datetime import datetime
import os

class LibrasDatabase:
    def __init__(self, db_path="libras_stats.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Cria as tabelas se não existirem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sessões de jogo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_mode TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                total_duration INTEGER,
                words_completed INTEGER DEFAULT 0,
                total_letters INTEGER DEFAULT 0,
                correct_letters INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de palavras praticadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practiced_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                word TEXT NOT NULL,
                completion_time INTEGER,
                letter_count INTEGER,
                correct_letters INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES game_sessions (id)
            )
        ''')
        
        # Tabela de tempos por letra
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS letter_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                word_id INTEGER,
                letter CHARACTER(1) NOT NULL,
                time_seconds REAL NOT NULL,
                position_in_word INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES game_sessions (id),
                FOREIGN KEY (word_id) REFERENCES practiced_words (id)
            )
        ''')
        
        # Tabela de estatísticas por letra
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS letter_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                letter CHARACTER(1) NOT NULL,
                total_attempts INTEGER DEFAULT 0,
                correct_attempts INTEGER DEFAULT 0,
                avg_time REAL DEFAULT 0,
                best_time REAL DEFAULT 0,
                worst_time REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, letter)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Banco de dados inicializado: {self.db_path}")
    
    def create_user(self, username):
        """Cria um novo usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            user_id = cursor.lastrowid
            conn.commit()
            print(f"Usuário criado: {username} (ID: {user_id})")
            return user_id
        except sqlite3.IntegrityError:
            print(f"Usuário já existe: {username}")
            return None
        finally:
            conn.close()
    
    def get_user(self, username):
        """Busca um usuário pelo nome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"Usuário encontrado: {result[1]} (ID: {result[0]})")
        
        return result
    
    def start_session(self, user_id, game_mode, difficulty):
        """Inicia uma nova sessão de jogo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_time = datetime.now()
        cursor.execute('''
            INSERT INTO game_sessions 
            (user_id, game_mode, difficulty, start_time) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, game_mode, difficulty, start_time))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Sessão iniciada: ID {session_id}, Modo: {game_mode}, Dificuldade: {difficulty}")
        return session_id
    
    def end_session(self, session_id, stats):
        """Finaliza uma sessão com estatísticas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_time = datetime.now()
        
        cursor.execute('''
            UPDATE game_sessions 
            SET end_time = ?, total_duration = ?, words_completed = ?,
                total_letters = ?, correct_letters = ?, accuracy = ?
            WHERE id = ?
        ''', (
            end_time,
            stats.get('total_duration', 0),
            stats.get('words_completed', 0),
            stats.get('total_letters', 0),
            stats.get('correct_letters', 0),
            stats.get('accuracy', 0),
            session_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Sessão finalizada: ID {session_id}")
        print(f"Estatísticas: {stats}")
    
    def save_word_practice(self, session_id, word, completion_time, letter_count, correct_letters):
        """Salva dados de uma palavra praticada"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO practiced_words 
            (session_id, word, completion_time, letter_count, correct_letters)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, word, completion_time, letter_count, correct_letters))
        
        word_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Palavra salva: {word} (ID: {word_id}) - {completion_time}s")
        return word_id
    
    def save_letter_times(self, session_id, word_id, letter_times_data):
        """Salva tempos individuais das letras"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i, (letter, time_seconds) in enumerate(letter_times_data):
            cursor.execute('''
                INSERT INTO letter_times 
                (session_id, word_id, letter, time_seconds, position_in_word)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, word_id, letter, time_seconds, i))
        
        conn.commit()
        conn.close()
        
        print(f"Tempos das letras salvos: {len(letter_times_data)} letras")
    
    def update_letter_stats(self, user_id, letter, time_seconds, was_correct):
        """Atualiza estatísticas por letra"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar estatísticas atuais
        cursor.execute('''
            SELECT total_attempts, correct_attempts, avg_time, best_time, worst_time 
            FROM letter_stats WHERE user_id = ? AND letter = ?
        ''', (user_id, letter))
        
        result = cursor.fetchone()
        
        if result:
            total_attempts, correct_attempts, avg_time, best_time, worst_time = result
            new_total = total_attempts + 1
            new_correct = correct_attempts + (1 if was_correct else 0)
            new_avg = ((avg_time * total_attempts) + time_seconds) / new_total
            new_best = min(best_time, time_seconds) if best_time > 0 else time_seconds
            new_worst = max(worst_time, time_seconds)
            
            cursor.execute('''
                UPDATE letter_stats 
                SET total_attempts = ?, correct_attempts = ?, avg_time = ?, 
                    best_time = ?, worst_time = ?, updated_at = ?
                WHERE user_id = ? AND letter = ?
            ''', (new_total, new_correct, new_avg, new_best, new_worst, datetime.now(), user_id, letter))
        else:
            cursor.execute('''
                INSERT INTO letter_stats 
                (user_id, letter, total_attempts, correct_attempts, avg_time, best_time, worst_time)
                VALUES (?, ?, 1, ?, ?, ?, ?)
            ''', (user_id, letter, 1 if was_correct else 0, time_seconds, time_seconds, time_seconds))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id, days=30):
        """Busca estatísticas do usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estatísticas gerais
        cursor.execute('''
            SELECT COUNT(*) as sessions, SUM(words_completed) as total_words,
                   AVG(accuracy) as avg_accuracy, SUM(total_duration) as total_time
            FROM game_sessions 
            WHERE user_id = ? AND start_time >= datetime('now', '-{} days')
        '''.format(days), (user_id,))
        
        general_stats = cursor.fetchone()
        
        # Melhores tempos por letra
        cursor.execute('''
            SELECT letter, best_time, avg_time, total_attempts, correct_attempts,
                   ROUND((correct_attempts * 100.0 / total_attempts), 2) as accuracy
            FROM letter_stats 
            WHERE user_id = ?
            ORDER BY letter
        ''', (user_id,))
        
        letter_stats = cursor.fetchall()
        
        # Últimas 10 sessões
        cursor.execute('''
            SELECT game_mode, difficulty, start_time, words_completed, accuracy
            FROM game_sessions 
            WHERE user_id = ?
            ORDER BY start_time DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_sessions = cursor.fetchall()
        
        conn.close()
        
        return {
            'general': general_stats,
            'letters': letter_stats,
            'recent_sessions': recent_sessions
        }
    
    def get_letter_progress(self, user_id, letter):
        """Busca progresso específico de uma letra"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT lt.time_seconds, lt.created_at
            FROM letter_times lt
            JOIN game_sessions gs ON lt.session_id = gs.id
            WHERE gs.user_id = ? AND lt.letter = ?
            ORDER BY lt.created_at DESC
            LIMIT 20
        ''', (user_id, letter))
        
        progress = cursor.fetchall()
        conn.close()
        
        return progress
    
    def cleanup_old_data(self, days=90):
        """Remove dados antigos para economizar espaço"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remover sessões antigas
        cursor.execute('''
            DELETE FROM game_sessions 
            WHERE start_time < datetime('now', '-{} days')
        '''.format(days))
        
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"Limpeza concluída: {rows_deleted} sessões antigas removidas")
        return rows_deleted