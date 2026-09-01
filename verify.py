# -*- coding: utf-8 -*-
"""
验尸台 —— 这套系统真正的意义所在

判断谁都会下。难的是到期之后，老老实实回来看自己错了几条。

用法：
    python verify.py                     列出全部判断，按到期日排序
    python verify.py --overdue           只看已到期、还没验的（最常用的一个）
    python verify.py --due 2026-09-04    只看某天到期的
    python verify.py --hit 3             第 3 条：没翻车，记一笔
    python verify.py --miss 3 --note "非农只掉 1 万，没到 10 万门槛，但我判的方向也错了"
    python verify.py --stat              命中率统计（这套系统的成绩单）
"""
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / "db" / "intel.db"
TODAY = date.today().isoformat()
KIND = {"cross": "联动", "play": "行动"}
ICON = {"pending": "[  ]", "hit": "[√]", "miss": "[×]"}


def rows(conn, due=None, overdue=False):
    sql = "SELECT id,day,kind,ref,judge,falsify,due,verdict,verdict_note FROM call"
    cond, args = [], []
    if due:
        cond.append("due=?")
        args.append(due)
    if overdue:
        cond.append("due<=?")
        args.append(TODAY)
        cond.append("(verdict IS NULL OR verdict='' OR verdict='pending')")
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    sql += " ORDER BY due, id"
    return conn.execute(sql, args).fetchall()


def seq_map(conn):
    """稳定编号：按全量（due,id 排序）生成 1..N。
    数据库自增 id 会因为反复导入而漂移（今天可能是 24，明天变 36），
    直接把 id 当编号给用户用，命令会失效。所以这里统一转成 1..N。"""
    return {r[0]: i for i, r in enumerate(rows(conn), 1)}


def show(conn, rs):
    smap = seq_map(conn)
    print(f"\n今天是 {TODAY}\n" + "=" * 78)
    for cid, day, kind, ref, judge, fal, due, verdict, note in rs:
        v = verdict or "pending"
        no = smap.get(cid, "?")
        flag = "  <<< 到期了，快验" if (due <= TODAY and v == "pending") else ""
        print(f"\n{ICON.get(v, '[  ]')} 第{no}条 [{KIND.get(kind, kind)}] {ref}   (作于 {day}){flag}")
        print(f"    判断：{judge[:70]}{'...' if len(judge) > 70 else ''}")
        print(f"    翻车线：{fal}")
        print(f"    到期日：{due}", end="")
        if v != "pending":
            print(f"  → 验毕：{'没翻车' if v == 'hit' else '翻车了'}")
            if note:
                print(f"    备注：{note}")
        else:
            print()
    print("\n" + "=" * 78)
    print(f"显示 {len(rs)} 条（共 {len(smap)} 条）。编号按到期日固定，重新导入不会错位。")
    print("用 python verify.py --hit <编号> 或 --miss <编号> 记录结果。")


def stat(conn):
    tot = conn.execute("SELECT COUNT(*) FROM call").fetchone()[0]
    hit = conn.execute("SELECT COUNT(*) FROM call WHERE verdict='hit'").fetchone()[0]
    miss = conn.execute("SELECT COUNT(*) FROM call WHERE verdict='miss'").fetchone()[0]
    pend = conn.execute(
        "SELECT COUNT(*) FROM call WHERE verdict IS NULL OR verdict='' OR verdict='pending'"
    ).fetchone()[0]
    od = conn.execute(
        "SELECT COUNT(*) FROM call WHERE due<=? AND (verdict IS NULL OR verdict='' OR verdict='pending')",
        (TODAY,),
    ).fetchone()[0]
    done = hit + miss
    print(f"\n{'='*78}\n验尸成绩单（{TODAY}）\n{'='*78}")
    print(f"  判断总数      {tot}")
    print(f"  已验          {done}")
    print(f"  没翻车        {hit}")
    print(f"  翻车了        {miss}")
    print(f"  还没验        {pend}（其中已到期 {od} 条）")
    if done:
        print(f"\n  命中率        {hit / done * 100:.1f}%")
        print("  —— 低于 50% 说明这套分析不如扔硬币，该改方法了。")
    else:
        print("\n  还没有一条到期验尸。现在说什么都早。")
    print("=" * 78)


def mark(conn, seq, verdict, note):
    """seq 是给用户的稳定编号（1..N），内部翻译成数据库 id"""
    order = rows(conn)
    if not 1 <= seq <= len(order):
        print(f"编号 {seq} 不存在，现在只有 {len(order)} 条。先跑 python verify.py 看看。")
        return
    cid = order[seq - 1][0]
    conn.execute(
        "UPDATE call SET verdict=?, verdict_note=?, checked_at=datetime('now','localtime') WHERE id=?",
        (verdict, note or "", cid),
    )
    conn.commit()
    word = "没翻车" if verdict == "hit" else "翻车了"
    print(f"已记录：第{seq}条「{order[seq - 1][3]}」→ {word}")
    if note:
        print(f"  备注：{note}")


def main():
    if not DB.exists():
        print("数据库不存在，请先运行 python init_db.py && python ingest.py")
        sys.exit(1)
    conn = sqlite3.connect(DB)
    a = sys.argv[1:]

    if not a:
        show(conn, rows(conn))
    elif a[0] == "--overdue":
        rs = rows(conn, overdue=True)
        show(conn, rs) if rs else print("没有到期未验的判断。")
    elif a[0] == "--due":
        show(conn, rows(conn, due=a[1]))
    elif a[0] == "--stat":
        stat(conn)
    elif a[0] in ("--hit", "--miss"):
        note = ""
        if "--note" in a:
            note = a[a.index("--note") + 1]
        mark(conn, int(a[1]), "hit" if a[0] == "--hit" else "miss", note)
    else:
        print(__doc__)
    conn.close()


if __name__ == "__main__":
    main()
