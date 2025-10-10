"""
Sistema de Gerenciamento de Gestos Libras
Armazena e gerencia gestos capturados pelo administrador
"""

import json
import os
import math
from datetime import datetime
import sqlite3
from typing import Dict, List, Optional, Any

class GestureManager:
    def __init__(self, db_path: str = "gestures.db"):
        self.db_path = db_path
        self._cache = {}  # Cache em memória para gestos
        self._cache_timestamp = 0  # Timestamp do último carregamento
        self._cache_timeout = 300  # Cache válido por 5 minutos
        
        self.init_database()
        self.preload_gestures()  # Pré-carregar gestos na inicialização
        
    def preload_gestures(self):
        """Pré-carrega todos os gestos na inicialização"""
        try:
            gestures = self.get_all_gestures()
            print(f"🔄 Pré-carregamento: {len(gestures)} gestos carregados em cache")
        except Exception as e:
            print(f"⚠️ Erro no pré-carregamento: {e}")
    
    def _refresh_cache_if_needed(self):
        """Atualiza o cache se necessário"""
        import time
        current_time = time.time()
        
        if (current_time - self._cache_timestamp) > self._cache_timeout:
            self._cache.clear()
            self._cache_timestamp = current_time
            print("🔄 Cache de gestos expirado, recarregando...")
    
    def invalidate_cache(self):
        """Força a invalidação do cache"""
        self._cache.clear()
        self._cache_timestamp = 0
        print("🗑️ Cache de gestos invalidado")
    
    def _update_cache_with_gesture(self, letter: str, landmarks: List[Dict], quality: int):
        """Atualiza o cache com um gesto específico"""
        try:
            import time
            gesture_data = {
                'letter': letter,
                'landmarks': landmarks,
                'quality': quality,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self._cache[letter] = gesture_data
            self._cache_timestamp = time.time()
            print(f"📝 Cache atualizado com gesto da letra {letter}")
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar cache: {e}")
        
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
                
            print(f"✅ Gesto da letra {letter} salvo com sucesso (qualidade: {quality}%)")
            
            # Invalidar cache para forçar recarregamento
            self.invalidate_cache()
            
            # Atualizar cache imediatamente com o novo gesto
            self._update_cache_with_gesture(letter, landmarks, quality)
            
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
        Recupera todos os gestos salvos (com cache)
        
        Returns:
            Dict com letra como chave e dados do gesto como valor
        """
        try:
            # Verificar se precisa atualizar o cache
            self._refresh_cache_if_needed()
            
            # Se cache está válido, usar ele
            if self._cache:
                return self._cache.copy()
            
            # Carregar do banco de dados
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
            
            # Atualizar cache
            self._cache = gestures.copy()
            import time
            self._cache_timestamp = time.time()
            
            print(f"📦 Carregados {len(gestures)} gestos do banco de dados (cache atualizado)")
            return gestures
            
        except Exception as e:
            print(f"❌ Erro ao carregar gestos: {e}")
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
                    print(f"✅ Gesto da letra {letter} removido com sucesso")
                    
                    # Invalidar cache e remover do cache local
                    self.invalidate_cache()
                    if letter in self._cache:
                        del self._cache[letter]
                    
                    return True
                else:
                    print(f"⚠️ Gesto da letra {letter} não encontrado para remoção")
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
            'method': 'none',
            'detailed_analysis': None
        }
        
        print("🔄 Iniciando reconhecimento híbrido...")
        
        # Reconhecimento tradicional
        try:
            traditional_result = self.recognize_gesture(landmarks)
            if traditional_result:
                result['traditional'] = traditional_result
                print(f"✅ Reconhecimento tradicional: {traditional_result['letter']} ({traditional_result['similarity']:.3f})")
            else:
                print("❌ Reconhecimento tradicional não encontrou correspondência")
        except Exception as e:
            print(f"❌ Erro no reconhecimento tradicional: {e}")
        
        # Reconhecimento ML se disponível
        if ml_system:
            try:
                print("🤖 Tentando reconhecimento ML...")
                ml_letter, ml_confidence = ml_system.predict_letter(landmarks)
                if ml_letter and ml_confidence > 0.1:  # Threshold mínimo para ML
                    result['ml'] = {
                        'letter': ml_letter,
                        'confidence': ml_confidence
                    }
                    print(f"✅ Reconhecimento ML: {ml_letter} ({ml_confidence:.3f})")
                else:
                    print("❌ Reconhecimento ML não encontrou correspondência confiável")
            except Exception as e:
                print(f"❌ Erro no reconhecimento ML: {e}")
        
        # Decidir resultado final com lógica melhorada
        traditional_conf = result['traditional'].get('similarity', 0) if result['traditional'] else 0
        ml_conf = result['ml']['confidence'] if result['ml'] else 0
        
        print(f"📊 Comparando resultados - Tradicional: {traditional_conf:.3f}, ML: {ml_conf:.3f}")
        
        # Priorizar resultado com maior confiança, mas dar preferência ao tradicional em empates
        if traditional_conf > 0.6 and traditional_conf >= ml_conf:
            # Tradicional com alta confiança
            result['final'] = result['traditional']['letter']
            result['confidence'] = traditional_conf
            result['method'] = 'traditional'
            result['detailed_analysis'] = result['traditional']
            print(f"🎯 Escolha final: Tradicional - {result['final']} ({result['confidence']:.3f})")
            
        elif ml_conf > 0.7:
            # ML com alta confiança
            result['final'] = result['ml']['letter']
            result['confidence'] = ml_conf
            result['method'] = 'ml'
            print(f"🎯 Escolha final: ML - {result['final']} ({result['confidence']:.3f})")
            
        elif traditional_conf > 0.4:
            # Tradicional com confiança moderada
            result['final'] = result['traditional']['letter']
            result['confidence'] = traditional_conf
            result['method'] = 'traditional'
            result['detailed_analysis'] = result['traditional']
            print(f"🎯 Escolha final: Tradicional (moderado) - {result['final']} ({result['confidence']:.3f})")
            
        elif ml_conf > 0.3:
            # ML como fallback
            result['final'] = result['ml']['letter']
            result['confidence'] = ml_conf
            result['method'] = 'ml_fallback'
            print(f"🎯 Escolha final: ML (fallback) - {result['final']} ({result['confidence']:.3f})")
        else:
            print("❌ Nenhum método de reconhecimento atingiu threshold mínimo")
        
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
                print("❌ Landmarks inválidos para reconhecimento")
                return None
            
            # Normalizar landmarks de entrada
            normalized_input = self._normalize_landmarks(landmarks)
            if not normalized_input:
                print("❌ Falha na normalização dos landmarks de entrada")
                return None
            
            best_match = None
            best_similarity = 0.0
            all_similarities = {}
            
            # Comparar com todos os gestos salvos
            all_gestures = self.get_all_gestures()
            
            if not all_gestures:
                print("⚠️ Nenhum gesto salvo encontrado para comparação")
                return None
            
            print(f"🔍 Comparando com {len(all_gestures)} gestos salvos...")
            
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
                all_similarities[letter] = similarity
                
                print(f"📊 Letra {letter}: {similarity:.3f} similaridade")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = letter
            
            # Ajustar threshold para ser mais permissivo após melhorias
            threshold = 0.4  # Reduzido de 0.3 para 0.4
            
            print(f"🎯 Melhor match: {best_match} com {best_similarity:.3f} (threshold: {threshold})")
            
            # Retornar apenas se similaridade for razoável
            if best_similarity > threshold:
                result = {
                    'letter': best_match,
                    'similarity': best_similarity,
                    'all_similarities': all_similarities,
                    'quality': 'excellent' if best_similarity > 0.8 else 'good' if best_similarity > 0.6 else 'acceptable'
                }
                print(f"✅ Gesto reconhecido: {best_match} ({result['quality']})")
                return result
            else:
                print(f"❌ Nenhum gesto reconhecido - melhor similaridade: {best_similarity:.3f}")
                return None
            
        except Exception as e:
            print(f"❌ Erro no reconhecimento tradicional: {e}")
            import traceback
            traceback.print_exc()
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
            
            # Normalizar escala (baseado na distância do pulso ao médio)
            try:
                middle_finger_tip = normalized[12]  # Ponta do dedo médio
                scale_distance = ((middle_finger_tip['x'])**2 + 
                                (middle_finger_tip['y'])**2 + 
                                (middle_finger_tip['z'])**2)**0.5
                
                if scale_distance > 0.01:  # Evitar divisão por zero
                    scale_factor = 1.0 / scale_distance
                    for point in normalized:
                        point['x'] *= scale_factor
                        point['y'] *= scale_factor
                        point['z'] *= scale_factor
            except:
                # Se houver erro na normalização de escala, continuar sem ela
                pass
            
            return normalized
            
        except Exception as e:
            print(f"Erro ao normalizar landmarks: {e}")
            return None

    def _calculate_similarity(self, landmarks1: List[Dict], landmarks2: List[Dict]) -> float:
        """Calcula similaridade entre dois conjuntos de landmarks"""
        try:
            if len(landmarks1) != len(landmarks2) or len(landmarks1) != 21:
                return 0.0
            
            # Pesos para diferentes pontos da mão (pontos mais importantes têm peso maior)
            point_weights = {
                0: 1.5,   # Pulso (muito importante para orientação)
                4: 2.0,   # Ponta do polegar
                8: 2.0,   # Ponta do indicador
                12: 2.0,  # Ponta do médio
                16: 2.0,  # Ponta do anelar
                20: 2.0,  # Ponta do mindinho
                # Articulações importantes
                5: 1.5, 9: 1.5, 13: 1.5, 17: 1.5,  # Base dos dedos
                # Outras articulações
                1: 1.0, 2: 1.2, 3: 1.3,  # Polegar (aumentar peso das articulações)
                6: 1.0, 7: 1.2,          # Indicador
                10: 1.0, 11: 1.2,        # Médio
                14: 1.0, 15: 1.2,        # Anelar
                18: 1.0, 19: 1.2         # Mindinho
            }
            
            total_weighted_distance = 0.0
            total_weight = 0.0
            
            for i in range(21):
                p1 = landmarks1[i]
                p2 = landmarks2[i]
                weight = point_weights.get(i, 1.0)
                
                # Calcular distância euclidiana 3D
                distance_3d = ((p1['x'] - p2['x']) ** 2 + 
                              (p1['y'] - p2['y']) ** 2 + 
                              (p1['z'] - p2['z']) ** 2) ** 0.5
                
                # Calcular distância 2D (para gestos principalmente planos)
                distance_2d = ((p1['x'] - p2['x']) ** 2 + 
                              (p1['y'] - p2['y']) ** 2) ** 0.5
                
                # Usar combinação de distâncias 2D e 3D
                # Para gestos de LIBRAS, a profundidade é menos importante
                combined_distance = (distance_2d * 0.8) + (distance_3d * 0.2)
                
                total_weighted_distance += combined_distance * weight
                total_weight += weight
            
            # Calcular distância média ponderada
            if total_weight > 0:
                avg_weighted_distance = total_weighted_distance / total_weight
            else:
                return 0.0
            
            # Converter para similaridade (0-1)
            # Ajustar o threshold máximo para ser mais sensível
            max_distance = 0.15  # Reduzido de 2.0 para 0.15 (após normalização)
            similarity = max(0.0, 1.0 - (avg_weighted_distance / max_distance))
            
            # Aplicar função de suavização para melhorar a diferenciação
            # Usar função sigmoide para tornar similaridades altas mais distintas
            enhanced_similarity = 1 / (1 + math.exp(-10 * (similarity - 0.5)))
            
            return min(1.0, enhanced_similarity)
            
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
    
    def test_recognition_with_saved_gesture(self, letter: str) -> Dict[str, Any]:
        """
        Testa o reconhecimento usando um gesto salvo como entrada
        
        Args:
            letter: Letra do gesto salvo para testar
            
        Returns:
            Dict com resultado do teste
        """
        try:
            # Buscar gesto salvo
            saved_gesture = self.get_gesture(letter)
            if not saved_gesture:
                return {"error": f"Gesto da letra {letter} não encontrado"}
            
            print(f"🧪 Testando reconhecimento da letra {letter}...")
            
            # Usar os landmarks do gesto salvo para teste
            test_landmarks = saved_gesture['landmarks']
            
            # Executar reconhecimento
            result = self.recognize_gesture(test_landmarks)
            
            test_result = {
                "test_letter": letter,
                "saved_quality": saved_gesture['quality'],
                "recognition_result": result,
                "success": result is not None and result.get('letter') == letter
            }
            
            if test_result["success"]:
                print(f"✅ Teste PASSOU - {letter} reconhecido corretamente com {result['similarity']:.3f} similaridade")
            else:
                recognized_letter = result.get('letter', 'None') if result else 'None'
                print(f"❌ Teste FALHOU - {letter} não foi reconhecido (resultado: {recognized_letter})")
            
            return test_result
            
        except Exception as e:
            print(f"❌ Erro no teste de reconhecimento: {e}")
            return {"error": str(e)}
    
    def test_all_saved_gestures(self) -> Dict[str, Any]:
        """
        Testa reconhecimento para todos os gestos salvos
        
        Returns:
            Dict com resultados dos testes
        """
        all_gestures = self.get_all_gestures()
        if not all_gestures:
            return {"error": "Nenhum gesto salvo encontrado"}
        
        results = {}
        passed = 0
        total = len(all_gestures)
        
        print(f"🧪 Iniciando teste de {total} gestos salvos...")
        
        for letter in all_gestures.keys():
            test_result = self.test_recognition_with_saved_gesture(letter)
            results[letter] = test_result
            
            if test_result.get("success", False):
                passed += 1
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "individual_results": results
        }
        
        print(f"📊 Resultado dos testes: {passed}/{total} passou ({summary['success_rate']:.1f}%)")
        
        return summary
    
    def get_gesture_sync_info(self) -> Dict[str, Any]:
        """
        Retorna informações de sincronização dos gestos
        
        Returns:
            Dict com informações de sincronização
        """
        try:
            gestures = self.get_all_gestures()
            
            # Calcular estatísticas
            total_gestures = len(gestures)
            letters_with_gestures = list(gestures.keys())
            letters_without_gestures = [
                letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" 
                if letter not in letters_with_gestures
            ]
            
            # Verificar qualidade dos gestos
            high_quality = sum(1 for g in gestures.values() if g['quality'] >= 80)
            medium_quality = sum(1 for g in gestures.values() if 60 <= g['quality'] < 80)
            low_quality = sum(1 for g in gestures.values() if g['quality'] < 60)
            
            # Cache info
            cache_status = "active" if self._cache else "empty"
            cache_size = len(self._cache)
            
            return {
                "total_gestures": total_gestures,
                "letters_with_gestures": letters_with_gestures,
                "letters_without_gestures": letters_without_gestures,
                "completion_percentage": (total_gestures / 26) * 100,
                "quality_distribution": {
                    "high_quality": high_quality,
                    "medium_quality": medium_quality,
                    "low_quality": low_quality
                },
                "cache_info": {
                    "status": cache_status,
                    "size": cache_size,
                    "timestamp": self._cache_timestamp
                },
                "sync_status": "synchronized" if total_gestures > 0 else "empty"
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter info de sincronização: {e}")
            return {
                "total_gestures": 0,
                "sync_status": "error",
                "error": str(e)
            }
    
    def ensure_gestures_available(self) -> bool:
        """
        Garante que os gestos estejam carregados e disponíveis
        
        Returns:
            bool: True se gestos estão disponíveis
        """
        try:
            gestures = self.get_all_gestures()
            available = len(gestures) > 0
            
            if available:
                print(f"✅ Gestos disponíveis: {len(gestures)} letras carregadas")
            else:
                print("⚠️ Nenhum gesto disponível - vá para /admin para capturar gestos")
            
            return available
            
        except Exception as e:
            print(f"❌ Erro ao verificar gestos: {e}")
            return False