#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性脚本：把 site/ 内容作为 gh-pages 分支根目录推上去（Pages 用）"""
import subprocess, json, base64, os, tempfile

REPO = "kumu314/daily-intel"


def gh_api(endpoint, payload=None, method=None, jq=None):
    cmd = ["gh", "api"]
    if method:
        cmd += ["-X", method]
    cmd.append(f"repos/{REPO}/{endpoint}")
    tmp = None
    if payload is not None:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(payload, tmp, ensure_ascii=False)
        tmp.close()
        cmd += ["--input", tmp.name]
    if jq:
        cmd += ["--jq", jq]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(f"gh api {endpoint} 失败: {r.stderr.strip()[:300]}")
        return r.stdout.strip()
    finally:
        if tmp:
            os.unlink(tmp.name)


SITE = "site"
entries = []
for root, _, files in os.walk(SITE):
    for fn in files:
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, SITE).replace("\\", "/")  # 去掉 site/ 前缀
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        sha = gh_api("git/blobs", {"content": b64, "encoding": "base64"}, jq=".sha")
        entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": sha})
        print(f"  blob ok: {rel}")

# gh-pages 是全新树（不带 base_tree，孤儿分支）
tree_sha = gh_api("git/trees", {"tree": entries}, jq=".sha")
commit_sha = gh_api("git/commits",
                    {"message": "deploy: intel PWA site", "tree": tree_sha, "parents": []},
                    jq=".sha")
# 创建/更新 gh-pages 引用
try:
    gh_api("git/refs", {"ref": "refs/heads/gh-pages", "sha": commit_sha}, method="POST")
except RuntimeError:
    gh_api("git/refs/heads/gh-pages", {"sha": commit_sha, "force": True}, method="PATCH")
print(f"gh-pages -> {commit_sha}")
