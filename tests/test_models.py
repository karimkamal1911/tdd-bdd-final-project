# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use:
    nosetests --stop tests/test_models.py:TestProductModel
"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up previous tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  EXISTING TEST CASES
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that the product was assigned an id and appears in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    ######################################################################
    #  NEW TEST CASES
    ######################################################################

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back from the database
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Update the description and save changes
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch the updated product to confirm changes
        updated_product = Product.find(product.id)
        self.assertEqual(updated_product.id, original_id)
        self.assertEqual(updated_product.description, "testing")
        # Ensure there's only one product in the system
        products = Product.all()
        self.assertEqual(len(products), 1)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # Delete the product and verify it's removed
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            p = ProductFactory()
            p.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        expected_count = len([p for p in products if p.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), expected_count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        availability = products[0].available
        expected_count = len([p for p in products if p.available == availability])
        found = Product.find_by_availability(availability)
        self.assertEqual(found.count(), expected_count)
        for product in found:
            self.assertEqual(product.available, availability)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        expected_count = len([p for p in products if p.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), expected_count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should Find a Product by Price"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        price = products[0].price
        expected_count = len([p for p in products if p.price == price])
        found = Product.find_by_price(price)
        self.assertEqual(found.count(), expected_count)
        for product in found:
            self.assertEqual(product.price, price)

    def test_deserialize_invalid_available(self):
        """It should raise DataValidationError if available is not a boolean"""
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
        product = ProductFactory()
        product.id = None  # explicitly ensure id is None
        with self.assertRaises(Exception) as context:
            product.update()
        self.assertIn("empty ID field", str(context.exception))

    def test_deserialize_invalid_category(self):
        """It should raise DataValidationError if the category is invalid"""
        product = Product()
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "15.00",
            "available": True,
            "category": "INVALID_CATEGORY"  # Not a valid attribute of Category
        }
        with self.assertRaises(Exception) as context:
            product.deserialize(data)
        self.assertIn("Invalid attribute", str(context.exception))

    def test_find_by_unknown_category(self):
        """It should return no products if no product has the UNKNOWN category"""
        # Create some products with a valid category different from UNKNOWN.
        products = ProductFactory.create_batch(5)
        for product in products:
            product.category = Category.CLOTHS
            product.create()
        # Query for products with the default UNKNOWN category
        found = Product.find_by_category(Category.UNKNOWN)
        self.assertEqual(found.count(), 0)

if __name__ == "__main__":
    unittest.main()
