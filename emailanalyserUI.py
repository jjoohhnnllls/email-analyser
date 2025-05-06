import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QStackedWidget, QFileDialog, QCheckBox,
                            QFrame, QScrollArea, QTextEdit, QListWidget, QSplitter,
                            QDateEdit, QMessageBox, QProgressBar, QTextBrowser)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, QDate, QThread, pyqtSignal
import datetime
from pathlib import Path
import logging
import markdown2

from utils import setup_logging
from file_handler import get_emails_in_timeframe, get_raw_email_contents
from llm_analyzer import analyze_emails_with_ollama
from visualisations import create_social_graph, visualize_social_graph, analyze_network

class AnalysisWorker(QThread):
    """Worker thread for running email analysis"""
    progress = pyqtSignal(int)  # Signal for progress updates (0-100)
    finished = pyqtSignal(dict)  # Signal for completion with results
    error = pyqtSignal(str)  # Signal for error messages

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
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # Report content area
        content_area = QWidget()
        layout = QVBoxLayout(content_area)
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
        self.email_summary_browser.setMinimumHeight(120)
        scroll_layout.addWidget(summary_title)
        scroll_layout.addWidget(self.email_summary_browser)
        # Network Statistics section
        network_stats_title = QLabel("Network Statistics")
        network_stats_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827; margin-top: 20px;")
        self.network_stats_browser = QTextBrowser()
        self.network_stats_browser.setOpenExternalLinks(True)
        self.network_stats_browser.setStyleSheet("font-size: 13px; background: #F3F4F6; border: none; padding: 8px; border-radius: 6px;")
        self.network_stats_browser.setMinimumHeight(120)
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
        network_layout.addWidget(network_title)
        network_layout.addWidget(self.network_viz)
        # Add sections to scroll layout
        scroll_layout.addSpacing(20)
        scroll_layout.addWidget(network_frame)
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
        # Sidebar for report sections
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #F9FAFB; border-left: 1px solid #E5E7EB;")
        sidebar_layout = QVBoxLayout(sidebar)
        sections_label = QLabel("Report Sections")
        sections_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #374151;")
        sections_list = QListWidget()
        sections_list.addItems([
            "Summary",
            "Communication Network",
            "Timeline Analysis",
            "Entity Relationships",
            "Anomaly Detection",
            "Attachment Analysis"
        ])
        sections_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #FEE2E2;
                color: #DC2626;
            }
        """)
        sections_list.setCurrentRow(0)
        export_label = QLabel("Export Options")
        export_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #374151; margin-top: 20px;")
        export_pdf_btn = QPushButton("📄 PDF Report")
        export_pdf_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        export_evidence_btn = QPushButton("👁️ Evidence View")
        export_evidence_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        sidebar_layout.addWidget(sections_label)
        sidebar_layout.addWidget(sections_list)
        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(export_label)
        sidebar_layout.addWidget(export_pdf_btn)
        sidebar_layout.addWidget(export_evidence_btn)
        sidebar_layout.addStretch()
        main_layout.addWidget(content_area)
        main_layout.addWidget(sidebar)
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
        chat_messages = QScrollArea()
        chat_messages.setWidgetResizable(True)
        chat_messages.setStyleSheet("border: none;")
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(15)
        
        chat_messages.setWidget(self.messages_widget)
        
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
        chat_layout.addWidget(chat_messages)
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
        
        # Create worker for LLM response
        self.chat_worker = ChatWorker(self.current_results['email_texts'], message)
        self.chat_worker.finished.connect(lambda response: self.add_chat_message(response, is_user=False))
        self.chat_worker.error.connect(lambda error: QMessageBox.critical(self, "Error", error))
        self.chat_worker.start()
        
    def add_chat_message(self, message, is_user=True):
        msg_frame = QFrame()
        msg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#F3F4F6' if is_user else '#FEF2F2'};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.setContentsMargins(15, 10, 15, 10)
        
        msg_text = QLabel(message)
        msg_text.setWordWrap(True)
        msg_layout.addWidget(msg_text)
        
        self.messages_layout.addWidget(msg_frame)
        
        # Scroll to bottom
        QApplication.processEvents()
        self.messages_widget.parent().verticalScrollBar().setValue(
            self.messages_widget.parent().verticalScrollBar().maximum()
        )
    
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
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.analyze_btn.setEnabled(False)
        self.worker.start()

    def handle_analysis_complete(self, results):
        """Handle analysis completion"""
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

    def show_error(self, error_message):
        """Handle analysis errors"""
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("Start Analysis 🔍")

    def update_report_page(self):
        """Update the report page with analysis results"""
        if not self.current_results:
            return
        stats = self.current_results['stats']
        analysis_results = self.current_results['analysis']
        llm_report = analysis_results.get('llm_report', '')
        email_summary = analysis_results.get('email_summary', '')
        # Convert markdown to HTML for display
        html = markdown2.markdown(llm_report)
        self.llm_report_browser.setHtml(html)
        # Email summary as simple HTML
        summary_html = f'<ul>' + ''.join(f'<li>{line}</li>' for line in email_summary.split('\n') if line.strip()) + '</ul>'
        self.email_summary_browser.setHtml(summary_html)
        # Network stats as simple HTML
        network_stats = []
        network_stats.append(f"<b>Nodes (Unique Contacts):</b> {stats.get('nodes', 0)}")
        network_stats.append(f"<b>Edges (Connections):</b> {stats.get('edges', 0)}")
        if stats.get('top_senders'):
            network_stats.append("<b>Top Senders:</b><ul>" + ''.join(f'<li>{sender}: {count}</li>' for sender, count in stats['top_senders']) + "</ul>")
        if stats.get('top_recipients'):
            network_stats.append("<b>Top Recipients:</b><ul>" + ''.join(f'<li>{recipient}: {count}</li>' for recipient, count in stats['top_recipients']) + "</ul>")
        if stats.get('key_connectors'):
            network_stats.append("<b>Key Connectors:</b><ul>" + ''.join(f'<li>{person}: {score:.4f}</li>' for person, score in stats['key_connectors']) + "</ul>")
        self.network_stats_browser.setHtml('<br>'.join(network_stats))
        # Generate and display network visualization
        if self.current_results.get('social_graph'):
            output_file = "outputs/email_network.png"
            visualize_social_graph(self.current_results['social_graph'], output_file=output_file)
            pixmap = QPixmap(output_file)
            self.network_viz.setPixmap(pixmap.scaled(self.network_viz.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.chat_btn.setEnabled(True)

class ChatWorker(QThread):
    """Worker thread for handling chat messages"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, email_texts, message):
        super().__init__()
        self.email_texts = email_texts
        self.message = message
        
    def run(self):
        try:
            # Prepare prompt for Ollama
            prompt = f"""Based on the analyzed emails, please answer the following question:
            
{self.message}

Please provide a detailed and insightful response, focusing on any patterns, anomalies, or important findings from the email analysis."""
            
            # Get response from Ollama
            response = ollama.chat(
                model='mistral',
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            self.finished.emit(response['message']['content'])
            
        except Exception as e:
            self.error.emit(str(e))

# Main application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmailAnalyzerApp()
    window.show()
    sys.exit(app.exec())