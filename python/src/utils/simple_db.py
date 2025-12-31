"""
超简单的 SQLite 数据缓存
Python 内置，无需额外安装，适合小白使用
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional


class SimpleDB:
    """超简单的 SQLite 缓存数据库"""

    def __init__(self, db_path: str = "data/cache.db", ttl_hours: int = 24):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
            ttl_hours: 缓存有效期（小时）
        """
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.ttl_hours = ttl_hours
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            key: 缓存键（比如 "token_0x123_holders"）

        Returns:
            缓存的数据，如果不存在或已过期返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查询数据
        cursor.execute(
            "SELECT data, created_at FROM cache WHERE key = ?",
            (key,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        data_json, created_at = result

        # 检查是否过期
        created_time = datetime.fromisoformat(created_at)
        if datetime.now() - created_time > timedelta(hours=self.ttl_hours):
            self.delete(key)  # 删除过期数据
            return None

        # 返回解析后的数据
        return json.loads(data_json)

    def set(self, key: str, data: Any) -> None:
        """
        保存缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据（会自动转成 JSON）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 转成 JSON 字符串存储
        data_json = json.dumps(data, ensure_ascii=False)

        # 插入或更新数据
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, data, created_at) VALUES (?, ?, ?)",
            (key, data_json, datetime.now().isoformat())
        )

        conn.commit()
        conn.close()

    def delete(self, key: str) -> None:
        """删除指定缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()

    def clear(self) -> None:
        """清空所有缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache")
        conn.commit()
        conn.close()

    def clear_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            删除的记录数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        expiry_time = datetime.now() - timedelta(hours=self.ttl_hours)

        cursor.execute(
            "DELETE FROM cache WHERE created_at < ?",
            (expiry_time.isoformat(),)
        )

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count


# 使用示例
if __name__ == "__main__":
    # 创建数据库实例
    db = SimpleDB()

    # 存储数据
    db.set("token_holders", {"address1": 1000, "address2": 500})

    # 读取数据
    holders = db.get("token_holders")
    print(holders)  # {'address1': 1000, 'address2': 500}

    # 清理过期数据
    deleted = db.clear_expired()
    print(f"Deleted {deleted} expired records")
