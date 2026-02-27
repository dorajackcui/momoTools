# Terminology Rule JSON 备注说明

示例文件：`docs/sample_terminology_rules.json`

## 1. 顶层结构

- `version`
  - 当前固定为 `1`。
- `files`（可选）
  - 控制“处理哪些 Excel 文件”。
  - 支持数组：`["abc", "cde.xlsx"]`
  - 也支持逗号字符串：`"abc, cde.xlsx"`
  - 缺省/空值/`"*"`/`"all"` 表示不过滤，处理输入目录下全部 Excel 文件。
  - 匹配规则（大小写不敏感）：
    - 写 `abc` 可匹配 `abc.xlsx` 或 `abc.xls`
    - 写 `abc.xlsx` 则只匹配 `abc.xlsx`
- `versions`（可选）
  - 控制“处理哪些版本行”（基于 Excel 行内 `version` 列）。
  - 支持数组：`["2.1.3", "2.2.3"]`
  - 也支持逗号字符串：`"2.1.3, 2.2.3"`
  - 缺省/空值/`"*"`/`"all"` 表示不过滤版本，处理所有版本行。
- `compound_delimiters`（可选）
  - 复合关系后处理使用的分隔符集合。
  - 支持数组和逗号字符串。
  - 默认值：`["·"]`。
- `normalization`
  - 术语规范化规则。
- `thresholds`
  - 关系识别与复核阈值。
- `extractors`
  - 抽取器列表，按顺序执行。

## 2. record_rule（key 命中）

- 必填字段：
  - `id`
  - `type`=`record_rule`
  - `enabled`
  - `skip_header`
  - `term_column`
  - `key`
- `key` 支持：
  - 数组：`["name", "title"]`
  - 逗号字符串：`"name, title"`
- `key_regex`（可选，默认 `false`）：
  - `false`：`key` 按“包含匹配”（大小写不敏感）。
  - `true`：`key` 按“正则匹配”（大小写不敏感）。
  - 正则写错会在配置加载阶段直接报错。
- 匹配语义：
  - 若配置了顶层 `versions`，行内 `version` 必须命中任一版本（OR）后才会进入 extractor。
  - 读取 Excel 行内 `key` 列，命中任一 `key` 规则（OR）。
  - `versions` 与 `key` 条件之间为 AND。

## 3. 重要破坏性变更

- 旧写法 `record_rule.conditions` 已废弃。
- 配置里出现 `conditions` 会直接报错。
- `record_rule.version` 也已废弃，出现会直接报错。
- 旧配置必须迁移到 `top-level versions + record_rule.key`。

## 4. tag_span 与 compound_split

- `tag_span`
  - 在 `source_columns` 指定列中提取标签包裹内容。
  - `open_tag` 支持单值或多值：
    - 单值字符串：`"<tag>"`
    - 逗号字符串：`"<tag>, <color>"`
    - 数组：`["<RedBold>", "<BlueBold>"]`
  - 也支持别名字段 `open_tags`（与 `open_tag` 二选一）。
  - `close_tags` 仍是数组，例如：`["</tag>", "</>"]`。
- `compound_split`
  - 不再参与 extractor 执行。
  - 若配置里保留 `type=compound_split`，当前行为是静默忽略。
  - 复合关系改为在“术语后处理”阶段基于去重后的 `terms` 识别。

## 5. 复合关系后处理

- 处理来源：`terms`（不是 candidates）。
- 识别方式：按 `compound_delimiters` 对术语做一次拆分（左首右余），例如 `X·Y`。
- 仅当 compound/head/suffix 三个词条都已存在于 `terms` 时，建立关系：
  - `compound -> head` (`has_head`)
  - `compound -> suffix` (`has_suffix`)
  - `head -> suffix` (`head_suffix_pair`)
- 不会自动新增词条。

## 6. 常见注意事项

- 当配置了 `files` 时，未命中的 Excel 会直接跳过，不参与统计和错误计数。
- 当配置了顶层 `versions` 时，Excel 必须存在 `version` 列（大小写不敏感，如 `Version`）。
- `key` 列按不区分大小写匹配（`KEY` 也可）。
- 推荐先看输出 `terms_summary` 与 `relations_summary`。
- 需要排查命中明细时，再看 `details`（包含 `file/sheet/row/col/key/version` 追溯字段）。

## 7. 输出结构（当前）

- `terms_summary`
  - 每个 term 一行，聚合 `files_list` / `keys_list`。
- `relations_summary`
  - 统一展示三类关系汇总：`file_presence`、`suffix_family`、`prefix_family`。
- `review`
  - 人工复核清单。
- `details`
  - 固定行级明细，便于追溯与排障。
