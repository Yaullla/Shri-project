import datetime as dt
import tempfile
import unittest
from pathlib import Path
from publisher import publish,validate,UTC

class TestPublisher(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,11,27,4,tzinfo=UTC)
        self.entry={"approved":True,"free_confirmed":True,"chat_id":-100123,"approval_reference":"Synthetic approval","job_id":"demo1","contact":"@demo_contact","scheduled_at":self.now.isoformat(),"approval_expires_at":(self.now+dt.timedelta(days=1)).isoformat()}
        self.calls=[]
    def fake(self,token,method,params):
        self.calls.append(method)
        return {"getChat":{"id":-100123,"type":"supergroup","permissions":{"can_send_messages":True,"can_send_photos":True}},"getMe":{"id":123},"getChatMember":{"status":"member"},"sendMessage":{"message_id":5},"sendPhoto":{"message_id":6}}[method]
    def test_denied_and_private(self):
        for entry in [dict(self.entry,approved=False),dict(self.entry,free_confirmed=False),dict(self.entry,chat_id=123),dict(self.entry,approval_expires_at="2026-11-26T00:00:00Z")]:
            with self.assertRaises(ValueError):validate(entry,self.now)
    def test_single_send_and_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            path=str(Path(d)/"test.sqlite3")
            self.assertEqual(publish(self.entry,"test",path,self.fake,self.now)["status"],"sent")
            self.assertEqual(publish(self.entry,"test",path,self.fake,self.now)["status"],"already_attempted")
            self.assertEqual(self.calls.count("sendMessage"),1)
            with self.assertRaises(ValueError):publish(dict(self.entry,job_id="demo2"),"test",path,self.fake,self.now)
    def test_missing_permission(self):
        def denied(token,method,params):
            return {"status":"left"} if method=="getChatMember" else self.fake(token,method,params)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):publish(self.entry,"test",str(Path(d)/"test.sqlite3"),denied,self.now)
        self.assertNotIn("sendMessage",self.calls)
if __name__=="__main__":unittest.main()
