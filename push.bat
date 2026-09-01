@echo off
REM 一键推送情报周报到 GitHub Pages（需先完成 GITHUB-PAT部署.md 里的 3 步：建仓库/生成PAT/gh auth login）
cd /d "D:\WorkBuddyData\WorkBuddy\2026-08-31-03-26-35\intel"

git add -A
git diff --cached --quiet && echo 没有新改动，跳过提交 || git commit -m "情报周报更新 %date% %time%"
git push origin main

echo.
echo 推送完成（若报 403/401 说明 PAT 没配好，回头看 GITHUB-PAT部署.md 排错）。
pause >nul
