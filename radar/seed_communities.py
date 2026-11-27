"""Opt-in local import of public community candidates; no messages sent."""
import json
from contextlib import closing
from pathlib import Path

from radar.community import Community, workspace_db

DEFAULT = Path(__file__).resolve().parents[1] / "data" / "community_candidates.json"


def seed(path=DEFAULT):
    records = [Community.model_validate(row) for row in json.loads(Path(path).read_text(encoding="utf-8"))]
    count = 0
    with closing(workspace_db()) as db, db:
        for row in records:
            result = db.execute("""INSERT INTO communities
                (name,url,country,routes,audience,rules,contact_status,ad_cost_rub,leads)
                VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(url) DO NOTHING""",
                tuple(row.model_dump().values()))
            count += result.rowcount
    return count


if __name__ == "__main__":
    print(f"Imported public community candidates: {seed()}")
