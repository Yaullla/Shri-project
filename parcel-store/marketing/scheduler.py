"""Private, persistent local scheduler. Never joins chats or messages private users.
Runs only explicitly approved one-shot jobs from a private JSON file.
No queue or token is stored in Git; no automatic retry after an attempted send.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from publisher import publish, parse_time, UTC

def load_queue(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not isinstance(data.get("jobs"),list):
        raise ValueError("Invalid queue")
    jobs=data["jobs"]
    if len(jobs)>100: raise ValueError("Maximum 100 explicitly approved jobs")
    if any(not isinstance(j,dict) or not isinstance(j.get("job_id"),str) for j in jobs):
        raise ValueError("Each job needs a unique job_id")
    if len({j["job_id"] for j in jobs})!=len(jobs): raise ValueError("Duplicate job_id")
    return data.get("enabled") is True,jobs

def tick(queue, dbpath, token, now=None, sender=publish, execute=False):
    now=now or dt.datetime.now(UTC)
    enabled,jobs=load_queue(queue)
    if not enabled: return {"mode":"paused","jobs":len(jobs),"sent":0}
    with sqlite3.connect(dbpath,timeout=10) as db:
        db.execute("CREATE TABLE IF NOT EXISTS publications(job_id TEXT PRIMARY KEY, chat_id INTEGER NOT NULL, attempted_at TEXT NOT NULL, state TEXT NOT NULL, message_id INTEGER)")
        done={r[0] for r in db.execute("SELECT job_id FROM publications")}
    summary={"mode":"live" if execute else "dry-run","jobs":len(jobs),"due":0,"sent":0,"blocked":0,"pending":0,"expired":0,"attempted":0}
    for j in jobs:
        if j["job_id"] in done: summary["attempted"]+=1;continue
        try:
            if j.get("approved") is not True or j.get("free_confirmed") is not True: raise ValueError()
            due=parse_time(j["scheduled_at"])
            end=parse_time(j["approval_expires_at"])
            if now>=end or now-due>dt.timedelta(hours=6):
                summary["expired"]+=1;continue
            if due>now: summary["pending"]+=1;continue
            from publisher import validate
            validate(j,now)
            summary["due"]+=1
            if not execute: continue
            # Recheck queue and kill switch immediately before send.
            enabled,current=load_queue(queue)
            if not enabled or j not in current:
                summary["blocked"]+=1;continue
            result=sender(j,token,str(dbpath),now=now)
            if result["status"]=="sent":summary["sent"]+=1
            else:summary["attempted"]+=1
            # One attempted publication per scheduler tick.
            break
        except (ValueError,KeyError,TypeError,RuntimeError,sqlite3.Error,OSError):
            summary["blocked"]+=1
            # No automatic retry in this run; publisher records ambiguous sends.
            if execute: break
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--send",action="store_true")
    p.add_argument("--watch",action="store_true")
    args=p.parse_args()
    root=os.environ.get("SAM_MARKETING_PRIVATE_DIR","")
    if not root or not Path(root).is_absolute():raise SystemExit("Set SAM_MARKETING_PRIVATE_DIR to an absolute private persistent directory")
    root=Path(root).resolve()
    repo=Path(__file__).resolve().parents[2]
    if root==repo or repo in root.parents:raise SystemExit("Private queue must be outside the repository")
    if not root.is_dir():raise SystemExit("Private directory must already exist")
    queue=root/"queue.json";db=root/"publications.sqlite3"
    token=os.environ.get("TELEGRAM_BOT_TOKEN","")
    if args.send and not token:raise SystemExit("Configure bot secret in the local environment")
    if args.watch and not args.send:raise SystemExit("Watch mode requires explicit --send")
    while True:
        if (root/"STOP").exists():
            print('{"mode":"stopped"}',flush=True);return
        try: print(json.dumps(tick(queue,db,token,execute=args.send),ensure_ascii=False),flush=True)
        except (ValueError,KeyError,TypeError,OSError,sqlite3.Error):
            print('{"mode":"blocked","reason":"queue or storage invalid"}',flush=True);return
        if not args.watch:return
        time.sleep(60)
if __name__=="__main__":main()
