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

        # Tabela específica para estatísticas do Soletrando
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS soletrando_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                letter CHARACTER(1) NOT NULL,
                word TEXT NOT NULL,
                word_position INTEGER NOT NULL,
                completion_time REAL NOT NULL,
                similarity_score REAL,
                attempt_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabela para resultados do modo Desafio
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenge_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                level TEXT NOT NULL,
                words_completed INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                time_taken INTEGER NOT NULL,
                total_time INTEGER NOT NULL,
                accuracy REAL DEFAULT 0,
                words_per_minute REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
    
    def save_soletrando_letter(self, user_id, letter, word, word_position, completion_time, similarity_score=None):
        """Salva estatísticas de uma letra completada no Soletrando"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO soletrando_stats 
                (user_id, letter, word, word_position, completion_time, similarity_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, letter, word, word_position, completion_time, similarity_score))
            
            conn.commit()
            print(f"Letra Soletrando salva: {letter} em '{word}' - Tempo: {completion_time:.2f}s")
            return cursor.lastrowid
        
        except Exception as e:
            print(f"Erro ao salvar letra Soletrando: {e}")
            return None
        finally:
            conn.close()
    
    def get_soletrando_stats(self, user_id):
        """Recupera estatísticas completas do Soletrando para um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estatísticas gerais
        cursor.execute('''
            SELECT 
                COUNT(*) as total_letters,
                COUNT(DISTINCT word) as total_words,
                AVG(completion_time) as avg_time,
                MIN(completion_time) as best_time,
                MAX(completion_time) as worst_time,
                AVG(similarity_score) as avg_similarity
            FROM soletrando_stats 
            WHERE user_id = ?
        ''', (user_id,))
        
        general_stats = cursor.fetchone()
        
        # Estatísticas por letra
        cursor.execute('''
            SELECT 
                letter,
                COUNT(*) as attempts,
                AVG(completion_time) as avg_time,
                MIN(completion_time) as best_time,
                AVG(similarity_score) as avg_similarity
            FROM soletrando_stats 
            WHERE user_id = ?
            GROUP BY letter
            ORDER BY letter
        ''', (user_id,))
        
        letter_stats = cursor.fetchall()
        
        # Últimas palavras completadas
        cursor.execute('''
            SELECT 
                word,
                COUNT(*) as letters_count,
                SUM(completion_time) as total_time,
                AVG(similarity_score) as avg_similarity,
                MIN(created_at) as started_at,
                MAX(created_at) as completed_at
            FROM soletrando_stats 
            WHERE user_id = ?
            GROUP BY word
            ORDER BY MAX(created_at) DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_words = cursor.fetchall()
        
        # Progresso diário (últimos 7 dias)
        cursor.execute('''
            SELECT 
                DATE(created_at) as day,
                COUNT(*) as letters_completed,
                COUNT(DISTINCT word) as words_worked,
                AVG(completion_time) as avg_time
            FROM soletrando_stats 
            WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        ''', (user_id,))
        
        daily_progress = cursor.fetchall()
        
        conn.close()
        
        return {
            'general': {
                'total_letters': general_stats[0] if general_stats[0] else 0,
                'total_words': general_stats[1] if general_stats[1] else 0,
                'avg_time': round(general_stats[2], 2) if general_stats[2] else 0,
                'best_time': round(general_stats[3], 2) if general_stats[3] else 0,
                'worst_time': round(general_stats[4], 2) if general_stats[4] else 0,
                'avg_similarity': round(general_stats[5], 2) if general_stats[5] else 0
            },
            'letter_stats': letter_stats,
            'recent_words': recent_words,
            'daily_progress': daily_progress
        }
    
    def get_user_statistics(self, username):
        """Recupera estatísticas gerais de um usuário (compatibilidade)"""
        user_result = self.get_user(username)
        if not user_result:
            return {"error": "Usuário não encontrado"}
        
        user_id = user_result[0]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Estatísticas básicas de compatibilidade
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT gs.id) as total_sessions,
                    COALESCE(SUM(gs.words_completed), 0) as total_words,
                    COALESCE(AVG(gs.accuracy), 0) as avg_accuracy,
                    COALESCE(SUM(gs.total_duration), 0) as total_time
                FROM game_sessions gs
                WHERE gs.user_id = ?
            ''', (user_id,))
            
            stats = cursor.fetchone()
            
            # Formatar tempo
            total_seconds = stats[3] if stats[3] else 0
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_formatted = f"{int(hours):02d}:{int(minutes):02d}"
            
            # Sessões recentes (exemplo simplificado)
            cursor.execute('''
                SELECT 
                    strftime('%d/%m', gs.start_time) as date,
                    gs.difficulty,
                    gs.words_completed,
                    gs.accuracy,
                    printf('%.1f min', CAST(gs.total_duration AS FLOAT) / 60) as duration
                FROM game_sessions gs
                WHERE gs.user_id = ?
                ORDER BY gs.start_time DESC
                LIMIT 5
            ''', (user_id,))
            
            recent_sessions = []
            for row in cursor.fetchall():
                recent_sessions.append({
                    'date': row[0],
                    'difficulty': row[1] or 'geral',
                    'words_completed': row[2] or 0,
                    'accuracy': row[3] or 0,
                    'duration': row[4]
                })
            
            return {
                'total_sessions': stats[0] if stats[0] else 0,
                'total_words': stats[1] if stats[1] else 0,
                'avg_accuracy': stats[2] if stats[2] else 0,
                'total_time_formatted': time_formatted,
                'recent_sessions': recent_sessions,
                'letter_performance': []  # Por simplicidade
            }
            
        except Exception as e:
            print(f"Erro ao buscar estatísticas do usuário: {e}")
            return {"error": f"Erro interno: {e}"}
        finally:
            conn.close()

    # ===== MÉTODOS PARA MODO DESAFIO =====
    def save_challenge_result(self, user_id, level, words_completed, score, time_taken):
        """Salva resultado de uma partida do modo Desafio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calcular métricas
            total_time_map = {
                'iniciante': 180,
                'intermediario': 120,
                'avancado': 90,
                'expert': 60
            }
            
            total_time = total_time_map.get(level, 120)
            accuracy = (words_completed / max(words_completed + 1, 1)) * 100  # Simples cálculo
            words_per_minute = (words_completed / max(time_taken / 60, 1)) if time_taken > 0 else 0
            
            cursor.execute('''
                INSERT INTO challenge_results 
                (user_id, level, words_completed, score, time_taken, total_time, accuracy, words_per_minute)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, level, words_completed, score, time_taken, total_time, accuracy, words_per_minute))
            
            result_id = cursor.lastrowid
            conn.commit()
            
            print(f"Resultado do Desafio salvo - ID: {result_id}, Usuário: {user_id}, Nível: {level}")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar resultado do Desafio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_challenge_stats(self, user_id):
        """Recupera estatísticas completas do Desafio para um usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Estatísticas gerais
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_games,
                    SUM(words_completed) as total_words,
                    SUM(score) as total_score,
                    AVG(score) as avg_score,
                    MAX(score) as best_score,
                    AVG(words_completed) as avg_words,
                    MAX(words_completed) as best_words,
                    AVG(words_per_minute) as avg_wpm,
                    MAX(words_per_minute) as best_wpm
                FROM challenge_results 
                WHERE user_id = ?
            ''', (user_id,))
            
            general_stats = cursor.fetchone()
            
            # Estatísticas por nível
            cursor.execute('''
                SELECT 
                    level,
                    COUNT(*) as games_played,
                    AVG(words_completed) as avg_words,
                    MAX(words_completed) as best_words,
                    AVG(score) as avg_score,
                    MAX(score) as best_score,
                    AVG(words_per_minute) as avg_wpm,
                    MAX(words_per_minute) as best_wpm
                FROM challenge_results 
                WHERE user_id = ?
                GROUP BY level
                ORDER BY 
                    CASE level 
                        WHEN 'iniciante' THEN 1
                        WHEN 'intermediario' THEN 2
                        WHEN 'avancado' THEN 3
                        WHEN 'expert' THEN 4
                    END
            ''', (user_id,))
            
            level_stats = cursor.fetchall()
            
            # Últimos jogos
            cursor.execute('''
                SELECT 
                    level,
                    words_completed,
                    score,
                    time_taken,
                    words_per_minute,
                    created_at
                FROM challenge_results 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 10
            ''', (user_id,))
            
            recent_games = cursor.fetchall()
            
            # Progresso diário (últimos 30 dias)
            cursor.execute('''
                SELECT 
                    DATE(created_at) as day,
                    COUNT(*) as games_played,
                    SUM(words_completed) as total_words,
                    MAX(score) as best_score,
                    AVG(words_per_minute) as avg_wpm
                FROM challenge_results 
                WHERE user_id = ? AND created_at >= datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY day DESC
            ''', (user_id,))
            
            daily_progress = cursor.fetchall()
            
            return {
                'general': {
                    'total_games': general_stats[0] if general_stats[0] else 0,
                    'total_words': general_stats[1] if general_stats[1] else 0,
                    'total_score': general_stats[2] if general_stats[2] else 0,
                    'avg_score': round(general_stats[3], 1) if general_stats[3] else 0,
                    'best_score': general_stats[4] if general_stats[4] else 0,
                    'avg_words': round(general_stats[5], 1) if general_stats[5] else 0,
                    'best_words': general_stats[6] if general_stats[6] else 0,
                    'avg_wpm': round(general_stats[7], 1) if general_stats[7] else 0,
                    'best_wpm': round(general_stats[8], 1) if general_stats[8] else 0
                },
                'level_stats': level_stats,
                'recent_games': recent_games,
                'daily_progress': daily_progress
            }
            
        except Exception as e:
            print(f"Erro ao buscar estatísticas do Desafio: {e}")
            return {}
        finally:
            conn.close()
    
    def get_challenge_ranking(self, level, limit=10):
        """Obtém ranking do Desafio por nível"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    u.username,
                    cr.words_completed,
                    cr.score,
                    cr.words_per_minute,
                    cr.time_taken,
                    cr.created_at
                FROM challenge_results cr
                JOIN users u ON cr.user_id = u.id
                WHERE cr.level = ?
                ORDER BY cr.score DESC, cr.words_completed DESC, cr.time_taken ASC
                LIMIT ?
            ''', (level, limit))
            
            ranking_data = cursor.fetchall()
            
            ranking = []
            for i, row in enumerate(ranking_data, 1):
                ranking.append({
                    'position': i,
                    'username': row[0],
                    'words_completed': row[1],
                    'score': row[2],
                    'words_per_minute': round(row[3], 1),
                    'time_taken': row[4],
                    'date': row[5][:10]  # Apenas data, sem hora
                })
            
            return ranking
            
        except Exception as e:
            print(f"Erro ao buscar ranking do Desafio: {e}")
            return []
        finally:
            conn.close()

def save_game_session(username, mode, difficulty, word, completed, time_spent, total_time, letters_completed, total_letters, accuracy):
    """Função helper para salvar resultado de uma sessão de jogo"""
    try:
        db = LibrasDatabase()
        
        # Obter ou criar usuário
        user_id = db.get_or_create_user(username)
        
        # Calcular duração
        duration = total_time - time_spent if time_spent < total_time else time_spent
        
        # Iniciar sessão
        session_id = db.start_session(user_id, mode, difficulty)
        
        # Adicionar palavra praticada
        db.add_practiced_word(session_id, word, duration, completed, letters_completed)
        
        # Finalizar sessão
        db.end_session(session_id, 1 if completed else 0, total_letters, letters_completed, accuracy)
        
        return True
        
    except Exception as e:
        print(f"Erro ao salvar sessão de jogo: {e}")
        return False