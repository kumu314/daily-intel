# -*- coding: utf-8 -*-
"""
情报日报生成器 —— 读取 data/*.json，输出单页可视化 HTML（零外部依赖，双击即看）

用法：
    python report.py              # 生成最新一份
    python report.py 2026-08-31   # 生成指定日期

三条纪律（改版时立下的，别破）：
    1. 不同性质的数字，绝不用同一张图比大小
    2. 主观打分必须写明「这是估计，不是数据」
    3. 每条判断后面必须跟一条翻车线
"""
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "reports"

DIM_ORDER = ["政策", "宏观", "市场", "国际", "产业", "舆论"]
DIM_COLOR = {
    "政策": "#2c5f8a", "宏观": "#2f7a4f", "市场": "#a8632c",
    "国际": "#7a4b8f", "产业": "#0f6d80", "舆论": "#b04a5a",
}
LEVEL_NAME = {1: "必须知道", 2: "值得知道", 3: "存档备查"}
LEVEL_COLOR = {1: "#c0563f", 2: "#2c5f8a", 3: "#9aa5b1"}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#eef1f5;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
     color:#1f2933;line-height:1.8;padding:32px 16px}
.wrap{max-width:1060px;margin:0 auto}
.hero{background:linear-gradient(135deg,#123a33,#17513f 55%,#1d6b52);color:#fff;
      border-radius:16px;padding:38px 40px;box-shadow:0 10px 30px rgba(15,50,40,.28)}
.hero .kicker{font-size:13px;letter-spacing:2px;opacity:.8;margin-bottom:12px}
.hero h1{font-size:34px;font-weight:700;letter-spacing:2px;margin-bottom:8px}
.hero .sub{font-size:13px;opacity:.82;margin-bottom:24px}
.hero .lead{font-size:19px;line-height:2;background:rgba(255,255,255,.12);
            border-left:3px solid #f0b429;padding:16px 20px;border-radius:0 8px 8px 0}
section{margin-top:26px}
h2{font-size:20px;font-weight:700;color:#123a33;margin-bottom:14px;
   padding-left:12px;border-left:4px solid #f0b429;display:flex;align-items:baseline;
   gap:10px;flex-wrap:wrap}
h2 small{font-size:12px;font-weight:400;color:#7b8794}
.card{background:#fff;border-radius:14px;padding:24px 26px;box-shadow:0 2px 12px rgba(20,40,70,.07)}
.grid{display:grid;gap:12px}
.g5{grid-template-columns:repeat(5,1fr)}
.g2{grid-template-columns:repeat(2,1fr)}
.kpi{background:#fff;border-radius:12px;padding:17px 16px;box-shadow:0 2px 10px rgba(20,40,70,.07);
     border-top:3px solid #d7dee6}
.kpi .n{font-size:12.5px;color:#7b8794;margin-bottom:8px;line-height:1.5}
.kpi .v{font-size:27px;font-weight:700;color:#123a33;line-height:1.1}
.kpi .v span{font-size:13px;font-weight:500;color:#52606d;margin-left:2px}
.kpi .d{font-size:11.5px;color:#8a94a0;margin-top:8px;line-height:1.5}
.kpi.cn{border-top-color:#2c5f8a}.kpi.us{border-top-color:#b04a5a}
.chartnote{font-size:12px;color:#8a94a0;background:#f7f9fb;border-radius:8px;
           padding:10px 14px;margin-top:12px;line-height:1.7}
.chain{background:#fff;border-radius:14px;padding:20px 24px;margin-bottom:12px;
       box-shadow:0 2px 12px rgba(20,40,70,.07);border-left:4px solid #2c5f8a}
.chain .path{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.pill{font-size:12px;padding:3px 11px;border-radius:20px;color:#fff;font-weight:600}
.arrow{color:#b0bac6;font-size:15px}
.chain .logic,.chain .judge{font-size:15px;line-height:1.9;margin-bottom:10px}
.chain .logic{color:#5c6773}
.chain .judge{color:#1f2933}
.chain .hz{display:inline-block;font-size:11px;color:#7b8794;background:#eef1f5;
           padding:2px 9px;border-radius:4px;margin-right:8px}
.falsify{font-size:13.5px;line-height:1.75;color:#8a4a1f;background:#fdf6ec;
         border:1px dashed #e0b070;border-radius:8px;padding:10px 14px;margin-top:12px}
.falsify b{color:#b5651d}
.ocean{border-radius:12px;padding:15px 17px;margin-bottom:10px;background:#fff;
       box-shadow:0 2px 10px rgba(20,40,70,.06)}
.ocean.red{border-left:4px solid #c0563f}
.ocean.blue{border-left:4px solid #2f9e6f}
.ocean h4{font-size:15px;margin-bottom:6px;display:flex;justify-content:space-between;
          align-items:center;gap:10px;line-height:1.5}
.ocean.red h4 b{color:#8f3a26}.ocean.blue h4 b{color:#1c6b4c}
.ocean p{font-size:13px;color:#6b7684;line-height:1.8}
.est{font-size:11px;font-weight:500;padding:2px 9px;border-radius:4px;white-space:nowrap}
.est.hot{background:#fdeceb;color:#c0563f}
.est.mid{background:#fdf4e3;color:#a8632c}
.est.cold{background:#e8f6ef;color:#2f9e6f}
.warnbox{font-size:12.5px;color:#8a4a1f;background:#fdf6ec;border:1px dashed #e0b070;
         border-radius:8px;padding:10px 14px;margin-bottom:14px;line-height:1.7}
table.tb{width:100%;border-collapse:collapse}
table.tb td{padding:14px 12px;border-bottom:1px solid #eef1f5;vertical-align:top}
table.tb tr:last-child td{border-bottom:none}
table.tb td:first-child{width:92px}
.watch{list-style:none;counter-reset:w}
.watch li{counter-increment:w;position:relative;padding:12px 0 12px 42px;font-size:14.5px;
          border-bottom:1px dashed #e4e9ef;line-height:1.8}
.watch li:last-child{border-bottom:none}
.watch li::before{content:counter(w);position:absolute;left:0;top:13px;width:24px;height:24px;
    background:#123a33;color:#fff;border-radius:50%;font-size:11px;
    display:flex;align-items:center;justify-content:center;font-weight:600}
.fact{border-left:3px solid #d7dee6;padding-left:15px;margin-bottom:18px}
.fact .t{font-size:15px;font-weight:600;color:#1f2933;margin-bottom:5px;line-height:1.7}
.fact .d{font-size:13.5px;color:#5c6773;line-height:1.85}
.fact .m{font-size:11.5px;color:#9aa5b1;margin-top:6px}
.fact .m em{font-style:normal;background:#eef1f5;padding:1px 7px;border-radius:3px;margin-right:6px}
.lvtag{font-size:10.5px;padding:1px 7px;border-radius:3px;color:#fff;margin-right:7px;
       vertical-align:2px;font-weight:500}
.dimblock{margin-bottom:24px}
.dimblock:last-child{margin-bottom:0}
.dimhd{display:inline-block;font-size:13px;font-weight:700;color:#fff;
       padding:3px 13px;border-radius:5px;margin-bottom:14px}
details{border-top:1px solid #eef1f5;margin-top:18px;padding-top:16px}
summary{cursor:pointer;font-size:13.5px;color:#2c5f8a;font-weight:600;padding:6px 0;
        list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"> ";display:inline-block;transition:.2s}
details[open] summary::before{transform:rotate(90deg)}
footer{margin-top:30px;text-align:center;font-size:11.5px;color:#9aa5b1;line-height:2}
@media(max-width:900px){.g5,.g2{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.g5,.g2{grid-template-columns:1fr}}
"""


def svg_groups(title, groups, note=""):
    """分组等距条形图。groups=[(组名, [(标签,值,颜色)], 组备注)] —— 同组才可互相比。"""
    w, rowh, pad_l, pad_r = 1000, 32, 250, 96
    rows = sum(len(g[1]) for g in groups)
    h = rows * rowh + len(groups) * (46 if any(len(g) > 2 for g in groups) else 30) + 34
    mx = max(v for g in groups for _, v, _ in g[1]) or 1
    bar_w = w - pad_l - pad_r
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="display:block">']
    o.append(f'<text x="0" y="17" font-size="14" font-weight="700" fill="#123a33">{escape(title)}</text>')
    y = 36
    for g in groups:
        gname, items = g[0], g[1]
        gnote = g[2] if len(g) > 2 else ""
        o.append(f'<text x="0" y="{y + 10}" font-size="12.5" font-weight="700" fill="#7b8794">{escape(gname)}</text>')
        if gnote:
            o.append(f'<text x="{w}" y="{y + 10}" font-size="11" fill="#a0aab5" text-anchor="end">{escape(gnote)}</text>')
        y += 24
        for lab, val, color in items:
            bw = val / mx * bar_w
            o.append(f'<text x="{pad_l - 14}" y="{y + 15}" font-size="13" fill="#3e4c59" text-anchor="end">{escape(lab)}</text>')
            o.append(f'<rect x="{pad_l}" y="{y + 3}" width="{bar_w}" height="18" rx="3" fill="#f0f3f6"/>')
            o.append(f'<rect x="{pad_l}" y="{y + 3}" width="{bw:.1f}" height="18" rx="3" fill="{color}"/>')
            o.append(f'<text x="{pad_l + bw + 10:.1f}" y="{y + 17}" font-size="13.5" font-weight="700" fill="{color}">{val}%</text>')
            y += rowh
        y += 10
    o.append("</svg>")
    if note:
        o.append(f'<div class="chartnote">{escape(note)}</div>')
    return "".join(o)


def svg_bipolar(title, rows, note=""):
    """正负双向条形图（只放同一性质的东西）。rows=[(标签,值,单位)]"""
    w, rowh, pad_l, pad_r = 1000, 34, 210, 70
    h = len(rows) * rowh + 44
    mx = max(abs(r[1]) for r in rows) or 1
    mid = pad_l + (w - pad_l - pad_r) / 2
    half = (w - pad_l - pad_r) / 2
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="display:block">']
    o.append(f'<text x="0" y="17" font-size="14" font-weight="700" fill="#123a33">{escape(title)}</text>')
    for i, (lab, val, unit) in enumerate(rows):
        y = 40 + i * rowh
        bar = abs(val) / mx * (half - 14)
        x = mid if val >= 0 else mid - bar
        c = "#2f9e6f" if val >= 0 else "#c0563f"
        o.append(f'<text x="{pad_l - 14}" y="{y + 16}" font-size="13" fill="#3e4c59" text-anchor="end">{escape(lab)}</text>')
        o.append(f'<rect x="{x:.1f}" y="{y + 3}" width="{bar:.1f}" height="18" rx="3" fill="{c}" opacity=".9"/>')
        tx = mid + bar + 9 if val >= 0 else mid - bar - 9
        anc = "start" if val >= 0 else "end"
        o.append(f'<text x="{tx:.1f}" y="{y + 17}" font-size="13.5" font-weight="700" fill="{c}" text-anchor="{anc}">{val:+.2f}{unit}</text>')
    o.append(f'<line x1="{mid:.1f}" y1="30" x2="{mid:.1f}" y2="{h - 10}" stroke="#cbd2d9"/>')
    o.append("</svg>")
    if note:
        o.append(f'<div class="chartnote">{escape(note)}</div>')
    return "".join(o)


def fmt_due(iso: str) -> str:
    """2026-09-04 → 9月4日"""
    try:
        _, m, d = iso.split("-")
        return f"{int(m)}月{int(d)}日"
    except Exception:
        return iso


def falsify_html(f):
    """翻车线区块。f 是 dict：{text, due, verdict}"""
    if not f:
        return '<div class="falsify"><b>翻车线：</b>这条判断还没写翻车条件，等于算命，不算数。</div>'
    if isinstance(f, str):          # 兼容旧格式
        return f'<div class="falsify"><b>翻车线：</b>{escape(f)}</div>'
    v = f.get("verdict", "pending")
    if v == "hit":
        tail = ' <span style="color:#2f9e6f">→ 已验：没翻车</span>'
    elif v == "miss":
        tail = ' <span style="color:#c0563f">→ 已验：翻车了</span>'
    else:
        tail = ""
    return (f'<div class="falsify"><b>翻车线（{fmt_due(f.get("due", ""))}到期）：</b>'
            f'{escape(f.get("text", ""))}{tail}</div>')


def est_label(kind, heat):
    """主观估计的文字档位 —— 不给数字，避免伪装成数据"""
    if kind == "red":
        if heat >= 8:
            return '<span class="est hot">挤破头</span>'
        if heat >= 6:
            return '<span class="est mid">有点挤</span>'
        return '<span class="est mid">开始挤了</span>'
    return '<span class="est cold">还没人去</span>' if heat <= 4 else '<span class="est mid">有人但不多</span>'


def build(p: dict) -> str:
    a = p["analysis"]
    facts = p["facts"]
    M = {m["name"]: m for m in p["metrics"]}

    def kpi(name, cls):
        m = M[name]
        return (f'<div class="kpi {cls}"><div class="n">{escape(m["name"])}</div>'
                f'<div class="v">{m["value"]}<span>{escape(m["unit"])}</span></div>'
                f'<div class="d">{escape(m["delta"])}</div></div>')

    kpi_html = (
        kpi("中国CPI同比(8月)", "cn") + kpi("中国PPI同比(8月)", "cn")
        + kpi("美国CPI同比(8月)", "us") + kpi("美国PPI同比(8月)", "us")
        + kpi("9月加息概率(CME)", "us")
    )

    chain_html = ""
    for c in a["cross"]:
        chain_html += (
            f'<div class="chain"><div class="path">'
            f'<span class="pill" style="background:{DIM_COLOR.get(c["from"], "#2c5f8a")}">{escape(c["from"])}</span>'
            f'<span class="arrow">&#8594;</span>'
            f'<span class="pill" style="background:{DIM_COLOR.get(c["to"], "#2c5f8a")}">{escape(c["to"])}</span>'
            f'<span class="hz">{escape(c["horizon"])}</span></div>'
            f'<div class="logic">{escape(c["logic"])}</div>'
            f'<div class="judge">{escape(c["judge"])}</div>'
            f'{falsify_html(c.get("falsify"))}</div>'
        )

    red, blue = "", ""
    for o in a["red_ocean"]:
        red += (f'<div class="ocean red"><h4><b>{escape(o["track"])}</b>{est_label("red", o["heat"])}</h4>'
                f'<p>{escape(o["reason"])}</p></div>')
    for o in a["blue_ocean"]:
        blue += (f'<div class="ocean blue"><h4><b>{escape(o["track"])}</b>{est_label("blue", o["heat"])}</h4>'
                 f'<p>{escape(o["reason"])}</p></div>')

    watch_html = "".join(f"<li>{escape(t)}</li>" for t in a.get("watchlist", []))

    pb = a.get("playbook")
    play_html = ""
    if pb:
        rows = ""
        for i in pb["items"]:
            fz = falsify_html(i.get("falsify"))
            rows += (
                f'<tr><td><span class="pill" style="background:#eef1f5;color:#123a33">'
                f'{escape(i["horizon"])}</span></td>'
                f'<td><div style="font-size:15.5px;font-weight:600;color:#123a33;margin-bottom:6px;line-height:1.7">'
                f'{escape(i["do"])}</div>'
                f'<div style="font-size:13.5px;color:#5c6773;line-height:1.9">{escape(i["why"])}</div>'
                f'<div style="font-size:11.5px;color:#8a94a0;margin-top:7px">依据：{escape(i["signal"])}</div>'
                f'{fz}</td></tr>')
        play_html = (
            f'<section><h2>这些跟我有什么关系 <small>不然看了也是白看</small></h2>'
            f'<div class="card"><div class="warnbox">{escape(pb["note"])}</div>'
            f'<table class="tb"><tbody>{rows}</tbody></table></div></section>')

    def fact_html(f):
        lv = f.get("level", 3)
        tag = (f'<span class="lvtag" style="background:{LEVEL_COLOR[lv]}">{LEVEL_NAME[lv]}</span>'
               if lv < 3 else "")
        return (f'<div class="fact"><div class="t">{tag}{escape(f["title"])}</div>'
                f'<div class="d">{escape(f["detail"])}</div>'
                f'<div class="m"><em>{escape(f["source"])}</em>信源 T{escape(str(f.get("tier", 2)))}'
                + ("" if not f.get("tag") else " · " + " / ".join(escape(t) for t in f["tag"]))
                + "</div></div>")

    main_facts = [f for f in facts if f.get("level", 3) <= 2]
    arch_facts = [f for f in facts if f.get("level", 3) == 3]
    dim_html = ""
    for dim in DIM_ORDER:
        items = [f for f in main_facts if f["dim"] == dim]
        if items:
            dim_html += (f'<div class="dimblock"><span class="dimhd" style="background:{DIM_COLOR[dim]}">'
                         f'{escape(dim)}</span>{"".join(fact_html(f) for f in items)}</div>')
    if arch_facts:
        inner = ""
        for dim in DIM_ORDER:
            items = [f for f in arch_facts if f["dim"] == dim]
            if items:
                inner += (f'<div class="dimblock"><span class="dimhd" style="background:#9aa5b1">'
                          f'{escape(dim)}</span>{"".join(fact_html(f) for f in items)}</div>')
        dim_html += (f'<details><summary>还有 {len(arch_facts)} 条不那么要紧的，点开看'
                     f'（存档备查，不占正文）</summary><div style="margin-top:14px">{inner}</div></details>')

    chart_price = svg_groups(
        "物价（CPI 类，同比）：一边卖不上价，一边降不下来",
        [("中国", [("CPI 同比", 0.8, "#2f7a4f"), ("核心 CPI 同比", 1.0, "#2f7a4f")], ""),
         ("美国", [("CPI 同比", 3.4, "#b04a5a"), ("核心 CPI 同比", 2.4, "#b04a5a")], "")],
        note="只跟同组比。中国 CPI 只涨 0.8%、核心 1.0%，是东西卖不上价、内需弱；美国 CPI 涨 3.4%、核心 2.4%，是通胀降不下来。两边都是病，只是病的方向相反。")

    chart_ppi = svg_groups(
        "生产端价格（PPI，同比）：都被外部冲击拽着走",
        [("生产端价格", [("中国 PPI 同比", 3.8, "#2c5f8a"), ("美国 PPI 同比", 5.4, "#7a4b8f")], "")],
        note="都是生产端、都是同比，可以摆一起。中国 PPI 由进口油价 + AI 芯片价格拉动；美国 PPI 由能源（柴油单月 +24%）拉动。两边都不是本国需求撑起来的。")

    chart_oil = svg_groups(
        "原油（美元/桶，9 月 11 日收盘）：一周重回百元上方",
        [("原油", [("布伦特", 104.61, "#8f3a26"), ("WTI", 100.05, "#b04a5a")], "")],
        note="9 月 10 日布伦特最高触 107.63、WTI 触 102.48，随后小幅回落。涨因是美伊冲突再起 + 胡塞袭击沙特设施，霍尔木兹与曼德海峡双航道承压。")

    chart_rate = svg_groups(
        "政策利率：一个动不了，一个要往上加",
        [("中国", [("1 年期 LPR", 3.0, "#2c5f8a"), ("5 年期以上 LPR", 3.5, "#2c5f8a")], "本周未变，9/20 待公布"),
         ("美国", [("联邦基金利率（上限）", 3.75, "#7a4b8f")], "9/16 或加到 4.00")],
        note="中国 LPR 已连续多月按兵不动，商业银行净息差只剩 1.41%，再降就要赔本。美国若 9/16 加息 25bp，上限变 4.00；市场当前押约 85% 概率。")

    chart_sector = svg_bipolar(
        "A 股本周行业涨跌（申万一级，%）",
        [("通信", 6.87, ""), ("建筑材料", 3.05, ""), ("综合", 2.09, ""),
         ("房地产", -2.93, ""), ("基础化工", -2.98, ""), ("有色金属", -3.98, "")],
        note="同周上证 -1.07%、创业板 +1.08%、科创综指 -2.56%；全周成交 9.46 万亿，连续 5 周缩量、创年内新低。涨的是通信建材，跌的是有色化工地产——钱在挑便宜和确定的方向。")

    n1 = sum(1 for f in facts if f.get("level") == 1)
    n2 = sum(1 for f in facts if f.get("level") == 2)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#123a33">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon.png">
<title>今日情报 {p['date']}</title><style>{CSS}</style></head>
<body><div class="wrap">

<div class="hero">
  <div class="kicker">{p['date']} · {escape(p.get('coverage', ''))}</div>
  <h1>今日情报</h1>
  <div class="sub">今天记了 {len(facts)} 条事实（{n1} 条必须知道、{n2} 条值得知道）、{len(p['metrics'])} 个数字、{len(a['cross'])} 条判断。每条判断都写了翻车的条件。</div>
  <div class="lead">{escape(a['headline'])}</div>
</div>

<section><h2>今天最要紧的五个数字 <small>别的都是次要的</small></h2>
<div class="grid g5">{kpi_html}</div></section>

<section><h2>中美物价：都涨，但原因相反 <small>一个卖不上价，一个降不下来</small></h2>
<div class="card">{chart_price}
<hr style="border:none;border-top:1px solid #eef1f5;margin:22px 0">{chart_ppi}</div></section>

<section><h2>油价一周重回百元 <small>美伊冲突 + 双航道承压</small></h2>
<div class="card">{chart_oil}
<hr style="border:none;border-top:1px solid #eef1f5;margin:22px 0">{chart_rate}</div></section>

<section><h2>谁影响了谁 <small>每件事都有个来龙去脉</small></h2>
{chain_html}</section>

<section><h2>A 股这一周 <small>钱在挑便宜和确定的方向</small></h2>
<div class="card">{chart_sector}</div></section>

<section><h2>哪里挤破头，哪里还没人去 <small>打分是我拍脑袋的，不是算出来的</small></h2>
<div class="grid g2">
  <div><div class="card" style="padding:18px 20px">
    <div style="font-size:14.5px;font-weight:700;color:#8f3a26;margin-bottom:6px">挤的地方 · 别往人堆里冲</div>
    <div class="warnbox">下面这些「挤 / 不挤」是我凭看到的消息估的，没有量化依据，别当成数据用。</div>
    {red}</div></div>
  <div><div class="card" style="padding:18px 20px">
    <div style="font-size:14.5px;font-weight:700;color:#1c6b4c;margin-bottom:6px">空的地方 · 做的人还不多</div>
    <div class="warnbox">同样只是估计。真要下场，先花两周自己验证，别信我这一句话。</div>
    {blue}</div></div>
</div></section>

{play_html}

<section><h2>接下来盯什么，几号来 <small>日子都标好了</small></h2>
<div class="card"><ul class="watch">{watch_html}</ul></div></section>

<section><h2>事实底稿 <small>每条都能查到出处</small></h2>
<div class="card">{dim_html}
<div class="chartnote" style="margin-top:16px">信源等级：T1 = 官方原始发布（国务院、央行、统计局等）；T2 = 官方媒体与交易所；T3 = 行业权威机构。数字照抄，官方的定性形容词全部删掉。</div>
</div></section>

<footer>
  来源：国务院、国家统计局、中国人民银行、工业和信息化部、美联储、BLS/BEA、IEA、Wind、交易所行情<br>
  {p['date']} 生成 · 判断部分为主观看法，都写了翻车线，到期请回来验尸 · 不构成投资建议
  </footer>

<script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('sw.js').catch(function(){{}})}}</script>
</div></body></html>"""


def main():
    if len(sys.argv) > 1:
        day = sys.argv[1]
    else:
        fs = sorted(DATA.glob("*.json"))
        if not fs:
            print("data/ 下没有情报文件")
            sys.exit(1)
        day = fs[-1].stem
    payload = json.loads((DATA / f"{day}.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    fp = OUT / f"{day}.html"
    fp.write_text(build(payload), encoding="utf-8")
    print(f"报告已生成：{fp}")


if __name__ == "__main__":
    main()
