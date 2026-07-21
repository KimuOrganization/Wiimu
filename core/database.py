import logging
import sqlite3
import asyncio
from core.config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    # TODO: agregar path al archivo db
    def __init__(self, path=DATABASE_PATH) -> None:
        self.path = path
        self.lock = asyncio.Lock()

    async def connect(self):
        self.connection = sqlite3.connect(
            self.path,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self.connection.execute(
            "PRAGMA journal_mode=WAL;"
        )

        self.connection.execute(
            "PRAGMA synchronous=NORMAL;"
        )

        logger.info("DB conectada correctamente.")
        

    async def fetch_one(self, query, params=()):
        async with self.lock:
            cursor = self.connection.execute(
                query,
                params
            )
            return cursor.fetchone()
    
    async def fetch_all(self, query, params=()):
        async with self.lock:
            cursor = self.connection.execute(
                query,
                params
            )
            return cursor.fetchall()
        
    async def execute(self, query, params=()):
        self.connection.execute(
            query,
            params
        )
        self.connection.commit()
