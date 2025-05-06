"""
Email Analyzer - Entry Point

This is the main entry point for the Email Analyzer application.
It can launch either the CLI or GUI version based on command line arguments.
"""

import sys
import argparse
from PyQt6.QtWidgets import QApplication

from main import main as cli_main
from emailanalyserUI import EmailAnalyzerApp

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Email Analyzer - CLI or GUI mode')
    parser.add_argument('--mode', type=str, choices=['cli', 'gui'], default='gui',
                      help='Run in CLI or GUI mode (default: gui)')
    parser.add_argument('--folder', type=str, help='Path to folder containing .eml files')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                      default='INFO', help='Set the logging level')
    
    return parser.parse_args()

def main():
    """
    Main entry point that launches either CLI or GUI version.
    """
    args = parse_arguments()
    
    if args.mode == 'cli':
        # Run CLI version
        sys.exit(cli_main())
    else:
        # Run GUI version
        app = QApplication(sys.argv)
        window = EmailAnalyzerApp()
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main() 