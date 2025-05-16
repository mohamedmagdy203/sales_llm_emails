import imaplib
import email
from email.header import decode_header
import time
import yagmail
import os
import re
import json
from datetime import datetime
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from utils import logger

customer_history = {}

class EmailHandler:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')

        if not self.email_user or not self.email_password:
            raise ValueError("Email credentials not configured in environment variables")

        try:
            with yagmail.SMTP(self.email_user, self.email_password):
                logger.info("Email credentials verified successfully")
        except Exception as e:
            logger.error(f"Email credential verification failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    def send_email(self, recipient: str, subject: str, body: str, cc: List[str] = None, attachments: List[str] = None) -> str:
        if not re.match(r"[^@]+@[^@]+\\.[^@]+", recipient):
            logger.warning(f"Invalid email address: {recipient}")
            return f"Invalid email address: {recipient}"

        try:
            with yagmail.SMTP(self.email_user, self.email_password) as yag:
                yag.send(
                    to=recipient,
                    subject=subject,
                    contents=body,
                    cc=cc,
                    attachments=attachments
                )
            self._log_interaction(recipient, "OUTGOING", subject, body)
            logger.info(f"Email sent successfully to {recipient}")
            return recipient
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            raise

    def listen_for_replies(self, expected_sender_email: str, timeout: int = 300) -> Optional[str]:
        logger.info(f"Listening for replies from {expected_sender_email} (timeout: {timeout}s)")
        start_time = time.time()

        try:
            imap = imaplib.IMAP4_SSL('imap.gmail.com')
            imap.login(self.email_user, self.email_password)

            while time.time() - start_time < timeout:
                imap.select('inbox')
                status, messages = imap.search(None, 'UNSEEN')

                if status != 'OK':
                    logger.warning("Failed to search for unseen messages")
                    time.sleep(4)
                    continue

                messages = messages[0].split()
                for mail in messages:
                    res, msg = imap.fetch(mail, "(RFC822)")
                    if res != 'OK':
                        continue

                    for response in msg:
                        if isinstance(response, tuple):
                            email_msg = email.message_from_bytes(response[1])
                            from_addr = email_msg.get("From", "")
                            logger.debug(f"Checking email from: {from_addr}")
                            if expected_sender_email.lower() in from_addr.lower():
                                subject = self._decode_header(email_msg.get("Subject", ""))
                                logger.info(f"Reply received from: {from_addr}, Subject: {subject}")
                                body = self._extract_email_body(email_msg)
                                clean_body = self._clean_reply(body)
                                self._log_interaction(from_addr, "INCOMING", subject, clean_body)
                                imap.close()
                                imap.logout()
                                return clean_body
                time.sleep(4)

            logger.info(f"Timeout reached waiting for reply from {expected_sender_email}")
            imap.close()
            imap.logout()
            return None
        except Exception as e:
            logger.error(f"Error listening for replies: {e}")
            try:
                imap.close()
                imap.logout()
            except:
                pass
            return None

    def _extract_email_body(self, email_msg) -> str:
        if email_msg.is_multipart():
            for part in email_msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    continue
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode()
            for part in email_msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode()
        else:
            payload = email_msg.get_payload(decode=True)
            if payload:
                return payload.decode()
        return ""

    def _clean_reply(self, body: str) -> str:
        try:
            patterns = [
                r"\r?\nOn .*wrote:.*",
                r"\r?\n>.*",
                r"\r?\n.*\bOriginal Message\b.*",
                r"\r?\n-{2,}.*",
                r"\r?\nFrom:.*Sent:.*To:.*Subject:.*",
            ]
            clean_body = body
            for pattern in patterns:
                clean_parts = re.split(pattern, clean_body, maxsplit=1, flags=re.DOTALL)
                if len(clean_parts) > 1:
                    clean_body = clean_parts[0]
            clean_body = re.sub(r'\s+', ' ', clean_body).strip()
            return clean_body
        except Exception as e:
            logger.error(f"Error cleaning email body: {e}")
            return body.strip()

    def _decode_header(self, header: str) -> str:
        decoded_parts = decode_header(header)
        decoded_header = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_header += part.decode(encoding)
                    except:
                        decoded_header += part.decode('utf-8', errors='replace')
                else:
                    decoded_header += part.decode('utf-8', errors='replace')
            else:
                decoded_header += str(part)
        return decoded_header

    def _log_interaction(self, email_addr: str, direction: str, subject: str, content: str):
        timestamp = datetime.now().isoformat()
        if email_addr not in customer_history:
            customer_history[email_addr] = []
        customer_history[email_addr].append({
            "timestamp": timestamp,
            "direction": direction,
            "subject": subject,
            "content": content
        })
        try:
            with open("customer_interactions.jsonl", "a") as f:
                f.write(json.dumps({
                    "email": email_addr,
                    "timestamp": timestamp,
                    "direction": direction,
                    "subject": subject,
                    "content": content
                }) + "\n")
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")