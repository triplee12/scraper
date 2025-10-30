from typing import Optional
from uuid import UUID
from asyncpg import UniqueViolationError
from databases import Database
from fastapi import HTTPException, status
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository
from scrape.models.products.product import ProductCreate, ProductUpdate, Product, ProductList


CREATE_PRODUCT_QUERY = """
    INSERT INTO products (
        name,
        url,
        price
    ) VALUES (
        :name,
        :url,
        :price
    ) RETURNING *
"""

GET_PRODUCTS_QUERY = """
    SELECT * FROM products
    ORDER BY created_at DESC
    LIMIT :limit
    OFFSET :offset
"""

GET_PRODUCTS_COUNT_QUERY = """
    SELECT COUNT(*) FROM products
"""

GET_PRODUCT_BY_ID_QUERY = """
    SELECT * FROM products WHERE id = :id
"""

DELETE_PRODUCT_BY_ID_QUERY = """
    DELETE FROM products WHERE id = :id
    RETURNING *
"""

UPDATE_PRODUCT_BY_ID_QUERY = """
    UPDATE products SET
        name = :name,
        url = :url,
        price = :price
    WHERE id = :id
    RETURNING *
"""


class ProductRepository(BaseRepository):
    def __init__(self, db: Database):
        super().__init__(db)
        logger.info("ProductRepository initialized.")

    async def create_product(self, product_data: ProductCreate) -> Optional[Product]:
        logger.info("Creating product: %s", product_data.name)
        try:
            values = product_data.model_dump()
            product = await self.db.fetch_one(CREATE_PRODUCT_QUERY, values=values)

            if not product:
                logger.warning("Product not created: %s", product_data.name)
                return None

            return Product(**product)
        except UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already exists."
            )
        except Exception as e:
            logger.exception(
                "Error creating product: %s. Exception: %s",
                product_data.name, e
            )
            raise e

    async def get_products(self, limit: int, offset: int) -> ProductList:
        logger.info("Getting products")
        try:
            values = {"limit": limit, "offset": offset}
            products = await self.db.fetch_all(GET_PRODUCTS_QUERY, values=values)

            if len(products) == 0:
                logger.warning("No products found")
                return ProductList(products=[], total=0)

            total = await self.db.fetch_one(GET_PRODUCTS_COUNT_QUERY)
            total = total[0] if total else 0

            products = [Product(**product) for product in products]

            return ProductList(products=products, total=total)
        except Exception as e:
            logger.exception("Error getting products. Exception: %s", e)
            raise e

    async def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        logger.info("Getting product by ID: %s", product_id)
        try:
            product = await self.db.fetch_one(
                GET_PRODUCT_BY_ID_QUERY,
                values={"id": product_id}
            )

            if not product:
                logger.warning("Product not found by ID: %s", product_id)
                return None

            return Product(**product)
        except Exception as e:
            logger.exception(
                "Error getting product by ID: %s. Exception: %s",
                product_id, e
            )
            raise e

    async def delete_product_by_id(self, product_id: UUID) -> Optional[Product]:
        logger.info("Deleting product by ID: %s", product_id)
        try:
            product = await self.db.fetch_one(
                DELETE_PRODUCT_BY_ID_QUERY,
                values={"id": product_id}
            )

            if not product:
                logger.warning("Product not found by ID: %s", product_id)
                return None

            return Product(**product)
        except Exception as e:
            logger.exception(
                "Error deleting product by ID: %s. Exception: %s",
                product_id, e
            )
            raise e

    async def update_product_by_id(self, product_id: UUID, product_data: ProductUpdate) -> Optional[Product]:
        logger.info("Updating product by ID: %s", product_id)
        try:
            values = product_data.model_dump()
            values["id"] = product_id
            product = await self.db.fetch_one(UPDATE_PRODUCT_BY_ID_QUERY, values=values)

            if not product:
                logger.warning("Product not found by ID: %s", product_id)
                return None

            return Product(**product)
        except Exception as e:
            logger.exception("Error updating product by ID: %s. Exception: %s", product_id, e)
            raise e
