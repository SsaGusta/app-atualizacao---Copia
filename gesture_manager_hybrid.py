import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class GestureManager:
    def __init__(self, db_path: str = "gestures.db", use_postgres: bool = False):
        self.use_postgres = use_postgres or (os.environ.get('DATABASE_URL') and os.environ.get('RAILWAY_ENVIRONMENT'))
        
        if self.use_postgres:
            self.database_url = os.environ.get('DATABASE_URL')
            print("🚀 GestureManager usando PostgreSQL")
            self._init_postgres_tables()
        else:
            self.db_path = db_path
            print(f"🏠 GestureManager usando SQLite: {db_path}")
            self._init_sqlite_tables()
    
    def _get_postgres_connection(self):
        """Conecta ao PostgreSQL"""
        import psycopg2
        import psycopg2.extras
        from urllib.parse import urlparse
        
        url = urlparse(self.database_url)
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    
    def _init_postgres_tables(self):
        """Inicializa tabelas no PostgreSQL"""
        try:
            conn = self._get_postgres_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gestures (
                    id SERIAL PRIMARY KEY,
                    letter VARCHAR(1) UNIQUE NOT NULL,
                    landmarks_json TEXT NOT NULL,
                    quality INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gesture_analytics (
                    id SERIAL PRIMARY KEY,
                    letter VARCHAR(1) NOT NULL,
                    recognition_count INTEGER DEFAULT 0,
                    last_recognized TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            print("Tabelas PostgreSQL para gestos criadas com sucesso!")
            
        except Exception as e:
            print(f"Erro ao inicializar PostgreSQL: {e}")
    
    def _init_sqlite_tables(self):
        """Inicializa tabelas no SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gestures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    letter TEXT UNIQUE NOT NULL,
                    landmarks_json TEXT NOT NULL,
                    quality INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gesture_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    letter TEXT NOT NULL,
                    recognition_count INTEGER DEFAULT 0,
                    last_recognized TIMESTAMP
                )
            """)
            conn.commit()

    def save_gesture(self, letter: str, landmarks: List[Dict], quality: int) -> bool:
        """Salva um gesto no banco de dados"""
        try:
            if not letter or len(letter) != 1 or not letter.isalpha():
                raise ValueError("Letra deve ser um único caractere alfabético")
            
            if not landmarks or len(landmarks) != 21:
                raise ValueError("Landmarks deve conter exatamente 21 pontos")
            
            if not 0 <= quality <= 100:
                raise ValueError("Qualidade deve estar entre 0 e 100")
            
            letter = letter.upper()
            landmarks_json = json.dumps(landmarks)
            
            if self.use_postgres:
                conn = self._get_postgres_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO gestures (letter, landmarks_json, quality, updated_at) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (letter) 
                    DO UPDATE SET 
                        landmarks_json = EXCLUDED.landmarks_json,
                        quality = EXCLUDED.quality,
                        updated_at = EXCLUDED.updated_at
                """, (letter, landmarks_json, quality, datetime.now()))
                
                cursor.execute("""
                    INSERT INTO gesture_analytics (letter, recognition_count) 
                    VALUES (%s, 0)
                    ON CONFLICT (letter) DO NOTHING
                """, (letter,))
                
                conn.commit()
                conn.close()
            else:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO gestures 
                        (letter, landmarks_json, quality, updated_at) 
                        VALUES (?, ?, ?, ?)
                    """, (letter, landmarks_json, quality, datetime.now().isoformat()))
                    
                    conn.execute("""
                        INSERT OR IGNORE INTO gesture_analytics (letter, recognition_count) 
                        VALUES (?, 0)
                    """, (letter,))
                    
                    conn.commit()
            
            print(f"Gesto da letra {letter} salvo com sucesso (qualidade: {quality}%)")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar gesto da letra {letter}: {e}")
            return False

    def get_gesture(self, letter: str) -> Optional[Dict[str, Any]]:
        """Recupera um gesto específico"""
        try:
            letter = letter.upper()
            
            if self.use_postgres:
                conn = self._get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT landmarks_json, quality, created_at, updated_at FROM gestures WHERE letter = %s",
                    (letter,)
                )
                result = cursor.fetchone()
                conn.close()
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT landmarks_json, quality, created_at, updated_at FROM gestures WHERE letter = ?",
                        (letter,)
                    )
                    result = cursor.fetchone()
            
            if result:
                return {
                    'letter': letter,
                    'landmarks': json.loads(result[0] if self.use_postgres else result[0]),
                    'quality': result[1],
                    'created_at': result[2],
                    'updated_at': result[3]
                }
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar gesto da letra {letter}: {e}")
            return None

    def get_all_gestures(self) -> Dict[str, Dict[str, Any]]:
        """Recupera todos os gestos salvos"""
        try:
            if self.use_postgres:
                conn = self._get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT letter, landmarks_json, quality, created_at, updated_at FROM gestures")
                results = cursor.fetchall()
                conn.close()
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT letter, landmarks_json, quality, created_at, updated_at FROM gestures")
                    results = cursor.fetchall()
            
            gestures = {}
            for row in results:
                if self.use_postgres:
                    letter = row['letter']
                    landmarks_json = row['landmarks_json']
                    quality = row['quality']
                    created_at = row['created_at']
                    updated_at = row['updated_at']
                else:
                    letter = row[0]
                    landmarks_json = row[1]
                    quality = row[2]
                    created_at = row[3]
                    updated_at = row[4]
                
                gestures[letter] = {
                    'landmarks': json.loads(landmarks_json),
                    'quality': quality,
                    'created_at': created_at,
                    'updated_at': updated_at
                }
            
            return gestures
            
        except Exception as e:
            print(f"Erro ao buscar gestos: {e}")
            return {}

    def delete_gesture(self, letter: str) -> bool:
        """Remove um gesto do banco"""
        try:
            letter = letter.upper()
            
            if self.use_postgres:
                conn = self._get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM gestures WHERE letter = %s", (letter,))
                cursor.execute("DELETE FROM gesture_analytics WHERE letter = %s", (letter,))
                conn.commit()
                conn.close()
            else:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM gestures WHERE letter = ?", (letter,))
                    conn.execute("DELETE FROM gesture_analytics WHERE letter = ?", (letter,))
                    conn.commit()
            
            print(f"Gesto da letra {letter} removido com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro ao remover gesto da letra {letter}: {e}")
            return False

    def recognize_gesture_hybrid(self, landmarks: List[Dict], ml_system=None) -> Dict[str, Any]:
        """Reconhecimento híbrido usando sistema tradicional + ML"""
        result = {
            'traditional': None,
            'ml': None,
            'final': None,
            'confidence': 0.0,
            'method': 'none'
        }
        
        # Reconhecimento tradicional
        traditional_result = self.recognize_gesture(landmarks)
        if traditional_result:
            result['traditional'] = traditional_result
        
        # Reconhecimento ML se disponível
        if ml_system:
            try:
                ml_letter, ml_confidence = ml_system.predict_letter(landmarks)
                if ml_letter:
                    result['ml'] = {
                        'letter': ml_letter,
                        'confidence': ml_confidence
                    }
            except Exception as e:
                print(f"Erro no reconhecimento ML: {e}")
        
        # Decidir resultado final
        traditional_conf = traditional_result.get('similarity', 0) if traditional_result else 0
        ml_conf = result['ml']['confidence'] if result['ml'] else 0
        
        # Priorizar ML se tiver alta confiança
        if ml_conf > 0.7:
            result['final'] = result['ml']['letter']
            result['confidence'] = ml_conf
            result['method'] = 'ml'
        # Usar tradicional se ML não estiver disponível ou tiver baixa confiança
        elif traditional_conf > 0.5:
            result['final'] = traditional_result['letter']
            result['confidence'] = traditional_conf
            result['method'] = 'traditional'
        # Usar ML mesmo com confiança menor se tradicional falhou
        elif ml_conf > 0.3:
            result['final'] = result['ml']['letter']
            result['confidence'] = ml_conf
            result['method'] = 'ml_fallback'
        
        return result

    def recognize_gesture(self, landmarks: List[Dict]) -> Optional[Dict[str, Any]]:
        """Reconhecimento tradicional baseado em comparação de landmarks"""
        try:
            if not landmarks or len(landmarks) != 21:
                return None
            
            # Normalizar landmarks de entrada
            normalized_input = self._normalize_landmarks(landmarks)
            if not normalized_input:
                return None
            
            best_match = None
            best_similarity = 0.0
            
            # Comparar com todos os gestos salvos
            all_gestures = self.get_all_gestures()
            
            for letter, gesture_data in all_gestures.items():
                if not gesture_data or not gesture_data.get('landmarks'):
                    continue
                
                # Normalizar landmarks salvos
                saved_landmarks = gesture_data['landmarks']
                normalized_saved = self._normalize_landmarks(saved_landmarks)
                if not normalized_saved:
                    continue
                
                # Calcular similaridade
                similarity = self._calculate_similarity(normalized_input, normalized_saved)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = letter
            
            # Retornar apenas se similaridade for razoável
            if best_similarity > 0.3:  # Threshold mínimo
                return {
                    'letter': best_match,
                    'similarity': best_similarity
                }
            
            return None
            
        except Exception as e:
            print(f"Erro no reconhecimento tradicional: {e}")
            return None

    def _normalize_landmarks(self, landmarks: List[Dict]) -> Optional[List[Dict]]:
        """Normaliza landmarks para comparação consistente"""
        try:
            if not landmarks or len(landmarks) != 21:
                return None
            
            # Converter para formato consistente se necessário
            normalized = []
            for point in landmarks:
                if isinstance(point, dict):
                    x = float(point.get('x', 0))
                    y = float(point.get('y', 0))
                    z = float(point.get('z', 0))
                else:
                    # Se for lista ou tupla
                    x, y, z = float(point[0]), float(point[1]), float(point[2]) if len(point) > 2 else 0
                
                normalized.append({'x': x, 'y': y, 'z': z})
            
            # Normalizar posição (centrar no pulso - ponto 0)
            wrist = normalized[0]
            for point in normalized:
                point['x'] -= wrist['x']
                point['y'] -= wrist['y']
                point['z'] -= wrist['z']
            
            return normalized
            
        except Exception as e:
            print(f"Erro ao normalizar landmarks: {e}")
            return None

    def _calculate_similarity(self, landmarks1: List[Dict], landmarks2: List[Dict]) -> float:
        """Calcula similaridade entre dois conjuntos de landmarks"""
        try:
            if len(landmarks1) != len(landmarks2) or len(landmarks1) != 21:
                return 0.0
            
            total_distance = 0.0
            max_possible_distance = 0.0
            
            for i in range(21):
                p1 = landmarks1[i]
                p2 = landmarks2[i]
                
                # Distância euclidiana 3D
                distance = ((p1['x'] - p2['x']) ** 2 + 
                           (p1['y'] - p2['y']) ** 2 + 
                           (p1['z'] - p2['z']) ** 2) ** 0.5
                
                total_distance += distance
                # Assumir distância máxima possível de 2.0 por ponto
                max_possible_distance += 2.0
            
            # Converter distância para similaridade (0-1)
            if max_possible_distance > 0:
                similarity = 1.0 - (total_distance / max_possible_distance)
                return max(0.0, similarity)
            
            return 0.0
            
        except Exception as e:
            print(f"Erro ao calcular similaridade: {e}")
            return 0.0

    def update_recognition_stats(self, letter: str):
        """Atualiza estatísticas de reconhecimento"""
        try:
            letter = letter.upper()
            
            if self.use_postgres:
                conn = self._get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE gesture_analytics 
                    SET recognition_count = recognition_count + 1, 
                        last_recognized = %s 
                    WHERE letter = %s
                """, (datetime.now(), letter))
                conn.commit()
                conn.close()
            else:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE gesture_analytics 
                        SET recognition_count = recognition_count + 1, 
                            last_recognized = ? 
                        WHERE letter = ?
                    """, (datetime.now().isoformat(), letter))
                    conn.commit()
            
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")

    def get_gesture_count(self) -> int:
        """Retorna o número total de gestos salvos"""
        try:
            if self.use_postgres:
                conn = self._get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM gestures")
                result = cursor.fetchone()
                conn.close()
                return result[0] if result else 0
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM gestures")
                    result = cursor.fetchone()
                    return result[0] if result else 0
                    
        except Exception as e:
            print(f"Erro ao contar gestos: {e}")
            return 0