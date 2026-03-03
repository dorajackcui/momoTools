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

Run local private-data regression:
- `python -m unittest tests.test_private_data_skip_blank_write -v`

Notes:
- This test will auto-skip if required private files/folders are missing.
- It never writes back to files under `tests/_private_data`.
