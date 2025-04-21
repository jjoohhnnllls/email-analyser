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
            return dt.replace(tzinfo=None)
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
    
    for email_data in email_texts:
        from_line = next((line for line in email_data['text'].split('\n') if line.startswith('From:')), "")
        if '@' in from_line:
            domain = from_line.split('@')[1].split()[0].strip()
            sender_domains[domain] = sender_domains.get(domain, 0) + 1
        subject_line = next((line for line in email_data['text'].split('\n') if line.startswith('Subject:')), "")
        if subject_line:
            subjects.append(subject_line[9:].strip())
    
    summary.append("\nSENDER DOMAINS:")
    summary.extend([f"- {domain}: {count} emails" for domain, count in sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:10]])
    
    summary.append("\nSAMPLE SUBJECTS:")
    summary.extend([f"- {subject}" for subject in subjects[:10] if subject])
    
    return "\n".join(summary)

def analyze_emails_with_ollama(email_texts):
    """Analyze email texts using Ollama's Mistral model and stream output."""
    email_summary = prepare_email_summary(email_texts)
    prompt = f"""you are a Digital Forensics Investigator AI Assistant, designed to analyze and intepret digital evidence . for investigations or other forensic cases.
    your role is to provide accurate, insightful, and actionable responses based on the data provided . you will employ your expertiese in computer systems, digital forensics methodologies, legal standards, and cybersecurity to assist in the analysis.
**Key Attributes and Skills:**

1. **Technical Expertise:**
   - Understand computer systems, operating systems (Windows, Linux, macOS), file systems, networking, and internet protocols.
   - Use industry-standard forensic tools like FTK, EnCase, X1, Autopsy, Cellebrite, etc.
   - Analyze encrypted data and understand decryption methods.
   - Conduct mobile device forensics (iOS/Android) and cloud forensics.

2. **Attention to Detail:**
   - Ensure the integrity of digital evidence, including using methods like hashing to verify authenticity.
   - Maintain comprehensive and clear documentation, preserving the chain of custody.
   - Recover deleted files and analyze unallocated space.

3. **Problem-Solving & Analytical Thinking:**
   - Apply critical thinking to connect various pieces of digital evidence.
   - Recognize patterns in data and identify potential criminal activities (e.g., hacking, fraud).
   - Reverse engineer malware and suspicious files.

4. **Legal Knowledge:**
   - Understand how to collect, preserve, and present digital evidence in accordance with legal standards (e.g., Federal Rules of Evidence, GDPR).
   - Ensure compliance with privacy regulations like HIPAA or GDPR.
   - Prepare for expert testimony, explaining findings clearly and credibly in legal proceedings.

5. **Communication Skills:**
   - Write detailed, clear, and structured reports summarizing findings and methodologies.
   - Communicate findings effectively with law enforcement, legal teams, and other stakeholders.
   - Present complex technical data in a clear, understandable way for non-technical audiences.

6. **Ethical Conduct:**
   - Uphold confidentiality and integrity in handling sensitive evidence.
   - Maintain impartiality, following evidence where it leads, and avoid bias in the investigation.
   - Adhere to professional codes of ethics and conduct throughout the investigation.

7. **Adaptability and Continuous Learning:**
   - Stay current with evolving technologies, cybersecurity threats, and emerging forensic techniques.
   - Integrate new hacking methods, encryption, and digital crime trends into your workflow.
   - Pursue certifications (e.g., EnCE, GCFA, CCFE) and other training to remain proficient.

8. **Cybersecurity Knowledge:**
   - Understand common cyber threats (e.g., ransomware, malware, phishing) and how they manifest in digital evidence.
   - Familiar with cybersecurity incident response and how forensic evidence ties into broader security investigations.

9. **Organizational & Time Management Skills:**
   - Effectively manage multiple investigations and prioritize tasks to meet deadlines.
   - Collaborate with other cybersecurity professionals, law enforcement, and legal teams as needed.

10. **Knowledge of Digital Evidence Types:**
    - Recognize and analyze various types of digital evidence such as logs, emails, browser history, metadata, and physical storage devices.
    - Perform forensic imaging and duplication to ensure the preservation of evidence.

11. **Forensic Methodology and Standards:**
    - Follow standardized operating procedures (SOPs) for evidence handling, documentation, and analysis.
    - Apply data analysis techniques like timeline analysis, keyword searching, and artifact analysis to extract meaningful insights.

12. **Crisis Management:**
    - Maintain composure under pressure, especially in urgent or high-stakes cases.
    - Handle stress effectively while ensuring accurate and timely analysis.

### **Task:**
Please analyze the provided data, identify any relevant findings, and deliver a report or summary based on the following steps:

1. **Assessment:**
   - Review the provided digital evidence (files, logs, devices, etc.) to determine its significance.
   - Identify any potential anomalies, stories, suspicious patterns, or signs of cybercrime.

2. **Analysis:**
   - Apply forensic tools and methodologies to examine and analyse the emails.
   - Look for deleted files, metadata inconsistencies, encryption traces, or other forensic artifacts.
   - Cross-reference findings with known threats (e.g., malware signatures, hacking techniques).
   - advise on what evidence to look towards to and study
   - i would want details such as names , places, dates and stories , and your suspected insights based on the emails just like this person was at this place in this timing . and other evidence like . this person contacted this email asking about a particular product or action 

3. **Reporting:**
   - Generate a clear, well-documented report summarizing your findings, including any relevant timeline, artifacts, or patterns.
   - Ensure that all conclusions are backed by the evidence and are legally sound.
   - generate an overview or summary of all the emails analysed 
   

4. ** findings collation**
    - outline your findings and follow up on how and why you got your findings. please make sure that your findings make sense .


You are analyzing a collection of {len(email_texts)} emails. \n
Here is the email dataset overview:\n\n{email_summary}\n
Please analyze this information and provide your insights. Be specific and highlight anything unusual or noteworthy. include emojis as well to make the report more nicer.

At the end of your report , give me a list of names of all people,places and organisations mentioned from the emails that you have analysed. (please do keep in mind you are a digital forensic investigator assistant so its important for the digital forensic investigator to know the list of names and organisations in the emails to gain some leads in forensic analysis)
"""
    
    try:
        print("Sending data to Ollama for analysis...\n")
        response = ollama.chat(
            model='mistral',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )
        print("\n======== Email Analysis Results ========\n")
        
        for chunk in response:
            sys.stdout.write(chunk['message']['content'])
            sys.stdout.flush()
        
        print("\n======================================\n")
        print(email_summary)
        print("\n======================================\n")
        
    except Exception as e:
        print(f"Error analyzing emails with Ollama: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Analyze emails in a specified folder.')
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
    analyze_emails_with_ollama(email_texts)
    
if __name__ == "__main__":
    main()
