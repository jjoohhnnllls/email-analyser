"""
LLM Analyzer Module

This module handles the interaction with the Ollama Large Language Model.
It prepares email data for analysis and manages the conversation with the LLM.
"""

import sys
import ollama
import logging
from prompts import get_base_prompt, get_qa_prompt

logger = logging.getLogger(__name__)

def prepare_email_summary(email_texts):
    """
    Prepare a summary of emails for the LLM with metadata and statistics.
    
    Args:
        email_texts (list): List of email data dictionaries
        
    Returns:
        str: Formatted summary of the emails
    """
    logger.info("Preparing email summary for LLM")
    total_emails = len(email_texts)
    
    summary = []
    if total_emails > 0:
        summary.append(f"TOTAL EMAILS: {total_emails} ({email_texts[0]['date'].strftime('%Y-%m-%d')} to {email_texts[-1]['date'].strftime('%Y-%m-%d')})")
    else:
        summary.append("TOTAL EMAILS: 0")
    
    # Analyze sender domains and collect subjects
    sender_domains = {}
    subjects = []
    email_senders = []

    for email_data in email_texts:
        # Extract sender domain
        from_line = next((line for line in email_data['text'].split('\n') if line.startswith('From:')), "")
        if '@' in from_line:
            email_address = from_line.split('From:')[1].strip()
            domain = email_address.split('@')[1].split()[0].strip()
            sender_domains[domain] = sender_domains.get(domain, 0) + 1
            email_senders.append(email_address)
            
        # Extract subject
        subject_line = next((line for line in email_data['text'].split('\n') if line.startswith('Subject:')), "")
        if subject_line:
            subjects.append(subject_line[9:].strip())
    
    # Add sender domain statistics
    summary.append("\nSENDER DOMAINS:")
    for domain, count in sorted(sender_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        summary.append(f"- {domain}: {count} emails")
    
    # Add sender email addresses
    summary.append("\nSENDER EMAILS:")
    for email in email_senders:
        summary.append(f"- {email}")
    
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
        email_texts (list): List of email data dictionaries
        
    Returns:
        str: Formatted content of all emails
    """
    logger.info("Preparing full email content for LLM")
    email_content = []
    
    for i, email_data in enumerate(email_texts):
        email_content.append(f"\nEMAIL #{i+1} ({email_data['date'].strftime('%Y-%m-%d %H:%M:%S')}) - File: {email_data['file']}")
        email_content.append("=" * 80)
        email_content.append(email_data['text'])
        email_content.append("-" * 80)
    
    return "\n".join(email_content)

def analyze_emails_with_ollama(email_texts):
    """
    Analyze email texts using Ollama's Mistral model and start interactive Q&A.
    
    Args:
        email_texts (list): List of email data dictionaries
    """
    logger.info("Starting email analysis with Ollama")
    
    # Prepare data for the LLM
    email_summary = prepare_email_summary(email_texts)
    email_content = prepare_email_content(email_texts)
    base_prompt = get_base_prompt()
    qa_prompt = get_qa_prompt()

    # Build the conversation context
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
        logger.info("Sending data to Ollama for analysis")
        print("Sending data to Ollama for analysis...\n")
        
        # Display email summary
        print("\n\n======== Email Summary Data ========\n")
        print(email_summary)
        print("\n======================================\n")
        print("\n======== Email Analysis Results ========\n")
        
        # Stream the LLM response
        response = ollama.chat(
            model='mistral',
            messages=conversation_context,
            stream=True
        )
        
        assistant_response = ""
        for chunk in response:
            content = chunk['message']['content']
            assistant_response += content
            sys.stdout.write(content)
            sys.stdout.flush()
        
        # Add the assistant's response to the conversation context
        conversation_context.append({'role': 'assistant', 'content': assistant_response})
        
        # Add the QA prompt to guide concise responses
        logger.info("Adding QA guidance to conversation context")
        conversation_context.append({'role': 'user', 'content': qa_prompt})
        response = ollama.chat(
            model='mistral',
            messages=conversation_context
        )
        conversation_context.append({'role': 'assistant', 'content': response['message']['content']})
        
        # Start interactive Q&A loop
        logger.info("Starting interactive Q&A mode")
        print("\n\n======== Interactive Q&A Mode ========")
        print("You can now ask questions about the emails. Type 'exit' to quit.")
        
        run_interactive_qa(conversation_context)
        
    except Exception as e:
        logger.error(f"Error analyzing emails with Ollama: {str(e)}")
        print(f"Error analyzing emails with Ollama: {str(e)}")

def run_interactive_qa(conversation_context):
    """
    Run an interactive Q&A session with the LLM using the established conversation context.
    
    Args:
        conversation_context (list): The conversation history for context
    """
    while True:
        try:
            user_question = input("\nQuestion (or 'exit' to quit): ")
            if user_question.lower() in ['exit', 'quit', 'q']:
                logger.info("User exited Q&A mode")
                print("Exiting Q&A mode. Goodbye!")
                break
            
            # For each question, remind the model to be concise
            actual_question = f"Please answer this question directly and concisely: {user_question}"
            logger.debug(f"User question: {user_question}")
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
            logger.info("User interrupted Q&A mode with keyboard")
            print("\nExiting Q&A mode. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in Q&A mode: {str(e)}")
            print(f"\nError: {str(e)}")
            print("Let's continue with a new question.")
