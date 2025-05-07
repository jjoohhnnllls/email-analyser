"""
Email Analyzer - Entry Point

This is the main entry point for the Email Analyzer application.
It can launch either the CLI or GUI version based on command line arguments.
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from main import main as cli_main
from emailanalyserUI import EmailAnalyzerApp
from utils import setup_logging

def setup_comprehensive_logging(log_level='INFO'):
    """
    Set up comprehensive logging for all components.
    
    Args:
        log_level (str): The logging level to use
    """
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Create a timestamp for the log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'email_analyzer_{timestamp}.log'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set up specific loggers for different components
    loggers = [
        'email_analyzer',
        'file_handler',
        'llm_analyzer',
        'visualisations',
        'utils',
        'emailanalyserUI'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level))
    
    # Log startup information
    logging.info(f"Starting Email Analyzer with log level: {log_level}")
    logging.info(f"Log file: {log_file}")
    
    return log_file

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
    
    # Set up logging
    log_file = setup_comprehensive_logging(args.log_level)
    
    try:
        if args.mode == 'cli':
            # Run CLI version
            logging.info("Starting in CLI mode")
            if args.folder:
                logging.info(f"Using specified folder: {args.folder}")
            sys.exit(cli_main())
        else:
            # Run GUI version
            logging.info("Starting in GUI mode")
            app = QApplication(sys.argv)
            window = EmailAnalyzerApp()
            window.show()
            logging.info("GUI window displayed")
            sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Application error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 