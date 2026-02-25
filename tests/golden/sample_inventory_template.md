# Sample Inventory Template

| Case ID | Processor | Input Source | Sanitized | Covers Edge Cases | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| single_update_001 | ExcelProcessor | Real data | Yes | duplicate key/match, empty key, header row | TBD | Pending |
| multi_update_001 | MultiColumnExcelProcessor | Real data | Yes | multi-column write, missing columns | TBD | Pending |
| reverse_update_001 | ReverseExcelProcessor | Real data | Yes | `min_row=2`, merge conflicts | TBD | Pending |
| stats_001 | UntranslatedStatsProcessor | Real data | Yes | chinese/english modes, empty translation | TBD | Pending |
| cleaner_001 | ExcelColumnClearer | Real data | Yes | clear/insert/delete column | TBD | Pending |
| compatibility_001 | ExcelCompatibilityProcessor | Real data | Yes | open/save fallback | TBD | Pending |
| deep_replace_001 | DeepReplaceProcessor | Real data | Yes | rollback on failure | TBD | Pending |
