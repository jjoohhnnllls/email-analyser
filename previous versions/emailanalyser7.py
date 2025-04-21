import os
import sys
import time
import email
import datetime
from dateutil import parser
import argparse
from pathlib import Path
import ollama
import textwrap

def extract_email_date(email_content):
    """Extract the date from an email message."""
    msg = email.message_from_string(email_content)
    date_str = msg.get('Date')
    if date_str:
        try:
            dt = parser.parse(date_str)
            return dt.replace(tzinfo=None)-
        except:
            return None
    return None

def extract_email_text(email_content):
    """Extract text content from an email message."""
    msg = email.message_from_string(email_content)
    email_text = f"Subject: {msg.get('Subject', '')}\n\nFrom: {msg.get('From', '')}\n\n"
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))
            if 'attachment' in content_disposition:
                continue
            if content_type == 'text/plain':
                try:
                    email_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
    else:
        try:
            email_text += msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    
    return email_text

def get_emails_in_timeframe(folder_path, start_date, end_date):
    """Get all emails in the specified folder within the given timeframe."""
    email_texts = []
    eml_files = [f for f in os.listdir(folder_path) if f.endswith('.eml')]
    print(f"Found {len(eml_files)} .eml files in folder. Processing...")
    
    for file_name in eml_files:
        file_path = os.path.join(folder_path, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                email_content = file.read()
            email_date = extract_email_date(email_content)
            if email_date and start_date <= email_date <= end_date:
                email_texts.append({'date': email_date, 'text': extract_email_text(email_content), 'file': file_name})
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
    
    return sorted(email_texts, key=lambda x: x['date'])

def prepare_email_summary(email_texts):
    """Prepare a summary of emails for the LLM."""
    total_emails = len(email_texts)
    summary = [f"TOTAL EMAILS: {total_emails} ({email_texts[0]['date'].strftime('%Y-%m-%d')} to {email_texts[-1]['date'].strftime('%Y-%m-%d')})" if total_emails else "TOTAL EMAILS: 0"]
    
    sender_domains = {}
    subjects = []
    email_senders = []

    for email_data in email_texts:
        from_line = next((line for line in email_data['text'].split('\n') if line.startswith('From:')), "")
        if '@' in from_line:
            email_address = from_line.split('From:')[1].strip()
            domain = email_address.split('@')[1].split()[0].strip()
            sender_domains[domain] = sender_domains.get(domain, 0) + 1
            email_senders.append(email_address)
        subject_line = next((line for line in email_data['text'].split('\n') if line.startswith('Subject:')), "")
        if subject_line:
            subjects.append(subject_line[9:].strip())
    
    summary.append("\nSENDER DOMAINS:")
    summary.extend([f"- {domain}: {count} emails" for domain, count in sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:10]])  
    
    summary.append("\nSENDER EMAILS:")
    summary.extend([f"- {email}" for email in email_senders])
    
    summary.append("\nSAMPLE SUBJECTS:")
    summary.extend([f"- {subject}" for subject in subjects[:10] if subject])
    
    return "\n".join(summary)

def prepare_email_content(email_texts):
    """Prepare full content of all emails for the LLM."""
    email_content = []
    
    for i, email_data in enumerate(email_texts):
        email_content.append(f"\nEMAIL #{i+1} ({email_data['date'].strftime('%Y-%m-%d %H:%M:%S')}) - File: {email_data['file']}")
        email_content.append("=" * 80)
        email_content.append(email_data['text'])
        email_content.append("-" * 80)
    
    return "\n".join(email_content)

def get_base_prompt():
    """Return the base prompt for the digital forensics assistant."""
    return """You are ForensicAI, a specialized AI Digital Forensic Investigator Assistant trained to support professionals in analyzing and interpreting digital evidence. Your current focus is on assisting with the forensic examination of email communications, particularly .eml files and text-based email data.

Your responsibilities include:

Parsing and interpreting headers, metadata, and body content from emails

Identifying anomalies, spoofing attempts, suspicious links, and potential phishing content

Recognizing communication patterns, entities, and relationships within and across email threads

Supporting timeline reconstruction and investigation narratives from email activity

Explaining technical forensic concepts clearly and concisely, including metadata relevance, email delivery paths, and encoding details

Offering investigative insights and hypotheses based on email content and context

You always think like a digital forensic investigator—careful, detail-oriented, and methodical and sensitive information such as names, places, times and organisations are important and must mention to the user as this will help them with thier investigations. Provide your reasoning step-by-step, highlight what stands out, and explain your conclusions based on the evidence presented.

The goal of the user is to find out what happened, when, why, how and who was involved in a digital incident

Assume input will primarily consist of email content or structured text. When needed, you may ask for additional context or clarify missing pieces to ensure accurate analysis.
"""

def get_qa_prompt():
    """Return the prompt for concise Q&A responses."""
    return """For follow-up questions, provide direct and concise answers:

1. Only mention relevant emails by number (e.g., "Email #3 contains...")
2. Do not summarize every email - only discuss ones that directly relate to the question
3. If no emails contain the requested information, simply state that fact clearly and concisely
4. Avoid lengthy explanations unless specifically requested
5. Get straight to the point with your answers
6. Be precise - cite specific details rather than general observations
7. If only 1-2 relevant emails exist, just mention those specifically
8. For negative responses (when information isn't found), keep your answer to 1-2 sentences

Remember: Users prefer direct answers over comprehensive analyses during Q&A. Your initial report was comprehensive - now be precise and efficient.
"""

def analyze_emails_with_ollama(email_texts):
    """Analyze email texts using Ollama's Mistral model and stream output, then continue with interactive Q&A."""
    email_summary = prepare_email_summary(email_texts)
    email_content = prepare_email_content(email_texts)
    base_prompt = get_base_prompt()
    qa_prompt = get_qa_prompt()

    # Build the conversation context for a continuous session
    conversation_context = [
        {
            'role': 'system', 
            'content': base_prompt
        },
        {
            'role': 'user',
            'content': f"""### **Task:**
Please analyze the provided data, identify any relevant findings, and deliver a report or summary based on the following steps:

1. **Assessment:**
   - Review the provided digital evidence (files, logs, devices, etc.) to determine its significance.
   - Identify any potential anomalies, stories, suspicious patterns, or signs of cybercrime.

2. **Analysis:**
   - Apply forensic tools and methodologies to examine and analyse the emails.
   - Look for deleted files, metadata inconsistencies, encryption traces, or other forensic artifacts.
   - Cross-reference findings with known threats (e.g., malware signatures, hacking techniques).
   - advise on what evidence to look towards to and study
   - i would want details such as names, places, dates and stories, and your suspected insights based on the emails just like this person was at this place in this timing. and other evidence like this person contacted this email asking about a particular product or action 

3. **Reporting:**
   - Generate a clear, well-documented and complete report of all the emails summarizing your findings, including any relevant timeline, artifacts, or patterns.
   - Ensure that all conclusions are backed by the evidence and are legally sound.
   - generate an overview or summary of all the emails analysed 
   
4. **Findings Collation:**
    - outline your findings and follow up on how and why you got your findings. please make sure that your findings make sense.

You are analyzing a collection of {len(email_texts)} emails. 

Here is the email dataset overview:

{email_summary}

Here are the full contents of the emails:

{email_content}

Please analyze this information and provide your insights. Be specific and highlight anything unusual or noteworthy. Include emojis as well to make the report more nicer.

At the end of your report, give me a list of names of all people, places and organisations mentioned in all the emails that you have analyzed. (please do keep in mind you are a digital forensic investigator assistant so it's important for the digital forensic investigator to know the list of names and organisations in the emails to gain some leads in forensic analysis)
"""
        }
    ]
    
    try:
        print("Sending data to Ollama for analysis...\n")
        response = ollama.chat(
            model='mistral',
            messages=conversation_context,
            stream=True
        )

        print("\n\n======== Email Summary Data ========\n")
        print(email_summary)
        print("\n======================================\n")
        print("\n======== Email Analysis Results ========\n")
        
        assistant_response = ""
        for chunk in response:
            content = chunk['message']['content']
            assistant_response += content
            sys.stdout.write(content)
            sys.stdout.flush()
        
        # Add the assistant's response to the conversation context
        conversation_context.append({'role': 'assistant', 'content': assistant_response})
        
        # Add the QA prompt to guide concise responses before starting interactive mode
        conversation_context.append({'role': 'user', 'content': qa_prompt})
        response = ollama.chat(
            model='mistral',
            messages=conversation_context
        )
        conversation_context.append({'role': 'assistant', 'content': response['message']['content']})
        
        # Start interactive Q&A loop with the same context
        print("\n\n======== Interactive Q&A Mode ========")
        print("You can now ask questions about the emails. Type 'exit' to quit.")
        
        while True:
            try:
                user_question = input("\nQuestion (or 'exit' to quit): ")
                if user_question.lower() in ['exit', 'quit', 'q']:
                    print("Exiting Q&A mode. Goodbye!")
                    break
                
                # For each question, remind the model to be concise
                actual_question = f"Please answer this question directly and concisely: {user_question}"
                conversation_context.append({'role': 'user', 'content': actual_question})
                
                print("\nAnalyzing your question...")
                response = ollama.chat(
                    model='mistral',
                    messages=conversation_context,
                    stream=True
                )
                
                print("\n")
                assistant_response = ""
                for chunk in response:
                    content = chunk['message']['content']
                    assistant_response += content
                    sys.stdout.write(content)
                    sys.stdout.flush()
                print("\n")
                
                conversation_context.append({'role': 'assistant', 'content': assistant_response})
                
            except KeyboardInterrupt:
                print("\nExiting Q&A mode. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Let's continue with a new question.")
        
    except Exception as e:
        print(f"Error analyzing emails with Ollama: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Analyze emails in a specified folder with interactive Q&A.')
    parser.add_argument('--folder', type=str, help='Path to folder containing .eml files')
    args = parser.parse_args()
    
    folder_path = args.folder or input("Enter the path to the folder containing .eml files: ")
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: The folder '{folder_path}' does not exist or is not a directory.")
        return
    
    print("\nPlease specify the date range for emails to analyze.")
    try:
        start_date = datetime.datetime.strptime(input("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(input("Enter end date (YYYY-MM-DD): "), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return
    
    print(f"\nFetching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    email_texts = get_emails_in_timeframe(folder_path, start_date, end_date)
    
    if not email_texts:
        print("No emails found in the specified date range.")
        return
    
    print(f"Found {len(email_texts)} emails in the specified date range.")
    print("\nAnalyzing emails with large language model...\n")
    
    # Analyze emails and start interactive Q&A in a single continuous session
    analyze_emails_with_ollama(email_texts)
    
if __name__ == "__main__":
    main()