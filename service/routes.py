######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
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
Product Store Service with UI
"""
from flask import jsonify, request, abort, url_for
from service.models import Product, Category
from service.common import status
from . import app

def check_content_type(content_type):
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
              f"Content-Type must be {content_type}")
    if request.headers["Content-Type"] != content_type:
        app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
              f"Content-Type must be {content_type}")

@app.route("/health")
def healthcheck():
    return jsonify(status=200, message="OK"), status.HTTP_200_OK

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/products", methods=["POST"])
def create_products():
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")
    data = request.get_json()
    product = Product()
    product.deserialize(data)
    product.create()
    message = product.serialize()
    location_url = "/"  # Placeholder until proper URL is set
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}

# List all products
@app.route("/products", methods=["GET"])
def list_all_products():
    products = Product.all()
    results = [p.serialize() for p in products]
    return jsonify(results), status.HTTP_200_OK

# List products by name
@app.route("/products/name/<string:name>", methods=["GET"])
def list_products_by_name(name):
    products = Product.find_by_name(name)
    results = [p.serialize() for p in products]
    return jsonify(results), status.HTTP_200_OK

# List products by category
@app.route("/products/category/<string:cat>", methods=["GET"])
def list_products_by_category(cat):
    try:
        category_value = getattr(Category, cat.upper())
    except AttributeError:
        abort(status.HTTP_400_BAD_REQUEST, f"Invalid category: {cat}")
    products = Product.find_by_category(category_value)
    results = [p.serialize() for p in products]
    return jsonify(results), status.HTTP_200_OK

# List products by availability
@app.route("/products/availability/<string:avail>", methods=["GET"])
def list_products_by_availability(avail):
    available_value = avail.lower() in ["true", "yes", "1"]
    products = Product.find_by_availability(available_value)
    results = [p.serialize() for p in products]
    return jsonify(results), status.HTTP_200_OK

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' not found.")
    return jsonify(product.serialize()), status.HTTP_200_OK

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    check_content_type("application/json")
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' not found.")
    product.deserialize(request.get_json())
    product.id = product_id
    product.update()
    return jsonify(product.serialize()), status.HTTP_200_OK

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.find(product_id)
    if product:
        product.delete()
    return "", status.HTTP_204_NO_CONTENT
