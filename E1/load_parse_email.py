#import email
import email

# Replace with your own test file
file_path = r'C:\Users\Demo PC2\Desktop\Email to EML downloader\gmail_export_20250320_104947\test\20250312_233025_67d27b81_050a0220_287957_147e_at_mx_google_com.eml'
with open(file_path, 'r', encoding='utf-8',errors='ignore') as f:
    raw_email = f.read()

# Your parsing code goes here
msg = email.message_from_string(raw_email)
print("-----full email content-----")
print(f"{msg}")
print("-----subject of email-----")
subject = msg.get('Subject')
print(f"{subject}")
print("-----From Address-----")
from_address = msg.get('From')
print(f"{from_address}")
print("-----date of email-----")
date = msg.get('Date')
print(f"{date}")
print("-----cc of email-----")
date = msg.get('Cc')
print(f"{date}")
print("-----reply-to of email-----")
date = msg.get('Reply-To')
print(f"{date}")
print("-----email body-----")
if msg.is_multipart():
    for part in msg.walk()
    content_type = part.get_content_type()
    content_disposition = str(part.get("Content-Disposition"))
    if content_type


