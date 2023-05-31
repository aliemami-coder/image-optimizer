import sys
import os
import logging
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QListWidget, QPushButton, QLabel, QProgressBar
from PIL import Image


logging.basicConfig(filename='image_compression.log', level=logging.ERROR)

BATCH_SIZE = 10


class ImageCompressionThread(QtCore.QThread):
    compression_complete = QtCore.pyqtSignal()
    progress_update = QtCore.pyqtSignal(int)

    def __init__(self, input_paths, output_dir, quality, suffix):
        super().__init__()
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.quality = quality
        self.suffix = suffix

    def run(self):
        num_images = len(self.input_paths)
        for i in range(0, num_images, BATCH_SIZE):
            batch_input_paths = self.input_paths[i:i + BATCH_SIZE]
            batch_output_paths = [self.get_output_path(input_path) for input_path in batch_input_paths]

            for input_path, output_path in zip(batch_input_paths, batch_output_paths):
                self.compress_image(input_path, output_path)

            progress = int((i + len(batch_input_paths)) / num_images * 100)
            self.progress_update.emit(progress)

        self.compression_complete.emit()

    def compress_image(self, input_path, output_path):
        try:
            with Image.open(input_path) as img:
                img.save(output_path, optimize=True, quality=self.quality)
        except Exception as e:
            logging.error(f"Error compressing image: {input_path}\n{str(e)}")

    def get_output_path(self, input_path):
        filename, extension = os.path.splitext(os.path.basename(input_path))
        filename = f"{filename}{self.suffix}{extension}"
        return os.path.join(self.output_dir, filename)


class ImageCompressionWindow(QMainWindow):
    progress_update = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Compression")
        self.setGeometry(100, 100, 400, 520)

        self.image_list = QListWidget(self)
        self.image_list.setGeometry(10, 10, 380, 350)

        self.select_images_button = QPushButton("Select Images", self)
        self.select_images_button.setGeometry(10, 370, 180, 30)
        self.select_images_button.clicked.connect(self.select_images)

        self.remove_image_button = QPushButton("Remove Image", self)
        self.remove_image_button.setGeometry(210, 370, 180, 30)
        self.remove_image_button.clicked.connect(self.remove_image)

        self.select_output_button = QPushButton("Select Output Directory", self)
        self.select_output_button.setGeometry(10, 410, 180, 30)
        self.select_output_button.clicked.connect(self.select_output_directory)

        self.compress_button = QPushButton("Start Compression", self)
        self.compress_button.setGeometry(210, 410, 180, 30)
        self.compress_button.clicked.connect(self.compress_selected_images)

        self.output_directory_label = QLabel(self)
        self.output_directory_label.setGeometry(10, 450, 380, 30)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(10, 490, 380, 20)

        self.output_directory = ""
        self.mutex = QtCore.QMutex()
        self.thread = None

    def compress_images(self, input_paths, output_dir, quality=80, suffix="_compressed"):
        self.thread = ImageCompressionThread(input_paths, output_dir, quality, suffix)
        self.thread.compression_complete.connect(self.compression_complete)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def compression_complete(self):
        QMessageBox.information(self, "Compression Complete", "Images compressed successfully!")
        self.progress_bar.setValue(0)
        self.thread = None
        self.image_list.clear()
        self.update_selected_image_count()

    def compress_selected_images(self):
        if self.thread is not None and self.thread.isRunning():
            return

        image_paths = [self.image_list.item(i).text() for i in range(self.image_list.count())]
        if image_paths:
            if not self.output_directory:
                QMessageBox.warning(self, "Missing Output Directory", "Please select an output directory.")
                return  # Abort compression if output directory is not selected

            self.progress_bar.setValue(0)
            self.compress_images(image_paths, self.output_directory)
        else:
            QMessageBox.warning(self, "Missing Selection", "Please select images.")

    def select_images(self):
        image_paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Image Files (*.png *.jpg *.jpeg)")
        if image_paths:
            with QtCore.QMutexLocker(self.mutex):
                for path in image_paths:
                    self.image_list.addItem(os.path.normpath(path))
            self.update_selected_image_count()

    def remove_image(self):
        current_item = self.image_list.currentItem()
        if current_item:
            with QtCore.QMutexLocker(self.mutex):
                self.image_list.takeItem(self.image_list.row(current_item))
            self.update_selected_image_count()

    def select_output_directory(self):
        output_directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_directory:
            self.output_directory = output_directory
            self.output_directory_label.setText("Output directory: "+output_directory)

    def update_selected_image_count(self):
        count = self.image_list.count()
        self.setWindowTitle(f"Image Compression ({count} Selected)")  # Update window title


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageCompressionWindow()
    window.show()
    sys.exit(app.exec_())
