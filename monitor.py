# monitor.py
import imaplib
import email
import time
import threading
import queue
from datetime import datetime
from email_handler import EmailHandler
from utils import logger

class EmailMonitor:
    def __init__(self, email_handler: EmailHandler):
        self.email_handler = email_handler
        self.running = False
        self.thread = None
        self.inbox_queue = queue.Queue()

    def start(self):
        if self.running:
            logger.warning("Email monitor already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Email monitor started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Email monitor stopped")

    def get_new_emails(self) -> list:
        emails = []
        while not self.inbox_queue.empty():
            emails.append(self.inbox_queue.get())
        return emails

    def _monitor_loop(self):
        email_user = self.email_handler.email_user
        email_password = self.email_handler.email_password

        while self.running:
            try:
                imap = imaplib.IMAP4_SSL('imap.gmail.com')
                imap.login(email_user, email_password)
                imap.select('inbox')
                status, messages = imap.search(None, 'UNSEEN')
                if status == 'OK':
                    for num in messages[0].split():
                        res, msg = imap.fetch(num, "(RFC822)")
                        for response in msg:
                            if isinstance(response, tuple):
                                email_msg = email.message_from_bytes(response[1])
                                from_addr = email_msg.get("From", "")
                                subject = self.email_handler._decode_header(email_msg.get("Subject", ""))
                                body = self.email_handler._extract_email_body(email_msg)
                                clean_body = self.email_handler._clean_reply(body)
                                self.inbox_queue.put({
                                    "from": from_addr,
                                    "subject": subject,
                                    "body": clean_body,
                                    "timestamp": datetime.now().isoformat(),
                                    "email_id": num.decode()
                                })
                                logger.info(f"New email from {from_addr} added to queue")
                imap.close()
                imap.logout()
            except Exception as e:
                logger.error(f"Error in email monitor: {e}")
            time.sleep(30)