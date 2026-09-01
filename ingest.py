# -*- coding: utf-8 -*-
"""
把当日情报 JSON 灌入数据库（同一天可重复运行，会先清掉当天旧记录）

用法：
    python ingest.py                 # 导入 data/ 下所有 JSON
    python ingest.py 2026-08-31      # 只导入指定日期
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / "db" / "intel.db"
DATA = ROOT / "data"


def ingest(conn, payload: dict) -> dict:
    day = payload["date"]
    cur = conn.cursor()

    # 同一天先清空，保证重复导入不产生脏数据
    for t in ("fact", "metric", "cross_note", "ocean"):
        cur.execute(f"DELETE FROM {t} WHERE day=?", (day,))
    # call 表特殊对待：只清掉「还没验尸」的判断，已验过尸的结果是有历史价值的，不能冲掉
    cur.execute(
        "DELETE FROM call WHERE day=? AND (verdict IS NULL OR verdict='' OR verdict='pending')",
        (day,),
    )

    facts = payload.get("facts", [])
    cur.executemany(
        "INSERT INTO fact(day,dim,source,tier,title,detail,url,tag,level) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        [
            (
                day,
                f["dim"],
                f["source"],
                f.get("tier", 2),
                f["title"],
                f.get("detail", ""),
                f.get("url", ""),
                ",".join(f.get("tag", [])),
                f.get("level", 3),
            )
            for f in facts
        ],
    )

    metrics = payload.get("metrics", [])
    cur.executemany(
        "INSERT INTO metric(day,name,value,unit,delta,dim,source) VALUES(?,?,?,?,?,?,?)",
        [
            (
                day,
                m["name"],
                m.get("value"),
                m.get("unit", ""),
                m.get("delta", ""),
                m.get("dim", ""),
                m.get("source", ""),
            )
            for m in metrics
        ],
    )

    cross = payload.get("analysis", {}).get("cross", [])
    cur.executemany(
        "INSERT INTO cross_note(day,from_dim,to_dim,logic,judge,horizon) VALUES(?,?,?,?,?,?)",
        [
            (day, c["from"], c["to"], c["logic"], c.get("judge", ""), c.get("horizon", ""))
            for c in cross
        ],
    )

    ocean = []
    for kind, key in (("red", "red_ocean"), ("blue", "blue_ocean")):
        for item in payload.get("analysis", {}).get(key, []):
            ocean.append((day, kind, item["track"], item.get("reason", ""), item.get("heat")))
    cur.executemany(
        "INSERT INTO ocean(day,kind,track,reason,heat) VALUES(?,?,?,?,?)", ocean
    )

    # 判断表：把所有带翻车线的判断抽出来单独存，到期后回来验尸。
    # verdict 已填过的（hit/miss）不覆盖，避免重复导入把验尸结果冲掉。
    calls, skipped = [], 0
    for c in cross:
        f = c.get("falsify")
        if isinstance(f, dict) and f.get("due"):
            calls.append((day, "cross", f"{c['from']}→{c['to']}",
                          c.get("judge", ""), f["text"], f["due"]))
    for it in payload.get("analysis", {}).get("playbook", {}).get("items", []):
        f = it.get("falsify")
        if isinstance(f, dict) and f.get("due"):
            calls.append((day, "play", it["do"][:40], it["do"], f["text"], f["due"]))

    for day_, kind, ref, judge, ftext, due in calls:
        row = cur.execute(
            "SELECT verdict FROM call WHERE day=? AND kind=? AND ref=?", (day_, kind, ref)
        ).fetchone()
        if row and row[0] not in (None, "", "pending"):
            skipped += 1          # 已经验过尸的判断，保留结果
            continue
        cur.execute(
            "INSERT INTO call(day,kind,ref,judge,falsify,due,verdict) VALUES(?,?,?,?,?,?,?)",
            (day_, kind, ref, judge, ftext, due, "pending"),
        )

    conn.commit()
    return {"day": day, "fact": len(facts), "metric": len(metrics),
            "cross": len(cross), "ocean": len(ocean),
            "call": len(calls), "call_kept": skipped}


def main():
    if not DB.exists():
        print("数据库不存在，请先运行 python init_db.py")
        sys.exit(1)

    if len(sys.argv) > 1:
        files = [DATA / f"{sys.argv[1]}.json"]
    else:
        files = sorted(DATA.glob("*.json"))

    conn = sqlite3.connect(DB)
    for fp in files:
        if not fp.exists():
            print(f"跳过（文件不存在）：{fp}")
            continue
        stat = ingest(conn, json.loads(fp.read_text(encoding="utf-8")))
        print(f"已导入 {stat['day']}：事实{stat['fact']}条 指标{stat['metric']}条 "
              f"联动{stat['cross']}条 红蓝海{stat['ocean']}条 "
              f"待验判断{stat['call']}条(保留验毕{stat['call_kept']}条)")
    conn.close()


if __name__ == "__main__":
    main()
