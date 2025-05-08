# Email Forensics Analyzer Documentation

This documentation explains how the Email Forensics Analyzer works, its components, and how to use them. It's written for beginners who want to understand the code and potentially modify it.

## Table of Contents
1. [Overview](#overview)
2. [Core Components](#core-components)
3. [How It Works](#how-it-works)
4. [Code Structure](#code-structure)
5. [Key Functions](#key-functions)
6. [Examples](#examples)

## Overview

The Email Forensics Analyzer is a Python application that helps analyze email communications. It uses artificial intelligence (AI) to understand email patterns and relationships, and provides visual tools to help understand the data better.

## Core Components

### 1. Main Entry Points
- `run.py`: The GUI version of the application
- `main.py`: The command-line version of the application

### 2. Analysis Components
- `llm_analyzer.py`: Handles AI analysis using Ollama
- `visualisations.py`: Creates graphs and visualizations
- `prompts.py`: Contains AI prompts for analysis

### 3. Utility Components
- `email_parser.py`: Extracts data from emails
- `file_handler.py`: Manages file operations
- `utils.py`: Contains helper functions

## How It Works

### Step 1: Loading Emails
The program starts by:
1. Reading .eml files from a specified folder
2. Extracting email content and metadata
3. Filtering emails by date range

### Step 2: Analysis
The AI (using Ollama's Gemma3 model):
1. Analyzes email content
2. Identifies patterns and relationships
3. Generates insights about communications

### Step 3: Visualization
The program creates:
1. Network graphs showing who communicates with whom
2. Word clouds showing common themes
3. Statistical analysis of communication patterns

### Step 4: Interactive Q&A
Users can:
1. Ask questions about the emails
2. Get AI-powered answers
3. Explore specific aspects of the data

## Code Structure

### 1. Main Entry Points

#### run.py
```python
# Main GUI entry point
def main():
    app = QApplication(sys.argv)
    window = EmailAnalyzerApp()
    window.show()
    sys.exit(app.exec())
```
This file launches the graphical user interface.

#### main.py
```python
# Main CLI entry point
def main():
    # Parse command line arguments
    # Load and analyze emails
    # Start interactive Q&A
```
This file handles the command-line interface.

### 2. Analysis Components

#### llm_analyzer.py
Key functions:
- `analyze_emails_with_ollama()`: Main analysis function
- `prepare_email_summary()`: Creates email summaries
- `prepare_email_content()`: Prepares email content for analysis

#### visualisations.py
Key functions:
- `create_social_graph()`: Creates network graphs
- `visualize_social_graph()`: Displays the graphs
- `generate_wordcloud()`: Creates word clouds

### 3. Utility Components

#### email_parser.py
Handles:
- Email metadata extraction
- Content parsing
- Header analysis

#### file_handler.py
Manages:
- File reading
- Date filtering
- Content extraction

## Key Functions

### 1. Email Analysis
```python
def analyze_emails_with_ollama(email_texts):
    """
    Analyzes emails using AI
    Args:
        email_texts: List of email content
    Returns:
        Analysis results
    """
```

### 2. Network Visualization
```python
def create_social_graph(email_contents):
    """
    Creates a network graph
    Args:
        email_contents: List of email content
    Returns:
        Network graph object
    """
```

### 3. Word Cloud Generation
```python
def generate_wordcloud(text, output_file):
    """
    Creates a word cloud
    Args:
        text: Email content
        output_file: Where to save the image
    Returns:
        Path to saved image
    """
```

## Examples

### 1. Running the GUI
```python
python run.py
```

### 2. Running the CLI
```python
python main.py --folder /path/to/emails
```

### 3. Analyzing Emails
```python
# Example of email analysis
emails = load_emails("/path/to/emails")
results = analyze_emails_with_ollama(emails)
```

### 4. Creating Visualizations
```python
# Example of creating a network graph
graph = create_social_graph(emails)
visualize_social_graph(graph, "output.png")
```

## Tips for Beginners

1. **Start with the GUI**: Use `run.py` to get familiar with the program
2. **Check the Logs**: Look in the `logs` directory for helpful information
3. **Modify Prompts**: Edit `prompts.py` to change how the AI analyzes emails
4. **Add Visualizations**: Extend `visualisations.py` to add new types of graphs
5. **Test Changes**: Always test your changes with a small set of emails first

## Common Issues and Solutions

1. **No Emails Found**
   - Check the date range
   - Verify file paths
   - Ensure .eml files are valid

2. **AI Analysis Errors**
   - Make sure Ollama is running
   - Check if the model is installed
   - Verify internet connection

3. **Visualization Problems**
   - Update matplotlib and networkx
   - Check for sufficient memory
   - Verify output directory exists

## Next Steps

1. Try running the program with your own emails
2. Experiment with different AI prompts
3. Add your own visualizations
4. Share your improvements with the community 