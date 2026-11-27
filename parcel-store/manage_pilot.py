"""Local operator CLI. Never put the database or credentials in Git."""
import argparse, json, os, re
from datetime import date
from pilot_api import Store, ApiError

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("approve");a.add_argument("sku");a.add_argument("grams",type=int);a.add_argument("price_kopecks",type=int)
    a.add_argument("--verified",action="store_true",required=True,help="Verify exact SKU, gross weight, lawful import, storage and costs first.")
    b=sub.add_parser("pause-product");b.add_argument("sku")
    c=sub.add_parser("parcel");c.add_argument("id",type=int);c.add_argument("status",choices=["closed","sent","arrived","ready"]);c.add_argument("--track");c.add_argument("--sent");c.add_argument("--eta-from");c.add_argument("--eta-to")
    sub.add_parser("summary")
    args=parser.parse_args()
    db=Store(os.environ.get("SAM_DB","samobranka.sqlite3"),int(os.environ.get("SAM_CAPACITY_GRAMS","29000")))
    if args.cmd=="summary":
        print(json.dumps(db.summary(),ensure_ascii=False,indent=2));return
    with db.connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if args.cmd=="approve":
            if not (0<args.grams<=db.open_parcel(conn)["capacity"] and 0<args.price_kopecks<=100_000_000):
                raise SystemExit("Invalid verified weight or price.")
            result=conn.execute("UPDATE products SET grams=?,price_kopecks=?,approved=1 WHERE id=?",(args.grams,args.price_kopecks,args.sku))
            if not result.rowcount: raise SystemExit("SKU not found.")
        elif args.cmd=="pause-product":
            result=conn.execute("UPDATE products SET approved=0 WHERE id=?",(args.sku,))
            if not result.rowcount: raise SystemExit("SKU not found.")
        else:
            p=conn.execute("SELECT * FROM parcels WHERE id=?",(args.id,)).fetchone()
            if not p: raise SystemExit("Parcel not found.")
            allowed={"open":"closed","closed":"sent","sent":"arrived","arrived":"ready"}
            if args.status!=p["status"] and allowed.get(p["status"])!=args.status: raise SystemExit("Invalid status transition.")
            track=args.track or p["track"];sent=args.sent or p["sent"];eta_from=args.eta_from or p["eta_from"];eta_to=args.eta_to or p["eta_to"]
            if track and not re.fullmatch(r"[A-Z]{2}[0-9]{9}[A-Z]{2}",track): raise SystemExit("Invalid international tracking format.")
            try:
                dates=[date.fromisoformat(x) if x else None for x in (sent,eta_from,eta_to)]
                if dates[0] and dates[0]>date.today(): raise ValueError()
                if bool(dates[1])!=bool(dates[2]) or (dates[1] and (dates[1]>dates[2] or (dates[0] and dates[1]<dates[0]))): raise ValueError()
            except ValueError: raise SystemExit("Invalid dates.")
            if args.status in ("sent","arrived","ready") and not sent: raise SystemExit("Actual dispatch date required.")
            if p["status"]=="open": db.rotate(conn,p)
            conn.execute("UPDATE parcels SET status=?,track=?,sent=?,eta_from=?,eta_to=? WHERE id=?",(args.status,track,sent,eta_from,eta_to,args.id))
        conn.commit()
    print("Saved.")
if __name__=="__main__": main()
