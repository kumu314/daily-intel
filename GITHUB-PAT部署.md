# GitHub Pages 部署 · PAT 方案（最彻底）

WorkBuddy 的 GitHub 集成是只读的，建不了仓库也推不动，所以走**你自己的个人访问令牌（PAT）**
+ 本机 git。不依赖任何连接器权限，一次配好长期有效，每周自动化也能全自动推送。

## 你来做（约 2 分钟，小羽代不了）

1. **建仓库**：github.com → 右上 `+` → New repository → 名字 `daily-intel` → 公开
   → 不勾「Add a README」（保持空仓库）→ Create repository。
2. **生成 PAT**：github.com → 右上头像 → Settings → Developer settings →
   Personal access tokens → Tokens (classic) → Generate new token (classic)
   → 勾 `repo`（整组）→ Generate → **复制那串 token（只显示一次，丢了自己重开）**。
3. **本机授权**（二选一）：
   - 装了 GitHub CLI：`gh auth login` → 选 GitHub.com → 选「用 token 登录」→ 粘 PAT。
   - 没装 gh：用 git credential manager，推送时用户名填 `kumu314`、密码粘 PAT 即可。

## 小羽已经做好

- `intel/` 已 `git init` 并提交初始版本（commit `init: 一手情报周报 PWA`），remote 已指向 `kumu314/daily-intel`。
- 每周自动化 `automation-1788148700200` 已改回 **git push（GitHub 优先）**，Cloudflare 作回退。

## 你最后跑一条

```bash
cd intel
git push -u origin main
```

或直接**双击 `intel/push.bat`**（Windows）/ 跑 `bash push.sh`（Git Bash）——已帮你写好，会自动 add/commit/push。
（`gh` 已登录就不会再问；没装 gh 就按提示填用户名 kumu314 + 密码 PAT。）

## 开 GitHub Pages

仓库 → Settings → Pages → Source: **Deploy from a branch** → Branch: **main** →
Folder: **/site** → Save。等一两分钟，访问 `https://kumu314.github.io/daily-intel/`。
手机用 https 打开 → 添加到主屏幕。

## 之后

- 每周日 21:00 自动化会 `git add -A && commit && push`，你零操作。
- 本地手动改了任何文件，直接 `git push` 即可。
- 公开仓库本身就是「边学 Python 边教数据分析」的 IP 作品资产，可往小红书/B站摆。

## 排错

- `push` 报 403/401：PAT 没勾 `repo`，或仓库名/owner 不对 → 重开 token 勾 repo，确认 remote 是 `kumu314/daily-intel`。
- `push` 报 `failed to push some refs`：远程非空（你建仓库时勾了 README）→ 先 `git pull --rebase origin main` 再 push。
- 不想用 GitHub 了：走 `部署说明-Cloudflare.md`，或纯本地开着服务手机连 WiFi 看。
