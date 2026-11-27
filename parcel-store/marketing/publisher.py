"""Publish one operator-approved announcement to a permitted Telegram group/channel.
No user sessions, scraping, private messages, paid broadcasts or automatic retry."""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bot import call

HERE=Path(__file__).resolve().parent
UTC=dt.timezone.utc

def parse_time(s):
    v=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if v.tzinfo is None: raise ValueError("Use an explicit timezone")
    return v.astimezone(UTC)

def validate(entry,now):
    if not isinstance(entry,dict) or entry.get("approved") is not True or entry.get("free_confirmed") is not True:
        raise ValueError("Explicit administrator approval and free placement are required")
    if type(entry.get("chat_id")) is not int or entry["chat_id"]>=0:
        raise ValueError("Only numeric group/channel IDs, never private messages")
    if not isinstance(entry.get("approval_reference"),str) or not entry["approval_reference"].strip():
        raise ValueError("Record administrator approval privately")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}",entry.get("job_id","")):
        raise ValueError("Invalid job ID")
    due=parse_time(entry["scheduled_at"])
    until=parse_time(entry["approval_expires_at"])
    if not due<=now<until or now-due>dt.timedelta(hours=6):
        raise ValueError("Outside approved scheduling window")
    if not isinstance(entry.get("contact"),str) or not re.fullmatch(r"@[A-Za-z0-9_]{5,32}",entry["contact"]):
        raise ValueError("Set the public contact username approved for the campaign")
    if entry.get("photo_file_id") and not re.fullmatch(r"[A-Za-z0-9_-]{1,500}",entry["photo_file_id"]):
        raise ValueError("Use a Telegram file_id already uploaded to this bot")
    return entry

def publish(entry,token,dbpath,telegram=call,now=None):
    now=now or dt.datetime.now(UTC)
    validate(entry,now)
    chat=telegram(token,"getChat",{"chat_id":entry["chat_id"]})
    if chat.get("id")!=entry["chat_id"] or chat.get("type") not in ("group","supergroup","channel"):
        raise ValueError("Target is not the approved group/channel")
    me=telegram(token,"getMe",{})
    member=telegram(token,"getChatMember",{"chat_id":chat["id"],"user_id":me["id"]})
    status=member.get("status")
    if chat["type"]=="channel":
        if not (status=="creator" or status=="administrator" and member.get("can_post_messages") is True):
            raise ValueError("Bot has no channel posting permission")
    elif status not in ("creator","administrator","member"):
        raise ValueError("Bot has not been admitted with posting permission")
    elif status=="member":
        perms=chat.get("permissions",{})
        if not perms.get("can_send_messages") or entry.get("photo_file_id") and not perms.get("can_send_photos"):
            raise ValueError("Group posting permissions unavailable")
    text=(HERE/"campaign-new-year.txt").read_text(encoding="utf-8").strip()+"\n\nКонтакт: "+entry["contact"]
    photo=entry.get("photo_file_id")
    if len(text)>(1024 if photo else 4096):
        raise ValueError("Message too long")
    conn=sqlite3.connect(dbpath,timeout=10)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS publications(job_id TEXT PRIMARY KEY, chat_id INTEGER NOT NULL, attempted_at TEXT NOT NULL, state TEXT NOT NULL, message_id INTEGER)")
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM publications WHERE job_id=?",(entry["job_id"],)).fetchone():
            conn.rollback();return {"status":"already_attempted"}
        recent=conn.execute("SELECT attempted_at FROM publications WHERE chat_id=? ORDER BY attempted_at DESC LIMIT 1",(chat["id"],)).fetchone()
        # Conservative global floor; operator must also respect stricter chat rules.
        if recent and now-parse_time(recent[0])<dt.timedelta(days=3):
            conn.rollback();raise ValueError("Less than three days since previous attempt in this chat")
        conn.execute("INSERT INTO publications VALUES(?,?,?,'attempted',NULL)",(entry["job_id"],chat["id"],now.isoformat()))
        conn.commit()
        params={"chat_id":chat["id"],"allow_paid_broadcast":False}
        if photo: params.update(photo=photo,caption=text)
        else: params.update(text=text)
        try:
            result=telegram(token,"sendPhoto" if photo else "sendMessage",params)
            mid=result["message_id"]
            conn.execute("UPDATE publications SET state='sent',message_id=? WHERE job_id=?",(mid,entry["job_id"]))
            conn.commit()
            return {"status":"sent","message_id":mid}
        except Exception:
            # Ambiguous network failure: do not retry automatically, inspect Telegram first.
            conn.execute("UPDATE publications SET state='needs_review' WHERE job_id=?",(entry["job_id"],))
            conn.commit()
            raise RuntimeError("Publication result unknown; review manually before any new job") from None
    finally: conn.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--send",action="store_true")
    args=p.parse_args()
    if not args.send:
        data=json.loads((HERE/"communities.json").read_text(encoding="utf-8"))
        print(json.dumps({"candidates":len(data["communities"]),"approved":0,"mode":"dry-run"},ensure_ascii=False))
        return
    token=os.environ.get("TELEGRAM_BOT_TOKEN","")
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+",token):
        raise SystemExit("Configure Telegram bot token securely first")
    dbpath=os.environ.get("SAM_MARKETING_DB","")
    if not dbpath or not Path(dbpath).is_absolute():
        raise SystemExit("An absolute persistent private publication-log path is required")
    entry=json.loads(os.environ.get("SAM_APPROVED_PUBLICATION","{}"))
    print(json.dumps(publish(entry,token,dbpath),ensure_ascii=False))
if __name__=="__main__":main()
