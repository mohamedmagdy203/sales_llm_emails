# product_manager.py
from sqlalchemy import text
from utils import engine, logger

class ProductManager:
    def __init__(self, sql_agent):
        self.sql_agent = sql_agent

    def query_product_availability(self, product_query: str) -> dict:
        try:
            query_prompt = f"""
            Find products that match this query: "{product_query}"

            Return these details for each matching product:
            - Product name
            - Price
            - Availability (in stock quantity)
            - Description
            - Any current discounts or promotions

            Present the information in a customer-friendly format.
            """
            response = self.sql_agent.run(query_prompt)
            logger.info(f"Product query successful: {product_query}")
            return {
                "query": product_query,
                "results": response,
                "timestamp": ""
            }
        except Exception as e:
            logger.error(f"Product query failed: {e}")
            return {
                "query": product_query,
                "results": f"Error retrieving product information: {str(e)}",
                "error": True,
                "timestamp": ""
            }

    def get_related_products(self, product_name: str, limit: int = 3) -> list:
        try:
            query = f"""
            SELECT 
                related_products.product_name, 
                related_products.price,
                related_products.description
            FROM products
            JOIN product_relations ON products.id = product_relations.product_id
            JOIN products AS related_products ON product_relations.related_product_id = related_products.id
            WHERE products.product_name ILIKE '%{product_name}%'
            LIMIT {limit}
            """
            with engine.connect() as connection:
                result = connection.execute(text(query))
                related = [
                    {
                        "product_name": row[0],
                        "price": row[1],
                        "description": row[2]
                    }
                    for row in result
                ]
                return related
        except Exception as e:
            logger.error(f"Error finding related products: {e}")
            return []
