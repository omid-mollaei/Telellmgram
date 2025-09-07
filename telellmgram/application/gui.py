import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QGridLayout, QScrollArea, QGroupBox
)
from PyQt5.QtGui import QFontDatabase, QFont, QPixmap
from PyQt5.QtCore import Qt

# Import the pages
from pages.media_analysis import MediaAnalysisPage
from pages.topic_analysis import TopicAnalysisPage

class TeleLLMgramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TeleLLMgram")
        self.resize(1200, 900)
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0f1a, stop:1 #060910); color: #f0f0f0;")
        
        self.load_fonts()
        self.init_ui()

    def load_fonts(self):
        # Load Persian fonts
        id_titr = QFontDatabase.addApplicationFont("resources/titr.ttf")
        id_vazir = QFontDatabase.addApplicationFont("resources/vazir.ttf")
        self.font_titr = QFont(QFontDatabase.applicationFontFamilies(id_titr)[0], 28)
        self.font_vazir = QFont(QFontDatabase.applicationFontFamilies(id_vazir)[0], 12)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignRight)
        title_label = QLabel("TeleLLMgram")
        title_label.setFont(self.font_titr)
        title_label.setStyleSheet("color: #8b5cf6;")
        subtitle_label = QLabel("تحلیل جامعه‌ی فارسی در تلگرام")
        subtitle_label.setFont(self.font_vazir)
        subtitle_label.setStyleSheet("color: #9aa6b2;")
        header_text_layout = QVBoxLayout()
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        header_layout.addLayout(header_text_layout)
        main_layout.addLayout(header_layout)

        # Introduction paragraph (full Persian text)
        intro_text = QLabel(
            "TeleLLMgram یک پروژه نوآورانه و پیشرفته در حوزه تحلیل اجتماعی است "
            "که با بهره‌گیری از قابلیت‌های تحلیلی مدل‌های زبانی بزرگ (Large Language Models یا LLMs)، "
            "به کاوش عمیق در جامعه فارسی‌زبان و ایرانیان می‌پردازد. هدف اصلی این پروژه، واکاوی و درکِ ساختاریافته‌ی "
            "دیدگاه‌ها، عقاید، گرایش‌های فکری، و دلایل پشت‌پردۀ رفتارهای اجتماعی این جامعه است. "
            "TeleLLMgram با جمع‌آوری و پردازش حجم عظیمی از داده‌های متنی تولیدشده توسط کاربران "
            "(مانند نظرات، مقالات، گفت‌وگوها و محتوای شبکه‌های اجتماعی)، به تحلیل ریشه‌ای مسائل فرهنگی، "
            "سیاسی، اجتماعی و اقتصادی می‌پردازد. این پروژه نه تنها به شناسایی الگوهای غالب فکری کمک می‌کند، "
            "بلکه با ردیابی تغییرات آرام در عقاید عمومی، ابزاری قدرتمند برای پژوهشگران علوم اجتماعی، "
            "تحلیلگران و نهادهای تصمیم‌ساز فراهم می‌آورد تا بتوانند درکی دقیق‌تر و داده‌محور از پیچیدگی‌های جامعه ایران به دست آورند."
        )
        intro_text.setWordWrap(True)
        intro_text.setFont(self.font_vazir)
        intro_text.setAlignment(Qt.AlignCenter)
        intro_text.setStyleSheet("margin: 20px;")
        main_layout.addWidget(intro_text)

        # Cards grid (Right-to-left)
        cards = [
            ("1. تحلیل رسانه خاص", "تحلیل دقیق یک کانال یا رسانه مشخص در تلگرام."),
            ("2. تحلیل موضوعی", "دسته‌بندی و تحلیل موضوعات پرتکرار و تم‌ها."),
            ("3. تحلیل بر اساس زمان", "نمایش تغییراتِ موضوعات و فعالیت به‌صورت زمانی."),
            ("4. گزارش نویسی", "تولید گزارش خودکار (خلاصه، نقاط کلیدی، نمودارها)."),
            ("5. تحلیل و تشخیص ترند", "شناسایی ترندهای رو به رشد و نوسان‌ها."),
            ("6. داده های آماری", "متریک‌ها، جداول و نمودارهای خلاصه آماری."),
            ("7. تحلیل فرد", "تحلیل رفتار یک کاربر/چهره در تلگرام."),
            ("8. دیتابیس", "دسترسی به پایگاه داده رسانه‌ها و کاربران."),
        ]

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setAlignment(Qt.AlignRight)
        num_cols = 4

        # Keep references to pages
        self.pages = {}

        for idx, (title, desc) in enumerate(cards):
            btn = QPushButton(f"{title}\n\n{desc}")
            btn.setFont(self.font_vazir)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                    padding: 15px;
                    text-align: center;
                }
                QPushButton:hover {
                    border-color: #4fd1c5;
                    background: rgba(79, 209, 197, 0.1);
                }
                QPushButton:pressed {
                    background: rgba(79, 209, 197, 0.2);
                }
            """)
            btn.setMinimumHeight(100)
            btn.setLayoutDirection(Qt.RightToLeft)  # RTL

            # Top-right-first filling
            col = num_cols - 1 - (idx % num_cols)
            row = idx // num_cols
            grid_layout.addWidget(btn, row, col)

            # Connect first and second buttons to respective pages
            if idx == 0:
                btn.clicked.connect(self.open_media_analysis)
            elif idx == 1:
                btn.clicked.connect(self.open_topic_analysis)

        grid_group = QGroupBox()
        grid_group.setLayout(grid_layout)
        main_layout.addWidget(grid_group)

        # Footer
        footer_layout = QVBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)
        footer_text = QLabel(
            "© 2025 — طراحی رابط برای پروژه‌ی تحلیل تلگرام\n"
            "Developer: Omid Mollaei | Email: omidmollaei@ut.ac.ir\n"
            "Professors: Dr. Y.Yaghoob Zadeh & Dr. M.J Dousti\n"
            "Final project of large language models, University of Tehran, Spring of 1404"
        )
        footer_text.setFont(self.font_vazir)
        footer_text.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_text)

        # Footer images
        images_layout = QHBoxLayout()
        images_layout.setAlignment(Qt.AlignCenter)
        image_files = ["resources/ut.png", "resources/ece.png"]
        for img_file in image_files:
            pixmap = QPixmap(img_file)
            pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label = QLabel()
            img_label.setPixmap(pixmap)
            images_layout.addWidget(img_label)
        footer_layout.addLayout(images_layout)

        main_layout.addLayout(footer_layout)

        # Scroll area
        scroll = QScrollArea()
        content_widget = QWidget()
        content_widget.setLayout(main_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll)

    def open_media_analysis(self):
        self.pages['media'] = MediaAnalysisPage()
        self.pages['media'].show()

    def open_topic_analysis(self):
        self.pages['topic'] = TopicAnalysisPage()
        self.pages['topic'].show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeleLLMgramApp()
    window.show()
    sys.exit(app.exec_())
