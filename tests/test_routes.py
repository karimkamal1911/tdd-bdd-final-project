######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Product Service Routes Test Suite

Test cases can be run with:
    nosetests -v --with-spec --spec-color
    coverage report -m
"""

import os
import logging
import unittest
from decimal import Decimal
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
# Base URL for product endpoints
BASE_URL = "/products"

# pylint: disable=too-many-public-methods
class TestProductRoutes(unittest.TestCase):
    """Test Cases for Product Service Routes"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # Clean up previous tests
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    ############################################################
    # Utility function to create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create multiple products using ProductFactory"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED,
                "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    # Test Cases
    ############################################################

    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product with no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_product(self):
        """It should Get a single Product"""
        test_product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)

    def test_update_product(self):
        """It should Update an existing Product"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_product = response.get_json()
        new_product["description"] = "Updated Description"
        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["description"], "Updated Description")

    def test_delete_product(self):
        """It should Delete a Product"""
        products = self._create_products(5)
        product_count = self.get_product_count()
        test_product = products[0]
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        new_count = self.get_product_count()
        self.assertEqual(new_count, product_count - 1)

    def test_get_product_list(self):
        """It should Get a list of Products"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_query_by_name(self):
        """It should Query Products by name"""
        # Create 5 products with a fixed name to ensure predictability.
        fixed_name = "Chevy"
        products = []
        for _ in range(5):
            product = ProductFactory(name=fixed_name)
            resp = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            new_product = resp.get_json()
            product.id = new_product["id"]
            products.append(product)
        expected_count = len(products)
        response = self.client.get(f"{BASE_URL}/name/{quote_plus(fixed_name)}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), expected_count)
        for prod in data:
            self.assertEqual(prod["name"], fixed_name)

    def test_query_by_category(self):
        """It should Query Products by category"""
        # Create 5 products with fixed category
        fixed_category = Category.CLOTHS
        products = []
        for _ in range(5):
            product = ProductFactory(category=fixed_category)
            resp = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            new_product = resp.get_json()
            product.id = new_product["id"]
            products.append(product)
        expected_count = len(products)
        response = self.client.get(f"{BASE_URL}/category/{fixed_category.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), expected_count)
        for prod in data:
            self.assertEqual(prod["category"], fixed_category.name)

    def test_query_by_availability(self):
        """It should Query Products by availability"""
        products = []
        # Create 5 products with alternating availability: True for even indices, False for odd
        for i in range(5):
            product = ProductFactory()
            product.available = (i % 2 == 0)
            resp = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            new_product = resp.get_json()
            product.id = new_product["id"]
            products.append(product)
        expected_count = len([p for p in products if p.available is True])
        avail_str = "true"  # Query string value for available True
        response = self.client.get(f"{BASE_URL}/availability/{avail_str}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), expected_count)
        for prod in data:
            self.assertTrue(prod["available"])

    def test_query_by_price(self):
        """It should find products by price using query parameter"""
        fixed_price = Decimal("19.99")
        products = []
        for _ in range(5):
            product = ProductFactory()
            product.price = fixed_price
            resp = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            new_product = resp.get_json()
            product.id = new_product["id"]
            products.append(product)
        expected_count = len(products)
        response = self.client.get(f"{BASE_URL}?price={fixed_price}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), expected_count)
        for prod in data:
            self.assertEqual(prod["price"], str(fixed_price))

    def test_deserialize_invalid_available(self):
        """It should raise DataValidationError if available is not a boolean"""
        from service.models import DataValidationError
        product = Product()
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "10.00",
            "available": "yes",  # invalid type: str instead of bool
            "category": "FOOD"
        }
        with self.assertRaises(Exception) as context:
            product.deserialize(data)
        self.assertIn("Invalid type for boolean", str(context.exception))

    def test_deserialize_missing_attribute(self):
        """It should raise DataValidationError if a required attribute is missing"""
        from service.models import DataValidationError
        product = Product()
        data = {
            # "name" key is missing
            "description": "Test description",
            "price": "10.00",
            "available": True,
            "category": "FOOD"
        }
        with self.assertRaises(Exception) as context:
            product.deserialize(data)
        self.assertIn("missing", str(context.exception))

    def test_deserialize_invalid_data(self):
        """It should raise DataValidationError if data is invalid (non-dict)"""
        from service.models import DataValidationError
        product = Product()
        with self.assertRaises(Exception) as context:
            product.deserialize(None)
        self.assertIn("bad or no data", str(context.exception))

    def test_deserialize_success(self):
        """It should correctly deserialize valid product data"""
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "19.99",
            "available": True,
            "category": "FOOD"
        }
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.description, "Test description")
        self.assertEqual(product.price, Decimal("19.99"))
        self.assertEqual(product.available, True)
        self.assertEqual(product.category, Category.FOOD)

    def test_update_with_no_id(self):
        """It should raise DataValidationError when updating a product with no id"""
        from service.models import DataValidationError
        product = ProductFactory()
        product.id = None  # explicitly ensure id is None
        with self.assertRaises(Exception) as context:
            product.update()
        self.assertIn("empty ID field", str(context.exception))

    def test_deserialize_invalid_category(self):
        """It should raise DataValidationError if the category is invalid"""
        from service.models import DataValidationError
        product = Product()
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "15.00",
            "available": True,
            "category": "INVALID_CATEGORY"
        }
        with self.assertRaises(Exception) as context:
            product.deserialize(data)
        self.assertIn("Invalid attribute", str(context.exception))

    def test_find_by_unknown_category(self):
        """It should return no products if no product has the UNKNOWN category"""
        # Create 5 products with fixed category CLOTHS
        products = []
        for _ in range(5):
            product = ProductFactory(category=Category.CLOTHS)
            resp = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            new_product = resp.get_json()
            product.id = new_product["id"]
            products.append(product)
        response = self.client.get(f"{BASE_URL}/category/{Category.UNKNOWN.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 0)

    ############################################################
    # Utility function to get product count
    ############################################################
    def get_product_count(self):
        """Return the current number of products."""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        return len(data)

if __name__ == "__main__":
    unittest.main()