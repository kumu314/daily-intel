#!/usr/bin/env bash
# 一键推送情报周报到 GitHub Pages（需先完成 GITHUB-PAT部署.md 里的 3 步）
# 用法：bash push.sh   或   chmod +x push.sh && ./push.sh
cd "$(dirname "$0")"

git add -A
if git diff --cached --quiet; then
  echo "没有新改动，跳过提交"
else
  git commit -m "情报周报更新 $(date '+%Y-%m-%d %H:%M')"
fi
git push origin main

echo "推送完成（若报 403/401 说明 PAT 没配好，回头看 GITHUB-PAT部署.md 排错）。"
