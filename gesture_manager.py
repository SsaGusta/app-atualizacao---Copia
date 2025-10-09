"""
Sistema de Gerenciamento de Gestos Libras
Armazena e gerencia gestos capturados pelo administrador
"""

import json
import os
from datetime import datetime
import sqlite3
from typing import Dict, List, Optional, Any

class GestureManager:
    def __init__(self, db_path: str = "gestures.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Inicializa o banco de dados de gestos"""
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
                    last_recognized TIMESTAMP,
                    FOREIGN KEY (letter) REFERENCES gestures (letter)
                )
            """)
            conn.commit()
    
    def save_gesture(self, letter: str, landmarks: List[Dict], quality: int) -> bool:
        """
        Salva um gesto no banco de dados
        
        Args:
            letter: Letra do alfabeto (A-Z)
            landmarks: Lista de 21 pontos com coordenadas x, y, z
            quality: Qualidade da captura (0-100)
        
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Validar entrada
            if not letter or len(letter) != 1 or not letter.isalpha():
                raise ValueError("Letra deve ser um único caractere alfabético")
            
            if not landmarks or len(landmarks) != 21:
                raise ValueError("Landmarks deve conter exatamente 21 pontos")
            
            if not 0 <= quality <= 100:
                raise ValueError("Qualidade deve estar entre 0 e 100")
            
            letter = letter.upper()
            landmarks_json = json.dumps(landmarks)
            
            with sqlite3.connect(self.db_path) as conn:
                # Usar INSERT OR REPLACE para atualizar se já existir
                conn.execute("""
                    INSERT OR REPLACE INTO gestures 
                    (letter, landmarks_json, quality, updated_at) 
                    VALUES (?, ?, ?, ?)
                """, (letter, landmarks_json, quality, datetime.now().isoformat()))
                
                # Inicializar analytics se não existir
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
        """
        Recupera um gesto específico
        
        Args:
            letter: Letra do alfabeto
            
        Returns:
            Dict com dados do gesto ou None se não encontrado
        """
        try:
            letter = letter.upper()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT letter, landmarks_json, quality, created_at, updated_at
                    FROM gestures 
                    WHERE letter = ?
                """, (letter,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'letter': row['letter'],
                        'landmarks': json.loads(row['landmarks_json']),
                        'quality': row['quality'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                return None
                
        except Exception as e:
            print(f"Erro ao recuperar gesto da letra {letter}: {e}")
            return None
    
    def get_all_gestures(self) -> Dict[str, Dict[str, Any]]:
        """
        Recupera todos os gestos salvos
        
        Returns:
            Dict com letra como chave e dados do gesto como valor
        """
        try:
            gestures = {}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT letter, landmarks_json, quality, created_at, updated_at
                    FROM gestures 
                    ORDER BY letter
                """)
                
                for row in cursor.fetchall():
                    gestures[row['letter']] = {
                        'letter': row['letter'],
                        'landmarks': json.loads(row['landmarks_json']),
                        'quality': row['quality'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    
            print(f"Carregados {len(gestures)} gestos do banco de dados")
            return gestures
            
        except Exception as e:
            print(f"Erro ao carregar gestos: {e}")
            return {}
    
    def delete_gesture(self, letter: str) -> bool:
        """
        Remove um gesto do banco de dados
        
        Args:
            letter: Letra do alfabeto
            
        Returns:
            bool: True se removeu com sucesso
        """
        try:
            letter = letter.upper()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM gestures WHERE letter = ?", (letter,))
                conn.execute("DELETE FROM gesture_analytics WHERE letter = ?", (letter,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"Gesto da letra {letter} removido com sucesso")
                    return True
                else:
                    print(f"Gesto da letra {letter} não encontrado para remoção")
                    return False
                    
        except Exception as e:
            print(f"Erro ao remover gesto da letra {letter}: {e}")
            return False
    
    def recognize_gesture_hybrid(self, landmarks: List[Dict], ml_system=None) -> Dict[str, Any]:
        """
        Reconhecimento híbrido usando sistema tradicional + ML
        
        Args:
            landmarks: Lista de 21 pontos com coordenadas
            ml_system: Sistema de ML opcional
            
        Returns:
            Dict com resultado do reconhecimento
        """
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
        """
        Reconhecimento tradicional baseado em comparação de landmarks
        
        Args:
            landmarks: Lista de 21 pontos com coordenadas
            
        Returns:
            Dict com letra reconhecida e similaridade ou None
        """
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
        """
        Atualiza estatísticas de reconhecimento de uma letra
        
        Args:
            letter: Letra que foi reconhecida
        """
        try:
            letter = letter.upper()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE gesture_analytics 
                    SET recognition_count = recognition_count + 1,
                        last_recognized = ?
                    WHERE letter = ?
                """, (datetime.now().isoformat(), letter))
                conn.commit()
                
        except Exception as e:
            print(f"Erro ao atualizar estatísticas da letra {letter}: {e}")
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Recupera estatísticas de uso dos gestos
        
        Returns:
            Dict com estatísticas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Estatísticas gerais
                total_gestures = conn.execute("SELECT COUNT(*) as count FROM gestures").fetchone()['count']
                
                # Gestos mais reconhecidos
                most_recognized = conn.execute("""
                    SELECT letter, recognition_count 
                    FROM gesture_analytics 
                    WHERE recognition_count > 0
                    ORDER BY recognition_count DESC 
                    LIMIT 5
                """).fetchall()
                
                # Gestos menos reconhecidos
                least_recognized = conn.execute("""
                    SELECT g.letter, COALESCE(ga.recognition_count, 0) as count
                    FROM gestures g
                    LEFT JOIN gesture_analytics ga ON g.letter = ga.letter
                    ORDER BY count ASC, g.letter ASC
                    LIMIT 5
                """).fetchall()
                
                return {
                    'total_gestures': total_gestures,
                    'most_recognized': [dict(row) for row in most_recognized],
                    'least_recognized': [dict(row) for row in least_recognized]
                }
                
        except Exception as e:
            print(f"Erro ao recuperar estatísticas: {e}")
            return {}
    
    def export_gestures(self) -> Dict[str, Any]:
        """
        Exporta todos os gestos em formato JSON para backup
        
        Returns:
            Dict com todos os dados dos gestos
        """
        try:
            gestures = self.get_all_gestures()
            analytics = self.get_analytics()
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'gestures': gestures,
                'analytics': analytics
            }
            
            print(f"📦 Exportando {len(gestures)} gestos para backup")
            return export_data
            
        except Exception as e:
            print(f"Erro ao exportar gestos: {e}")
            return {}
    
    def import_gestures(self, import_data: Dict[str, Any]) -> bool:
        """
        Importa gestos de um backup
        
        Args:
            import_data: Dados do backup
            
        Returns:
            bool: True se importou com sucesso
        """
        try:
            if 'gestures' not in import_data:
                raise ValueError("Dados de importação inválidos")
            
            imported_count = 0
            
            for letter, gesture_data in import_data['gestures'].items():
                if self.save_gesture(
                    letter, 
                    gesture_data['landmarks'], 
                    gesture_data['quality']
                ):
                    imported_count += 1
            
            print(f"📥 Importados {imported_count} gestos com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro ao importar gestos: {e}")
            return False
    
    def get_gesture_count(self) -> int:
        """
        Retorna o número total de gestos salvos
        
        Returns:
            int: Número de gestos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM gestures")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao contar gestos: {e}")
            return 0