# ===== IMPORTS =====
import warnings
warnings.filterwarnings("ignore")
import sys
import os
import time
import random
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

from palavras import palavras, palavras_iniciante, palavras_avancado, palavras_expert

# Importar sistema de banco de dados
try:
    from database import LibrasDatabase
    from reports import ReportsDialog
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Aviso: Sistema de banco não disponível: {e}")
    DATABASE_AVAILABLE = False

# ===== FUNÇÃO AUXILIAR PARA RECURSOS =====
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ===== CLASSE PRINCIPAL DO APLICATIVO =====
class MainWindow(QWidget):
    # ===== CONFIGURAÇÕES E CONSTANTES =====
    VIDEO_MIN_SIZE = (800, 600)  # Resolução menor para melhor performance
    VIDEO_FPS = 15  # FPS mais baixo para processamento mais rápido
    VIDEO_PLAYBACK_FPS = 20
    DELAY_TIME = 2
    CHALLENGE_TIME = 60
    ML_ESTIMATORS = 20  # Menos estimadores para ML mais rápido
    MP_DETECTION_CONFIDENCE = 0.5  # Menor confiança para detecção mais rápida
    MP_TRACKING_CONFIDENCE = 0.3  # Menor confiança para tracking mais rápido
    FRAME_SKIP = 2  # Pular frames para acelerar processamento
    MAX_VIDEO_SCALE = 2.0
    
    # ===== NÍVEIS DE DIFICULDADE =====
    DIFFICULTY_LEVELS = {
        "INICIANTE": {
            "name": "Iniciante",
            "description": "Palavras simples • Tempo ilimitado • Com dicas visuais",
            "letters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "time_limit": None,
            "show_hints": True,
            "challenge_time": 180,
            "color": (0, 255, 0)
        },
        "INTERMEDIARIO": {
            "name": "Intermediário", 
            "description": "Palavras normais • Tempo moderado • Algumas dicas",
            "letters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "time_limit": 25,
            "show_hints": True,
            "challenge_time": 120,
            "color": (255, 255, 0)
        },
        "AVANCADO": {
            "name": "Avançado",
            "description": "Palavras compostas • Tempo limitado • Sem dicas",
            "letters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "time_limit": 20,
            "show_hints": False,
            "challenge_time": 90,
            "color": (255, 165, 0)
        },
        "EXPERT": {
            "name": "Expert",
            "description": "Frases completas • Tempo muito limitado • Sem ajuda",
            "letters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "time_limit": 15,
            "show_hints": False,
            "challenge_time": 60,
            "color": (255, 0, 0)
        }
    }
    
    # ===== INICIALIZAÇÃO =====
    def __init__(self):
        super().__init__()
        self.init_variables()
        self.init_ui()
        self.init_ml_model()
        self.connect_buttons()
        self.init_database()

    def init_ui(self):
        self.setWindowTitle("Reconhecimento de Letras em Libras")
        self.showMaximized()
        
        # ===== WIDGETS PRINCIPAIS =====
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(*self.VIDEO_MIN_SIZE)
        self.image_label.setStyleSheet("border: 2px solid gray; background-color: black;")
        
        self.text_label = QLabel("Letra: ")
        self.text_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333; padding: 5px; border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5;")
        self.soletra_label = QLabel("")
        
        self.input_word = QLineEdit()
        self.input_word.setPlaceholderText("Digite a palavra para soletrar")
        self.input_word.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_word.setStyleSheet("padding: 8px; font-size: 12px; border-radius: 4px; border: 2px solid #ccc; min-height: 25px; margin: 5px 0;")
        
        # ===== BOTÕES DE CONTROLE =====
        self.start_normal_btn = QPushButton("Reconhecimento Normal")
        self.start_normal_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.start_normal_btn.setMinimumHeight(40)
        
        self.start_soletra_btn = QPushButton("Iniciar Soletração")
        self.start_soletra_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.start_soletra_btn.setMinimumHeight(40)
        
        self.desafio_btn = QPushButton("Desafio")
        self.desafio_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.desafio_btn.setMinimumHeight(40)
        
        self.change_word_btn = QPushButton("Alterar Palavra")
        self.change_word_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.change_word_btn.setMinimumHeight(35)
        
        self.back_to_menu_btn = QPushButton("Voltar ao Menu Principal")
        self.back_to_menu_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.back_to_menu_btn.setMinimumHeight(35)
        
        self.finish_btn = QPushButton("Finalizar Programa")
        self.finish_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.finish_btn.setMinimumHeight(35)
        self.finish_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold; border-radius: 5px;")
        
        # ===== BOTÃO DE RELATÓRIOS =====
        self.reports_btn = QPushButton("📊 Ver Relatórios")
        self.reports_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.reports_btn.setMinimumHeight(35)
        self.reports_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; border-radius: 5px;")
        
        # ===== BOTÕES DE DIFICULDADE =====
        self.difficulty_btn = QPushButton(f"Dificuldade: {self.difficulty_config['name']}")
        self.difficulty_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.difficulty_btn.setMinimumHeight(35)
        self.difficulty_btn.clicked.connect(self.show_difficulty_selection)
        self.difficulty_btn.setStyleSheet(f"background-color: rgb{self.difficulty_config['color']}; font-weight: bold; border-radius: 5px; padding: 6px; font-size: 12px;")
        
        self.difficulty_buttons = {}
        for key, config in self.DIFFICULTY_LEVELS.items():
            btn = QPushButton(f"{config['name']}")
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setMinimumHeight(30)
            btn.clicked.connect(lambda checked, diff=key: self.select_difficulty(diff))
            btn.setStyleSheet(f"background-color: rgb{config['color']}; font-weight: bold; border-radius: 4px; margin: 2px; padding: 4px; font-size: 11px;")
            btn.hide()
            self.difficulty_buttons[key] = btn
        
        self.difficulty_info_label = QLabel("")
        self.difficulty_info_label.setAlignment(Qt.AlignCenter)
        self.difficulty_info_label.setWordWrap(True)
        self.difficulty_info_label.hide()
        
        # ===== ESTADOS INICIAIS DOS BOTÕES =====
        self.change_word_btn.setEnabled(False)
        self.back_to_menu_btn.setEnabled(False)
        self.back_to_menu_btn.hide()
        
        for btn in self.difficulty_buttons.values():
            btn.hide()
        self.difficulty_info_label.hide()
        
        # ===== LAYOUT PRINCIPAL =====
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        video_area_layout = QVBoxLayout()
        video_area_layout.setSpacing(10)
        
        video_layout = QHBoxLayout()
        video_layout.addStretch(1)
        video_layout.addWidget(self.image_label)
        video_layout.addStretch(1)
        
        video_area_layout.addLayout(video_layout, 1)
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(12)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        
        menu_title = QLabel("CONTROLES")
        menu_title.setAlignment(Qt.AlignCenter)
        menu_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; padding: 8px; border-bottom: 2px solid #ccc; margin-bottom: 10px;")
        sidebar_layout.addWidget(menu_title)
        
        input_label = QLabel("Digite a palavra:")
        input_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 10px;")
        sidebar_layout.addWidget(input_label)
        sidebar_layout.addWidget(self.input_word)
        
        game_info_label = QLabel("Informações:")
        game_info_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 15px;")
        sidebar_layout.addWidget(game_info_label)
        sidebar_layout.addWidget(self.text_label)
        
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet("font-size: 12px; color: #333; padding: 12px; border: 1px solid #ddd; border-radius: 6px; background-color: #f9f9f9; margin: 5px 0; line-height: 1.4;")
        self.results_label.setAlignment(Qt.AlignTop)
        self.results_label.setMinimumHeight(220)
        self.results_label.setMaximumHeight(350)
        self.results_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sidebar_layout.addWidget(self.results_label)
        
        game_modes_label = QLabel("Modos de Jogo:")
        game_modes_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 15px;")
        sidebar_layout.addWidget(game_modes_label)
        
        sidebar_layout.addWidget(self.start_normal_btn)
        sidebar_layout.addWidget(self.start_soletra_btn)
        sidebar_layout.addWidget(self.desafio_btn)
        
        settings_label = QLabel("Configurações:")
        settings_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 15px;")
        sidebar_layout.addWidget(settings_label)
        
        sidebar_layout.addWidget(self.difficulty_btn)
        
        difficulty_buttons_layout = QVBoxLayout()
        difficulty_buttons_layout.setSpacing(5)
        for btn in self.difficulty_buttons.values():
            difficulty_buttons_layout.addWidget(btn)
        sidebar_layout.addLayout(difficulty_buttons_layout)
        sidebar_layout.addWidget(self.difficulty_info_label)
        
        controls_label = QLabel("Controles:")
        controls_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 15px;")
        sidebar_layout.addWidget(controls_label)
        
        sidebar_layout.addWidget(self.change_word_btn)
        sidebar_layout.addWidget(self.back_to_menu_btn)
        
        sidebar_layout.addStretch()
        
        finish_label = QLabel("Sistema:")
        finish_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 15px;")
        sidebar_layout.addWidget(finish_label)
        sidebar_layout.addWidget(self.reports_btn)
        sidebar_layout.addWidget(self.finish_btn)
        
        main_layout.addLayout(video_area_layout, 2)
        main_layout.addLayout(sidebar_layout, 1)
        
        self.setLayout(main_layout)

    # ===== MODELO ML E MEDIAPIPE =====
    def init_ml_model(self):
        caminho_do_arquivo_csv = resource_path("dados_libras.csv")
        df = pd.read_csv(caminho_do_arquivo_csv)
        self.X = df.drop('label', axis=1)
        y = df['label']
        
        # Modelo mais leve para performance
        self.clf = RandomForestClassifier(
            n_estimators=self.ML_ESTIMATORS, 
            max_depth=10,  # Limitar profundidade
            min_samples_split=5,  # Reduzir overfitting
            min_samples_leaf=2,  # Acelerar predições
            random_state=42,
            n_jobs=1  # Usar apenas 1 thread para evitar overhead
        )
        self.clf.fit(self.X, y)
        
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configuração otimizada do MediaPipe
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=1, 
            min_detection_confidence=self.MP_DETECTION_CONFIDENCE,
            min_tracking_confidence=self.MP_TRACKING_CONFIDENCE,
            model_complexity=0  # Modelo mais simples para velocidade
        )

    # ===== INICIALIZAÇÃO DE VARIÁVEIS =====
    def init_variables(self):
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.mode = None
        self.last_frame = None
        
        self.current_difficulty = "INTERMEDIARIO"
        self.difficulty_config = self.DIFFICULTY_LEVELS[self.current_difficulty]
        self.letter_start_time = 0
        self.showing_difficulty_selection = False
        
        game_vars = {
            'palavra': "", 'letra_idx': 0, 'prep_time': 0,
            'waiting_prep': False, 'waiting_delay': False, 'delay_start': 0,
            'showing_video': False, 'video_cap': None, 'video_frame_count': 0, 'video_total_frames': 0,
            'desafio_ativo': False, 'palavra_atual': "", 'letra_idx_desafio': 0,
            'acertos': 0, 'inicio_desafio': 0, 'tempo_total': self.CHALLENGE_TIME
        }
        
        stats_vars = {
            'game_start_time': 0, 'total_letters': 0, 'correct_letters': 0,
            'words_completed': 0, 'letter_times': [], 'current_letter_start_time': 0, 'current_mode': ""
        }
        
        # Variáveis do banco de dados
        db_vars = {
            'db': None, 'current_user_id': None, 'current_session_id': None, 'current_word_id': None
        }
        
        # Variáveis de otimização de performance
        performance_vars = {
            'frame_count': 0, 'last_prediction': '', 'prediction_buffer': [], 
            'last_landmarks_time': 0, 'landmarks_cache': None
        }
        
        for var, value in {**game_vars, **stats_vars, **db_vars, **performance_vars}.items():
            setattr(self, var, value)

    # ===== CONEXÃO DOS BOTÕES =====
    def connect_buttons(self):
        self.start_soletra_btn.clicked.connect(self.start_soletrando)
        self.start_normal_btn.clicked.connect(self.start_normal)
        self.desafio_btn.clicked.connect(self.iniciar_desafio)
        self.change_word_btn.clicked.connect(self.change_word)
        self.back_to_menu_btn.clicked.connect(self.voltar_menu)
        self.finish_btn.clicked.connect(self.finish_program)
        self.reports_btn.clicked.connect(self.show_reports)

    # ===== INICIALIZAÇÃO DO BANCO DE DADOS =====
    def init_database(self):
        """Inicializa o banco de dados e configura usuário"""
        if not DATABASE_AVAILABLE:
            print("Sistema de banco de dados não disponível")
            return
        
        try:
            self.db = LibrasDatabase()
            self.setup_user()
            print("Banco de dados inicializado com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            self.db = None
    
    def setup_user(self):
        """Configura usuário padrão (pode ser expandido para login)"""
        if not self.db:
            return
        
        username = "usuario_padrao"  # Pode ser alterado para um sistema de login
        
        user = self.db.get_user(username)
        if user:
            self.current_user_id = user[0]
        else:
            self.current_user_id = self.db.create_user(username)

    # ===== GERENCIAMENTO DE ESTADOS =====
    def set_menu_state(self):
        self.input_word.setEnabled(True)
        self.start_soletra_btn.setEnabled(True)
        self.start_normal_btn.setEnabled(True)
        self.desafio_btn.setEnabled(True)
        self.change_word_btn.setEnabled(False)
        self.back_to_menu_btn.setEnabled(False)
        self.back_to_menu_btn.hide()
        self.finish_btn.setEnabled(True)
        self.finish_btn.show()

    def set_active_mode_state(self):
        self.input_word.setEnabled(False)
        self.start_soletra_btn.setEnabled(False)
        self.start_normal_btn.setEnabled(False)
        self.desafio_btn.setEnabled(False)
        self.back_to_menu_btn.setEnabled(True)
        self.back_to_menu_btn.show()
        self.finish_btn.setEnabled(False)
        self.finish_btn.hide()

    def set_video_mode_state(self):
        self.set_active_mode_state()
        self.change_word_btn.setEnabled(True)

    # ===== CONTROLE DE DIFICULDADE =====
    def show_difficulty_selection(self):
        self.showing_difficulty_selection = not self.showing_difficulty_selection
        
        for btn in self.difficulty_buttons.values():
            if self.showing_difficulty_selection:
                btn.show()
            else:
                btn.hide()
        
        if self.showing_difficulty_selection:
            self.difficulty_info_label.setText(f"Atual: {self.difficulty_config['name']}\n{self.difficulty_config['description']}")
            self.difficulty_info_label.show()
        else:
            self.difficulty_info_label.hide()

    def select_difficulty(self, difficulty_key):
        self.current_difficulty = difficulty_key
        self.difficulty_config = self.DIFFICULTY_LEVELS[difficulty_key]
        
        self.difficulty_btn.setText(f"Dificuldade: {self.difficulty_config['name']}")
        self.difficulty_btn.setStyleSheet(f"background-color: rgb{self.difficulty_config['color']}; font-weight: bold; border-radius: 5px; padding: 6px; font-size: 12px;")
        
        self.tempo_total = self.difficulty_config['challenge_time']
        
        self.show_difficulty_selection()
        
        self.soletra_label.setText(f"Dificuldade alterada para: {self.difficulty_config['name']}")

    # ===== VALIDAÇÃO DE DIFICULDADE =====
    def is_letter_allowed(self, letter):
        return letter.upper() in self.difficulty_config['letters']

    def filter_word_by_difficulty(self, word):
        allowed_letters = self.difficulty_config['letters']
        
        if self.current_difficulty == "AVANCADO":
            filtered_word = ''.join([char for char in word.upper() if char in allowed_letters or char == '-'])
            return filtered_word if any(char in allowed_letters for char in filtered_word) else None
        
        elif self.current_difficulty == "EXPERT":
            filtered_word = ''.join([char for char in word.upper() if char in allowed_letters or char == ' '])
            return filtered_word if any(char in allowed_letters for char in filtered_word) else None
        
        else:
            filtered_word = ''.join([char for char in word.upper() if char in allowed_letters])
            return filtered_word if filtered_word else None

    # ===== GERENCIAMENTO DE CÂMERA E VÍDEO =====
    def start_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "Erro", "Não foi possível acessar a câmera.")
                return False
            
            # Otimizações de performance da câmera
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.VIDEO_MIN_SIZE[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.VIDEO_MIN_SIZE[1])
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para reduzir latência
            
        self.timer.start(int(1000 / self.VIDEO_FPS))  # Converter para milissegundos
        return True

    def get_video_path(self, letra):
        video_paths = [
            f"Videos/Letra_{letra}.mp4",
            os.path.join(os.path.dirname(__file__), "..", "Videos", f"Letra_{letra}.mp4"),
            resource_path(f"Videos/Letra_{letra}.mp4")
        ]
        
        for path in video_paths:
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                return normalized_path
        
        return None

    def stop_camera(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        if self.video_cap and self.video_cap.isOpened():
            self.video_cap.release()
            self.video_cap = None
    
    def start_letter_video(self):
        if self.letra_idx >= len(self.palavra):
            return
            
        letra = self.palavra[self.letra_idx]
        video_path = self.get_video_path(letra)
        
        if not video_path:
            print(f"DEBUG: Vídeo não encontrado para letra {letra}, pulando para detecção")
            self.start_detection_after_video()
            return
            
        self.video_cap = cv2.VideoCapture(video_path)
        if not self.video_cap.isOpened():
            print(f"DEBUG: Não foi possível abrir o vídeo: {video_path}")
            self.start_detection_after_video()
            return
            
        self.showing_video = True
        self.video_frame_count = 0
        self.video_total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"DEBUG: Vídeo carregado com sucesso! Total de frames: {self.video_total_frames}")
        
        self.soletra_label.setText(f"Demonstracao da letra {letra} - {self.palavra}")
        self.set_video_mode_state()
        
        self.timer.start(self.VIDEO_PLAYBACK_FPS)
    
    def start_detection_after_video(self):
        self.showing_video = False
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
            
        if not self.start_camera():
            return
        
        self.letter_start_time = 0
        # Inicializar cronômetro da letra atual
        self.current_letter_start_time = time.time()
        
        letra = self.palavra[self.letra_idx]
        if self.difficulty_config['show_hints']:
            self.soletra_label.setText(f"Agora reproduza a letra {letra} - {self.palavra} (Nível: {self.difficulty_config['name']})")
        else:
            self.soletra_label.setText(f"Reproduza a letra {letra} (Nível: {self.difficulty_config['name']})")

    # ===== FUNÇÕES DE RESET E NAVEGAÇÃO =====
    def reset_to_menu(self):
        self.stop_camera()
        self.mode = None
        self.desafio_ativo = False
        self.showing_video = False
        self.soletra_label.setText("")
        self.text_label.setText("Letra: ")
        self.set_menu_state()
        self.show_frame(np.zeros((480, 640, 3), dtype=np.uint8))

    # ===== MODOS DE JOGO =====
    def start_soletrando(self):
        palavra = self.input_word.text().upper().strip()
        if not palavra.isalpha():
            QMessageBox.warning(self, "Erro", "Digite uma palavra válida (apenas letras).")
            return
        
        palavra_filtrada = self.filter_word_by_difficulty(palavra)
        if not palavra_filtrada:
            allowed_letters = ", ".join(self.difficulty_config['letters'])
            QMessageBox.warning(self, "Erro", f"A palavra '{palavra}' não contém letras permitidas na dificuldade {self.difficulty_config['name']}.\n\nLetras permitidas: {allowed_letters}")
            return
        
        if palavra_filtrada != palavra:
            reply = QMessageBox.question(self, "Palavra Modificada", 
                f"A palavra original '{palavra}' foi adaptada para '{palavra_filtrada}' conforme a dificuldade {self.difficulty_config['name']}.\n\nContinuar?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
            
        self.mode = "soletra"
        self.palavra = palavra_filtrada
        self.letra_idx = 0
        self.waiting_prep = False
        self.prep_time = 0
        self.letter_start_time = 0
        
        self.reset_statistics()
        self.game_start_time = time.time()
        self.current_mode = "SOLETRAÇÃO"
        # Inicializar cronômetro da primeira letra
        self.current_letter_start_time = time.time()
        
        # Iniciar sessão no banco de dados
        if self.db and self.current_user_id:
            try:
                self.current_session_id = self.db.start_session(
                    self.current_user_id, 
                    "SOLETRAÇÃO", 
                    self.current_difficulty
                )
            except Exception as e:
                print(f"Erro ao iniciar sessão: {e}")
        
        self.start_letter_video()
        self.finish_btn.hide()

    def start_normal(self):
        if not self.start_camera():
            return
            
        self.mode = "normal"
        self.soletra_label.setText("Reconhecimento em tempo real")
        self.set_active_mode_state()

    def iniciar_desafio(self):           
        if not self.start_camera():
            return
            
        self.reset_statistics()
        self.game_start_time = time.time()
        self.current_mode = "DESAFIO"
        
        # Iniciar sessão no banco de dados
        if self.db and self.current_user_id:
            try:
                self.current_session_id = self.db.start_session(
                    self.current_user_id, 
                    "DESAFIO", 
                    self.current_difficulty
                )
            except Exception as e:
                print(f"Erro ao iniciar sessão: {e}")
            
        self.desafio_ativo = True
        self.acertos = 0
        self.inicio_desafio = time.time()
        self.nova_palavra_desafio()
        self.set_active_mode_state()

    def get_word_list_by_difficulty(self):
        word_lists = {
            "INICIANTE": palavras_iniciante,
            "AVANCADO": palavras_avancado, 
            "EXPERT": palavras_expert
        }
        return word_lists.get(self.current_difficulty, palavras)

    def nova_palavra_desafio(self):
        word_list = self.get_word_list_by_difficulty()
        attempts = 0
        max_attempts = 50
        
        while attempts < max_attempts:
            nova = random.choice(word_list).upper()
            nova_filtrada = self.filter_word_by_difficulty(nova)
            
            if nova_filtrada and nova_filtrada != getattr(self, "palavra_atual", "") and len(nova_filtrada) >= 2:
                self.palavra_atual = nova_filtrada
                break
            attempts += 1
        
        if attempts >= max_attempts:
            if self.current_difficulty == "INICIANTE":
                self.palavra_atual = "AEIOU"[:3]
            else:
                allowed = self.difficulty_config['letters']
                self.palavra_atual = ''.join(allowed[:min(3, len(allowed))])
        
        self.letra_idx_desafio = 0
        self.soletra_label.setText(f"Palavra: {'_' * len(self.palavra_atual)} | Acertos: {self.acertos}")

    def change_word(self):
        self.reset_to_menu()

    def voltar_menu(self):
        self.reset_statistics()
        self.reset_to_menu()

    def show_reports(self):
        """Mostra janela de relatórios do usuário"""
        if not DATABASE_AVAILABLE:
            QMessageBox.warning(self, "Erro", "Sistema de relatórios não disponível.\nVerifique se os módulos necessários estão instalados.")
            return
        
        if not self.db or not self.current_user_id:
            QMessageBox.warning(self, "Erro", "Banco de dados não disponível ou usuário não identificado.")
            return
        
        try:
            reports_dialog = ReportsDialog(self.current_user_id, self.db.db_path, self)
            reports_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir relatórios:\n{str(e)}")

    def finish_program(self):
        self.stop_camera()
        QApplication.quit()

    # ===== PROCESSAMENTO DE IMAGEM =====
    def get_frame(self):
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        return frame

    def predict_letter(self, landmarks):
        # Otimização: extrair apenas coordenadas essenciais (sem Z para economia)
        row = []
        for lm in landmarks.landmark:
            row.extend([lm.x, lm.y, lm.z])
        
        if len(row) == self.X.shape[1]:
            # Usar numpy diretamente ao invés de DataFrame para mais velocidade
            import numpy as np
            row_array = np.array([row])
            prediction = self.clf.predict(row_array)[0]
            
            # Buffer de predições para suavização
            self.prediction_buffer.append(prediction)
            if len(self.prediction_buffer) > 3:
                self.prediction_buffer.pop(0)
            
            # Retornar predição mais comum
            if len(self.prediction_buffer) >= 2:
                from collections import Counter
                most_common = Counter(self.prediction_buffer).most_common(1)
                if most_common:
                    return most_common[0][0]
            
            return prediction
        return ""

    def draw_text_with_background(self, frame, text, pos, font_scale=1, color=(255,255,255), bg_color=(0,0,0)):
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        
        if not hasattr(self, '_text_cache'):
            self._text_cache = {}
            
        cache_key = (text, font_scale, thickness)
        if cache_key not in self._text_cache:
            (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
            self._text_cache[cache_key] = (text_w, text_h)
        else:
            text_w, text_h = self._text_cache[cache_key]
        
        cv2.rectangle(frame, (pos[0], pos[1] - text_h - 10), 
                     (pos[0] + text_w, pos[1] + 5), bg_color, -1)
        cv2.putText(frame, text, pos, font, font_scale, color, thickness)

    def draw_multiline_text(self, frame, text, start_pos, font_scale=0.6, color=(255,255,255), bg_color=(0,0,0), max_width=None):
        if max_width is None:
            max_width = frame.shape[1] - 20
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            (test_w, test_h), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
            
            if test_w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(current_line)
        
        line_height = int(cv2.getTextSize("A", font, font_scale, thickness)[0][1] * 1.5)
        y_pos = start_pos[1]
        
        for line in lines:
            (line_w, line_h), _ = cv2.getTextSize(line, font, font_scale, thickness)
            
            cv2.rectangle(frame, (start_pos[0], y_pos - line_h - 5), 
                         (start_pos[0] + line_w + 10, y_pos + 5), bg_color, -1)
            
            cv2.putText(frame, line, (start_pos[0] + 5, y_pos), font, font_scale, color, thickness)
            
            y_pos += line_height
        
        return y_pos

    # ===== LOOP PRINCIPAL DE ATUALIZAÇÃO =====
    def update_frame(self):
        if self.showing_video:
            self.handle_video_playback()
            return
            
        if not self.cap or not self.cap.isOpened():
            return

        if self.desafio_ativo:
            self.handle_desafio_mode()
            return

        if self.waiting_prep or self.waiting_delay:
            self.handle_delays()
            return

        # Skip frames para melhor performance
        self.frame_count += 1
        if self.frame_count % self.FRAME_SKIP != 0:
            return

        frame = self.get_frame()
        if frame is None:
            return

        letra_predita = self.process_frame(frame)

        if self.mode == "soletra":
            self.handle_soletra_mode(frame, letra_predita)
        else:
            self.handle_normal_mode(frame, letra_predita)

    def handle_desafio_mode(self):
        tempo_restante = max(0, self.tempo_total - int(time.time() - self.inicio_desafio))
        
        if tempo_restante <= 0:
            self.stop_camera()
            self.desafio_ativo = False
            
            if self.game_start_time == 0:
                self.game_start_time = self.inicio_desafio
                
            self.show_game_results()
            return

        frame = self.get_frame()
        if frame is None:
            return
            
        letra_predita = self.process_frame(frame)

        if not self.palavra_atual:
            self.nova_palavra_desafio()
            return

        if self.skip_non_letter_characters_desafio():
            self.acertos += 1
            self.nova_palavra_desafio()
            return

        letra_esperada = self.palavra_atual[self.letra_idx_desafio]
        palavra_mostrada = (self.palavra_atual[:self.letra_idx_desafio] + 
                           '_' * (len(self.palavra_atual) - self.letra_idx_desafio))

        self.draw_text_with_background(frame, f"Tempo: {tempo_restante}s | Acertos: {self.acertos}", 
                                     (10, 30), 0.7, (0,255,255), (0,0,0))
        
        if self.current_difficulty == "EXPERT" or len(palavra_mostrada) > 30:
            self.draw_multiline_text(frame, f"Palavra: {palavra_mostrada}", (10, 60), 0.6, (255,255,255))
            y_pos_answer = frame.shape[0] - 40
        else:
            self.draw_text_with_background(frame, f"Palavra: {palavra_mostrada}", 
                                         (10, 60), 0.7, (255,255,255), (0,0,0))
            y_pos_answer = frame.shape[0] - 20
        
        if self.current_difficulty == "EXPERT" or len(self.palavra_atual) > 30:
            self.draw_multiline_text(frame, f"Palavra sorteada: {self.palavra_atual}", 
                                   (10, y_pos_answer), 0.5, (0,255,0))
        else:
            self.draw_text_with_background(frame, f"Palavra sorteada: {self.palavra_atual}", 
                                         (10, y_pos_answer), 0.6, (0,255,0), (0,0,0))

        if letra_predita == letra_esperada:
            self.correct_letters += 1
            self.total_letters += 1
            
            self.letra_idx_desafio += 1
            
            if self.skip_non_letter_characters_desafio():
                self.acertos += 1
                self.nova_palavra_desafio()
                return
            
            if self.letra_idx_desafio >= len(self.palavra_atual):
                self.acertos += 1
                self.nova_palavra_desafio()
        elif letra_predita and letra_predita != letra_esperada:
            self.mistakes_made += 1

        self.show_frame(frame)

    def handle_video_playback(self):
        if not self.video_cap or not self.video_cap.isOpened():
            self.start_detection_after_video()
            return
            
        ret, frame = self.video_cap.read()
        if not ret or self.video_frame_count >= self.video_total_frames:
            self.start_detection_after_video()
            return
            
        self.video_frame_count += 1
        
        letra = self.palavra[self.letra_idx]
        texto = f"Demonstracao da letra {letra}"
        self.draw_text_with_background(frame, texto, (10, 30), 1.0, (0, 255, 255), (0, 0, 0))
        
        self.show_frame(frame)
    
    def handle_delays(self):
        if self.last_frame is not None:
            self.show_frame(self.last_frame)

        if self.waiting_prep:
            self.waiting_prep = False
            self.prep_time = 0

        if self.waiting_delay:
            if time.time() - self.delay_start >= self.DELAY_TIME:
                self.letra_idx += 1
                self.waiting_delay = False
                
                if self.skip_non_letter_characters():
                    self.finish_word()
                    return
                
                if self.letra_idx >= len(self.palavra):
                    self.finish_word()
                    return
                
                # Iniciar cronômetro da próxima letra
                self.current_letter_start_time = time.time()
                self.stop_camera()
                self.start_letter_video()

    def finish_word(self):
        if self.last_frame is not None:
            frame = self.last_frame.copy()
            msg = "Parabéns! Palavra completa!"
            self.draw_text_with_background(frame, msg, (50, frame.shape[0] - 50), 0.8, (0,255,0))
            self.show_frame(frame)
        
        self.stop_camera()
        
        self.words_completed += 1
        
        # Salvar palavra no banco de dados
        if self.db and self.current_session_id and hasattr(self, 'palavra') and self.palavra:
            try:
                word_completion_time = time.time() - self.game_start_time if self.game_start_time > 0 else 0
                letter_count = len([c for c in self.palavra if c.isalpha()])
                
                self.current_word_id = self.db.save_word_practice(
                    self.current_session_id,
                    self.palavra,
                    int(word_completion_time),
                    letter_count,
                    self.correct_letters
                )
                
                # Salvar tempos das letras
                if self.letter_times and self.current_word_id:
                    letter_times_data = []
                    letter_count = 0
                    for char in self.palavra:
                        if char.isalpha() and letter_count < len(self.letter_times):
                            letter_times_data.append((char.upper(), self.letter_times[letter_count]))
                            
                            # Atualizar estatísticas da letra
                            self.db.update_letter_stats(
                                self.current_user_id,
                                char.upper(),
                                self.letter_times[letter_count],
                                True  # Assumindo que completou a palavra
                            )
                            letter_count += 1
                    
                    if letter_times_data:
                        self.db.save_letter_times(self.current_session_id, self.current_word_id, letter_times_data)
                
            except Exception as e:
                print(f"Erro ao salvar palavra no banco: {e}")
        
        self.show_game_results()
        
    def show_game_results(self):
        if self.game_start_time == 0:
            total_time = 0
            minutes = 0
            seconds = 0
        else:
            total_time = time.time() - self.game_start_time
            minutes = int(total_time // 60)
            seconds = int(total_time % 60)
        
        accuracy = (self.correct_letters / max(1, self.total_letters)) * 100 if self.total_letters > 0 else 0
        
        if self.current_mode == "DESAFIO":
            result_msg = f"""=== RESULTADOS DO DESAFIO ===

Palavras completadas: {self.acertos}
Nível: {self.difficulty_config['name'] if hasattr(self, 'difficulty_config') else 'Padrão'}
Tempo total: {minutes}m {seconds}s

Letras corretas: {self.correct_letters}
Total de letras: {self.total_letters}
Precisão: {accuracy:.1f}%"""
        else:
            # Calcular tempo médio por letra
            avg_time = sum(self.letter_times) / len(self.letter_times) if self.letter_times else 0
            
            # Criar string com tempos individuais das letras
            times_str = ""
            if hasattr(self, 'palavra') and self.palavra and self.letter_times:
                times_str = "\n\nTempos por letra:\n"
                letter_count = 0
                for i, char in enumerate(self.palavra.upper()):
                    if char.isalpha() and letter_count < len(self.letter_times):
                        times_str += f"  {char}: {self.letter_times[letter_count]:.1f}s\n"
                        letter_count += 1
            
            result_msg = f"""=== RESULTADOS DA SOLETRAÇÃO ===

Palavras completadas: {self.words_completed}
Nível: {self.difficulty_config['name'] if hasattr(self, 'difficulty_config') else 'Padrão'}
Tempo total: {minutes}m {seconds}s

Letras corretas: {self.correct_letters}
Total de letras: {self.total_letters}
Precisão: {accuracy:.1f}%
Tempo médio por letra: {avg_time:.1f}s{times_str}

Palavra atual: {self.palavra if hasattr(self, 'palavra') and self.palavra else 'N/A'}
Progresso: {self.letra_idx if hasattr(self, 'letra_idx') else 0}"""
        
        # Finalizar sessão no banco de dados
        if self.db and self.current_session_id:
            try:
                stats = {
                    'total_duration': int(total_time),
                    'words_completed': self.words_completed,
                    'total_letters': self.total_letters,
                    'correct_letters': self.correct_letters,
                    'accuracy': accuracy
                }
                
                self.db.end_session(self.current_session_id, stats)
                
                # Adicionar estatísticas do banco aos resultados
                if self.current_user_id:
                    user_stats = self.db.get_user_stats(self.current_user_id)
                    
                    if user_stats['general'] and user_stats['general'][0] > 0:
                        sessions, total_words, avg_acc, total_time_db = user_stats['general']
                        result_msg += f"\n\n=== ESTATÍSTICAS HISTÓRICAS (30 dias) ===\n"
                        result_msg += f"Sessões totais: {sessions or 0}\n"
                        result_msg += f"Palavras completadas: {total_words or 0}\n"
                        result_msg += f"Precisão média: {avg_acc or 0:.1f}%\n"
                        result_msg += f"Tempo total: {(total_time_db or 0) // 60:.0f}min\n"
                
            except Exception as e:
                print(f"Erro ao finalizar sessão: {e}")
        
        self.results_label.setText(result_msg)
        
        self.soletra_label.setText("Resultados exibidos na lateral →")
        
        self.back_to_menu_btn.setEnabled(True)
        self.back_to_menu_btn.show()
        self.back_to_menu_btn.setText("Voltar ao Menu")

    # ===== FUNÇÕES AUXILIARES =====
    def reset_statistics(self):
        reset_vars = {
            'game_start_time': 0, 'total_letters': 0, 'correct_letters': 0,
            'words_completed': 0, 'letter_times': [], 'current_letter_start_time': 0, 'current_mode': ""
        }
        
        for var, value in reset_vars.items():
            setattr(self, var, value)
        
        if hasattr(self, 'results_label'):
            self.results_label.setText("")

    def skip_non_letter_characters_generic(self, palavra, letra_idx):
        while letra_idx < len(palavra) and palavra[letra_idx] in ['-', ' ']:
            letra_idx += 1
        return letra_idx, letra_idx >= len(palavra)

    def skip_non_letter_characters(self):
        self.letra_idx, finished = self.skip_non_letter_characters_generic(self.palavra, self.letra_idx)
        return finished

    def skip_non_letter_characters_desafio(self):
        self.letra_idx_desafio, finished = self.skip_non_letter_characters_generic(self.palavra_atual, self.letra_idx_desafio)
        return finished

    def process_frame(self, frame):
        current_time = time.time()
        
        # Cache de landmarks para evitar processamento desnecessário
        if (current_time - self.last_landmarks_time < 0.1 and 
            self.landmarks_cache is not None):
            return self.landmarks_cache
        
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        letra_predita = ""

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                letra_predita = self.predict_letter(hand_landmarks)
                break

        # Atualizar cache
        self.last_landmarks_time = current_time
        self.landmarks_cache = letra_predita
        
        return letra_predita

    def handle_soletra_mode(self, frame, letra_predita):
        if self.palavra is None:
            return

        if self.skip_non_letter_characters():
            self.finish_word()
            return

        letra_esperada = self.palavra[self.letra_idx]
        
        if self.letter_start_time == 0:
            self.letter_start_time = time.time()
            self.current_letter_start_time = time.time()
        
        time_limit = self.difficulty_config['time_limit']
        if time_limit:
            elapsed_time = time.time() - self.letter_start_time
            remaining_time = max(0, time_limit - elapsed_time)
            
            if remaining_time <= 0:
                # Salvar tempo da letra mesmo se não acertou
                letter_time = time.time() - self.current_letter_start_time
                self.letter_times.append(letter_time)
                self.waiting_delay = True
                self.delay_start = time.time()
                self.letter_start_time = 0
        
        texto_esperada = f"Letra esperada: {letra_esperada}"
        texto_feita = f"Letra feita: {letra_predita if letra_predita else '_'}"
        
        self.draw_text_with_background(frame, texto_esperada, (10, 30), 0.8, (0,0,255))
        self.draw_text_with_background(frame, texto_feita, (10, 70), 0.8, (0,255,0))
        
        if letra_predita == letra_esperada and not self.waiting_delay:
            self.correct_letters += 1
            self.total_letters += 1
            
            # Calcular e salvar tempo da letra
            letter_time = time.time() - self.current_letter_start_time
            self.letter_times.append(letter_time)
            
            if self.letra_idx < len(self.palavra) - 1:
                self.draw_text_with_background(frame, "Correto! Próxima...", 
                                             (10, frame.shape[0] - 50), 0.8, (0,255,0))
            self.waiting_delay = True
            self.delay_start = time.time()
            self.letter_start_time = 0

        # Otimização: só atualizar texto se mudou
        if letra_predita != self.last_prediction:
            self.text_label.setText(f"Letra: {letra_predita}")
            self.last_prediction = letra_predita
        
        self.last_frame = frame.copy()
        self.show_frame(frame)

    def handle_normal_mode(self, frame, letra_predita):
        if letra_predita:
            self.draw_text_with_background(frame, f"Letra: {letra_predita}", (10, 30), 1.2, (0,255,0))
        
        # Otimização: só atualizar texto se mudou
        if letra_predita != self.last_prediction:
            self.text_label.setText(f"Letra: {letra_predita}")
            self.last_prediction = letra_predita
            
        self.last_frame = frame.copy()
        self.show_frame(frame)

    def show_frame(self, frame):
        if frame is None:
            return
        
        # Otimização: redimensionar antes da conversão de cor para economizar processamento
        label_size = self.image_label.size()
        label_w, label_h = label_size.width(), label_size.height()
        
        h, w = frame.shape[:2]
        scale_w = label_w / w
        scale_h = label_h / h
        scale = min(scale_w, scale_h, self.MAX_VIDEO_SCALE)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        if scale != 1.0:
            frame = cv2.resize(frame, (new_w, new_h))
        
        # Converter cor após redimensionamento
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
            
        bytes_per_line = ch * w
        qt_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        self.image_label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

# ===== EXECUÇÃO PRINCIPAL =====
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())