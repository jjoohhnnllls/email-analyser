# Email Forensics Analyzer

A powerful Python tool for analyzing email communications using artificial intelligence. This tool helps investigators and analysts understand email patterns, relationships, and content through advanced visualization and AI-powered analysis.

## 🌟 Features

- **Email Analysis**: Parse and analyze .eml files with detailed metadata extraction
- **AI-Powered Insights**: Uses Ollama's Gemma3 model for intelligent email analysis
- **Interactive Q&A**: Ask questions about your emails and get AI-powered answers
- **Network Visualization**: Create visual graphs of email communications
- **Word Cloud Generation**: Visualize common themes in email content
- **Date Range Filtering**: Focus on specific time periods
- **User-Friendly Interface**: Available in both GUI and CLI modes

## 📋 Requirements

- Python 3.7 or higher
- Ollama installed and running locally (https://ollama.ai/)
- Gemma3 model pulled in Ollama (`ollama pull gemma3`)

## 🚀 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/email-forensics-analyzer.git
cd email-forensics-analyzer
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Pull the required Ollama model:
```bash
ollama pull gemma3
```

## 💻 Usage

### GUI Mode (Recommended for Beginners)

Run the graphical interface:
```bash
python run.py
```

The GUI provides:
- Easy file selection
- Interactive date range picker
- Visual network graphs
- Word cloud generation
- Chat interface for asking questions

### CLI Mode

Run the command-line interface:
```bash
python main.py --folder /path/to/email/files
```

You'll be prompted to:
- Enter a date range (YYYY-MM-DD format)
- Choose whether to visualize the network
- Ask questions about the emails

## 📁 Project Structure

- `run.py` - Main entry point for GUI mode
- `main.py` - Entry point for CLI mode
- `llm_analyzer.py` - AI analysis using Ollama
- `visualisations.py` - Network graphs and word clouds
- `prompts.py` - AI prompts for analysis
- `email_parser.py` - Email parsing utilities
- `file_handler.py` - File operations
- `utils.py` - Helper functions

## 🔍 How It Works

1. **Email Loading**: The program reads .eml files from your specified folder
2. **Date Filtering**: Emails are filtered by your chosen date range
3. **Analysis**: The AI analyzes email content, relationships, and patterns
4. **Visualization**: Network graphs show communication patterns
5. **Interactive Q&A**: Ask questions about the emails in natural language

## 📊 Output Examples

- **Network Graph**: Shows who communicates with whom
- **Word Cloud**: Displays common themes in email content
- **AI Analysis**: Provides insights about communication patterns
- **Q&A Responses**: Answers specific questions about the emails

## 🛠️ Customization

### Changing AI Model

To use a different Ollama model:
1. Pull the model: `ollama pull [model-name]`
2. Update the model name in `llm_analyzer.py`

### Adding Features

The modular design makes it easy to extend:
- Add new visualizations in `visualisations.py`
- Modify AI prompts in `prompts.py`
- Add new analysis features in `llm_analyzer.py`

## 🔧 Troubleshooting

- **No emails found**: Check your date range and file paths
- **Ollama errors**: Ensure Ollama is running (`ollama serve`)
- **Visualization issues**: Check matplotlib and networkx installation
- **Encoding errors**: The program handles most encoding issues automatically

## 📝 Logs

Logs are stored in the `logs` directory with timestamps. Check these for:
- Error messages
- Operation details
- Debug information

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.



## 🔮 Future Improvements

- Support for more email formats
- Enhanced visualization options
- PDF/HTML report export
- Batch processing capabilities
- Integration with other forensic tools
