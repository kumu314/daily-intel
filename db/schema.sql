-- 一手情报数据库结构
-- 设计原则：只存「一手事实」，不存二手解读。解读放在 data/*.json 的 analysis 字段里，与事实物理隔离。

PRAGMA foreign_keys = ON;

-- 事实表：一条 = 一条可追溯到原始出处的信息
CREATE TABLE IF NOT EXISTS fact (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day         TEXT    NOT NULL,          -- 情报日期 YYYY-MM-DD
    dim         TEXT    NOT NULL,          -- 维度：政策 / 宏观 / 市场 / 国际 / 产业 / 舆论
    source      TEXT    NOT NULL,          -- 一手来源机构，如「国家统计局」「美联储」
    tier        INTEGER NOT NULL DEFAULT 2,-- 来源等级 1=官方原始发布 2=官方媒体/交易所 3=行业权威机构
    title       TEXT    NOT NULL,          -- 事实标题
    detail      TEXT,                      -- 事实内容（含数字）
    url         TEXT,                      -- 原始链接
    tag         TEXT,                      -- 逗号分隔标签，供交叉检索
    level       INTEGER NOT NULL DEFAULT 3,-- 重要度 1=必须知道 2=值得知道 3=存档备查
    created_at  TEXT    DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_fact_day ON fact(day);
CREATE INDEX IF NOT EXISTS idx_fact_dim ON fact(dim);
CREATE INDEX IF NOT EXISTS idx_fact_tag ON fact(tag);

-- 指标表：结构化数字，用于画图和跨期对比
CREATE TABLE IF NOT EXISTS metric (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    day     TEXT    NOT NULL,
    name    TEXT    NOT NULL,              -- 指标名，如「LPR 1Y」
    value   REAL,                          -- 数值
    unit    TEXT,                          -- 单位：% / 亿美元 / 点
    delta   TEXT,                          -- 变化描述，如「+1.2%」「连续15个月持平」
    dim     TEXT,
    source  TEXT
);
CREATE INDEX IF NOT EXISTS idx_metric_name ON metric(name);

-- 交叉分析表：把两个维度的联动判断沉淀下来，日积月累形成「联动规律库」
CREATE TABLE IF NOT EXISTS cross_note (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    day      TEXT    NOT NULL,
    from_dim TEXT    NOT NULL,             -- 因：政策 / 国际 / ...
    to_dim   TEXT    NOT NULL,             -- 果：市场 / 产业 / ...
    logic    TEXT    NOT NULL,             -- 传导链条
    judge    TEXT,                         -- 结论判断
    horizon  TEXT                          -- 时效：短期(1-4周) / 中期(1-2季) / 长期(1-5年)
);
CREATE INDEX IF NOT EXISTS idx_cross_day ON cross_note(day);

-- 判断表（本库最值钱的一张表）：每条判断都必须挂一条翻车线和到期日
-- 没有翻车线的判断不配进这张表。到期后回来验尸，命中率才是这套系统的成绩单。
CREATE TABLE IF NOT EXISTS call (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    day          TEXT    NOT NULL,          -- 判断作出的日期
    kind         TEXT    NOT NULL,          -- cross=联动判断 / play=个人行动
    ref          TEXT    NOT NULL,          -- 判断摘要（联动写「国际→市场」，行动写首句）
    judge        TEXT,                      -- 判断原文
    falsify      TEXT    NOT NULL,          -- 翻车线：什么情况出现说明我错了
    due          TEXT    NOT NULL,          -- 到期日 YYYY-MM-DD
    verdict      TEXT,                      -- 验尸结果：pending / hit(没翻车) / miss(翻车了)
    verdict_note TEXT,                      -- 验尸备注
    checked_at   TEXT                       -- 验尸时间
);
CREATE INDEX IF NOT EXISTS idx_call_due ON call(due);
CREATE INDEX IF NOT EXISTS idx_call_verdict ON call(verdict);

-- 红海 / 蓝海判定表：追踪赛道拥挤度随时间的变化
-- 注意：heat 是主观估计，不是量化数据。展示时必须标注，不得伪装成测量结果。
CREATE TABLE IF NOT EXISTS ocean (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    day     TEXT    NOT NULL,
    kind    TEXT    NOT NULL,              -- red=红海 / blue=蓝海
    track   TEXT    NOT NULL,              -- 赛道名
    reason  TEXT,                          -- 判定依据
    heat    INTEGER                        -- 主观估计 1-10，仅供排序，不可当数据用
);
CREATE INDEX IF NOT EXISTS idx_ocean_day ON ocean(day);
