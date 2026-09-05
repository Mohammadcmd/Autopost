"""Point the app at an isolated, throwaway data directory before any test
module imports app.config, so tests never touch real local data."""
import os
import tempfile

_tmp_data_dir = tempfile.mkdtemp(prefix="autopost_test_data_")
os.environ.setdefault("AUTOPOST_DATA_DIR", _tmp_data_dir)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_data_dir}/test.db")
# Never let a test's PUT /api/style write over the real shipped style file.
os.environ.setdefault("CAPTION_STYLE_FILE", f"{_tmp_data_dir}/caption_style.json")
