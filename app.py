# ===== APLICAÇÃO WEB FLASK PARA LIBRAS (Versão Deploy) =====
import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, abort
from flask_session import Session
import threading
import logging

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

# Variáveis globais para o jogo
current_word = ""
current_mode = "iniciante"
game_active = False
score = 0
words_completed = []

# ===== FUNÇÕES AUXILIARES =====
def get_video_path(letra):
    """Obter caminho do vídeo para uma letra específica"""
    video_path = os.path.join('Videos', f'Letra_{letra.upper()}.mp4')
    if os.path.exists(video_path):
        return video_path
    return None

def get_random_word(mode="iniciante"):
    """Obter palavra aleatória baseada no modo"""
    import random
    
    if mode == "iniciante":
        return random.choice(palavras_iniciante)
    elif mode == "avancado":
        return random.choice(palavras_avancado)
    elif mode == "expert":
        return random.choice(palavras_expert)
    else:
        return random.choice(palavras)

# ===== ROTAS PRINCIPAIS =====
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if username:
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            logger.info(f"Usuário logado: {username}")
            return redirect(url_for('game'))
        else:
            return render_template('login.html', error="Nome de usuário é obrigatório")
    
    return render_template('login.html')

@app.route('/game')
def game():
    """Página principal do jogo"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('game.html', 
                         username=session['username'],
                         recognition_enabled=RECOGNITION_ENABLED)

@app.route('/statistics')
def statistics():
    """Página de estatísticas"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    stats = {}
    if DATABASE_AVAILABLE:
        try:
            db = LibrasDatabase()
            stats = db.get_user_statistics(session['username'])
        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas: {e}")
            stats = {"error": "Não foi possível carregar as estatísticas"}
    else:
        stats = {"info": "Sistema de estatísticas não disponível"}
    
    return render_template('statistics.html', stats=stats)

# ===== API ROUTES =====
@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Iniciar novo jogo"""
    global current_word, current_mode, game_active, score, words_completed
    
    data = request.get_json()
    mode = data.get('mode', 'iniciante')
    
    current_mode = mode
    current_word = get_random_word(mode)
    game_active = True
    score = 0
    words_completed = []
    
    return jsonify({
        "success": True,
        "word": current_word,
        "mode": mode,
        "recognition_enabled": RECOGNITION_ENABLED
    })

@app.route('/api/next_word', methods=['POST'])
def next_word():
    """Próxima palavra do jogo"""
    global current_word, words_completed
    
    if game_active:
        # Adicionar palavra atual como completada
        if current_word:
            words_completed.append(current_word)
        
        # Obter próxima palavra
        current_word = get_random_word(current_mode)
        
        return jsonify({
            "success": True,
            "word": current_word,
            "completed_words": len(words_completed)
        })
    
    return jsonify({"success": False, "error": "Jogo não está ativo"})

@app.route('/api/check_letter', methods=['POST'])
def check_letter():
    """Verificar letra (simulado sem reconhecimento)"""
    data = request.get_json()
    letter = data.get('letter', '').upper()
    
    if not current_word:
        return jsonify({"success": False, "error": "Nenhuma palavra ativa"})
    
    # Simulação: sempre retorna sucesso para demonstração
    if letter in current_word:
        return jsonify({
            "success": True,
            "letter": letter,
            "word": current_word,
            "correct": True,
            "message": f"Correto! A letra '{letter}' está em '{current_word}'"
        })
    else:
        return jsonify({
            "success": True,
            "letter": letter,
            "word": current_word,
            "correct": False,
            "message": f"A letra '{letter}' não está em '{current_word}'"
        })

@app.route('/api/game_status')
def game_status():
    """Status atual do jogo"""
    return jsonify({
        "active": game_active,
        "word": current_word if game_active else "",
        "mode": current_mode,
        "score": score,
        "completed_words": len(words_completed),
        "recognition_enabled": RECOGNITION_ENABLED
    })

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

# ===== ROTAS DE SISTEMA =====
@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout do usuário"""
    username = session.get('username', 'Usuário')
    session.clear()
    logger.info(f"Usuário deslogado: {username}")
    return jsonify({"success": True, "message": "Logout realizado com sucesso"})

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