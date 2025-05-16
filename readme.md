# LLM Emails: AI-Powered Sales Communication Agent

## 🚀 Overview

**LLM Emails** is an AI-driven sales assistant designed to automate and enhance customer email interactions. It leverages Large Language Models (LLMs), SQL agents, and email processing pipelines to provide personalized, professional, and context-aware communication for sales teams.

This agent acts on behalf of a sales representative to:

* Send customized email offers
* Listen for replies
* Analyze customer responses
* Query product information
* Recommend related products

All interactions are logged, analyzed, and used to build a continuous customer profile.

## ✨ Features

* ✉️ Intelligent email sending and listening
* 🤔 Natural Language analysis of customer interest
* 📈 Product lookup and recommendation using SQL
* 🤖 ReAct-based tool selection with LangChain
* ⏳ Real-time monitoring of inbox using IMAP
* 📅 Persistent customer interaction logging (JSONL)

## ⚙️ Technologies Used

* Python 3.10+
* [LangChain](https://www.langchain.com/)
* [Groq (LLaMA 3)](https://groq.com/)
* PostgreSQL + SQLAlchemy
* yagmail (Gmail API wrapper)
* IMAP/SMTP
* Tenacity (retry handling)
* dotenv (env variables)
* Logging and threading for async handling

## 🌐 Architecture

```text
+-------------------+
|  SalesAgent (LLM) |
+---------+---------+
          |
    +-----v------+
    | Tools      | <-----> ProductManager (SQL)
    |            | <-----> EmailHandler (SMTP/IMAP)
    |            | <-----> CustomerAnalyzer (LLM)
    +------------+
          |
   +------v-------+
   | AgentExecutor |
   +--------------+
```

## 🚧 Setup Instructions

```bash
# Clone repo
$ git clone https://github.com/yourusername/llm-emails.git
$ cd llm-emails

# Create virtual environment
$ python -m venv venv
$ source venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt

# Setup environment variables
$ cp .env.example .env
$ nano .env  # fill in EMAIL_USERNAME, PASSWORD, DATABASE_URL, etc.
```

## ⚡ Usage

```bash
# Run the agent
$ python main.py
```

You can customize prompts in `main.py` or call `sales_agent.run({"input": "your_prompt_here"})` directly.

## 💡 Example Prompt

```text
Send a professional email to mm2588905@gmail.com offering a Smart Watch for $5 instead of $20.
Make sure it's respectful, ethical, and signed as Apple Sales Team.
```

## 🗂️ File Structure

```
llm_emails/
├── main.py
├── email_handler.py
├── product_manager.py
├── analyzer.py
├── sales_agent.py
├── monitor.py
├── customer_interactions.jsonl
├── .env.example
├── requirements.txt
└── README.md
```

## ⚙️ Future Improvements

* CI/CD with GitHub Actions
* FastAPI for external integration
* UI dashboard (Streamlit/React)
* Vector DB for customer memory
* Multilingual support

---

MIT License © 2025 Mohamed Magdy
