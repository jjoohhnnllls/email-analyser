"""
Email Analyzer - Main Module

This is the entry point for the Email Analyzer application.
It handles command line arguments and coordinates the analysis process.
"""

import sys
import argparse
import datetime
from pathlib import Path
import logging

from utils import setup_logging
from file_handler import get_emails_in_timeframe
from llm_analyzer import analyze_emails_with_ollama
from visualisations import create_social_graph, visualize_social_graph, analyze_network
from file_handler import get_raw_email_contents

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Analyze emails in a specified folder with interactive Q&A.')
    parser.add_argument('--folder', type=str, help='Path to folder containing .eml files')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Set the logging level')
    
    return parser.parse_args()

def main():
    """
    Main function to run the email analyzer application.
    """
    # Set up logging
    logger = setup_logging()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level from arguments
    log_level = getattr(logging, args.log_level)
    logger.setLevel(log_level)
    
    logger.info("Starting Email Analyzer application")
    
    # Get folder path from args or user input
    folder_path = args.folder
    if not folder_path:
        folder_path = input("Enter the path to the folder containing .eml files: ")
    
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        logger.error(f"The folder '{folder_path}' does not exist or is not a directory.")
        print(f"Error: The folder '{folder_path}' does not exist or is not a directory.")
        return 1
    
    # Get date range from user
    logger.info("Requesting date range from user")
    print("\nPlease specify the date range for emails to analyze.")
    try:
        start_date = datetime.datetime.strptime(input("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(input("Enter end date (YYYY-MM-DD): "), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        logger.info(f"Date range set: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return 1
    
    # Fetch emails in the specified date range
    print(f"\nFetching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    email_texts = get_emails_in_timeframe(folder_path, start_date, end_date)
    
    if not email_texts:
        logger.warning("No emails found in the specified date range")
        print("No emails found in the specified date range.")
        return 0
    
    logger.info(f"Found {len(email_texts)} emails in the specified date range")
    print(f"Found {len(email_texts)} emails in the specified date range.")
    print("\nAnalyzing emails with large language model...\n")
    
    # Create and analyze social graph
    print("\nCreating social graph of email communications...")
    raw_contents = get_raw_email_contents(email_texts)
    
    social_graph = create_social_graph(raw_contents)
    
    # Print network statistics
    stats = analyze_network(social_graph)
    print("\n======== Email Network Analysis ========")
    print(f"Total unique contacts: {stats['nodes']}")
    print(f"Total connections: {stats['edges']}")
    
    print("\nTop senders:")
    for sender, count in stats['top_senders']:
        print(f"- {sender}: {count} emails sent")
    
    print("\nTop recipients:")
    for recipient, count in stats['top_recipients']:
        print(f"- {recipient}: {count} emails received")
    
    if stats.get('key_connectors'):
        print("\nKey connectors (people who bridge communication groups):")
        for person, score in stats['key_connectors']:
            print(f"- {person}: {score:.4f}")
    
    # Ask user if they want to visualize the graph
    visualize = input("\nWould you like to visualize the email network? (y/n): ")
    if visualize.lower() in ['y', 'yes']:
        output_file = "outputs/email_network.png"
        visualize_social_graph(social_graph, output_file=output_file)
        print(f"\nNetwork visualization saved to {output_file}")


    # Analyze emails with LLM and start interactive Q&A
    analyze_emails_with_ollama(email_texts)
    
    logger.info("Email Analyzer application completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())