# ===== APLICAÇÃO WEB FLASK PARA LIBRAS =====
import os
import json
import time
import cv2
import numpy as np
import mediapipe as mp
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, abort
from flask_session import Session
from sklearn.ensemble import RandomForestClassifier
import base64
from io import BytesIO
from PIL import Image
import threading
import logging
from flask_cors import CORS

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

# ===== CONFIGURAÇÃO DA APLICAÇÃO =====
app = Flask(__name__)
app.secret_key = 'libras_web_app_2024_secret_key'  # Mudar em produção
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
Session(app)

# Habilitar CORS para todas as rotas
CORS(app, supports_credentials=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== INICIALIZAÇÃO DE COMPONENTES =====
try:
    if DATABASE_AVAILABLE:
        db = LibrasDatabase()
        logger.info("Banco de dados conectado com sucesso")
    else:
        db = None
        logger.warning("Banco de dados não disponível")
except Exception as e:
    DATABASE_AVAILABLE = False
    db = None
    logger.error(f"Erro ao conectar banco de dados: {e}")

# Configuração MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ===== CLASSE PARA PROCESSAMENTO ML =====
class LibrasMLProcessor:
    def __init__(self):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.3
        )
        self.model = None
        self.letters_data = []
        self.setup_model()
    
    def setup_model(self):
        """Configura o modelo de machine learning"""
        try:
            # Dados de treinamento básicos (simplificado para web)
            dados_path = 'dados_libras.csv'
            if os.path.exists(dados_path):
                dados = pd.read_csv(dados_path)
                if 'letter' in dados.columns:
                    X = dados.drop(['letter'], axis=1)
                    y = dados['letter']
                    
                    self.model = RandomForestClassifier(n_estimators=20, random_state=42)
                    self.model.fit(X, y)
                    logger.info("Modelo ML carregado com dados CSV")
                else:
                    logger.warning("Coluna 'letter' não encontrada no CSV")
                    self.create_dummy_model()
            else:
                logger.warning("Arquivo de dados não encontrado, usando modelo simulado")
                self.create_dummy_model()
        except Exception as e:
            logger.error(f"Erro ao configurar modelo ML: {e}")
            self.create_dummy_model()
    
    def create_dummy_model(self):
        """Cria um modelo simulado para demonstração"""
        # Criar dados sintéticos para demonstração
        import random
        from string import ascii_uppercase
        
        # Dados sintéticos (63 features para 26 letras)
        X_dummy = []
        y_dummy = []
        
        for letter in ascii_uppercase:
            for _ in range(10):  # 10 amostras por letra
                # Criar landmarks fictícios (63 features)
                features = [random.uniform(-1, 1) for _ in range(63)]
                X_dummy.append(features)
                y_dummy.append(letter)
        
        self.model = RandomForestClassifier(n_estimators=20, random_state=42)
        self.model.fit(X_dummy, y_dummy)
        logger.info("Modelo ML simulado criado com sucesso")
    
    def extract_landmarks(self, frame):
        """Extrai landmarks da mão do frame"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                landmarks = []
                for hand_landmarks in results.multi_hand_landmarks:
                    for landmark in hand_landmarks.landmark:
                        landmarks.extend([landmark.x, landmark.y, landmark.z])
                
                # Normalizar para 63 features (21 pontos * 3 coordenadas)
                while len(landmarks) < 63:
                    landmarks.append(0.0)
                
                return landmarks[:63]
            
            return [0.0] * 63
        except Exception as e:
            logger.error(f"Erro ao extrair landmarks: {e}")
            return [0.0] * 63
    
    def predict_letter(self, landmarks):
        """Prediz a letra baseada nos landmarks"""
        try:
            if self.model and landmarks:
                prediction = self.model.predict([landmarks])
                confidence = max(self.model.predict_proba([landmarks])[0])
                return prediction[0], confidence
            return None, 0.0
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            return None, 0.0

# Instância global do processador ML
ml_processor = LibrasMLProcessor()

# ===== ROTAS PRINCIPAIS =====
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Sistema de login"""
    if request.method == 'POST':
        try:
            # Verificar se é JSON ou form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            username = data.get('username', '').strip()
            
            if not username:
                return jsonify({'success': False, 'message': 'Nome de usuário obrigatório'}), 400
            
            # Verificar se usuário existe ou criar novo
            if DATABASE_AVAILABLE and db:
                try:
                    user_id = db.get_user_id(username)
                    if not user_id:
                        user_id = db.create_user(username)
                    
                    session['user_id'] = user_id
                    session['username'] = username
                    logger.info(f"Usuário {username} logado com sucesso")
                except Exception as db_error:
                    logger.error(f"Erro no banco de dados: {db_error}")
                    # Continuar sem banco
                    session['username'] = username
                    session['user_id'] = 1
            else:
                # Modo sem banco de dados
                session['username'] = username
                session['user_id'] = 1
            
            return jsonify({'success': True, 'message': f'Bem-vindo, {username}!'})
        
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    
    return render_template('login.html')

@app.route('/game')
def game():
    """Página do jogo"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('game.html', username=session['username'])

@app.route('/statistics')
def statistics():
    """Página de estatísticas"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    stats = {}
    if DATABASE_AVAILABLE and 'user_id' in session:
        try:
            stats = db.get_user_statistics(session['user_id'])
        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas: {e}")
    
    return render_template('statistics.html', stats=stats, username=session['username'])

@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('index'))

# ===== API ENDPOINTS =====
@app.route('/api/health')
def health_check():
    """Endpoint de saúde da aplicação"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': DATABASE_AVAILABLE,
        'ml_model': ml_processor.model is not None
    })

@app.route('/api/words/<difficulty>')
def get_words(difficulty):
    """Retorna palavras por dificuldade"""
    try:
        word_lists = {
            'iniciante': palavras_iniciante,
            'intermediario': palavras,
            'avancado': palavras_avancado,
            'expert': palavras_expert
        }
        
        words = word_lists.get(difficulty, palavras_iniciante)
        return jsonify({'success': True, 'words': words})
    
    except Exception as e:
        logger.error(f"Erro ao buscar palavras: {e}")
        return jsonify({'success': False, 'message': 'Erro ao carregar palavras'})

@app.route('/api/validate_word', methods=['POST'])
def validate_word():
    """Valida palavra customizada para modo soletração"""
    try:
        data = request.get_json()
        word = data.get('word', '').upper().strip()
        difficulty = data.get('difficulty', 'iniciante')
        
        if not word:
            return jsonify({'success': False, 'message': 'Palavra não fornecida'})
        
        if not word.isalpha():
            return jsonify({'success': False, 'message': 'Palavra deve conter apenas letras'})
        
        # Configurações de dificuldade (baseado no código original)
        difficulty_configs = {
            'iniciante': {'letters': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')},  # Todas as letras
            'intermediario': {'letters': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')},
            'avancado': {'letters': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')},
            'expert': {'letters': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}
        }
        
        config = difficulty_configs.get(difficulty, difficulty_configs['iniciante'])
        allowed_letters = set(config['letters'])
        
        # Filtrar palavra baseado na dificuldade
        filtered_word = ''.join([letter for letter in word if letter in allowed_letters])
        
        if not filtered_word:
            return jsonify({
                'success': False, 
                'message': f'A palavra não contém letras permitidas na dificuldade {difficulty}'
            })
        
        response_data = {'success': True, 'filtered_word': filtered_word}
        
        if filtered_word != word:
            response_data['warning'] = f'Palavra adaptada de "{word}" para "{filtered_word}"'
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Erro ao validar palavra: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """Processa frame da câmera para reconhecimento"""
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'Imagem não fornecida'})
        
        # Decodificar imagem base64
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64,
        image_bytes = base64.b64decode(image_data)
        
        # Converter para numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'success': False, 'message': 'Erro ao decodificar imagem'})
        
        # Processar com ML
        landmarks = ml_processor.extract_landmarks(frame)
        letter, confidence = ml_processor.predict_letter(landmarks)
        
        return jsonify({
            'success': True,
            'letter': letter,
            'confidence': float(confidence) if confidence else 0.0,
            'has_hand': len([x for x in landmarks if x != 0.0]) > 0
        })
    
    except Exception as e:
        logger.error(f"Erro ao processar frame: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Inicia uma nova sessão de jogo"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Usuário não logado'})
        
        data = request.get_json()
        game_mode = data.get('mode', 'normal')  # normal, soletracao, desafio
        difficulty = data.get('difficulty', 'iniciante')
        custom_word = data.get('custom_word', '')  # Para modo soletração
        
        session_data = {
            'mode': game_mode,
            'difficulty': difficulty,
            'start_time': time.time()
        }
        
        if game_mode == 'soletracao' and custom_word:
            session_data['custom_word'] = custom_word.upper()
        
        if DATABASE_AVAILABLE and db:
            session_id = db.start_game_session(session['user_id'], game_mode, difficulty)
            session['current_session_id'] = session_id
            session_data['session_id'] = session_id
        else:
            session['current_session_id'] = int(time.time())
            session_data['session_id'] = session['current_session_id']
        
        session['game_session_data'] = session_data
        
        return jsonify({'success': True, 'session_data': session_data})
    
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

@app.route('/api/end_session', methods=['POST'])
def end_session():
    """Finaliza a sessão de jogo"""
    try:
        if 'current_session_id' not in session:
            return jsonify({'success': False, 'message': 'Nenhuma sessão ativa'})
        
        data = request.get_json()
        stats = data.get('stats', {})
        
        if DATABASE_AVAILABLE and 'user_id' in session:
            db.end_game_session(
                session['current_session_id'],
                stats.get('words_completed', 0),
                stats.get('total_letters', 0),
                stats.get('correct_letters', 0),
                stats.get('accuracy', 0)
            )
        
        del session['current_session_id']
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Erro ao finalizar sessão: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

@app.route('/api/user_stats')
def get_user_stats():
    """Retorna estatísticas do usuário"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Usuário não logado'})
        
        stats = {}
        if DATABASE_AVAILABLE:
            stats = db.get_user_statistics(session['user_id'])
        
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

# ===== HANDLERS DE ERRO =====
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message="Página não encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="Erro interno do servidor"), 500

# ===== ROTAS PARA VÍDEOS DE DEMONSTRAÇÃO =====
@app.route('/videos/<letra>')
def serve_video(letra):
    """Serve vídeos de demonstração das letras"""
    try:
        # Validar letra (apenas A-Z)
        letra = letra.upper()
        if len(letra) != 1 or not letra.isalpha():
            abort(404)
        
        # Construir caminho do vídeo
        video_filename = f"Letra_{letra}.mp4"
        video_path = os.path.join('Videos', video_filename)
        
        # Verificar se o arquivo existe
        if not os.path.exists(video_path):
            logger.warning(f"Vídeo não encontrado: {video_path}")
            abort(404)
        
        return send_file(video_path, mimetype='video/mp4')
    
    except Exception as e:
        logger.error(f"Erro ao servir vídeo {letra}: {e}")
        abort(500)

@app.route('/api/get_video_demo/<letra>')
def get_video_demo_info(letra):
    """Retorna informações sobre o vídeo de demonstração de uma letra"""
    try:
        letra = letra.upper()
        if len(letra) != 1 or not letra.isalpha():
            return jsonify({"success": False, "message": "Letra inválida"}), 400
        
        video_filename = f"Letra_{letra}.mp4"
        video_path = os.path.join('Videos', video_filename)
        
        if os.path.exists(video_path):
            return jsonify({
                "success": True,
                "letter": letra,
                "video_url": f"/videos/{letra}",
                "video_available": True
            })
        else:
            return jsonify({
                "success": True,
                "letter": letra,
                "video_available": False,
                "message": f"Vídeo não disponível para a letra {letra}"
            })
    
    except Exception as e:
        logger.error(f"Erro ao obter info do vídeo {letra}: {e}")
        return jsonify({"success": False, "message": "Erro interno"}), 500

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