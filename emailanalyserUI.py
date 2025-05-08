import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QStackedWidget, QFileDialog, QCheckBox,
                            QFrame, QScrollArea, QTextEdit, QListWidget, QSplitter,
                            QDateEdit, QMessageBox, QProgressBar, QTextBrowser, QComboBox, QDialog)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, QDate, QThread, pyqtSignal, QTimer
import datetime
from pathlib import Path
import logging
import markdown2
import ollama
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import os

from utils import setup_logging
from file_handler import get_emails_in_timeframe, get_raw_email_contents
from llm_analyzer import analyze_emails_with_ollama, get_chat_response
from visualisations import create_social_graph, visualize_social_graph, analyze_network, generate_wordcloud, create_email_heatmap

class AnalysisWorker(QThread):
    """Worker thread for running email analysis"""
    progress = pyqtSignal(int)  # Signal for progress updates (0-100)
    finished = pyqtSignal(dict)  # Signal for completion with results
    error = pyqtSignal(str)  # Signal for error messages
    visualization_ready = pyqtSignal(str, str)  # Signal for visualization updates (type, path)

    def __init__(self, folder_path, start_date, end_date):
        super().__init__()
        self.folder_path = folder_path
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            # Load emails within timeframe
            self.progress.emit(10)
            email_texts = get_emails_in_timeframe(self.folder_path, self.start_date, self.end_date)
            
            if not email_texts:
                self.error.emit("No emails found in the specified date range")
                return
            
            # Create social graph
            self.progress.emit(30)
            raw_contents = get_raw_email_contents(email_texts)
            social_graph = create_social_graph(raw_contents)
            
            # Analyze network
            self.progress.emit(50)
            stats = analyze_network(social_graph)
            
            # Perform LLM analysis
            self.progress.emit(70)
            analysis_results = analyze_emails_with_ollama(email_texts)
            
            # Generate visualizations in the worker thread
            self.progress.emit(80)
            
            # Generate network visualization
            network_output = "outputs/email_network.png"
            visualize_social_graph(social_graph, output_file=network_output)
            self.visualization_ready.emit("network", network_output)
            
            # Generate word cloud
            all_text = ' '.join(email_texts)
            wordcloud_output = generate_wordcloud(all_text)
            if wordcloud_output:
                self.visualization_ready.emit("wordcloud", wordcloud_output)
            
            # Generate initial heatmap
            heatmap_output = create_email_heatmap(email_texts, timeframe='daily')
            if heatmap_output:
                self.visualization_ready.emit("heatmap", heatmap_output)
            
            # Prepare results dictionary
            results = {
                'email_texts': email_texts,
                'social_graph': social_graph,
                'stats': stats,
                'analysis': analysis_results
            }
            
            # Emit results
            self.progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class HeatmapWorker(QThread):
    """Worker thread for generating heatmap visualizations"""
    finished = pyqtSignal(str)  # Signal for completion with file path
    error = pyqtSignal(str)  # Signal for error messages

    def __init__(self, email_texts, timeframe, output_file):
        super().__init__()
        self.email_texts = email_texts
        self.timeframe = timeframe
        self.output_file = output_file

    def run(self):
        try:
            heatmap_path = create_email_heatmap(
                self.email_texts,
                timeframe=self.timeframe,
                output_file=self.output_file
            )
            if heatmap_path:
                self.finished.emit(heatmap_path)
            else:
                self.error.emit("Failed to generate heatmap")
        except Exception as e:
            self.error.emit(str(e))

class VisualizationWindow(QDialog):
    """Window for displaying interactive visualizations"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1000, 800)  # Made window larger
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8))  # Made figure larger
        self.canvas = FigureCanvas(self.figure)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        
        # Add canvas
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Enable interactive features
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.canvas.setFocus()
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

class EmailAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Expert Singapore - Email Forensics Analyzer")
        self.setMinimumSize(1200, 800)
        
        # State tracking
        self.is_analysis_complete = False
        self.current_results = None
        self.logger = setup_logging()
        self.worker = None
        
        # Initialize widgets as None
        self.llm_report_browser = None
        self.email_summary_browser = None
        self.network_stats_browser = None
        self.wordcloud_label = None
        self.network_viz = None
        self.heatmap_viz = None
        self.timeframe_combo = None
        
        # Initialize visualization windows
        self.network_window = None
        self.wordcloud_window = None
        self.heatmap_window = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(80)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar.setStyleSheet("background-color: #1F2937;")
        
        # Logo at top of sidebar
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create stylized logo (in a real app, you would use an actual image)
        logo_label = QLabel()
        logo_label.setFixedSize(40, 40)
        logo_label.setStyleSheet("background-color: rgba(239, 68, 68, 0.7); border-radius: 20px;")
        logo_layout.addWidget(logo_label)
        
        company_label = QLabel("DATA\nEXPERT")
        company_label.setStyleSheet("color: white; font-weight: bold; font-size: 9px; text-align: center;")
        company_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(company_label)
        
        sidebar_layout.addWidget(logo_widget)
        sidebar_layout.addSpacing(20)
        
        # Navigation buttons
        self.upload_btn = self.create_sidebar_button("📁", "Upload")
        self.analyze_btn = self.create_sidebar_button("🔍", "Analyze")
        self.report_btn = self.create_sidebar_button("📊", "Report")
        self.chat_btn = self.create_sidebar_button("💬", "Chat")
        
        sidebar_layout.addWidget(self.upload_btn)
        sidebar_layout.addWidget(self.analyze_btn)
        sidebar_layout.addWidget(self.report_btn)
        sidebar_layout.addWidget(self.chat_btn)
        
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)
        
        # Content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #E5E7EB;")
        header_layout = QHBoxLayout(header)
        
        title_label = QLabel("Email Forensics Analyzer")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #374151;")
        
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        content_layout.addWidget(header)
        
        # Stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # Create pages
        self.upload_page = self.create_upload_page()
        self.analyze_page = self.create_analyze_page()
        self.report_page = self.create_report_page()
        self.chat_page = self.create_chat_page()
        
        self.stacked_widget.addWidget(self.upload_page)
        self.stacked_widget.addWidget(self.analyze_page)
        self.stacked_widget.addWidget(self.report_page)
        self.stacked_widget.addWidget(self.chat_page)
        
        main_layout.addWidget(content_area)
        
        # Connect signals
        self.upload_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.analyze_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.report_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.chat_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # Start on upload page
        self.stacked_widget.setCurrentIndex(0)
        self.upload_btn.setStyleSheet(self.upload_btn.styleSheet() + "background-color: #DC2626;")
    
    def create_sidebar_button(self, icon_text, tooltip):
        btn = QPushButton(icon_text)
        btn.setFixedSize(60, 60)
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                font-size: 24px;
                color: white;
                background-color: transparent;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        return btn
    
    def create_upload_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Upload Email Data")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        # Drop area
        drop_area = QFrame()
        drop_area.setFrameShape(QFrame.Shape.StyledPanel)
        drop_area.setFrameShadow(QFrame.Shadow.Plain)
        drop_area.setStyleSheet("""
            QFrame {
                border: 2px dashed #D1D5DB;
                border-radius: 8px;
                background-color: #F9FAFB;
            }
        """)
        drop_layout = QVBoxLayout(drop_area)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drop_icon = QLabel("📄")
        drop_icon.setStyleSheet("font-size: 48px; color: #9CA3AF;")
        drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drop_text = QLabel("Select the folder containing the emails")
        drop_text.setStyleSheet("font-size: 18px; color: #374151;")
        drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drop_format = QLabel("Supports .eml formats")
        drop_format.setStyleSheet("font-size: 14px; color: #6B7280;")
        drop_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add file label
        self.file_label = QLabel("No folder selected")
        self.file_label.setStyleSheet("font-size: 14px; color: #6B7280;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        browse_btn = QPushButton("Browse Files")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        browse_btn.clicked.connect(self.select_files)
        
        drop_layout.addWidget(drop_icon)
        drop_layout.addWidget(drop_text)
        drop_layout.addWidget(drop_format)
        drop_layout.addWidget(self.file_label)
        drop_layout.addSpacing(15)
        drop_layout.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(drop_area)
        layout.addStretch()
        
        # Continue button
        continue_btn = QPushButton("Continue →")
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        continue_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(continue_btn)
        layout.addLayout(button_layout)
        
        return page
    
    def create_analyze_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Analyze Email Data")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        # Date range selection
        date_frame = QFrame()
        date_frame.setFrameShape(QFrame.Shape.StyledPanel)
        date_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        date_layout = QVBoxLayout(date_frame)
        
        date_title = QLabel("Select Date Range")
        date_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
        
        date_range_widget = QWidget()
        date_range_layout = QHBoxLayout(date_range_widget)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.end_date)
        date_range_layout.addStretch()
        
        date_layout.addWidget(date_title)
        date_layout.addWidget(date_range_widget)
        
        layout.addWidget(date_frame)
        layout.addSpacing(15)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Start analysis button
        self.analyze_btn = QPushButton("Start Analysis 🔍")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        self.analyze_btn.clicked.connect(self.run_analysis)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.analyze_btn)
        layout.addLayout(button_layout)
        
        return page
    
    def create_report_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Analysis Report")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        # Create scroll area for report content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # AI Analysis Report section
        ai_report_title = QLabel("AI Analysis Report")
        ai_report_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827; margin-top: 10px;")
        self.llm_report_browser = QTextBrowser()
        self.llm_report_browser.setOpenExternalLinks(True)
        self.llm_report_browser.setStyleSheet("font-size: 14px; background: #F9FAFB; border: none; padding: 8px; border-radius: 6px;")
        self.llm_report_browser.setMinimumHeight(250)
        scroll_layout.addWidget(ai_report_title)
        scroll_layout.addWidget(self.llm_report_browser)
        
        # Email Summary section
        summary_title = QLabel("Email Summary")
        summary_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827; margin-top: 20px;")
        self.email_summary_browser = QTextBrowser()
        self.email_summary_browser.setOpenExternalLinks(True)
        self.email_summary_browser.setStyleSheet("font-size: 13px; background: #F3F4F6; border: none; padding: 8px; border-radius: 6px;")
        self.email_summary_browser.setMinimumHeight(300)
        scroll_layout.addWidget(summary_title)
        scroll_layout.addWidget(self.email_summary_browser)
        
        # Network Statistics section
        network_stats_title = QLabel("Network Statistics")
        network_stats_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827; margin-top: 20px;")
        self.network_stats_browser = QTextBrowser()
        self.network_stats_browser.setOpenExternalLinks(True)
        self.network_stats_browser.setStyleSheet("font-size: 13px; background: #F3F4F6; border: none; padding: 8px; border-radius: 6px;")
        self.network_stats_browser.setMinimumHeight(300)
        scroll_layout.addWidget(network_stats_title)
        scroll_layout.addWidget(self.network_stats_browser)
        
        # Network visualization section
        network_frame = QFrame()
        network_frame.setFrameShape(QFrame.Shape.StyledPanel)
        network_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        network_layout = QVBoxLayout(network_frame)
        network_title = QLabel("Communication Network")
        network_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        self.network_viz = QLabel()
        self.network_viz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.network_viz.setFixedHeight(250)
        self.network_viz.setStyleSheet("background-color: #F3F4F6; border-radius: 4px;")
        
        # Add interactive button for network graph
        network_btn = QPushButton("View Network Graph")
        network_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        network_btn.clicked.connect(self.show_network_graph)
        
        network_layout.addWidget(network_title)
        network_layout.addWidget(self.network_viz)
        network_layout.addWidget(network_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add network frame to scroll layout
        scroll_layout.addSpacing(20)
        scroll_layout.addWidget(network_frame)
        
        # Word Cloud section with interactive button
        wordcloud_frame = QFrame()
        wordcloud_frame.setFrameShape(QFrame.Shape.StyledPanel)
        wordcloud_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        wordcloud_layout = QVBoxLayout(wordcloud_frame)
        
        wordcloud_title = QLabel("Word Cloud Analysis")
        wordcloud_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        self.wordcloud_label = QLabel()
        self.wordcloud_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wordcloud_label.setMinimumHeight(300)
        self.wordcloud_label.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #E5E7EB;")
        
        # Add interactive button for word cloud
        wordcloud_btn = QPushButton("View Word Cloud")
        wordcloud_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        wordcloud_btn.clicked.connect(self.show_wordcloud)
        
        wordcloud_layout.addWidget(wordcloud_title)
        wordcloud_layout.addWidget(self.wordcloud_label)
        wordcloud_layout.addWidget(wordcloud_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        scroll_layout.addWidget(wordcloud_frame)
        
        # Add heatmap visualization section
        heatmap_frame = QFrame()
        heatmap_frame.setFrameShape(QFrame.Shape.StyledPanel)
        heatmap_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        heatmap_layout = QVBoxLayout(heatmap_frame)
        
        # Heatmap title and controls
        heatmap_header = QWidget()
        heatmap_header_layout = QHBoxLayout(heatmap_header)
        
        heatmap_title = QLabel("Email Volume Analysis")
        heatmap_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        
        # Timeframe selector
        timeframe_label = QLabel("Timeframe:")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.timeframe_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                padding: 5px;
                background: white;
            }
        """)
        self.timeframe_combo.currentTextChanged.connect(self.update_heatmap)
        
        heatmap_header_layout.addWidget(heatmap_title)
        heatmap_header_layout.addStretch()
        heatmap_header_layout.addWidget(timeframe_label)
        heatmap_header_layout.addWidget(self.timeframe_combo)
        
        # Heatmap visualization
        self.heatmap_viz = QLabel()
        self.heatmap_viz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.heatmap_viz.setFixedHeight(300)
        self.heatmap_viz.setStyleSheet("background-color: #F3F4F6; border-radius: 4px;")
        
        # Add interactive button for heatmap
        heatmap_btn = QPushButton("View Heatmap")
        heatmap_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        heatmap_btn.clicked.connect(self.show_heatmap)
        
        heatmap_layout.addWidget(heatmap_header)
        heatmap_layout.addWidget(self.heatmap_viz)
        heatmap_layout.addWidget(heatmap_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add heatmap frame to scroll layout
        scroll_layout.addSpacing(20)
        scroll_layout.addWidget(heatmap_frame)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Ask AI button
        ask_ai_btn = QPushButton("Ask AI about findings 💬")
        ask_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        ask_ai_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ask_ai_btn)
        layout.addLayout(button_layout)
        
        return page
    
    def create_chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("AI Assistant")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        # Chat container
        chat_frame = QFrame()
        chat_frame.setFrameShape(QFrame.Shape.StyledPanel)
        chat_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        chat_layout = QVBoxLayout(chat_frame)
        
        # Chat header
        chat_header = QLabel("Ask questions about the analyzed email data")
        chat_header.setStyleSheet("color: #6B7280; padding: 10px 0;")
        
        # Chat messages area
        self.chat_messages = QScrollArea()
        self.chat_messages.setWidgetResizable(True)
        self.chat_messages.setStyleSheet("border: none;")
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(15)
        
        self.chat_messages.setWidget(self.messages_widget)
        
        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Ask a question about the analyzed emails...")
        self.chat_input.setMaximumHeight(80)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 1px solid #DC2626;
            }
        """)
        
        send_btn = QPushButton("Send")
        send_btn.setFixedSize(80, 40)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
            }
        """)
        send_btn.clicked.connect(self.send_chat_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        
        # Add all elements to chat layout
        chat_layout.addWidget(chat_header)
        chat_layout.addWidget(self.chat_messages)
        chat_layout.addWidget(input_widget)
        
        layout.addWidget(chat_frame)
        
        return page
    
    def select_files(self):
        """Open file dialog to select email files"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Email Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            self.selected_files = folder_path
            self.file_label.setText(f"Selected folder: {folder_path}")
            self.analyze_btn.setEnabled(True)
    
    def send_chat_message(self):
        if not self.is_analysis_complete:
            QMessageBox.warning(self, "No Analysis", "Please analyze emails first before asking questions.")
            return
            
        message = self.chat_input.toPlainText().strip()
        if not message:
            return
            
        # Add user message to chat
        self.add_chat_message(message, is_user=True)
        self.chat_input.clear()
        
        # Show loading message
        loading_msg = "AI is thinking..."
        loading_frame = self.add_chat_message(loading_msg, is_user=False)
        
        # Create worker for LLM response with full context
        self.chat_worker = get_chat_response(
            self.current_results['email_texts'],
            message,
            analysis_results=self.current_results['analysis'],
            social_graph=self.current_results['social_graph'],
            stats=self.current_results['stats']
        )
        self.chat_worker.finished.connect(lambda response: self.handle_chat_response(response, loading_frame))
        self.chat_worker.error.connect(lambda error: self.handle_chat_error(error, loading_frame))
        self.chat_worker.start()
        
    def add_chat_message(self, message, is_user=True):
        msg_frame = QFrame()
        msg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#F3F4F6' if is_user else '#FEF2F2'};
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }}
        """)
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setContentsMargins(15, 10, 15, 10)
        
        # Add sender label
        sender_label = QLabel("You" if is_user else "AI Assistant")
        sender_label.setStyleSheet("font-weight: bold; color: #374151;")
        msg_layout.addWidget(sender_label)
        
        # Add message text
        msg_text = QLabel(message)
        msg_text.setWordWrap(True)
        msg_text.setStyleSheet("color: #1F2937;")
        msg_layout.addWidget(msg_text)
        
        self.messages_layout.addWidget(msg_frame)
        
        # Scroll to bottom using the scroll area
        QTimer.singleShot(100, lambda: self.scroll_to_bottom())
        
        return msg_frame
        
    def scroll_to_bottom(self):
        """Scroll the chat messages to the bottom"""
        if self.chat_messages:
            self.chat_messages.verticalScrollBar().setValue(
                self.chat_messages.verticalScrollBar().maximum()
            )
    
    def handle_chat_response(self, response, loading_frame):
        # Remove loading message
        self.messages_layout.removeWidget(loading_frame)
        loading_frame.deleteLater()
        
        # Add AI response
        self.add_chat_message(response, is_user=False)
        
    def handle_chat_error(self, error, loading_frame):
        # Remove loading message
        self.messages_layout.removeWidget(loading_frame)
        loading_frame.deleteLater()
        
        # Show error message
        self.add_chat_message(f"Error: {error}", is_user=False)
    
    def run_analysis(self):
        """Start the email analysis process"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select a folder containing email files first.")
            return
        
        # Get date range
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # Create and start worker
        self.worker = AnalysisWorker(self.selected_files, start_date, end_date)
        
        # Connect signals
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.handle_analysis_complete)
        self.worker.visualization_ready.connect(self.update_visualization)
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.analyze_btn.setEnabled(False)
        self.worker.start()

    def update_visualization(self, viz_type, file_path):
        """Update a specific visualization from the worker thread"""
        try:
            if viz_type == "network" and hasattr(self, 'network_viz') and self.network_viz is not None:
                pixmap = QPixmap(file_path)
                self.network_viz.setPixmap(pixmap.scaled(
                    self.network_viz.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            elif viz_type == "wordcloud" and hasattr(self, 'wordcloud_label') and self.wordcloud_label is not None:
                pixmap = QPixmap(file_path)
                self.wordcloud_label.setPixmap(pixmap.scaled(
                    self.wordcloud_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            elif viz_type == "heatmap" and hasattr(self, 'heatmap_viz') and self.heatmap_viz is not None:
                pixmap = QPixmap(file_path)
                self.heatmap_viz.setPixmap(pixmap.scaled(
                    self.heatmap_viz.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
        except Exception as e:
            self.logger.error(f"Error updating {viz_type} visualization: {str(e)}")

    def handle_analysis_complete(self, results):
        """Handle analysis completion"""
        try:
            if not isinstance(results, dict):
                self.show_error("Invalid analysis results received")
                return
                
            self.current_results = results
            self.is_analysis_complete = True
            
            # Update UI
            self.progress_bar.setVisible(False)
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("Start Analysis 🔍")
            
            # Enable report and chat buttons
            self.report_btn.setEnabled(True)
            self.chat_btn.setEnabled(True)
            
            # Switch to report page
            self.stacked_widget.setCurrentIndex(2)
            self.update_report_page()
            
        except Exception as e:
            self.logger.error(f"Error handling analysis completion: {str(e)}")
            self.show_error(f"Error updating report: {str(e)}")

    def show_error(self, error_message):
        """Handle analysis errors"""
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("Start Analysis 🔍")

    def update_report_page(self):
        """Update the report page with analysis results"""
        try:
            if not self.current_results:
                return
            
            stats = self.current_results['stats']
            analysis_results = self.current_results['analysis']
            llm_report = analysis_results.get('llm_report', '')
            email_summary = analysis_results.get('email_summary', '')
            email_texts = self.current_results.get('email_texts', [])
            
            # Check if widgets exist before updating
            if hasattr(self, 'llm_report_browser') and self.llm_report_browser is not None:
                try:
                    # Convert markdown to HTML for display
                    html = markdown2.markdown(llm_report)
                    self.llm_report_browser.setHtml(html)
                except Exception as e:
                    self.logger.error(f"Error updating LLM report: {str(e)}")
            
            if hasattr(self, 'email_summary_browser') and self.email_summary_browser is not None:
                try:
                    # Email summary as plain text
                    self.email_summary_browser.setPlainText(email_summary)
                except Exception as e:
                    self.logger.error(f"Error updating email summary: {str(e)}")
            
            if hasattr(self, 'network_stats_browser') and self.network_stats_browser is not None:
                try:
                    # Network stats as plain text
                    network_stats = []
                    network_stats.append(f"Nodes (Unique Contacts): {stats.get('nodes', 0)}")
                    network_stats.append(f"Edges (Connections): {stats.get('edges', 0)}")
                    if stats.get('top_senders'):
                        network_stats.append("\nTop Senders:")
                        for sender, count in stats['top_senders']:
                            network_stats.append(f"- {sender}: {count}")
                    if stats.get('top_recipients'):
                        network_stats.append("\nTop Recipients:")
                        for recipient, count in stats['top_recipients']:
                            network_stats.append(f"- {recipient}: {count}")
                    if stats.get('key_connectors'):
                        network_stats.append("\nKey Connectors:")
                        for person, score in stats['key_connectors']:
                            network_stats.append(f"- {person}: {score:.4f}")
                    
                    self.network_stats_browser.setPlainText('\n'.join(network_stats))
                except Exception as e:
                    self.logger.error(f"Error updating network stats: {str(e)}")
            
            # Generate and display word cloud
            if email_texts and hasattr(self, 'wordcloud_label') and self.wordcloud_label is not None:
                try:
                    # Combine all email texts
                    all_text = ' '.join(email_texts)
                    wordcloud_path = generate_wordcloud(all_text)
                    if wordcloud_path:
                        wordcloud_pixmap = QPixmap(wordcloud_path)
                        self.wordcloud_label.setPixmap(wordcloud_pixmap.scaled(
                            self.wordcloud_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        ))
                except Exception as e:
                    self.logger.error(f"Error updating word cloud: {str(e)}")
            
            # Generate and display network visualization
            if (self.current_results.get('social_graph') and 
                hasattr(self, 'network_viz') and 
                self.network_viz is not None):
                try:
                    output_file = "outputs/email_network.png"
                    visualize_social_graph(self.current_results['social_graph'], output_file=output_file)
                    pixmap = QPixmap(output_file)
                    self.network_viz.setPixmap(pixmap.scaled(
                        self.network_viz.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio
                    ))
                except Exception as e:
                    self.logger.error(f"Error updating network visualization: {str(e)}")
            
            # Update heatmap
            if hasattr(self, 'heatmap_viz') and self.heatmap_viz is not None:
                try:
                    self.update_heatmap()
                except Exception as e:
                    self.logger.error(f"Error updating heatmap: {str(e)}")
            
            self.chat_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error updating report page: {str(e)}")
            QMessageBox.warning(self, "Update Error", 
                              "There was an error updating the report page. Some visualizations may not be displayed correctly.")

    def update_heatmap(self):
        """Update the heatmap visualization based on selected timeframe"""
        try:
            if not self.is_analysis_complete or not self.current_results:
                return
                
            if not hasattr(self, 'timeframe_combo') or self.timeframe_combo is None:
                self.logger.error("Timeframe combo box not initialized")
                return
                
            timeframe = self.timeframe_combo.currentText().lower()
            output_file = f"outputs/email_heatmap_{timeframe}.png"
            
            # Create and start worker thread
            self.heatmap_worker = HeatmapWorker(
                self.current_results['email_texts'],
                timeframe,
                output_file
            )
            
            # Connect signals
            self.heatmap_worker.finished.connect(
                lambda path: self.update_visualization("heatmap", path)
            )
            self.heatmap_worker.error.connect(
                lambda error: self.logger.error(f"Error generating heatmap: {error}")
            )
            
            # Start the worker
            self.heatmap_worker.start()
            
        except Exception as e:
            self.logger.error(f"Error updating heatmap: {str(e)}")
            QMessageBox.warning(self, "Heatmap Error", 
                              "There was an error updating the heatmap visualization.")

    def show_network_graph(self):
        """Show the interactive network graph in a separate window"""
        if not self.is_analysis_complete or not self.current_results:
            return
            
        if not self.network_window:
            self.network_window = VisualizationWindow("Email Communication Network")
        
        # Clear previous figure
        self.network_window.figure.clear()
        
        # Create new plot
        ax = self.network_window.figure.add_subplot(111)
        visualize_social_graph(self.current_results['social_graph'], ax=ax)
        
        # Update canvas
        self.network_window.canvas.draw()
        self.network_window.show()

    def show_wordcloud(self):
        """Show the interactive word cloud in a separate window"""
        if not self.is_analysis_complete or not self.current_results:
            return
            
        if not self.wordcloud_window:
            self.wordcloud_window = VisualizationWindow("Word Cloud Analysis")
        
        # Clear previous figure
        self.wordcloud_window.figure.clear()
        
        # Create new plot
        ax = self.wordcloud_window.figure.add_subplot(111)
        
        # Load the existing word cloud image
        wordcloud_path = "outputs/wordcloud.png"
        if os.path.exists(wordcloud_path):
            img = plt.imread(wordcloud_path)
            ax.imshow(img)
            ax.axis('off')
        else:
            # Fallback to generating new word cloud if file doesn't exist
            all_text = ' '.join(self.current_results['email_texts'])
            generate_wordcloud(all_text, ax=ax)
        
        # Update canvas
        self.wordcloud_window.canvas.draw()
        self.wordcloud_window.show()

    def show_heatmap(self):
        """Show the interactive heatmap in a separate window"""
        if not self.is_analysis_complete or not self.current_results:
            return
            
        if not self.heatmap_window:
            self.heatmap_window = VisualizationWindow("Email Volume Analysis")
        
        # Clear previous figure
        self.heatmap_window.figure.clear()
        
        # Create new plot
        ax = self.heatmap_window.figure.add_subplot(111)
        
        # Load the existing heatmap image
        timeframe = self.timeframe_combo.currentText().lower()
        heatmap_path = f"outputs/email_heatmap_{timeframe}.png"
        if os.path.exists(heatmap_path):
            img = plt.imread(heatmap_path)
            ax.imshow(img)
            ax.axis('off')
        else:
            # Fallback to generating new heatmap if file doesn't exist
            create_email_heatmap(
                self.current_results['email_texts'],
                timeframe=timeframe,
                ax=ax
            )
        
        # Update canvas
        self.heatmap_window.canvas.draw()
        self.heatmap_window.show()

# Main application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmailAnalyzerApp()
    window.show()
    sys.exit(app.exec())