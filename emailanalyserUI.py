import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QStackedWidget, QFileDialog, QCheckBox,
                            QFrame, QScrollArea, QTextEdit, QListWidget, QSplitter)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize


class EmailAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Expert Singapore - Email Forensics Analyzer")
        self.setMinimumSize(1200, 800)
        
        # State tracking
        self.analysis_complete = False
        
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
        
        drop_text = QLabel("Drag and drop email files here")
        drop_text.setStyleSheet("font-size: 18px; color: #374151;")
        drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drop_format = QLabel("Supports .eml, .msg, .pst, and .mbox formats")
        drop_format.setStyleSheet("font-size: 14px; color: #6B7280;")
        drop_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
        browse_btn.clicked.connect(self.browse_files)
        
        drop_layout.addWidget(drop_icon)
        drop_layout.addWidget(drop_text)
        drop_layout.addWidget(drop_format)
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
        
        # Email sources section
        sources_frame = QFrame()
        sources_frame.setFrameShape(QFrame.Shape.StyledPanel)
        sources_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        sources_layout = QVBoxLayout(sources_frame)
        
        sources_title = QLabel("Email Sources")
        sources_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
        
        sources_items = QWidget()
        sources_items_layout = QHBoxLayout(sources_items)
        sources_items_layout.setContentsMargins(0, 0, 0, 0)
        
        source1 = QFrame()
        source1.setStyleSheet("""
            QFrame {
                background-color: #F3F4F6;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        source1_layout = QHBoxLayout(source1)
        source1_layout.setContentsMargins(10, 5, 10, 5)
        source1_label = QLabel("📄 emails_july2024.pst")
        source1_label.setStyleSheet("color: #374151;")
        source1_layout.addWidget(source1_label)
        
        source2 = QFrame()
        source2.setStyleSheet("""
            QFrame {
                background-color: #F3F4F6;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        source2_layout = QHBoxLayout(source2)
        source2_layout.setContentsMargins(10, 5, 10, 5)
        source2_label = QLabel("📄 investigation_emails.mbox")
        source2_label.setStyleSheet("color: #374151;")
        source2_layout.addWidget(source2_label)
        
        sources_items_layout.addWidget(source1)
        sources_items_layout.addWidget(source2)
        sources_items_layout.addStretch()
        
        sources_layout.addWidget(sources_title)
        sources_layout.addWidget(sources_items)
        
        layout.addWidget(sources_frame)
        layout.addSpacing(15)
        
        # Analysis options section
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.Shape.StyledPanel)
        options_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        options_layout = QVBoxLayout(options_frame)
        
        options_title = QLabel("Analysis Options")
        options_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
        
        options_grid = QWidget()
        options_grid_layout = QHBoxLayout(options_grid)
        options_grid_layout.setContentsMargins(0, 0, 0, 0)
        
        options_col1 = QVBoxLayout()
        options_col2 = QVBoxLayout()
        
        # Create checkboxes
        option1 = QCheckBox("Entity extraction")
        option2 = QCheckBox("Sentiment analysis")
        option3 = QCheckBox("Thread reconstruction")
        option4 = QCheckBox("Anomaly detection")
        option5 = QCheckBox("Header analysis")
        option6 = QCheckBox("Attachment inspection")
        
        # Set all checked by default
        for option in [option1, option2, option3, option4, option5, option6]:
            option.setChecked(True)
            option.setStyleSheet("QCheckBox { color: #374151; }")
        
        options_col1.addWidget(option1)
        options_col1.addWidget(option2)
        options_col1.addWidget(option3)
        
        options_col2.addWidget(option4)
        options_col2.addWidget(option5)
        options_col2.addWidget(option6)
        
        options_grid_layout.addLayout(options_col1)
        options_grid_layout.addLayout(options_col2)
        
        options_layout.addWidget(options_title)
        options_layout.addWidget(options_grid)
        
        layout.addWidget(options_frame)
        layout.addStretch()
        
        # Start analysis button
        analyze_btn = QPushButton("Start Analysis 🔍")
        analyze_btn.setStyleSheet("""
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
        analyze_btn.clicked.connect(self.run_analysis)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(analyze_btn)
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
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        
        # Header
        summary_header = QWidget()
        summary_header_layout = QVBoxLayout(summary_header)
        summary_header_layout.setContentsMargins(0, 0, 0, 15)
        
        summary_title = QLabel("Email Analysis Summary")
        summary_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        
        summary_date = QLabel("Completed on April 21, 2025 at 14:32")
        summary_date.setStyleSheet("color: #6B7280;")
        
        summary_header_layout.addWidget(summary_title)
        summary_header_layout.addWidget(summary_date)
        
        # Stats section
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 15, 0, 15)
        
        stat1 = QLabel("<b>Total Emails Analyzed:</b> 5,247")
        stat2 = QLabel("<b>Time Period:</b> Jan 2025 - Mar 2025")
        stat3 = QLabel("<b>Unique Senders:</b> 187")
        
        stats_layout.addWidget(stat1)
        stats_layout.addWidget(stat2)
        stats_layout.addWidget(stat3)
        
        # Key findings
        findings_title = QLabel("Key Findings")
        findings_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827; margin-top: 10px;")
        
        finding1 = QLabel("⚠️ <b>Suspicious Communication Patterns</b><br>3 email clusters detected with unusual timing patterns")
        finding1.setStyleSheet("color: #374151; margin-top: 5px;")
        
        finding2 = QLabel("⚠️ <b>Potential Data Exfiltration</b><br>Large attachments sent to external domains")
        finding2.setStyleSheet("color: #374151; margin-top: 5px;")
        
        finding3 = QLabel("⚠️ <b>Security Policy Violations</b><br>Financial data shared via unencrypted channels")
        finding3.setStyleSheet("color: #374151; margin-top: 5px;")
        
        # Add all widgets to summary layout
        summary_layout.addWidget(summary_header)
        summary_layout.addWidget(QLabel(""))  # Separator
        summary_layout.addWidget(stats_widget)
        summary_layout.addWidget(QLabel(""))  # Separator
        summary_layout.addWidget(findings_title)
        summary_layout.addWidget(finding1)
        summary_layout.addWidget(finding2)
        summary_layout.addWidget(finding3)
        
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
        
        network_viz = QLabel("[Network Visualization Graph]")
        network_viz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        network_viz.setFixedHeight(250)
        network_viz.setStyleSheet("background-color: #F3F4F6; border-radius: 4px;")
        
        network_layout.addWidget(network_title)
        network_layout.addWidget(network_viz)
        
        # Add sections to scroll layout
        scroll_layout.addWidget(summary_frame)
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
        
        messages_widget = QWidget()
        messages_layout = QVBoxLayout(messages_widget)
        messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        messages_layout.setSpacing(15)
        
        # Sample messages
        user_msg1 = QFrame()
        user_msg1.setStyleSheet("background-color: #F3F4F6; border-radius: 8px; padding: 10px;")
        user_msg1_layout = QVBoxLayout(user_msg1)
        user_msg1_layout.setContentsMargins(15, 10, 15, 10)
        user_msg1_text = QLabel("What are the main topics discussed in these emails?")
        user_msg1_layout.addWidget(user_msg1_text)
        
        ai_msg1 = QFrame()
        ai_msg1.setStyleSheet("background-color: #FEF2F2; border-radius: 8px; padding: 10px;")
        ai_msg1_layout = QVBoxLayout(ai_msg1)
        ai_msg1_layout.setContentsMargins(15, 10, 15, 10)
        ai_msg1_text = QLabel("Based on my analysis, there are 3 primary topics discussed:<br><br>"
                             "1. Project Alpha financial reporting (42% of communications)<br>"
                             "2. Server infrastructure updates (27% of communications)<br>"
                             "3. Client meeting preparations (18% of communications)<br><br>"
                             "The remaining communications cover miscellaneous topics including HR announcements and social events.")
        ai_msg1_text.setWordWrap(True)
        ai_msg1_layout.addWidget(ai_msg1_text)
        
        user_msg2 = QFrame()
        user_msg2.setStyleSheet("background-color: #F3F4F6; border-radius: 8px; padding: 10px;")
        user_msg2_layout = QVBoxLayout(user_msg2)
        user_msg2_layout.setContentsMargins(15, 10, 15, 10)
        user_msg2_text = QLabel("Who communicated most frequently with external domains?")
        user_msg2_layout.addWidget(user_msg2_text)
        
        ai_msg2 = QFrame()
        ai_msg2.setStyleSheet("background-color: #FEF2F2; border-radius: 8px; padding: 10px;")
        ai_msg2_layout = QVBoxLayout(ai_msg2)
        ai_msg2_layout.setContentsMargins(15, 10, 15, 10)
        ai_msg2_text = QLabel("User john.smith@dataexpert.sg had the highest volume of external communications "
                             "(214 emails), primarily with clients at acme-corp.com and consultant-group.com domains.<br><br>"
                             "Would you like me to provide more details about these communications?")
        ai_msg2_text.setWordWrap(True)
        ai_msg2_layout.addWidget(ai_msg2_text)
        
        # Add messages to layout
        messages_layout.addWidget(user_msg1)
        messages_layout.addWidget(ai_msg1)
        messages_layout.addWidget(user_msg2)
        messages_layout.addWidget(ai_msg2)
        messages_layout.addStretch()
        
        chat_messages.setWidget(messages_widget)
        
        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        chat_input = QTextEdit()
        chat_input.setPlaceholderText("Ask a question about the analyzed emails...")
        chat_input.setMaximumHeight(80)
        chat_input.setStyleSheet("""
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
        
        input_layout.addWidget(chat_input)
        input_layout.addWidget(send_btn)
        
        # Add all elements to chat layout
        chat_layout.addWidget(chat_header)
        chat_layout.addWidget(chat_messages)
        chat_layout.addWidget(input_widget)
        
        layout.addWidget(chat_frame)
        
        return page
    
    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Email Files",
            "",
            "Email Files (*.eml *.msg *.pst *.mbox);;All Files (*)"
        )
        # In a real app, you would process these files
        if files:
            print(f"Selected files: {files}")
    
    def run_analysis(self):
        # In a real app, this would start the actual analysis process
        # For demo purposes, we'll just switch to the report page after a delay
        self.analyze_btn.setText("Analyzing...")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #9CA3AF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
            }
        """)
        self.analyze_btn.setEnabled(False)
        
        # Simulate analysis delay
        QApplication.processEvents()
        import time
        time.sleep(2)  # In a real app, you would use QTimer instead
        
        # Complete analysis and update UI
        self.analysis_complete = True
        self.report_btn.setEnabled(True)
        self.chat_btn.setEnabled(True)
        self.stacked_widget.setCurrentIndex(2)  # Switch to report page
        self.report_btn.setStyleSheet(self.report_btn.styleSheet() + "background-color: #DC2626;")
        self.analyze_btn.setText("Start Analysis 🔍")
        self.analyze_btn.setEnabled(True)
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

# Main application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmailAnalyzerApp()
    window.show()
    sys.exit(app.exec())