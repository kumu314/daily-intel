# -*- coding: utf-8 -*-
"""
把情报库渲染成一个可部署的静态站点（PWA），直接推 GitHub Pages 即可。

输出目录：site/
  index.html            每日列表仪表盘（最新在上）
  <日期>.html           每一天的日报（已带 PWA 头 + 离线缓存）
  manifest.webmanifest  安装用
  sw.js                 离线缓存
  icon.png              图标

用法：
  python build_site.py           # 渲染 data/ 下所有日期
  python build_site.py 2026-08-31 # 只渲染指定一天

之后把 site/ 整个目录推到 GitHub Pages 源（main 分支的 /site 或 gh-pages 分支）。
"""
import json
import shutil
import sys
from pathlib import Path
from html import escape

from report import build, DATA, ROOT

PWA = ROOT / 'pwa'
SITE = ROOT / 'site'


def copy_shell():
    SITE.mkdir(parents=True, exist_ok=True)
    for f in ['manifest.webmanifest', 'sw.js', 'icon.png']:
        src = PWA / f
        if src.exists():
            shutil.copyfile(src, SITE / f)


def render_day(day: str) -> Path:
    payload = json.loads((DATA / f'{day}.json').read_text(encoding='utf-8'))
    fp = SITE / f'{day}.html'
    fp.write_text(build(payload), encoding='utf-8')
    return fp


def build_index(days):
    cards = []
    for d in days:
        try:
            p = json.loads((DATA / f'{d}.json').read_text(encoding='utf-8'))
            facts = len(p.get('facts', []))
            cross = len(p.get('analysis', {}).get('cross', []))
            headline = p.get('analysis', {}).get('headline', '')
        except Exception:
            facts = cross = 0
            headline = ''
        # 取月日做卡片标题
        md = d[5:].replace('-', '月') + '日'
        cards.append(
            f'<a class="card" href="{d}.html">'
            f'<div class="md">{md}</div>'
            f'<div class="hl">{escape(headline[:38])}{"…" if len(headline) > 38 else ""}</div>'
            f'<div class="meta">{facts} 条事实 · {cross} 条判断</div>'
            f'</a>'
        )
    cards_html = '\n'.join(cards)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#123a33">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon.png">
<title>枯木每日情报</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#eef1f5;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
     color:#1f2933;line-height:1.7;padding:20px 14px}}
.wrap{{max-width:720px;margin:0 auto}}
.hero{{background:linear-gradient(135deg,#123a33,#1d6b52);color:#fff;border-radius:16px;
      padding:28px 24px;margin-bottom:18px}}
.hero h1{{font-size:24px;letter-spacing:1px}}
.hero .sub{{font-size:12.5px;opacity:.82;margin-top:8px}}
.hint{{font-size:12px;color:#123a33;background:#fdf6ec;border:1px dashed #e0b070;
      border-radius:8px;padding:10px 14px;margin-bottom:16px;line-height:1.7}}
.grid{{display:grid;gap:12px}}
.card{{display:block;text-decoration:none;background:#fff;border-radius:13px;padding:16px 18px;
      box-shadow:0 2px 10px rgba(20,40,70,.07);border-left:4px solid #f0b429;color:#1f2933}}
.card .md{{font-size:17px;font-weight:700;color:#123a33}}
.card .hl{{font-size:13.5px;color:#5c6773;margin:6px 0;line-height:1.7}}
.card .meta{{font-size:11.5px;color:#9aa5b1}}
footer{{margin-top:22px;text-align:center;font-size:11px;color:#9aa5b1;line-height:1.9}}
</style></head>
<body><div class="wrap">
<div class="hero"><h1>枯木每日情报</h1>
<div class="sub">一手信息交叉分析 · 装到手机桌面，每天看一页</div></div>
<div class="hint">第一次打开？手机浏览器菜单里点「添加到主屏幕 / 安装」，就能像 App 一样放在桌面上。断网也能看已打开过的那天。</div>
<div class="grid">
{cards_html}
</div>
<footer>判断为主观看法，都写了翻车线，到期回来验尸 · 不构成投资建议</footer>
<script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('sw.js').catch(function(){{}})}}</script>
</div></body></html>"""
    (SITE / 'index.html').write_text(html, encoding='utf-8')


def main():
    if len(sys.argv) > 1:
        targets = [sys.argv[1]]
    else:
        targets = sorted(f.stem for f in DATA.glob('*.json'))
    copy_shell()
    rendered = []
    for d in targets:
        fp = render_day(d)
        rendered.append(d)
        print(f"渲染：{fp}")
    # 始终重建索引（覆盖全部日期）
    all_days = sorted(f.stem for f in DATA.glob('*.json'))
    build_index(all_days)
    print(f"站点已生成：{SITE}  （共 {len(all_days)} 天，本次渲染 {len(rendered)} 天）")


if __name__ == '__main__':
    main()
