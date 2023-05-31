import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QProgressBar, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QThread, Signal
from PIL import Image

BATCH_SIZE = 10

class ImageCompressionWorker(QThread):
    progressChanged = Signal(int)
    compressionFinished = Signal()

    def __init__(self, input_paths, output_dir, quality=85, suffix="_compressed"):
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
            self.progressChanged.emit(progress)

        self.compressionFinished.emit()

    def compress_image(self, input_path, output_path):
        try:
            with Image.open(input_path) as img:
                img.save(output_path, optimize=True, quality=self.quality)
        except Exception as e:
            print(f"Error compressing image: {input_path}\n{str(e)}")

    def get_output_path(self, input_path):
        filename, extension = os.path.splitext(os.path.basename(input_path))
        filename = f"{filename}{self.suffix}{extension}"
        return os.path.join(self.output_dir, filename)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Compression")
        self.setGeometry(100, 100, 400, 500)

        self.image_list = QListWidget(self)
        self.image_list.setAlternatingRowColors(True)
        self.image_list.setSelectionMode(QListWidget.ExtendedSelection)

        select_images_button = QPushButton("Select Images", self)
        select_images_button.clicked.connect(self.select_images)

        remove_image_button = QPushButton("Remove Image", self)
        remove_image_button.clicked.connect(self.remove_image)

        select_output_button = QPushButton("Select Output Directory", self)
        select_output_button.clicked.connect(self.select_output_directory)

        compress_button = QPushButton("Start Compression", self)
        compress_button.clicked.connect(self.compress_selected_images)

        self.output_directory_label = QLabel(self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(True)

        layout = QVBoxLayout()
        layout.addWidget(select_images_button)
        layout.addWidget(remove_image_button)
        layout.addWidget(select_output_button)
        layout.addWidget(compress_button)
        layout.addWidget(self.image_list)
        layout.addWidget(self.output_directory_label)
        layout.addWidget(self.progress_bar)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.output_directory = ""

    def select_images(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            for file_path in file_paths:
                self.image_list.addItem(file_path)

    def remove_image(self):
        selected_items = self.image_list.selectedItems()
        for item in selected_items:
            self.image_list.takeItem(self.image_list.row(item))

    def select_output_directory(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec():
            self.output_directory = dialog.selectedFiles()[0]
            self.output_directory_label.setText(self.output_directory)

    def compress_selected_images(self):
        image_paths = [self.image_list.item(i).text() for i in range(self.image_list.count())]
        if image_paths:
            if not self.output_directory:
                QMessageBox.warning(self, "Missing Output Directory", "Please select an output directory.")
                return  # Abort compression if output directory is not selected
            worker = ImageCompressionWorker(image_paths, self.output_directory)
            worker.progressChanged.connect(self.update_progress)
            worker.compressionFinished.connect(self.compression_complete)
            worker.start()
        else:
            QMessageBox.warning(self, "Missing Selection", "Please select images.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def compression_complete(self):
        QMessageBox.information(self, "Compression Complete", "Images compressed successfully!")
        self.progress_bar.setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
