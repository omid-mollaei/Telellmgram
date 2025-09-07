import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLineEdit, QTextEdit, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFontDatabase, QFont, QColor
from telellmgram.pipelines.social_pipelines import SpecificMediaAnalysis

# Dummy function to simulate analysis
def analyze_media(prompt: str, selected_id: int, start_date: str, end_date: str) -> str:
    pipeline = SpecificMediaAnalysis(prompt, selected_id, start_date, end_date)
    return pipeline.run()

class MediaAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تحلیل رسانه خاص")
        self.resize(700, 600)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0f1a, stop:1 #060910);
                color: #f0f0f0;
            }
        """)
        self.load_fonts()
        self.init_ui()

    def load_fonts(self):
        id_titr = QFontDatabase.addApplicationFont("resources/titr.ttf")
        id_vazir = QFontDatabase.addApplicationFont("resources/vazir.ttf")
        self.font_titr = QFont(QFontDatabase.applicationFontFamilies(id_titr)[0], 16)
        self.font_vazir = QFont(QFontDatabase.applicationFontFamilies(id_vazir)[0], 13)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)

        # Load CSV
        self.items = []
        self.item_ids = []
        csv_path = "/home/omid/workspace/Telellmgram/telellmgram/media/metadata.csv"
        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.items.append(row['name'])
                    self.item_ids.append(int(row['id']))
        except Exception as e:
            print(f"Error loading CSV: {e}")
            self.items = ["Sample 1", "Sample 2"]
            self.item_ids = [1, 2]

        # ComboBox
        layout.addWidget(QLabel("انتخاب رسانه:"))
        self.combo = QComboBox()
        self.combo.setFont(self.font_vazir)
        self.combo.addItems(self.items)
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 5px;
                color: #f0f0f0;
            }
            QComboBox QAbstractItemView {
                background-color: #0a0f1a;
                selection-background-color: #4fd1c5;
                color: #f0f0f0;
            }
        """)
        layout.addWidget(self.combo)

        # Date interval
        date_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("dd/MM/yy")
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("dd/MM/yy")
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)

        date_layout.addWidget(QLabel("شروع بازه زمانی:"))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QLabel("پایان بازه زمانی:"))
        date_layout.addWidget(self.end_date_edit)
        layout.addLayout(date_layout)

        # Prompt input
        layout.addWidget(QLabel("ورود متن:"))
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setFont(self.font_vazir)
        self.prompt_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                color: #f0f0f0;
            }
        """)
        self.prompt_edit.setMinimumHeight(35)  # bigger
        layout.addWidget(self.prompt_edit)

        # Analyze button
        self.analyze_btn = QPushButton("تحلیل")
        self.analyze_btn.setFont(self.font_titr)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: rgba(79, 209, 197, 0.2);
                border-radius: 10px;
                padding: 12px;
                font-weight: bold;
                color: #f0f0f0;
            }
            QPushButton:hover {
                background: rgba(79, 209, 197, 0.35);
            }
            QPushButton:pressed {
                background: rgba(79, 209, 197, 0.5);
            }
        """)
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)
        layout.addWidget(self.analyze_btn)

        # Result display
        layout.addWidget(QLabel("نتیجه تحلیل:"))
        self.result_text = QTextEdit()
        self.result_text.setFont(self.font_vazir)
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                color: #f0f0f0;
            }
        """)
        self.result_text.setMinimumHeight(200)  # bigger
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def on_analyze_clicked(self):
        prompt = self.prompt_edit.text()
        selected_index = self.combo.currentIndex()
        selected_id = self.item_ids[selected_index]
        start_date = self.start_date_edit.date().toString("dd/MM/yy")
        end_date = self.end_date_edit.date().toString("dd/MM/yy")

        # Call analysis function
        result = analyze_media(prompt, selected_id, start_date, end_date)
        self.result_text.setText(result)
