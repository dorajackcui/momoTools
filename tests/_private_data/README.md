# Private Local Test Data

Place your local `master` workbook and language package files in this folder.

Rules:
- This folder is ignored by Git by default.
- Do not use `git add -f` for files under this folder.
- Pre-commit and pre-push hooks will block any commit/push containing files from this folder.

Suggested structure:
- `tests/_private_data/master/`
- `tests/_private_data/packages/lang_pack_1/`
- `tests/_private_data/packages/lang_pack_2/`
