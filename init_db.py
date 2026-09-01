# -*- coding: utf-8 -*-
"""
初始化情报数据库（幂等，重复运行不会清空数据）

用法： python init_db.py
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / "db" / "intel.db"
SCHEMA = ROOT / "db" / "schema.sql"


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    print(f"数据库就绪：{DB}")
    print("数据表：", "、".join(t[0] for t in tables))


if __name__ == "__main__":
    main()
