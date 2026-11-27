from contextlib import closing
from datetime import UTC, datetime

import pytest

from radar.offers import connect
from radar.wholesale import import_csv


def test_private_import(tmp_path):
    path = tmp_path / "prices.csv"
    stamp = datetime.now(UTC).isoformat()
    path.write_text(f"product_key,observed_at,price_rub\nbrand|model|8gb|new,{stamp},1000\n")
    with closing(connect(tmp_path / "db.sqlite3")) as db:
        assert import_csv(db, path, "fixture") == 1
        assert import_csv(db, path, "fixture") == 0
        assert db.execute("SELECT COUNT(*) FROM offers").fetchone()[0] == 0
        path.write_text(f"product_key,observed_at,price_rub\nbrand|model|16gb|new,{stamp},1200\ninvalid,{stamp},0\n")
        with pytest.raises(ValueError):
            import_csv(db, path, "fixture")
        assert db.execute("SELECT COUNT(*) FROM wholesale_quotes").fetchone()[0] == 1
