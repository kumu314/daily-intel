# 部署说明 · Cloudflare Pages 版（不用 GitHub，绕开 MCP 403）

GitHub MCP 建仓库/推送被 403 挡住（token 只读）。Cloudflare Pages 可以直接上传
静态文件夹，**不需要建 git 仓库**，HTTPS 自动给，PWA「添加到主屏幕」照常工作。
免费额度个人用绰绰有余。站点目录还是 `intel/site/`（自包含）。

---

## 方式一：拖拽上传（今晚就能试，零命令行）

1. 注册 Cloudflare 账号（免费）：https://dash.cloudflare.com/sign-up
2. 左侧 **Workers & Pages** → 创建 → Pages → **直接上传（Upload assets）**
3. 把 `intel/site/` 整个文件夹拖上去（或先压成 zip 再传）
4. 项目名填 `daily-intel`，点部署
5. 几秒后拿到地址 `https://daily-intel.pages.dev`
6. 手机用 https 打开 → 浏览器菜单「添加到主屏幕」→ 桌面出现「枯木每日情报」

缺点：每周更新要手动再传一次。适合先验证排版和内容。

---

## 方式二：wrangler 命令行（接每周自动推送，零手动）

1. 确认有 Node.js（你已有 22 / 24 版本）。
2. 授权（二选一）：
   - `npx wrangler login`（浏览器点一次授权，token 存本地）
   - 或建 API Token：Cloudflare 控制台 → My Profile → API Tokens → 勾 **Pages:Edit**
     → 设环境变量 `CLOUDFLARE_API_TOKEN=xxxx`（重要：别写进会提交的脚本里）
3. 部署（在 `intel/` 目录下）：
   ```bash
   npx wrangler pages deploy site --project-name daily-intel
   ```
   首次会让你确认建项目，之后每次就是更新。
4. 上线地址同上 `https://daily-intel.pages.dev`。要自定义域名（如 intel.你的域名）
   在 Pages 项目里绑，需要你自己的域名（可选，非必需）。

---

## 每周自动化怎么接

把每周任务的「推送」步骤从 git push 改成 wrangler deploy：

```
4. 推送（尽力而为，失败不致命）：
   若环境变量 CLOUDFLARE_API_TOKEN 已设置或 npx wrangler login 已做过：
     cd intel && npx wrangler pages deploy site --project-name daily-intel
   若没配置 Cloudflare 凭证：打印提示"请先 npx wrangler login 或设 CLOUDFLARE_API_TOKEN"，
   然后跳过 push，明说"本次只在本机生成了 site/，未上线"。
   若 deploy 报权限错，明说"Cloudflare 推送失败，检查 API Token 权限"，不要反复重试。
```

这样每周日 21:00 自动采→出站点→上线，你零操作。

---

## 和 GitHub 版的区别

| | GitHub Pages | Cloudflare Pages |
|---|---|---|
| 是否需要建仓库 | 需要（被 MCP 403 挡） | 不需要 |
| HTTPS | 自动 | 自动 |
| 部署方式 | git push | 直接传文件夹 / wrangler |
| 自定义域名 | 需自有域名 | 需自有域名（可选） |
| 适合 | 爱用 git 的人 | 想省事、绕开权限坑 |

先自己看、跑顺再当 IP 入口，公开地址发小红书/B站都行。
