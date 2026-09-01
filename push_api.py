#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_api.py — 通过 GitHub API 推送本仓库（绕过被代理封锁的 github.com git 通道）

原理：走 api.github.com 的 Git Data API，逐文件建 blob → 建树 → 建提交 → 更新引用。
前置条件：gh CLI 已登录（gh auth status 正常）。
用法：python push_api.py "提交信息"   （不带参数则用默认消息）
"""
import subprocess
import sys
import json
import base64
import os
import tempfile

REPO = "kumu314/daily-intel"
BRANCH = "main"


def gh_api(endpoint, payload=None, method=None, jq=None):
    """调用 gh api；payload 为 dict 时走 --input 临时 JSON 文件（避开命令行长度限制）"""
    cmd = ["gh", "api"]
    if method:
        cmd += ["-X", method]
    cmd.append(endpoint if endpoint.startswith("repos/") else f"repos/{REPO}/{endpoint}")
    tmp = None
    if payload is not None:
        tmp = tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(payload, tmp, ensure_ascii=False)
        tmp.close()
        cmd += ["--input", tmp.name]
    if jq:
        cmd += ["--jq", jq]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(f"gh api {endpoint} 失败: {r.stderr.strip()[:500]}")
        return r.stdout.strip()
    finally:
        if tmp:
            os.unlink(tmp.name)


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "chore: update intel site"

    # 1. 列出 git 索引中的全部文件（仅已跟踪文件）
    r = subprocess.run(["git", "ls-files", "-z"], capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git ls-files 失败（请在仓库目录内运行）")
    files = [f.decode("utf-8") for f in r.stdout.split(b"\0") if f]
    if not files:
        raise SystemExit("没有可推送的文件")
    print(f"待推送 {len(files)} 个文件")

    # 2. 逐文件建 blob
    tree_entries = []
    for f in files:
        with open(f, "rb") as fp:
            b64 = base64.b64encode(fp.read()).decode()
        sha = gh_api("git/blobs",
                     {"content": b64, "encoding": "base64"}, jq=".sha")
        tree_entries.append({"path": f, "mode": "100644",
                             "type": "blob", "sha": sha})
        print(f"  blob ok: {f}")

    # 3. 建树（若远端 main 已存在则以它为基准，否则全新）
    parents = []
    base_tree_sha = None
    ref = gh_api(f"git/ref/heads/{BRANCH}", method="GET")
    if ref and ref != "null" and not ref.startswith("{"):
        commit_sha = json.loads(ref or "{}")["object"]["sha"] \
            if isinstance(ref, str) and ref.startswith("{") else None
    # 简化：直接尝试读取远端分支，失败则视为首推
    head_commit = None
    try:
        out = gh_api(f"git/ref/heads/{BRANCH}", jq=".object.sha")
        head_commit = out if out and not out.startswith("null") else None
    except RuntimeError:
        head_commit = None

    tree_payload = {"tree": tree_entries}
    if head_commit:
        # 取旧提交的 tree 作为 base，保留未变更文件
        old = gh_api(f"git/commits/{head_commit}", jq=".tree.sha")
        tree_payload["base_tree"] = old
        parents = [head_commit]
    tree_sha = gh_api("git/trees", tree_payload, jq=".sha")
    print(f"tree: {tree_sha}")

    # 4. 建提交
    commit_sha = gh_api("git/commits",
                        {"message": msg, "tree": tree_sha, "parents": parents},
                        jq=".sha")
    print(f"commit: {commit_sha}")

    # 5. 更新/创建引用
    if head_commit:
        gh_api(f"git/refs/heads/{BRANCH}",
               {"sha": commit_sha, "force": False}, method="PATCH")
    else:
        gh_api("git/refs",
               {"ref": f"refs/heads/{BRANCH}", "sha": commit_sha}, method="POST")
    print(f"已推送 {BRANCH} -> {commit_sha}")
    print(f"https://github.com/{REPO}")


if __name__ == "__main__":
    main()
