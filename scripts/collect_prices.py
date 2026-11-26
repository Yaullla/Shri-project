"""Run selected fixed public-page probes; no credentials or LLM calls."""
import argparse
import json
import time
from datetime import UTC, datetime

from radar.collector import TARGETS, collect_and_store
from radar.fx import fetch_rates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="+", choices=sorted(TARGETS))
    parser.add_argument("--fx", action="store_true")
    args = parser.parse_args()
    if len(args.targets) > 5:
        parser.error("At most five targets per run")
    for index, target in enumerate(dict.fromkeys(args.targets)):
        if index:
            time.sleep(2)
        print(json.dumps(collect_and_store(target), ensure_ascii=False), flush=True)
    if args.fx:
        try:
            rates = fetch_rates(datetime.now(UTC).date().isoformat())
            print(json.dumps({"fx_status": "received", **rates}), flush=True)
        except (OSError, ValueError, KeyError):
            print(json.dumps({"fx_status": "unavailable"}), flush=True)


if __name__ == "__main__":
    main()
