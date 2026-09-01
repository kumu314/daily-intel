# -*- coding: utf-8 -*-
"""
情报库检索工具 —— 沉淀之后真正值钱的是「回溯」

用法：
    python query.py                      查看库存概览
    python query.py 霍尔木兹              全文搜索关键词
    python query.py --dim 国际 --last 7   只看某维度最近 7 天
    python query.py --name "LPR 1Y"      看某个指标的历史序列
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / "db" / "intel.db"


def overview(conn):
    print("\n== 库存概览 ==")
    days = conn.execute("SELECT day, COUNT(*) FROM fact GROUP BY day ORDER BY day").fetchall()
    for d, n in days:
        print(f"  {d}  事实 {n} 条")
    print(f"\n  累计 {len(days)} 天，共 {sum(n for _, n in days)} 条事实")
    print("\n== 维度分布 ==")
    for row in conn.execute("SELECT dim, COUNT(*) c FROM fact GROUP BY dim ORDER BY c DESC"):
        print(f"  {row[0]:<6} {row[1]} 条")
    names = conn.execute("SELECT DISTINCT name FROM metric ORDER BY name").fetchall()
    if names:
        print(f"\n== 可查序列的指标（{len(names)} 个）==")
        print("  " + "、".join(n[0] for n in names))


def search(conn, kw):
    like = f"%{kw}%"
    rows = conn.execute(
        "SELECT day, dim, source, title, detail FROM fact "
        "WHERE title LIKE ? OR detail LIKE ? OR tag LIKE ? OR source LIKE ? ORDER BY day DESC",
        (like, like, like, like),
    ).fetchall()
    print(f"\n命中 {len(rows)} 条（关键词：{kw}）")
    for d, dim, src, t, det in rows:
        print(f"\n[{d}] [{dim}] {src}\n  {t}")
        if det:
            print(f"  {det[:160]}")


def by_dim(conn, dim, last):
    rows = conn.execute(
        "SELECT day, source, title, detail FROM fact WHERE dim=? ORDER BY day DESC LIMIT ?",
        (dim, last),
    ).fetchall()
    print(f"\n【{dim}】最近 {len(rows)} 条")
    for d, src, t, det in rows:
        print(f"  {d} | {src} | {t}")


def series(conn, name):
    rows = conn.execute(
        "SELECT day, value, unit, delta FROM metric WHERE name=? ORDER BY day", (name,)
    ).fetchall()
    if not rows:
        print(f"没有指标「{name}」的记录")
        return
    print(f"\n【{name}】历史序列")
    for d, v, u, dl in rows:
        print(f"  {d}  {v}{u}  {dl}")


def main():
    if not DB.exists():
        print("数据库不存在，请先运行 python init_db.py")
        sys.exit(1)
    conn = sqlite3.connect(DB)
    args = sys.argv[1:]

    if not args:
        overview(conn)
    elif args[0] == "--dim":
        by_dim(conn, args[1], int(args[3]) if "--last" in args else 30)
    elif args[0] == "--name":
        series(conn, args[1])
    else:
        search(conn, args[0])

    conn.close()


if __name__ == "__main__":
    main()
