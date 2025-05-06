# Email Analyzer

A powerful email analysis tool for digital forensics investigators that uses large language models to analyze email communications and generate insights.

## Features

- Email parsing and analysis (.eml, .msg, .pst, .mbox formats)
- Date range filtering
- Social network analysis
- Entity extraction
- Sentiment analysis
- Thread reconstruction
- Anomaly detection
- Interactive AI-powered Q&A
- Beautiful and intuitive user interface
- Command-line interface for automation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/email-analyzer.git
cd email-analyzer
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Ollama (required for LLM analysis):
- Follow the instructions at https://ollama.ai/download
- Pull the Mistral model:
```bash
ollama pull mistral
```

## Usage

### GUI Mode (Default)

Run the program with the graphical user interface:

```bash
python run.py
```

The GUI provides:
- File selection and upload
- Date range selection
- Analysis options configuration
- Interactive results visualization
- AI-powered chat interface
- Export capabilities

### CLI Mode

Run the program in command-line mode:

```bash
python run.py --mode cli
```

Additional CLI options:
```bash
python run.py --mode cli --folder /path/to/emails --log-level DEBUG
```

## Analysis Features

### Email Processing
- Parses various email formats (.eml, .msg, .pst, .mbox)
- Extracts metadata (sender, recipient, date, subject)
- Handles attachments and embedded content

### Network Analysis
- Creates social graphs of email communications
- Identifies key connectors and communication patterns
- Visualizes network relationships
- Detects anomalies in communication patterns

### AI Analysis
- Uses Ollama's Mistral model for deep analysis
- Provides insights on communication patterns
- Identifies potential security concerns
- Answers questions about the analyzed data

## Output

The program generates:
- Network visualizations (saved as PNG)
- Analysis reports
- Log files
- Interactive visualizations in the GUI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
