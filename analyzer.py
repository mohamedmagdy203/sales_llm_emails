# analyzer.py
import re
import json
from datetime import datetime
from utils import logger
from email_handler import customer_history

class CustomerAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    def analyze_reply(self, reply: str, customer_email: str, previous_context: str = "") -> dict:
        customer_context = self._get_customer_context(customer_email)

        prompt = f"""
        Analyze the following customer reply:
        "{reply}"

        {previous_context if previous_context else ""}

        {customer_context if customer_context else ""}

        Determine:
        1. Interest level: Interested, Not Interested, Unsure, or Needs More Information
        2. Products mentioned or requested (be specific)
        3. Any price sensitivity indicators
        4. Questions the customer has asked
        5. Next best action to take (send information, offer discount, etc.)
        6. Sentiment (positive, negative, neutral)

        Format your response as a JSON with these fields:
        - interest_level
        - products_mentioned
        - price_sensitivity
        - questions
        - next_action
        - sentiment
        """
        try:
            response = self.llm.invoke(prompt)
            if "{" in str(response) and "}" in str(response):
                json_text = re.search(r'({.*})', str(response).replace('\n', ' '), re.DOTALL)
                if json_text:
                    try:
                        return json.loads(json_text.group(1))
                    except json.JSONDecodeError:
                        pass
            return self._parse_analysis_text(str(response))
        except Exception as e:
            logger.error(f"Error analyzing customer reply: {e}")
            return {
                "interest_level": "Unsure",
                "products_mentioned": [],
                "price_sensitivity": "Unknown",
                "questions": [],
                "next_action": "Ask for clarification",
                "sentiment": "Neutral",
                "error": str(e)
            }

    def _parse_analysis_text(self, text: str) -> dict:
        result = {
            "interest_level": "Unsure",
            "products_mentioned": [],
            "price_sensitivity": "Unknown",
            "questions": [],
            "next_action": "Follow up",
            "sentiment": "Neutral"
        }
        interest_patterns = {
            r"(?i)interested|showing interest|express(?:es|ed) interest": "Interested",
            r"(?i)not interested|decline|reject|uninterested": "Not Interested",
            r"(?i)unsure|unclear|ambiguous": "Unsure",
            r"(?i)need(?:s)? more info|additional information|clarification": "Needs More Information"
        }
        for pattern, level in interest_patterns.items():
            if re.search(pattern, text):
                result["interest_level"] = level
                break
        product_match = re.search(r"(?i)product(?:s)?(?: mentioned)?:?\s*(.*?)(?:\n|$)", text)
        if product_match:
            products = product_match.group(1).strip()
            result["products_mentioned"] = [p.strip() for p in re.split(r',|\band\b', products) if p.strip()]
        if re.search(r"(?i)price sensitive|concerns about (?:the )?price|expensive|costly|cheaper", text):
            result["price_sensitivity"] = "High"
        elif re.search(r"(?i)willing to pay|price is (?:fine|good|acceptable)|not concerned about price", text):
            result["price_sensitivity"] = "Low"
        questions = re.findall(r"(?i)question(?:s)?:?\s*(.*?)(?:\n|$)", text)
        if questions:
            result["questions"] = [q.strip() for q in questions]
        action_match = re.search(r"(?i)next (?:best )?action:?\s*(.*?)(?:\n|$)", text)
        if action_match:
            result["next_action"] = action_match.group(1).strip()
        sentiment_patterns = {
            r"(?i)positive sentiment|happy|pleased|satisfied": "Positive",
            r"(?i)negative sentiment|unhappy|displeased|frustrated": "Negative",
            r"(?i)neutral sentiment|neither positive nor negative": "Neutral"
        }
        for pattern, sentiment in sentiment_patterns.items():
            if re.search(pattern, text):
                result["sentiment"] = sentiment
                break
        return result

    def _get_customer_context(self, customer_email: str) -> str:
        if customer_email not in customer_history or not customer_history[customer_email]:
            return ""
        recent_interactions = customer_history[customer_email][-5:]
        context = "Previous customer interactions:\n"
        for interaction in recent_interactions:
            direction = "Customer" if interaction["direction"] == "INCOMING" else "Agent"
            timestamp = datetime.fromisoformat(interaction["timestamp"]).strftime("%Y-%m-%d %H:%M")
            context += f"[{timestamp}] {direction}: {interaction['content'][:100]}...\n"
        return context