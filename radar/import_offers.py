"""Operator-only import of explicitly reviewed observations from JSON."""
import argparse
import json
from contextlib import closing
from pathlib import Path
from radar.offers import connect, ingest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', type=Path)
    args = parser.parse_args()
    if args.json_file.stat().st_size > 5_000_000:
        raise ValueError('File too large')
    rows = json.loads(args.json_file.read_text(encoding='utf-8'))
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError('Expected at most 10000 rows')
    with closing(connect()) as db, db:
        for row in rows:
            ingest(db, row)
    print(f'Processed {len(rows)} observations')


if __name__ == '__main__':
    main()
