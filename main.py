import time
import json
from sales_agent import SalesAgent
from monitor import EmailMonitor
from utils import logger

if __name__ == "__main__":
    sales_agent = SalesAgent()
    email_monitor = EmailMonitor(sales_agent.email_handler)
    email_monitor.start()

    prompt = "Send a formal email to mm2588905@gmail.com with an exclusive offer for a Smart Watch priced at $5, down from $20. Ensure the email is professional and ethical. His name is ENG Mohamed Magdy and the company name is Apple."
    result = sales_agent.run(prompt)
    print(json.dumps(result, indent=2))

    while True:
        new_emails = email_monitor.get_new_emails()
        for email_data in new_emails:
            logger.info(f"Processing new email from {email_data['from']}")
            analysis_prompt = f"Analyze this new customer email and respond appropriately: From: {email_data['from']}, Subject: {email_data['subject']}, Body: {email_data['body']}"
            sales_agent.run(analysis_prompt)
        time.sleep(60)
