# Email Forensics Analyzer

A modular Python tool for digital forensic analysis of email (.eml) files using large language models.

## Overview

Email Forensics Analyzer is designed to help digital forensic investigators analyze collections of email files by:

1. Parsing email metadata and content from .eml files
2. Filtering emails by date range
3. Using Ollama's Mistral LLM to analyze email content
4. Providing an interactive Q&A interface for investigators to query the emails

## Requirements

- Python 3.7 or higher
- Ollama installed and running locally (https://ollama.ai/)
- Mistral model pulled in Ollama (`ollama pull mistral`)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/email-forensics-analyzer.git
cd email-forensics-analyzer
```

2. Install required packages:
```
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the analyzer with:

```
python main.py --folder /path/to/email/files
```

You'll be prompted to enter:
- A date range for filtering emails (YYYY-MM-DD format)

The program will:
1. Find all .eml files in the specified folder
2. Filter them by the given date range
3. Analyze the emails using the Mistral LLM
4. Provide a comprehensive forensic report
5. Enter an interactive Q&A mode where you can ask specific questions about the emails

### Command Line Arguments

- `--folder`: Path to the folder containing .eml files
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)

Example:
```
python main.py --folder /path/to/emails --log-level DEBUG
```

## Project Structure

- `main.py` - Entry point of the application
- `email_parser.py` - Functions for extracting data from emails
- `file_handler.py` - Functions for loading emails from files
- `llm_analyzer.py` - Functions for interacting with Ollama LLM
- `prompts.py` - Store LLM prompts separately
- `utils.py` - Utility functions and logging setup

## Features

- **Modular Design**: Easily extend or modify individual components
- **Comprehensive Logging**: Track operations and debug issues
- **Interactive Q&A**: Ask specific questions about the analyzed emails
- **Date Filtering**: Focus only on emails within a specific timeframe
- **Detailed Reporting**: Get comprehensive forensic analysis with names, places, and organizations

## Customization

### Adding New Features

The modular design makes it easy to extend functionality:

1. To add new email parsing capabilities, modify `email_parser.py`
2. To change how emails are loaded, update `file_handler.py`
3. To improve LLM analysis, edit prompts in `prompts.py`
4. To add new commands or options, update argument parsing in `main.py`

### Changing LLM Models

To use a different Ollama model:

1. Pull the model using Ollama CLI: `ollama pull [model-name]`
2. Update the model name in `llm_analyzer.py`

## Troubleshooting

- **No emails found**: Check the date range and ensure emails have parseable date headers
- **Ollama connection error**: Make sure Ollama is running (`ollama serve`)
- **Unicode errors**: The program handles encoding issues, but some emails might have unusual character encoding

## Logs

Logs are stored in the `logs` directory with timestamps. Check these for debugging information if you encounter issues.

## Future Improvements

- Add support for other email formats beyond .eml
- Implement visualization of email connections and timelines
- Add export options for reports in PDF or HTML format
- Support for batch processing of multiple email folders
- Integration with other forensic tools and databases
