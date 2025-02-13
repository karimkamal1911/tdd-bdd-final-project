# Copyright 2016, 2023 John Rofrano. All Rights Reserved.
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

"""
Models for Product Demo Service

All of the models are stored in this module

Models
------
Product - A Product used in the Product Store

Attributes:
-----------
name (string) - the name of the product
description (string) - the description of the product
price (Numeric) - the price of the product
available (boolean) - True for products that are available
category (enum) - the category the product belongs to
"""

import logging
from enum import Enum
from decimal import Decimal
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Product.init_db(app)


class DataValidationError(Exception):
    """Used for data validation errors when deserializing"""


class Category(Enum):
    """Enumeration of valid Product Categories"""

    UNKNOWN = 0
    CLOTHS = 1
    FOOD = 2
    HOUSEWARES = 3
    AUTOMOTIVE = 4
    TOOLS = 5


class Product(db.Model):
    """
    Class that represents a Product

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    available = db.Column(db.Boolean(), nullable=False, default=True)
    category = db.Column(
        db.Enum(Category), nullable=False, server_default=Category.UNKNOWN.name
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Product in the database.
        """
        logger.info("Creating %s", self.name)
        # Set id to None to generate the next primary key
        self.id = None  # pylint: disable=invalid-name
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a Product in the database.
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes a Product from the data store."""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self) -> dict:
        """Serializes a Product into a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "available": self.available,
            "category": self.category.name  # convert enum to string
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Product from a dictionary.

        Args:
            data (dict): A dictionary containing the Product data

        Returns:
            self: The Product instance with updated data

        Raises:
            DataValidationError: If a required attribute is missing or has an invalid type.
        """
        try:
            self.name = data["name"]
            self.description = data["description"]
            self.price = Decimal(data["price"])
            if isinstance(data["available"], bool):
                self.available = data["available"]
            else:
                raise DataValidationError(
                    "Invalid type for boolean [available]: " + str(type(data["available"]))
                )
            # Convert the category from string to enum using getattr
            self.category = getattr(Category, data["category"])
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError("Invalid product: missing " + error.args[0]) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid product: body of request contained bad or no data " + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app: Flask):
        """
        Initializes the database session

        Args:
            app (Flask): The Flask app
        """
        logger.info("Initializing database")
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # create our sqlalchemy tables

    @classmethod
    def all(cls) -> list:
        """Returns all of the Products in the database."""
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, product_id: int):
        """
        Finds a Product by its ID.

        Args:
            product_id (int): The id of the Product to find

        Returns:
            Product: The product instance with the product_id, or None if not found.
        """
        logger.info("Processing lookup for id %s ...", product_id)
        return cls.query.get(product_id)

    @classmethod
    def find_by_name(cls, name: str):
        """
        Returns a query for all Products with the given name.

        Args:
            name (str): The name of the Products to match

        Returns:
            SQLAlchemy query: A query object with Products matching the name.
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_price(cls, price: Decimal):
        """
        Returns a query for all Products with the given price.

        Args:
            price (Decimal or str): The price to search for

        Returns:
            SQLAlchemy query: A query object with Products matching the price.
        """
        logger.info("Processing price query for %s ...", price)
        price_value = price
        if isinstance(price, str):
            price_value = Decimal(price.strip(' "'))
        return cls.query.filter(cls.price == price_value)

    @classmethod
    def find_by_availability(cls, available: bool = True):
        """
        Returns a query for all Products by their availability.

        Args:
            available (bool): True for products that are available

        Returns:
            SQLAlchemy query: A query object with Products matching the availability.
        """
        logger.info("Processing available query for %s ...", available)
        return cls.query.filter(cls.available == available)

    @classmethod
    def find_by_category(cls, category: Category = Category.UNKNOWN):
        """
        Returns a query for all Products by their Category.

        Args:
            category (Category): The category to match (one of the Category enum values)

        Returns:
            SQLAlchemy query: A query object with Products matching the category.
        """
        logger.info("Processing category query for %s ...", category.name)
        return cls.query.filter(cls.category == category)
