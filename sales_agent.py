import json
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain import SQLDatabase
from langchain.agents import create_sql_agent

from email_handler import EmailHandler
from product_manager import ProductManager
from analyzer import CustomerAnalyzer
from utils import llm, engine, logger

sql_agent = create_sql_agent(llm=llm, db=SQLDatabase(engine), verbose=True)

class SalesAgent:
    def __init__(self):
        self.email_handler = EmailHandler()
        self.product_manager = ProductManager(sql_agent)
        self.customer_analyzer = CustomerAnalyzer(llm)

        self.send_tool = Tool(
            name="SendEmail",
            func=lambda x: self._parse_and_send_email(x),
            description="Send an email. Input format: 'recipient_email|||subject|||email_body'"
        )
        self.listen_tool = Tool(
            name="ListenForReplies",
            func=lambda x: self.email_handler.listen_for_replies(x),
            description="Listen for replies from a specific email address. Input is the email address to listen for."
        )
        self.analyze_tool = Tool(
            name="AnalyzeReply",
            func=lambda x: self._parse_and_analyze(x),
            description="Analyze customer reply. Input format: 'customer_email|||reply_text'"
        )
        self.product_tool = Tool(
            name="QueryProduct",
            func=lambda x: self.product_manager.query_product_availability(x),
            description="Query product information. Input is the product description or query."
        )
        self.related_products_tool = Tool(
            name="GetRelatedProducts",
            func=lambda x: self.product_manager.get_related_products(x),
            description="Get related products. Input is the product name."
        )

        prompt_template = PromptTemplate.from_template(
            """You are a professional sales assistant for Apple company. Your goal is to provide excellent customer service and drive sales.

Your tasks are:
1. Use the 'SendEmail' tool to send emails to customers (format: 'email|||subject|||body')
2. Use 'ListenForReplies' to wait for customer responses
3. Use 'AnalyzeReply' to understand customer interest and needs
4. Use 'QueryProduct' to get product information when needed
5. Use 'GetRelatedProducts' to suggest similar products when appropriate

When emailing customers:
- Be professional, concise, and respectful
- Focus on value proposition, not just price
- Address customers by name when possible
- Include clear call-to-action
- Ask open-ended questions to engage conversation
- Sign emails professionally as \"Apple Sales Team\"

When analyzing replies:
- Look for explicit and implicit interest signals
- Identify product questions or concerns
- Gauge price sensitivity
- Determine next best action

Available tools:
{tools}

Use the following format:
Question: {input}
Thought: You should think about what to do next.
Action: The action to take, should be one of [{tool_names}]
Action Input: The input to the action
Observation: The result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer.
Final Answer: [specific final response based on the customer's reply, including the purchase decision.]

Begin!

Question: {input}
{agent_scratchpad}"""
        )

        self.agent = create_react_agent(
            llm=llm,
            tools=[self.send_tool, self.listen_tool, self.analyze_tool, self.product_tool, self.related_products_tool],
            prompt=prompt_template
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=[self.send_tool, self.listen_tool, self.analyze_tool, self.product_tool, self.related_products_tool],
            verbose=True,
            handle_parsing_errors=True
        )

    def run(self, input_query: str) -> dict:
        try:
            return self.agent_executor.invoke({"input": input_query})
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {"error": str(e)}

    def _parse_and_send_email(self, input_str: str) -> str:
        try:
            parts = input_str.split('|||')
            if len(parts) >= 3:
                recipient = parts[0].strip()
                subject = parts[1].strip()
                body = parts[2].strip()
                cc = [email.strip() for email in parts[3].split(',')] if len(parts) > 3 and parts[3].strip() else None
                attachments = [path.strip() for path in parts[4].split(',')] if len(parts) > 4 and parts[4].strip() else None
                return self.email_handler.send_email(recipient, subject, body, cc=cc, attachments=attachments)
            return "Invalid input format. Use: 'recipient|||subject|||body[|||cc][|||attachments]'"
        except Exception as e:
            logger.error(f"Error parsing and sending email: {e}")
            return f"Error: {str(e)}"

    def _parse_and_analyze(self, input_str: str) -> str:
        try:
            parts = input_str.split('|||')
            if len(parts) >= 2:
                customer_email = parts[0].strip()
                reply_text = parts[1].strip()
                previous_context = parts[2].strip() if len(parts) > 2 else ""
                analysis = self.customer_analyzer.analyze_reply(reply=reply_text, customer_email=customer_email, previous_context=previous_context)
                return json.dumps(analysis, indent=2)
            return "Invalid input format. Use: 'customer_email|||reply_text[|||previous_context]'"
        except Exception as e:
            logger.error(f"Error parsing and analyzing reply: {e}")
            return f"Error: {str(e)}"
