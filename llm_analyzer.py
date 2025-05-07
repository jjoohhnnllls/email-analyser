"""
LLM Analyzer Module

This module handles the interaction with the Ollama Large Language Model.
It prepares email data for analysis and manages the conversation with the LLM.
"""

import sys
import ollama
import logging
from prompts import get_base_prompt, get_qa_prompt
import email
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

def prepare_email_summary(email_texts):
    """
    Prepare a summary of emails for the LLM with metadata and statistics.
    
    Args:
        email_texts (list): List of raw email content strings
        
    Returns:
        str: Formatted summary of the emails
    """
    logger.info("Preparing email summary for LLM")
    total_emails = len(email_texts)
    
    summary = []
    summary.append(f"TOTAL EMAILS: {total_emails}")
    
    # Analyze sender domains and collect subjects
    sender_domains = {}
    subjects = []
    email_senders = []

    for email_content in email_texts:
        try:
            msg = email.message_from_string(email_content)
            from_field = msg.get('From', '')
            subject_field = msg.get('Subject', '')
            if from_field:
                email_senders.append(from_field)
                if '@' in from_field:
                    domain = from_field.split('@')[1].split()[0].strip()
                    sender_domains[domain] = sender_domains.get(domain, 0) + 1
            if subject_field:
                subjects.append(subject_field.strip())
        except Exception as e:
            logger.warning(f"Error parsing email for summary: {e}")
    
    # Add sender domain statistics
    summary.append("\nSENDER DOMAINS:")
    for domain, count in sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        summary.append(f"- {domain}: {count} emails")
    
    # Add sender email addresses
    summary.append("\nSENDER EMAILS:")
    for email_addr in email_senders:
        summary.append(f"- {email_addr}")
    
    # Add sample subjects
    summary.append("\nSAMPLE SUBJECTS:")
    for subject in subjects[:10]:
        if subject:
            summary.append(f"- {subject}")
    
    return "\n".join(summary)

def prepare_email_content(email_texts):
    """
    Prepare full content of all emails for the LLM.
    
    Args:
        email_texts (list): List of raw email content strings
        
    Returns:
        str: Formatted content of all emails
    """
    logger.info("Preparing full email content for LLM")
    email_content = []
    
    for i, email_raw in enumerate(email_texts):
        try:
            msg = email.message_from_string(email_raw)
            subject = msg.get('Subject', '')
            from_field = msg.get('From', '')
            email_content.append(f"\nEMAIL #{i+1} - Subject: {subject} - From: {from_field}")
            email_content.append("=" * 80)
            # Try to extract the plain text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition'))
                    if 'attachment' in content_disposition:
                        continue
                    if content_type == 'text/plain':
                        try:
                            body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except Exception:
                            pass
            else:
                try:
                    body += msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception:
                    pass
            email_content.append(body)
            email_content.append("-" * 80)
        except Exception as e:
            logger.warning(f"Error parsing email for content: {e}")
    
    return "\n".join(email_content)

def analyze_emails_with_ollama(email_texts):
    """
    Analyze email texts using model and return the LLM report, email summary, and email content.
    Args:
        email_texts (list): List of raw email content strings
    Returns:
        dict: {'llm_report': ..., 'email_summary': ..., 'email_content': ...}
    """
    logger.info("Starting email analysis with Ollama")
    email_summary = prepare_email_summary(email_texts)
    email_content = prepare_email_content(email_texts)
    base_prompt = get_base_prompt()
    qa_prompt = get_qa_prompt()
    conversation_context = [
        {
            'role': 'system',
            'content': base_prompt
        },
        {
            'role': 'user',
            'content': f"""
### **Task:**

Please analyze the provided data, identify any relevant findings, and deliver a report or summary based on the following steps:

1. **Assessment:**
   - First mention the number of emails that you had analysed.
   - Review the provided digital evidence (files, logs, devices, etc.) to determine its significance.
   - Identify any potential anomalies, stories, suspicious patterns, or signs of cybercrime.

2. **Analysis:**
   - Apply forensic tools and methodologies to examine and analyse the emails.
   - Look for deleted files, metadata inconsistencies, encryption traces, or other forensic artifacts.
   - Cross-reference findings with known threats (e.g., malware signatures, hacking techniques).
   - Advise on what evidence to look towards and study.
   - I would want details such as names, places, dates and stories, and your suspected insights based on the emails, just like:
     - "This person was at this place at this time."
     - "This person contacted this email asking about a particular product or action."

3. **Reporting:**
   - Generate a clear, well-documented and complete report of all the emails summarizing your findings, including any relevant timeline, artifacts, or patterns.
   - Ensure that all conclusions are backed by the evidence and are legally sound.
   - Generate an overview or summary of all the emails analysed.

4. **Findings Collation:**
   - Outline your findings and follow up on how and why you got your findings.
   - Please make sure that your findings make sense.

You are analyzing a collection of {len(email_texts)} emails.

---

### **Email Dataset Overview:**

{email_summary}

---

### **Full Contents of the Emails:**

{email_content}

---

Please analyze this information and provide your insights. Be specific and highlight anything unusual or noteworthy. Include emojis as well to make the report more engaging.

---

### **Analyze the emails and *ONLY* respond in the following format:**

**Email Analysis Report**

**Date and Time Sent:**  
[timestamp]

**Summary of Email Content:**  
[summarize the main message]

**Key Points / Highlights:**  
[point 1]  
[point 2]  
[point 3]  

**Tone and Intent:**  
[describe the tone and intent]

**Notable Entities Identified:**  
[entity 1]  
[entity 2]  

**Potential Red Flags (if any):**  
[list if present]

**Overall Analysis/Conclusion:**  
[final thoughts or important insight]  
(Please do keep in mind you are a digital forensic investigator assistant, so it's important for the digital forensic investigator to know the list of names and organisations in the emails to gain some leads in forensic analysis)
"""

        }
    ]
    try:
        logger.info("Sending data to Ollama for analysis")
        response = ollama.chat(
            model='gemma3',
            messages=conversation_context
        )
        llm_report = response['message']['content']
        return {
            'llm_report': llm_report,
            'email_summary': email_summary,
            'email_content': email_content
        }
    except Exception as e:
        logger.error(f"Error analyzing emails with Ollama: {str(e)}")
        return {
            'llm_report': f"Error analyzing emails with Ollama: {str(e)}",
            'email_summary': email_summary,
            'email_content': email_content
        }

def analyze_emails_with_ollama_stream(email_texts):
    """
    Stream LLM markdown output for email analysis. Yields each markdown chunk as it arrives.
    Args:
        email_texts (list): List of raw email content strings
    Yields:
        str: Markdown chunk from the LLM
    """
    logger.info("Starting streaming email analysis with Ollama (markdown output)")
    email_summary = prepare_email_summary(email_texts)
    email_content = prepare_email_content(email_texts)
    base_prompt = get_base_prompt()
    conversation_context = [
        {
            'role': 'system',
            'content': base_prompt
        },
        {
            'role': 'user',
            'content': f'''
### **Task:**

Please analyze the provided data and deliver a concise, visually structured, and easy-to-read report in markdown. **Follow these formatting and content rules:**

- Use clear headings, subheadings, and whitespace.
- Use bullet points or numbered lists for key points.
- Limit each section to the 3–5 most important items.
- Use tables for statistics or lists if appropriate.
- Keep explanations concise (1–2 sentences per point).
- Avoid repeating information.
- Make the report visually scannable and easy to read.
- Use emojis for section headers or to highlight important points.

---

**Email Analysis Report**

**Date and Time Sent:**  
[timestamp]

**Summary of Email Content:**  
- [1–2 sentence summary]

**Key Points / Highlights:**  
- [Point 1]
- [Point 2]
- [Point 3]

**Statistics:**
| Metric         | Value |
| -------------- | ----- |
| Unique Senders |   X   |
| Top Sender     |   Y   |

**Notable Entities Identified:**  
- [Entity 1]
- [Entity 2]

**Potential Red Flags (if any):**  
- [Red flag 1]
- [Red flag 2]

**Overall Analysis/Conclusion:**  
- [1–2 sentence conclusion]

---

You are analyzing a collection of {len(email_texts)} emails.

### **Email Dataset Overview:**

{email_summary}

---

### **Full Contents of the Emails:**

{email_content}

---

**IMPORTANT:** Format your entire response using markdown. Do not repeat information. Make the report visually appealing and easy to scan for a digital forensics investigator. Do not include any other text or response other than the markdown.
'''
        }
    ]
    try:
        logger.info("Sending data to Ollama for streaming markdown analysis")
        response = ollama.chat(
            model='gemma3',
            messages=conversation_context,
            stream=True
        )
        for chunk in response:
            content = chunk['message']['content']
            yield content
    except Exception as e:
        logger.error(f"Error streaming analysis with Ollama: {str(e)}")
        yield f"**Error analyzing emails with Ollama:** {str(e)}"

class ChatWorker(QThread):
    """Worker thread for handling chat messages"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, email_texts, message, analysis_results=None, social_graph=None, stats=None):
        super().__init__()
        self.email_texts = email_texts
        self.message = message
        self.analysis_results = analysis_results
        self.social_graph = social_graph
        self.stats = stats
        
    def run(self):
        try:
            # Prepare context from analysis results
            context = []
            
            # Add email summary if available
            if self.analysis_results and 'email_summary' in self.analysis_results:
                context.append("Email Summary:")
                context.append(self.analysis_results['email_summary'])
            
            # Add network statistics if available
            if self.stats:
                context.append("\nNetwork Statistics:")
                if 'nodes' in self.stats:
                    context.append(f"Total unique contacts: {self.stats['nodes']}")
                if 'edges' in self.stats:
                    context.append(f"Total connections: {self.stats['edges']}")
                if 'top_senders' in self.stats:
                    context.append("\nTop Senders:")
                    for sender, count in self.stats['top_senders']:
                        context.append(f"- {sender}: {count} emails")
                if 'top_recipients' in self.stats:
                    context.append("\nTop Recipients:")
                    for recipient, count in self.stats['top_recipients']:
                        context.append(f"- {recipient}: {count} emails")
                if 'key_connectors' in self.stats:
                    context.append("\nKey Connectors:")
                    for person, score in self.stats['key_connectors']:
                        context.append(f"- {person}: {score:.4f} connection score")
            
            # Add LLM analysis if available
            if self.analysis_results and 'llm_report' in self.analysis_results:
                context.append("\nPrevious AI Analysis:")
                context.append(self.analysis_results['llm_report'])
            
            # Combine all context
            full_context = "\n".join(context)
            
            # Prepare prompt for Ollama
            prompt = f"""You are an AI assistant analyzing email communications. Here is the context from the email analysis:

{full_context}

Based on this context and the analyzed emails, please answer the following question:
{self.message}

Please provide a detailed and insightful response that:
1. Directly addresses the question using the available context
2. References specific patterns or findings from the email analysis
3. Provides concrete examples or statistics when relevant
4. Maintains a professional and analytical tone
5. Acknowledges any limitations in the available data

Your response:"""
            
            try:
                # Get response from Ollama
                response = ollama.chat(
                    model='gemma3',
                    messages=[{'role': 'user', 'content': prompt}]
                )
                
                self.finished.emit(response['message']['content'])
            except Exception as e:
                self.error.emit(f"Error connecting to Ollama: {str(e)}. Please ensure Ollama is running and the gemma3 model is installed.")
            
        except Exception as e:
            self.error.emit(str(e))

def get_chat_response(email_texts, message, analysis_results=None, social_graph=None, stats=None):
    """
    Get a response from the AI assistant for a chat message.
    
    Args:
        email_texts (list): List of email content strings
        message (str): The user's question
        analysis_results (dict): Results from previous analysis
        social_graph: The social network graph
        stats (dict): Network statistics
        
    Returns:
        ChatWorker: A worker thread that will emit the response
    """
    logger.info("Creating chat worker for AI response")
    worker = ChatWorker(email_texts, message, analysis_results, social_graph, stats)
    return worker
