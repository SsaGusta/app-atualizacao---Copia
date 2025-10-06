import sqlite3
from datetime import datetime, timedelta
from database import LibrasDatabase
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTabWidget, QWidget, QScrollArea
from PyQt5.QtCore import Qt

class LibrasReports:
    def __init__(self, db_path="libras_stats.db"):
        self.db = LibrasDatabase(db_path)
    
    def generate_progress_report(self, user_id, days=30):
        """Gera relatório de progresso"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Progresso diário
        cursor.execute('''
            SELECT DATE(start_time) as date, 
                   COUNT(*) as sessions,
                   AVG(accuracy) as avg_accuracy,
                   SUM(words_completed) as words,
                   AVG(total_duration) as avg_duration
            FROM game_sessions 
            WHERE user_id = ? AND start_time >= datetime('now', '-{} days')
            GROUP BY DATE(start_time)
            ORDER BY date
        '''.format(days), (user_id,))
        
        daily_progress = cursor.fetchall()
        
        # Letras mais difíceis
        cursor.execute('''
            SELECT letter, 
                   ROUND((correct_attempts * 100.0 / total_attempts), 2) as accuracy,
                   avg_time,
                   best_time,
                   total_attempts
            FROM letter_stats 
            WHERE user_id = ? AND total_attempts >= 3
            ORDER BY accuracy ASC, avg_time DESC
            LIMIT 5
        ''', (user_id,))
        
        difficult_letters = cursor.fetchall()
        
        # Letras com melhor performance
        cursor.execute('''
            SELECT letter, 
                   ROUND((correct_attempts * 100.0 / total_attempts), 2) as accuracy,
                   avg_time,
                   best_time,
                   total_attempts
            FROM letter_stats 
            WHERE user_id = ? AND total_attempts >= 3
            ORDER BY accuracy DESC, avg_time ASC
            LIMIT 5
        ''', (user_id,))
        
        best_letters = cursor.fetchall()
        
        # Palavras mais praticadas
        cursor.execute('''
            SELECT word, COUNT(*) as count, AVG(completion_time) as avg_time
            FROM practiced_words pw
            JOIN game_sessions gs ON pw.session_id = gs.id
            WHERE gs.user_id = ?
            GROUP BY word
            ORDER BY count DESC
            LIMIT 10
        ''', (user_id,))
        
        popular_words = cursor.fetchall()
        
        conn.close()
        
        return {
            'daily_progress': daily_progress,
            'difficult_letters': difficult_letters,
            'best_letters': best_letters,
            'popular_words': popular_words
        }
    
    def plot_progress_chart(self, user_id, days=30):
        """Cria gráfico de progresso"""
        report = self.generate_progress_report(user_id, days)
        
        if not report['daily_progress']:
            return None
        
        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in report['daily_progress']]
        accuracies = [row[2] if row[2] else 0 for row in report['daily_progress']]
        sessions = [row[1] for row in report['daily_progress']]
        
        # Criar gráfico com dois eixos Y
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Eixo 1: Precisão
        color1 = 'tab:blue'
        ax1.set_xlabel('Data')
        ax1.set_ylabel('Precisão (%)', color=color1)
        line1 = ax1.plot(dates, accuracies, color=color1, marker='o', label='Precisão')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3)
        
        # Eixo 2: Número de sessões
        ax2 = ax1.twinx()
        color2 = 'tab:red'
        ax2.set_ylabel('Sessões por dia', color=color2)
        bars = ax2.bar(dates, sessions, alpha=0.3, color=color2, label='Sessões')
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Formatação das datas
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))
        plt.xticks(rotation=45)
        
        plt.title('Progresso de Aprendizado ao Longo do Tempo', fontsize=14, fontweight='bold')
        
        # Legenda
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        
        filename = f"progress_chart_{user_id}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def plot_letter_performance(self, user_id):
        """Cria gráfico de performance por letra"""
        user_stats = self.db.get_user_stats(user_id)
        
        if not user_stats['letters']:
            return None
        
        letters = [row[0] for row in user_stats['letters']]
        accuracies = [round((row[4] * 100.0 / row[3]), 2) if row[3] > 0 else 0 for row in user_stats['letters']]
        avg_times = [row[2] for row in user_stats['letters']]
        
        # Criar gráfico de barras
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Gráfico 1: Precisão por letra
        bars1 = ax1.bar(letters, accuracies, color=['green' if acc >= 80 else 'orange' if acc >= 60 else 'red' for acc in accuracies])
        ax1.set_ylabel('Precisão (%)')
        ax1.set_title('Precisão por Letra')
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.3)
        
        # Adicionar valores nas barras
        for bar, acc in zip(bars1, accuracies):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Gráfico 2: Tempo médio por letra
        bars2 = ax2.bar(letters, avg_times, color=['green' if time <= 5 else 'orange' if time <= 10 else 'red' for time in avg_times])
        ax2.set_xlabel('Letras')
        ax2.set_ylabel('Tempo Médio (segundos)')
        ax2.set_title('Tempo Médio por Letra')
        ax2.grid(True, alpha=0.3)
        
        # Adicionar valores nas barras
        for bar, time in zip(bars2, avg_times):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{time:.1f}s', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        filename = f"letter_performance_{user_id}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filename

class ReportsDialog(QDialog):
    def __init__(self, user_id, db_path="libras_stats.db", parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = LibrasDatabase(db_path)
        self.reports = LibrasReports(db_path)
        self.init_ui()
        self.load_reports()
    
    def init_ui(self):
        self.setWindowTitle("Relatórios de Progresso - Libras")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # Criar abas
        self.tab_widget = QTabWidget()
        
        # Aba 1: Estatísticas Gerais
        self.stats_tab = QWidget()
        self.stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_layout.addWidget(self.stats_text)
        self.stats_tab.setLayout(self.stats_layout)
        
        # Aba 2: Performance por Letra
        self.letters_tab = QWidget()
        self.letters_layout = QVBoxLayout()
        self.letters_text = QTextEdit()
        self.letters_text.setReadOnly(True)
        self.letters_layout.addWidget(self.letters_text)
        self.letters_tab.setLayout(self.letters_layout)
        
        # Aba 3: Histórico de Sessões
        self.sessions_tab = QWidget()
        self.sessions_layout = QVBoxLayout()
        self.sessions_text = QTextEdit()
        self.sessions_text.setReadOnly(True)
        self.sessions_layout.addWidget(self.sessions_text)
        self.sessions_tab.setLayout(self.sessions_layout)
        
        # Adicionar abas
        self.tab_widget.addTab(self.stats_tab, "📊 Estatísticas Gerais")
        self.tab_widget.addTab(self.letters_tab, "🔤 Performance por Letra")
        self.tab_widget.addTab(self.sessions_tab, "📈 Histórico de Sessões")
        
        layout.addWidget(self.tab_widget)
        
        # Botões
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Atualizar")
        self.refresh_btn.clicked.connect(self.load_reports)
        
        self.export_btn = QPushButton("📊 Gerar Gráficos")
        self.export_btn.clicked.connect(self.generate_charts)
        
        self.close_btn = QPushButton("❌ Fechar")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_reports(self):
        """Carrega todos os relatórios"""
        self.load_general_stats()
        self.load_letter_performance()
        self.load_session_history()
    
    def load_general_stats(self):
        """Carrega estatísticas gerais"""
        user_stats = self.db.get_user_stats(self.user_id)
        report_data = self.reports.generate_progress_report(self.user_id)
        
        text = "=== ESTATÍSTICAS GERAIS (ÚLTIMOS 30 DIAS) ===\n\n"
        
        if user_stats['general'] and user_stats['general'][0] > 0:
            sessions, total_words, avg_acc, total_time = user_stats['general']
            
            text += f"📊 RESUMO GERAL:\n"
            text += f"• Sessões realizadas: {sessions or 0}\n"
            text += f"• Palavras completadas: {total_words or 0}\n"
            text += f"• Precisão média: {avg_acc or 0:.1f}%\n"
            
            if total_time:
                hours = int(total_time // 3600)
                minutes = int((total_time % 3600) // 60)
                text += f"• Tempo total praticado: {hours}h {minutes}min\n\n"
            else:
                text += f"• Tempo total praticado: 0h 0min\n\n"
        else:
            text += "📊 RESUMO GERAL:\n"
            text += "• Ainda não há dados suficientes\n"
            text += "• Continue praticando para ver suas estatísticas!\n\n"
        
        # Palavras mais praticadas
        if report_data['popular_words']:
            text += "🎯 PALAVRAS MAIS PRATICADAS:\n"
            for i, (word, count, avg_time) in enumerate(report_data['popular_words'][:5], 1):
                text += f"{i}. {word.upper()}: {count} vezes (média: {avg_time:.1f}s)\n"
            text += "\n"
        
        # Progresso diário
        if report_data['daily_progress']:
            text += "📈 PROGRESSO DOS ÚLTIMOS DIAS:\n"
            for date, sessions, accuracy, words, duration in report_data['daily_progress'][-7:]:
                text += f"• {date}: {sessions} sessões, {accuracy:.1f}% precisão\n"
        
        self.stats_text.setText(text)
    
    def load_letter_performance(self):
        """Carrega performance por letra"""
        user_stats = self.db.get_user_stats(self.user_id)
        report_data = self.reports.generate_progress_report(self.user_id)
        
        text = "=== PERFORMANCE POR LETRA ===\n\n"
        
        if user_stats['letters']:
            text += "📊 TODAS AS LETRAS:\n"
            text += f"{'Letra':<6} {'Precisão':<10} {'Tempo Médio':<12} {'Melhor':<10} {'Tentativas':<10}\n"
            text += "-" * 60 + "\n"
            
            for letter, best_time, avg_time, attempts, correct, accuracy in user_stats['letters']:
                if attempts > 0:
                    acc = (correct * 100.0 / attempts)
                    text += f"{letter:<6} {acc:<10.1f}% {avg_time:<12.1f}s {best_time:<10.1f}s {attempts:<10}\n"
            
            text += "\n"
        
        # Letras que precisam de mais prática
        if report_data['difficult_letters']:
            text += "🎯 LETRAS QUE PRECISAM DE MAIS PRÁTICA:\n"
            for i, (letter, accuracy, avg_time, best_time, attempts) in enumerate(report_data['difficult_letters'], 1):
                text += f"{i}. {letter}: {accuracy}% precisão, {avg_time:.1f}s média ({attempts} tentativas)\n"
            text += "\n"
        
        # Melhores letras
        if report_data['best_letters']:
            text += "🏆 LETRAS COM MELHOR PERFORMANCE:\n"
            for i, (letter, accuracy, avg_time, best_time, attempts) in enumerate(report_data['best_letters'], 1):
                text += f"{i}. {letter}: {accuracy}% precisão, {avg_time:.1f}s média ({attempts} tentativas)\n"
        
        self.letters_text.setText(text)
    
    def load_session_history(self):
        """Carrega histórico de sessões"""
        user_stats = self.db.get_user_stats(self.user_id)
        
        text = "=== HISTÓRICO DE SESSÕES ===\n\n"
        
        if user_stats['recent_sessions']:
            text += "📈 ÚLTIMAS 10 SESSÕES:\n"
            text += f"{'Data/Hora':<20} {'Modo':<12} {'Dificuldade':<12} {'Palavras':<8} {'Precisão':<10}\n"
            text += "-" * 70 + "\n"
            
            for session in user_stats['recent_sessions']:
                mode, difficulty, start_time, words, accuracy = session
                # Converter timestamp para formato legível
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')) if 'Z' in start_time else datetime.fromisoformat(start_time)
                date_str = dt.strftime('%d/%m/%Y %H:%M')
                
                text += f"{date_str:<20} {mode:<12} {difficulty:<12} {words or 0:<8} {accuracy or 0:<10.1f}%\n"
        else:
            text += "📈 Ainda não há sessões registradas.\n"
            text += "Comece a praticar para ver seu histórico aqui!"
        
        self.sessions_text.setText(text)
    
    def generate_charts(self):
        """Gera gráficos de progresso"""
        try:
            # Gerar gráfico de progresso
            progress_file = self.reports.plot_progress_chart(self.user_id)
            
            # Gerar gráfico de performance por letra
            letter_file = self.reports.plot_letter_performance(self.user_id)
            
            message = "Gráficos gerados com sucesso!\n\n"
            if progress_file:
                message += f"📊 Gráfico de progresso: {progress_file}\n"
            if letter_file:
                message += f"🔤 Gráfico de letras: {letter_file}\n"
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Gráficos Gerados", message)
            
        except ImportError:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", 
                "Não foi possível gerar os gráficos.\n"
                "Instale o matplotlib: pip install matplotlib")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráficos:\n{str(e)}")