"""Manual review only. No automatic approval of remote content."""
import argparse
from contextlib import closing

from radar.offers import connect, review_observation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("url")
    parser.add_argument("observed_at")
    parser.add_argument("--confirmed", action="store_true",
                        help="I verified identity, condition, seller, price and availability")
    args = parser.parse_args()
    with closing(connect()) as db, db:
        review_observation(db, args.source, args.url, args.observed_at,
                           confirmed=args.confirmed)
    print("Reviewed observation recorded")


if __name__ == "__main__":
    main()
