import sqlite3
import unittest

from data_sensei.pipeline import QueryPipeline


class QueryPipelineTest(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.pipeline = QueryPipeline(connection=self.connection)

    def test_area_select_query(self):
        result = self.pipeline.run("Show supplement consumption in Vijay Nagar")

        self.assertEqual(result.analysis.intent, "SELECT")
        self.assertIn("area = 'Vijay Nagar'", result.sql.display_sql)
        self.assertTrue(all(row["area"].lower() == "vijay nagar" for row in result.rows))

    def test_average_whey_spend_query(self):
        result = self.pipeline.run("What is the average monthly spend on whey protein?")

        self.assertEqual(result.analysis.intent, "AVG")
        self.assertIn("AVG(monthly_spend)", result.sql.display_sql)
        self.assertEqual(result.rows[0]["average_monthly_spend"], 3275.0)

    def test_count_creatine_query(self):
        result = self.pipeline.run("How many people use creatine?")

        self.assertEqual(result.analysis.intent, "COUNT")
        self.assertEqual(result.rows[0]["customer_count"], 6)

    def test_top_supplement_query(self):
        result = self.pipeline.run("Which supplement is consumed the most in Indore?")

        self.assertIn("GROUP BY supplement", result.sql.display_sql)
        self.assertEqual(result.rows[0]["supplement"], "Whey Protein")

    def test_spend_filter_query(self):
        result = self.pipeline.run("Show customers spending more than 3000")

        self.assertIn("monthly_spend > 3000", result.sql.display_sql)
        self.assertTrue(all(row["monthly_spend"] > 3000 for row in result.rows))

    def test_load_and_clean_csv(self):
        import io
        csv_content = """Product Name,Category,Discounted Price,Actual Price,Rating Count
Product A,Electronics,₹399,"₹1,099","24,269"
Product B,Office,₹150,₹300,500
Product C,Electronics,"₹1,500","₹3,000",120
"""
        csv_file = io.StringIO(csv_content)
        self.pipeline.load_csv(csv_file, table_name="test_products")
        
        # Verify metadata
        self.assertEqual(self.pipeline.table_name, "test_products")
        self.assertIn("discounted_price", self.pipeline.numeric_columns)
        self.assertIn("actual_price", self.pipeline.numeric_columns)
        self.assertIn("rating_count", self.pipeline.numeric_columns)
        self.assertIn("category", self.pipeline.categorical_columns)
        self.assertIn("product_name", self.pipeline.text_columns)
        
        # Verify database content is numeric
        rows = self.pipeline.dataset()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["discounted_price"], 399.0)
        self.assertEqual(rows[0]["actual_price"], 1099.0)
        self.assertEqual(rows[0]["rating_count"], 24269.0)
        
    def test_custom_dataset_query(self):
        import io
        csv_content = """product_name,category,discounted_price,rating
Product A,Electronics,₹399,4.5
Product B,Office,₹150,3.8
Product C,Electronics,"₹1,500",4.8
"""
        csv_file = io.StringIO(csv_content)
        self.pipeline.load_csv(csv_file, table_name="test_products_query")
        
        # Query 1: Filter on category
        result = self.pipeline.run("Show data where category is Electronics")
        self.assertEqual(len(result.rows), 2)
        self.assertTrue(all(r["category"].lower() == "electronics" for r in result.rows))
        
        # Query 2: Avg on price with filter
        result = self.pipeline.run("What is the average discounted_price of category Electronics?")
        self.assertEqual(result.rows[0]["average_discounted_price"], 949.5)
        
        # Query 3: Comparison filter
        result = self.pipeline.run("Show records where rating is greater than 4.0")
        self.assertEqual(len(result.rows), 2)
        self.assertTrue(all(r["rating"] > 4.0 for r in result.rows))


if __name__ == "__main__":
    unittest.main()