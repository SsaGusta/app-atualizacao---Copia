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

# Importar módulos locais
try:
    from database import LibrasDatabase
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
    # Palavras padrão de fallback
    palavras = ["CASA", "AMOR", "PAZ", "VIDA", "FELIZ"]
    palavras_iniciante = ["A", "B", "C", "D", "E"]
    palavras_avancado = ["MUNDO", "BRASIL", "AMIGO"]
    palavras_expert = ["INTELIGENCIA", "PROGRAMACAO"]

try:
    from gesture_manager import GestureManager
    GESTURE_MANAGER_AVAILABLE = True
    logger.info("Módulo gesture_manager importado com sucesso")
    gesture_manager = GestureManager()
    
    # Garantir que os gestos estejam carregados
    gesture_manager.ensure_gestures_available()
    
except ImportError as e:
    GESTURE_MANAGER_AVAILABLE = False
    print(f"Aviso: Sistema de gestos não disponível: {e}")
    gesture_manager = None

# Importar sistema de Machine Learning
try:
    from ml_system import LibrasMLSystem
    ML_SYSTEM_AVAILABLE = True
    logger.info("Sistema de ML importado com sucesso")
    ml_system = LibrasMLSystem()
except ImportError as e:
    ML_SYSTEM_AVAILABLE = False
    print(f"Aviso: Sistema de ML não disponível: {e}")
    ml_system = None

# ===== CONFIGURAÇÃO DA APLICAÇÃO =====
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'libras_web_app_2025_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = '/tmp/sessions'
app.config['SESSION_FILE_THRESHOLD'] = 100

# Inicializar extensões
Session(app)
if CORS_AVAILABLE:
    CORS(app)

# ===== CONFIGURAÇÃO GLOBAL =====
# Sistema de reconhecimento desabilitado para deploy
RECOGNITION_ENABLED = False

# ===== FUNÇÕES AUXILIARES =====
def get_video_path(letra):
    """Obter caminho do vídeo para uma letra específica"""
    video_path = os.path.join('Videos', f'Letra_{letra.upper()}.mp4')
    if os.path.exists(video_path):
        return video_path
    return None

# ===== ROTAS PRINCIPAIS =====
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        # Verificar se é uma requisição AJAX (JSON)
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            data = request.get_json()
            username = data.get('username', '').strip() if data else ''
        else:
            username = request.form.get('username', '').strip()
        
        if username:
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            logger.info(f"Usuário logado: {username}")
            
            # Se for requisição AJAX, retornar JSON
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": "Login realizado com sucesso",
                    "redirect": url_for('mediapipe')
                })
            else:
                return redirect(url_for('mediapipe'))
        else:
            # Se for requisição AJAX, retornar erro JSON
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    "success": False,
                    "error": "Nome de usuário é obrigatório"
                }), 400
            else:
                return render_template('login.html', error="Nome de usuário é obrigatório")
    
    return render_template('login.html')

@app.route('/mediapipe')
def mediapipe():
    """Página de reconhecimento de mãos com MediaPipe"""
    return render_template('mediapipe.html')

@app.route('/admin')
def admin():
    """Página de administração para captura de gestos"""
    # Por segurança, pode adicionar autenticação admin aqui
    return render_template('admin.html')

@app.route('/ml_admin')
def ml_admin():
    """Página de administração do sistema de Machine Learning"""
    # Por segurança, pode adicionar autenticação admin aqui
    return render_template('ml_admin.html')

@app.route('/statistics')
def statistics():
    """Página de estatísticas"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    stats = {}
    soletrando_stats = {}
    
    if DATABASE_AVAILABLE:
        try:
            db = LibrasDatabase()
            
            # Estatísticas gerais existentes
            stats = db.get_user_statistics(session['username'])
            
            # Estatísticas específicas do Soletrando
            user_result = db.get_user(session['username'])
            if user_result:
                user_id = user_result[0]
                soletrando_stats = db.get_soletrando_stats(user_id)
            
        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas: {e}")
            stats = {"error": "Não foi possível carregar as estatísticas"}
            soletrando_stats = {"error": "Erro ao carregar estatísticas do Soletrando"}
    else:
        stats = {"info": "Sistema de estatísticas não disponível"}
        soletrando_stats = {"info": "Sistema de estatísticas não disponível"}
    
    return render_template('statistics.html', stats=stats, soletrando_stats=soletrando_stats)

# ===== ROTAS DE VÍDEO =====
@app.route('/videos/<letra>')
def serve_video(letra):
    """Servir vídeos de demonstração"""
    try:
        letra = letra.upper()
        video_path = get_video_path(letra)
        
        if video_path and os.path.exists(video_path):
            return send_file(video_path, mimetype='video/mp4')
        else:
            logger.warning(f"Vídeo não encontrado para letra: {letra}")
            abort(404)
    except Exception as e:
        logger.error(f"Erro ao servir vídeo para letra {letra}: {e}")
        abort(500)

@app.route('/api/get_video_demo/<letra>')
def get_video_demo(letra):
    """API para obter demonstração em vídeo"""
    try:
        letra = letra.upper()
        video_path = get_video_path(letra)
        
        if video_path and os.path.exists(video_path):
            video_url = url_for('serve_video', letra=letra)
            return jsonify({
                "success": True,
                "video_url": video_url,
                "letra": letra
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Vídeo não encontrado para a letra {letra}"
            })
    except Exception as e:
        logger.error(f"Erro na API de vídeo para letra {letra}: {e}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {e}"
        })

# ===== ROTA DO JOGO SOLETRANDO =====
@app.route('/soletrando')
def soletrando():
    """Página do jogo Soletrando"""
    return render_template('soletrando.html')

@app.route('/api/save_soletrando_letter', methods=['POST'])
def save_soletrando_letter():
    """API para salvar estatísticas de letra completada no Soletrando"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "Dados não fornecidos"})
        
        # Verificar se usuário está logado
        if 'username' not in session:
            return jsonify({"success": False, "error": "Usuário não logado"})
        
        # Extrair dados
        letter = data.get('letter', '').upper()
        word = data.get('word', '').upper()
        word_position = data.get('position', 0)
        completion_time = data.get('time', 0)
        similarity_score = data.get('similarity', None)
        
        # Validar dados
        if not letter or not word or completion_time <= 0:
            return jsonify({"success": False, "error": "Dados inválidos"})
        
        if not DATABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de estatísticas não disponível"})
        
        # Salvar no banco
        db = LibrasDatabase()
        username = session['username']
        
        # Buscar ou criar usuário
        user_result = db.get_user(username)
        if not user_result:
            user_id = db.create_user(username)
        else:
            user_id = user_result[0]
        
        if user_id:
            # Salvar estatística da letra
            stat_id = db.save_soletrando_letter(
                user_id=user_id,
                letter=letter,
                word=word,
                word_position=word_position,
                completion_time=completion_time,
                similarity_score=similarity_score
            )
            
            if stat_id:
                return jsonify({
                    "success": True,
                    "message": f"Letra {letter} salva com sucesso",
                    "stat_id": stat_id
                })
            else:
                return jsonify({"success": False, "error": "Erro ao salvar no banco"})
        else:
            return jsonify({"success": False, "error": "Erro ao identificar usuário"})
    
    except Exception as e:
        logger.error(f"Erro ao salvar estatística Soletrando: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/get_soletrando_stats')
def get_soletrando_stats():
    """API para recuperar estatísticas do Soletrando do usuário"""
    try:
        # Verificar se usuário está logado
        if 'username' not in session:
            return jsonify({"success": False, "error": "Usuário não logado"})
        
        if not DATABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de estatísticas não disponível"})
        
        db = LibrasDatabase()
        username = session['username']
        
        # Buscar usuário
        user_result = db.get_user(username)
        if not user_result:
            return jsonify({"success": False, "error": "Usuário não encontrado"})
        
        user_id = user_result[0]
        stats = db.get_soletrando_stats(user_id)
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Erro ao recuperar estatísticas Soletrando: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

# ===== MODO DESAFIO =====
@app.route('/desafio')
def desafio():
    """Página do jogo Desafio"""
    return render_template('desafio.html')

@app.route('/api/get_challenge_words/<level>')
def get_challenge_words(level):
    """API para obter palavras do nível de desafio especificado"""
    try:
        if not WORDS_AVAILABLE:
            return jsonify({
                "success": False, 
                "error": "Sistema de palavras não disponível",
                "words": ["CASA", "GATO", "AGUA", "LIVRO", "AMIGO"]
            })
        
        words_map = {
            'iniciante': palavras_iniciante,
            'intermediario': palavras,
            'avancado': palavras_avancado,
            'expert': palavras_expert
        }
        
        selected_words = words_map.get(level, palavras_iniciante)
        
        # Para níveis expert e avançado, processa espaços e hífens automaticamente
        if level in ['expert', 'avancado']:
            processed_words = []
            for word in selected_words:
                # Quebra frases em palavras individuais para o desafio
                if level == 'expert':
                    # Para expert, pega frases completas mas marca espaços/hífens
                    processed_words.append(word)
                else:
                    # Para avançado, pode dividir palavras compostas
                    processed_words.append(word)
            selected_words = processed_words
        
        return jsonify({
            "success": True,
            "words": selected_words,
            "level": level,
            "total": len(selected_words)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar palavras do desafio: {e}")
        return jsonify({
            "success": False, 
            "error": f"Erro interno: {str(e)}",
            "words": ["CASA", "GATO", "AGUA", "LIVRO", "AMIGO"]
        })

@app.route('/api/save_challenge_result', methods=['POST'])
def save_challenge_result():
    """API para salvar resultado do desafio"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "Dados não fornecidos"})
        
        # Verificar se usuário está logado
        if 'username' not in session:
            return jsonify({"success": False, "error": "Usuário não logado"})
        
        if not DATABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de banco não disponível"})
        
        # Extrair dados
        level = data.get('level', 'iniciante')
        words_completed = data.get('words_completed', 0)
        score = data.get('score', 0)
        time_taken = data.get('time_taken', 0)
        
        # Validar dados
        if not all([level, isinstance(words_completed, int), isinstance(score, int)]):
            return jsonify({"success": False, "error": "Dados inválidos fornecidos"})
        
        db = LibrasDatabase()
        username = session['username']
        
        # Buscar usuário
        user_result = db.get_user(username)
        if not user_result:
            return jsonify({"success": False, "error": "Usuário não encontrado"})
        
        user_id = user_result[0]
        
        # Salvar resultado do desafio
        success = db.save_challenge_result(user_id, level, words_completed, score, time_taken)
        
        if success:
            return jsonify({
                "success": True, 
                "message": "Resultado do desafio salvo com sucesso!",
                "level": level,
                "words_completed": words_completed,
                "score": score
            })
        else:
            return jsonify({"success": False, "error": "Erro ao salvar resultado no banco"})
    
    except Exception as e:
        logger.error(f"Erro ao salvar resultado do desafio: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/get_challenge_stats')
def get_challenge_stats():
    """API para recuperar estatísticas do Desafio do usuário"""
    try:
        # Verificar se usuário está logado
        if 'username' not in session:
            return jsonify({"success": False, "error": "Usuário não logado"})
        
        if not DATABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de estatísticas não disponível"})
        
        db = LibrasDatabase()
        username = session['username']
        
        # Buscar usuário
        user_result = db.get_user(username)
        if not user_result:
            return jsonify({"success": False, "error": "Usuário não encontrado"})
        
        user_id = user_result[0]
        stats = db.get_challenge_stats(user_id)
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Erro ao recuperar estatísticas do Desafio: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/get_challenge_ranking/<level>')
def get_challenge_ranking(level):
    """API para obter ranking do desafio por nível"""
    try:
        if not DATABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ranking não disponível"})
        
        db = LibrasDatabase()
        ranking = db.get_challenge_ranking(level, limit=10)
        
        return jsonify({
            "success": True,
            "ranking": ranking,
            "level": level
        })
    
    except Exception as e:
        logger.error(f"Erro ao recuperar ranking do desafio: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

# ===== APIs DE MACHINE LEARNING =====
@app.route('/api/ml/collect_example', methods=['POST'])
def collect_ml_example():
    """API para coletar exemplos de gestos para ML"""
    try:
        data = request.get_json()
        
        if not data or 'letter' not in data or 'landmarks' not in data:
            return jsonify({"success": False, "error": "Dados insuficientes"})
        
        if not ML_SYSTEM_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ML não disponível"})
        
        letter = data.get('letter', '').upper()
        landmarks = data.get('landmarks', [])
        confidence = data.get('confidence', None)
        source = data.get('source', 'game')
        
        # Obter user_id se logado
        user_id = None
        if 'username' in session and DATABASE_AVAILABLE:
            try:
                db = LibrasDatabase()
                user_result = db.get_user(session['username'])
                if user_result:
                    user_id = user_result[0]
            except:
                pass
        
        # Coletar exemplo
        example_id = ml_system.collect_gesture_example(
            letter=letter,
            landmarks=landmarks,
            user_id=user_id,
            confidence=confidence,
            source=source
        )
        
        if example_id:
            return jsonify({
                "success": True,
                "message": f"Exemplo coletado para letra {letter}",
                "example_id": example_id
            })
        else:
            return jsonify({"success": False, "error": "Erro ao coletar exemplo"})
    
    except Exception as e:
        logger.error(f"Erro ao coletar exemplo ML: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/ml/predict', methods=['POST'])
def ml_predict():
    """API para predição usando modelos ML"""
    try:
        data = request.get_json()
        
        if not data or 'landmarks' not in data:
            return jsonify({"success": False, "error": "Landmarks não fornecidos"})
        
        if not ML_SYSTEM_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ML não disponível"})
        
        landmarks = data.get('landmarks', [])
        return_probabilities = data.get('return_probabilities', False)
        
        # Fazer predição
        if return_probabilities:
            letter, confidence, all_predictions = ml_system.predict_letter(
                landmarks, return_probabilities=True
            )
            
            return jsonify({
                "success": True,
                "predicted_letter": letter,
                "confidence": float(confidence) if confidence else 0.0,
                "all_predictions": {k: float(v) for k, v in all_predictions.items()}
            })
        else:
            letter, confidence = ml_system.predict_letter(landmarks)
            
            return jsonify({
                "success": True,
                "predicted_letter": letter,
                "confidence": float(confidence) if confidence else 0.0
            })
    
    except Exception as e:
        logger.error(f"Erro na predição ML: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/ml/feedback', methods=['POST'])
def ml_feedback():
    """API para feedback de usuário sobre predições"""
    try:
        data = request.get_json()
        
        required_fields = ['predicted_letter', 'actual_letter', 'landmarks']
        if not data or not all(field in data for field in required_fields):
            return jsonify({"success": False, "error": "Dados insuficientes"})
        
        if not ML_SYSTEM_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ML não disponível"})
        
        # Obter user_id se logado
        user_id = None
        if 'username' in session and DATABASE_AVAILABLE:
            try:
                db = LibrasDatabase()
                user_result = db.get_user(session['username'])
                if user_result:
                    user_id = user_result[0]
            except:
                pass
        
        predicted_letter = data.get('predicted_letter', '').upper()
        actual_letter = data.get('actual_letter', '').upper()
        landmarks = data.get('landmarks', [])
        confidence = data.get('confidence', None)
        feedback_type = data.get('feedback_type', 'correction')
        
        # Registrar feedback
        feedback_id = ml_system.add_user_feedback(
            user_id=user_id,
            predicted_letter=predicted_letter,
            actual_letter=actual_letter,
            confidence=confidence,
            landmarks=landmarks,
            feedback_type=feedback_type
        )
        
        if feedback_id:
            return jsonify({
                "success": True,
                "message": f"Feedback registrado: {predicted_letter} -> {actual_letter}",
                "feedback_id": feedback_id
            })
        else:
            return jsonify({"success": False, "error": "Erro ao registrar feedback"})
    
    except Exception as e:
        logger.error(f"Erro ao registrar feedback ML: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/ml/train/<letter>', methods=['POST'])
def train_letter_model(letter):
    """API para treinar modelo de uma letra específica"""
    try:
        if not ML_SYSTEM_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ML não disponível"})
        
        letter = letter.upper()
        
        # Treinar modelo
        success = ml_system.train_letter_model(letter)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Modelo da letra {letter} treinado com sucesso"
            })
        else:
            return jsonify({"success": False, "error": f"Erro no treinamento do modelo {letter}"})
    
    except Exception as e:
        logger.error(f"Erro ao treinar modelo {letter}: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/ml/train_all', methods=['POST'])
def train_all_models():
    """API para treinar todos os modelos"""
    try:
        if not ML_SYSTEM_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ML não disponível"})
        
        data = request.get_json() or {}
        min_examples = data.get('min_examples', 10)
        
        # Treinar todos os modelos
        trained_count = ml_system.train_all_models(min_examples=min_examples)
        
        return jsonify({
            "success": True,
            "message": f"{trained_count} modelos treinados com sucesso",
            "trained_count": trained_count
        })
    
    except Exception as e:
        logger.error(f"Erro ao treinar todos os modelos: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/ml/stats')
def ml_stats():
    """API para estatísticas dos modelos ML"""
    try:
        if not ML_SYSTEM_AVAILABLE:
            return jsonify({"success": False, "error": "Sistema de ML não disponível"})
        
        stats = ml_system.get_model_stats()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas ML: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"})

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """Processar frame da câmera para reconhecimento LIBRAS"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                "success": False,
                "error": "Dados de imagem não fornecidos"
            })
        
        # Extract base64 image data
        image_data = data['image']
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Simulate letter recognition for now
        # In a real implementation, this would use a trained ML model
        recognized_letter = simulate_letter_recognition(image_data)
        
        return jsonify({
            "success": True,
            "letter": recognized_letter,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar frame: {e}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {e}"
        })

def simulate_letter_recognition(image_data):
    """Simular reconhecimento de letra LIBRAS"""
    # Para demonstração, vamos simular o reconhecimento
    # Em uma implementação real, aqui seria usado um modelo treinado
    
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    
    # Simular detecção baseada em timestamp para variedade
    timestamp = int(time.time() * 10) % len(letters)
    return letters[timestamp]

# ===== FUNÇÕES DE RECONHECIMENTO =====
def recognize_landmarks_against_saved_gestures(landmarks):
    """
    Reconhece landmarks comparando com gestos salvos
    
    Args:
        landmarks: Lista de 21 pontos com coordenadas x, y, z
        
    Returns:
        Dict com letra e similaridade ou None se não reconhecido
    """
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return None
        
        saved_gestures = gesture_manager.get_all_gestures()
        if not saved_gestures:
            return None
        
        best_match = None
        highest_similarity = 0
        similarity_threshold = 0.50  # 50% de similaridade mínima
        detailed_results = []
        
        for letter, gesture_data in saved_gestures.items():
            saved_landmarks = gesture_data['landmarks']
            analysis_result = calculate_landmark_similarity(landmarks, saved_landmarks)
            
            # Extrair similaridade do resultado detalhado
            similarity = analysis_result["similarity"] if isinstance(analysis_result, dict) else analysis_result
            
            # Salvar resultado detalhado para debug
            detailed_results.append({
                'letter': letter,
                'similarity': similarity,
                'analysis': analysis_result if isinstance(analysis_result, dict) else None
            })
            
            if similarity > highest_similarity and similarity > similarity_threshold:
                highest_similarity = similarity
                best_match = {
                    'letter': letter,
                    'similarity': similarity,
                    'quality': gesture_data['quality'],
                    'detailed_analysis': analysis_result if isinstance(analysis_result, dict) else None,
                    'all_comparisons': detailed_results  # Para debug completo
                }
        
        return best_match
        
    except Exception as e:
        logger.error(f"Erro no reconhecimento: {e}")
        return None

def calculate_landmark_similarity(landmarks1, landmarks2):
    """
    Calcula similaridade detalhada entre dois conjuntos de landmarks
    
    Args:
        landmarks1: Primeiro conjunto de landmarks
        landmarks2: Segundo conjunto de landmarks
        
    Returns:
        dict: Resultado detalhado com similaridade e análise por pontos
    """
    try:
        if len(landmarks1) != 21 or len(landmarks2) != 21:
            return {"similarity": 0.0, "point_analysis": [], "total_distance": float('inf')}
        
        point_analysis = []
        total_distance = 0.0
        weighted_distance = 0.0
        
        # Pesos para diferentes pontos da mão (pontos mais importantes têm peso maior)
        point_weights = {
            0: 1.5,   # Pulso (muito importante para orientação)
            4: 1.3,   # Ponta do polegar
            8: 1.3,   # Ponta do indicador
            12: 1.3,  # Ponta do médio
            16: 1.3,  # Ponta do anelar
            20: 1.3,  # Ponta do mindinho
            # Articulações importantes
            5: 1.2, 9: 1.2, 13: 1.2, 17: 1.2,  # Base dos dedos
            # Outras articulações
            1: 1.0, 2: 1.0, 3: 1.0,  # Polegar
            6: 1.0, 7: 1.0,          # Indicador
            10: 1.0, 11: 1.0,        # Médio
            14: 1.0, 15: 1.0,        # Anelar
            18: 1.0, 19: 1.0         # Mindinho
        }
        
        # Analisar cada ponto individualmente
        for i in range(21):
            p1 = landmarks1[i]
            p2 = landmarks2[i]
            weight = point_weights.get(i, 1.0)
            
            # Calcular distância euclidiana 3D
            distance_3d = ((p1['x'] - p2['x']) ** 2 + 
                          (p1['y'] - p2['y']) ** 2 + 
                          (p1['z'] - p2['z']) ** 2) ** 0.5
            
            # Calcular distância 2D (para gestos planos)
            distance_2d = ((p1['x'] - p2['x']) ** 2 + 
                          (p1['y'] - p2['y']) ** 2) ** 0.5
            
            # Usar a menor distância (mais tolerante)
            distance = min(distance_3d, distance_2d * 1.1)  # Leve penalidade para 2D
            
            # Classificar qualidade do match do ponto
            point_quality = "excelente" if distance < 0.05 else \
                           "bom" if distance < 0.1 else \
                           "aceitável" if distance < 0.2 else \
                           "ruim"
            
            point_analysis.append({
                "point_id": i,
                "distance": distance,
                "distance_3d": distance_3d,
                "distance_2d": distance_2d,
                "weight": weight,
                "quality": point_quality,
                "coordinates_saved": {"x": p2['x'], "y": p2['y'], "z": p2['z']},
                "coordinates_current": {"x": p1['x'], "y": p1['y'], "z": p1['z']}
            })
            
            total_distance += distance
            weighted_distance += distance * weight
        
        # Calcular similaridades
        avg_distance = total_distance / 21
        weighted_avg_distance = weighted_distance / sum(point_weights.values())
        
        # Converter para similaridade (0-1)
        max_distance = 0.8  # Distância máxima considerada (ajustado empiricamente)
        similarity = max(0.0, 1.0 - (weighted_avg_distance / max_distance))
        
        # Análise estatística dos pontos
        excellent_points = sum(1 for p in point_analysis if p["quality"] == "excelente")
        good_points = sum(1 for p in point_analysis if p["quality"] == "bom")
        acceptable_points = sum(1 for p in point_analysis if p["quality"] == "aceitável")
        bad_points = sum(1 for p in point_analysis if p["quality"] == "ruim")
        
        return {
            "similarity": similarity,
            "point_analysis": point_analysis,
            "total_distance": total_distance,
            "avg_distance": avg_distance,
            "weighted_avg_distance": weighted_avg_distance,
            "statistics": {
                "excellent_points": excellent_points,
                "good_points": good_points,
                "acceptable_points": acceptable_points,
                "bad_points": bad_points,
                "match_percentage": (excellent_points + good_points) / 21 * 100
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no cálculo de similaridade: {e}")
        return {"similarity": 0.0, "point_analysis": [], "total_distance": float('inf')}

# ===== ROTAS DE SISTEMA =====
@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout do usuário"""
    username = session.get('username', 'Usuário')
    session.clear()
    logger.info(f"Usuário deslogado: {username}")
    return jsonify({"success": True, "message": "Logout realizado com sucesso"})

# ===== APIs DE GESTÃO DE GESTOS =====
@app.route('/api/save_gesture', methods=['POST'])
def save_gesture():
    """Salva um gesto capturado pelo administrador"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({"success": False, "error": "Sistema de gestos não disponível"}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dados não fornecidos"}), 400
        
        letter = data.get('letter', '').upper()
        landmarks = data.get('landmarks', [])
        quality = data.get('quality', 0)
        
        # Validar dados
        if not letter or len(letter) != 1:
            return jsonify({"success": False, "error": "Letra inválida"}), 400
        
        if not landmarks or len(landmarks) != 21:
            return jsonify({"success": False, "error": "Landmarks inválidos - deve ter 21 pontos"}), 400
        
        if not 0 <= quality <= 100:
            return jsonify({"success": False, "error": "Qualidade deve estar entre 0 e 100"}), 400
        
        # Salvar gesto
        success = gesture_manager.save_gesture(letter, landmarks, quality)
        
        if success:
            logger.info(f"Gesto da letra {letter} salvo com qualidade {quality}%")
            return jsonify({"success": True, "message": f"Gesto da letra {letter} salvo com sucesso"})
        else:
            return jsonify({"success": False, "error": "Erro ao salvar gesto"}), 500
            
    except Exception as e:
        logger.error(f"Erro ao salvar gesto: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {e}"}), 500

@app.route('/api/get_gestures', methods=['GET'])
def get_gestures():
    """Recupera todos os gestos salvos"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({})
        
        gestures = gesture_manager.get_all_gestures()
        return jsonify(gestures)
        
    except Exception as e:
        logger.error(f"Erro ao recuperar gestos: {e}")
        return jsonify({}), 500

@app.route('/api/get_gesture/<letter>', methods=['GET'])
def get_gesture(letter):
    """Recupera um gesto específico"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({"success": False, "error": "Sistema de gestos não disponível"}), 500
        
        gesture = gesture_manager.get_gesture(letter.upper())
        
        if gesture:
            return jsonify({"success": True, "gesture": gesture})
        else:
            return jsonify({"success": False, "error": "Gesto não encontrado"}), 404
            
    except Exception as e:
        logger.error(f"Erro ao recuperar gesto da letra {letter}: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {e}"}), 500

@app.route('/api/delete_gesture/<letter>', methods=['DELETE'])
def delete_gesture(letter):
    """Remove um gesto específico"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({"success": False, "error": "Sistema de gestos não disponível"}), 500
        
        success = gesture_manager.delete_gesture(letter.upper())
        
        if success:
            logger.info(f"Gesto da letra {letter} removido")
            return jsonify({"success": True, "message": f"Gesto da letra {letter} removido"})
        else:
            return jsonify({"success": False, "error": "Gesto não encontrado"}), 404
            
    except Exception as e:
        logger.error(f"Erro ao remover gesto da letra {letter}: {e}")
        return jsonify({"success": False, "error": f"Erro interno: {e}"}), 500

@app.route('/api/recognize_gesture', methods=['POST'])
def recognize_gesture():
    """Reconhece um gesto usando sistema híbrido (tradicional + ML)"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            logger.error("Sistema de gestos não disponível")
            return jsonify({"success": False, "error": "Sistema de gestos não disponível"}), 500
        
        data = request.get_json()
        if not data:
            logger.error("Dados não fornecidos na requisição")
            return jsonify({"success": False, "error": "Dados não fornecidos"}), 400
        
        landmarks = data.get('landmarks', [])
        collect_for_ml = data.get('collect_for_ml', True)  # Coletar para ML por padrão
        
        if not landmarks or len(landmarks) != 21:
            logger.error(f"Landmarks inválidos: {len(landmarks) if landmarks else 0} pontos")
            return jsonify({"success": False, "error": "Landmarks inválidos - deve ter 21 pontos"}), 400
        
        logger.info(f"Reconhecendo gesto com {len(landmarks)} landmarks")
        
        # Reconhecimento híbrido
        if ML_SYSTEM_AVAILABLE and ml_system:
            result = gesture_manager.recognize_gesture_hybrid(landmarks, ml_system)
        else:
            # Fallback para reconhecimento tradicional usando método híbrido sem ML
            result = gesture_manager.recognize_gesture_hybrid(landmarks, None)
            if not result:
                result = {
                    'traditional': None,
                    'ml': None,
                    'final': None,
                    'confidence': 0,
                    'method': 'traditional'
                }
        
        logger.info(f"Resultado do reconhecimento: {result}")
        
        if result['final']:
            # Atualizar estatísticas
            gesture_manager.update_recognition_stats(result['final'])
            
            # Coletar exemplo para ML (se reconhecimento foi bem-sucedido e confiança alta)
            if collect_for_ml and ML_SYSTEM_AVAILABLE and ml_system and result['confidence'] > 0.7:
                try:
                    # Obter user_id se logado
                    user_id = None
                    if 'username' in session and DATABASE_AVAILABLE:
                        try:
                            db = LibrasDatabase()
                            user_result = db.get_user(session['username'])
                            if user_result:
                                user_id = user_result[0]
                        except Exception as db_e:
                            logger.warning(f"Erro ao obter user_id: {db_e}")
                    
                    ml_system.collect_gesture_example(
                        letter=result['final'],
                        landmarks=landmarks,
                        user_id=user_id,
                        confidence=result['confidence'],
                        source='recognition'
                    )
                    logger.info(f"Exemplo ML coletado para letra {result['final']}")
                except Exception as ml_e:
                    logger.warning(f"Erro ao coletar exemplo ML: {ml_e}")
            
            logger.info(f"Gesto reconhecido: {result['final']} com confiança {result['confidence']:.3f}")
            return jsonify({
                "success": True, 
                "result": {
                    "letter": result['final'],
                    "similarity": result['confidence'],
                    "method": result['method'],
                    "detailed_analysis": result.get('detailed_analysis', {})
                }
            })
        else:
            logger.info("Nenhuma letra reconhecida")
            return jsonify({
                "success": False, 
                "message": "Nenhuma letra reconhecida",
                "debug_info": {
                    "traditional_result": result.get('traditional'),
                    "ml_result": result.get('ml'),
                    "method": result.get('method', 'none')
                }
            })
            
    except Exception as e:
        logger.error(f"Erro ao reconhecer gesto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Erro interno: {e}"}), 500

@app.route('/api/export_gestures', methods=['GET'])
def export_gestures():
    """Exporta todos os gestos para backup"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({"error": "Sistema de gestos não disponível"}), 500
        
        export_data = gesture_manager.export_gestures()
        
        # Criar resposta como arquivo JSON
        response = app.response_class(
            response=json.dumps(export_data, indent=2),
            status=200,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=libras_gestures_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao exportar gestos: {e}")
        return jsonify({"error": f"Erro interno: {e}"}), 500

@app.route('/api/gesture_analytics', methods=['GET'])
def gesture_analytics():
    """Retorna estatísticas de uso dos gestos"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({})
        
        analytics = gesture_manager.get_analytics()
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Erro ao recuperar estatísticas: {e}")
        return jsonify({}), 500

@app.route('/api/gesture_sync_info', methods=['GET'])
def gesture_sync_info():
    """Retorna informações de sincronização dos gestos"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({"error": "Sistema de gestos não disponível"}), 500
        
        sync_info = gesture_manager.get_gesture_sync_info()
        return jsonify(sync_info)
        
    except Exception as e:
        logger.error(f"Erro ao obter info de sincronização: {e}")
        return jsonify({"error": f"Erro interno: {e}"}), 500

@app.route('/api/refresh_gestures', methods=['POST'])
def refresh_gestures():
    """Força o recarregamento dos gestos"""
    try:
        if not GESTURE_MANAGER_AVAILABLE or not gesture_manager:
            return jsonify({"error": "Sistema de gestos não disponível"}), 500
        
        # Invalidar cache e recarregar
        gesture_manager.invalidate_cache()
        gestures = gesture_manager.get_all_gestures()
        
        return jsonify({
            "success": True,
            "message": "Gestos recarregados com sucesso",
            "total_gestures": len(gestures),
            "letters": list(gestures.keys())
        })
        
    except Exception as e:
        logger.error(f"Erro ao recarregar gestos: {e}")
        return jsonify({"error": f"Erro interno: {e}"}), 500

@app.route('/debug-recognition')
def debug_recognition():
    """Página de debug para problemas de reconhecimento"""
    return render_template('debug-recognition.html')

@app.route('/fix-recognition')
def fix_recognition():
    """Página para ajustar configurações de reconhecimento"""
    return render_template('fix-recognition.html')

@app.route('/test-game-integration')
def test_game_integration():
    """Página para testar integração jogo-reconhecedor"""
    return render_template('test-game-integration.html')

@app.route('/system-updated')
def system_updated():
    """Página de confirmação de atualizações do sistema"""
    return render_template('system-updated.html')

@app.route('/debug-isolation')
def debug_isolation():
    """Página de debug para isolar problema de reconhecimento"""
    return render_template('debug-isolation.html')

@app.route('/test-apis')
def test_apis():
    """Página de teste das APIs"""
    return render_template('test-apis.html')

@app.route('/test-optimized')
def test_optimized():
    """Página de teste do reconhecedor otimizado"""
    return render_template('test-optimized.html')

@app.route('/test-simple')
def test_simple():
    """Página de teste simples"""
    return render_template('test-simple.html')

@app.route('/static/dados_libras.csv')
def serve_csv():
    """Serve o arquivo CSV de dados de libras"""
    try:
        return send_file('dados_libras.csv', 
                        mimetype='text/csv',
                        as_attachment=False,
                        download_name='dados_libras.csv')
    except Exception as e:
        logger.error(f"Erro ao servir CSV: {e}")
        abort(404)

@app.route('/health')
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "recognition_enabled": RECOGNITION_ENABLED,
        "database_available": DATABASE_AVAILABLE,
        "words_available": WORDS_AVAILABLE
    })

# ===== TRATAMENTO DE ERROS =====
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Página não encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Erro interno do servidor"), 500

# ===== INICIALIZAÇÃO =====
if __name__ == '__main__':
    # Criar diretório de templates se não existir
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Configurações para produção
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Executar aplicação
    app.run(host='0.0.0.0', port=port, debug=debug_mode)