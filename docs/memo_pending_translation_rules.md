# Memo: Pending Translation/Data Handling Decisions

Date: 2026-02-25
Owner: TBD
Status: Pending

## 1) Empty translation overwrite policy

### Current behavior
- Three fill workflows now support mode toggle:
  - `覆盖` (default): keep current overwrite behavior.
  - `填空`: only write when target translation cell is blank.
- Blank definition is fixed: `None`, `""`, and whitespace-only strings.

### Why this is pending
- No longer pending for overwrite strategy toggle.
- Still pending only for business policy nuances around empty source value (`""`) under each mode.

### Suggested acceptance check
- Matched row with empty translation:
  - Option A: clear output cell
  - Option B: keep original output cell unchanged

## 2) Number-to-string fidelity policy

### Current behavior
- Values are generally passed using Python `str(value)` semantics, not Excel display-format semantics.
- This can change representation details (example: formatted numeric cells may not preserve display format).
- Risk point: falsy checks can treat `0` as empty in some paths if logic uses `if value else ""`.

### Why this is pending
- Need strict rule: preserve logical value as string (`str(value)`), or preserve exact displayed text/format from Excel.
- Need explicit handling for numeric `0` so it is not converted to empty.

### Suggested acceptance check
- Input values: `0`, `1`, `1.0`, `00123`, percentage/date-formatted cells.
- Verify output matches agreed policy (logical string vs display string).

## 3) Post-process toggle defaults (implemented)

### Current behavior
- `Master -> 小表` 和 `多列更新` 均支持“后处理（Excel COM 兼容性保存）”开关。
- 两个工具页开关独立，默认值均为开启。
- 开关状态不持久化；应用重启后恢复默认开启。

### Expected effect
- 关闭时仅跳过后处理步骤，不影响前置填表写入逻辑与列更新范围。

## 4) Fill mode toggle defaults (implemented)

### Current behavior
- `Master -> 小表`、`多列更新`、`小表 -> Master` 三个填表功能都支持“仅填空（关闭=覆盖）”toggle。
- 默认关闭（即覆盖模式），不持久化。

### Expected effect
- 覆盖模式：命中后直接写入（历史行为）。
- 填空模式：仅在目标译文单元格为空时写入。
