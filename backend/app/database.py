"""MongoDB connection and index initialisation."""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, IndexModel
from app.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_client_loop: asyncio.AbstractEventLoop | None = None


def get_client() -> AsyncIOMotorClient:
    global _client, _client_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _client is None or (current_loop is not None and _client_loop != current_loop):
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
        _client_loop = current_loop

    return _client


def get_db():
    return get_client()[settings.MONGODB_DB]


async def init_db():
    """Create indexes on first startup."""
    db = get_db()

    await db.users.create_indexes([
        IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
    ])

    await db.uploads.create_indexes([
        IndexModel([("owner_id", ASCENDING)], name="uploads_owner"),
        IndexModel([("owner_id", ASCENDING), ("_id", ASCENDING)], name="uploads_owner_id"),
    ])

    await db.sales_records.create_indexes([
        IndexModel([("owner_id", ASCENDING), ("upload_id", ASCENDING)],
                   name="sales_owner_upload"),
    ])

    await db.analytics_results.create_indexes([
        IndexModel([("owner_id", ASCENDING), ("upload_id", ASCENDING)],
                   unique=True, name="analytics_owner_upload"),
    ])

    logger.info("MongoDB indexes initialized")
