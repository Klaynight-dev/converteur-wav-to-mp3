import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QListWidget, QMessageBox, QMenu, QProgressBar, QTextEdit
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QThread, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
import sip

from moviepy.editor import AudioFileClip
import logging

class ProgressWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Conversion Progress')
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel('Converting files...', self)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.log_textedit = QTextEdit(self)
        layout.addWidget(self.log_textedit)

        self.setLayout(layout)

    @pyqtSlot(str)
    def update_log(self, message):
        self.log_textedit.append(message)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

class ConverterThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        total_files = len(self.files)
        for i, file_path in enumerate(self.files):
            output_path = os.path.splitext(file_path)[0] + '.mp3'
            try:
                self.update_log.emit(f"MoviePy - Writing audio in {output_path}")
                audio_clip = AudioFileClip(file_path)
                audio_clip.write_audiofile(output_path, codec='libmp3lame', bitrate='320k')
                audio_clip.close()
                self.update_log.emit("MoviePy - Done.")
                logging.info(f"Successfully converted {file_path} to {output_path}")
            except Exception as e:
                logging.error(f"Error converting {file_path}: {str(e)}")
                self.update_log.emit(f"Error converting {file_path}: {str(e)}")
                return
            progress = int(((i + 1) / total_files) * 100)
            self.update_progress.emit(progress)
        self.finished.emit()

class WavToMp3Converter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('WAV to MP3 Converter')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel('Selectionner le(s) fichier(s) WAV pour les convertir en MP3 (320 kbps)', self)
        layout.addWidget(self.label)

        self.btn_select = QPushButton('Select WAV Files', self)
        self.btn_select.clicked.connect(self.select_files)
        layout.addWidget(self.btn_select)

        self.list_widget = QListWidget(self)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        self.btn_convert = QPushButton('Convert to MP3', self)
        self.btn_convert.clicked.connect(self.convert_files)
        layout.addWidget(self.btn_convert)

        self.setLayout(layout)

        logging.basicConfig(filename='conversion.log', level=logging.DEBUG)
        # Dans la méthode initUI de WavToMp3Converter

        # Ajouter des icônes aux boutons
        self.btn_select.setIcon(QIcon('content/img/select.png'))
        self.btn_convert.setIcon(QIcon('content/img/converter.png'))

        with open('content/CSS/style.css', 'r') as f:
            app.setStyleSheet(f.read())


    def select_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        files, _ = QFileDialog.getOpenFileNames(self, "Select WAV Files", "", "WAV Files (*.wav);;All Files (*)", options=options)
        if files:
            self.list_widget.addItems(files)
            logging.info(f"Selected files: {files}")

    def show_context_menu(self, pos: QPoint):
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        if action == delete_action:
            for item in self.list_widget.selectedItems():
                self.list_widget.takeItem(self.list_widget.row(item))

    def convert_files(self):
        selected_files = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if not selected_files:
            QMessageBox.warning(self, "No Files", "Please select WAV files to convert.")
            return

        # Créer une instance de ProgressWindow
        self.progress_window = ProgressWindow()
        self.progress_window.show()

        # Créer et démarrer le thread de conversion
        thread = ConverterThread(selected_files)
        thread.update_progress.connect(self.progress_window.set_progress)
        thread.update_log.connect(self.progress_window.update_log)
        thread.finished.connect(self.progress_window.close)  # Fermer la fenêtre de progression lorsque la conversion est terminée
        thread.start()

        # Créer un QTimer pour vérifier régulièrement si le thread est encore en cours d'exécution
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.check_thread_running(thread, timer))
        timer.start(1000)  # Vérifier toutes les secondes


    def check_thread_running(self, thread, timer):
        if not thread.isRunning():
            timer.stop()  # Arrêter le QTimer
            thread.quit()  # Arrêter le thread

if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter = WavToMp3Converter()
    converter.show()
    sys.exit(app.exec_())