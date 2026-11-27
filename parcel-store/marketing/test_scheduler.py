import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scheduler import tick,UTC

class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.queue=self.root/"queue.json"
        self.db=self.root/"log.sqlite3"
        self.now=dt.datetime(2026,11,27,9,tzinfo=UTC)
        self.job={"job_id":"test1","chat_id":-100123,"approved":True,"free_confirmed":True,"approval_reference":"Synthetic permission","contact":"@test_contact","scheduled_at":self.now.isoformat(),"approval_expires_at":(self.now+dt.timedelta(hours=3)).isoformat()}
        self.calls=[]
    def save(self,enabled=True,jobs=None):
        self.queue.write_text(json.dumps({"enabled":enabled,"jobs":[self.job] if jobs is None else jobs}))
    def fake(self,j,token,dbpath,now=None):
        self.calls.append(j["job_id"]);return {"status":"sent"}
    def test_paused(self):
        self.save(False);self.assertEqual(tick(self.queue,self.db,"",self.now,self.fake,True)["mode"],"paused");self.assertEqual(self.calls,[])
    def test_dry_run_and_due(self):
        self.save();self.assertEqual(tick(self.queue,self.db,"",self.now,self.fake)["due"],1);self.assertEqual(self.calls,[])
        self.assertEqual(tick(self.queue,self.db,"",self.now,self.fake,True)["sent"],1)
    def test_unapproved_and_expired(self):
        self.save(jobs=[dict(self.job,approved=False),dict(self.job,job_id="expired",approval_expires_at=(self.now-dt.timedelta(seconds=1)).isoformat())])
        s=tick(self.queue,self.db,"",self.now,self.fake,True);self.assertEqual(s["blocked"],1);self.assertEqual(self.calls,[])
        self.save(jobs=[dict(self.job,approval_expires_at=self.now.isoformat())]);self.assertEqual(tick(self.queue,self.db,"",self.now,self.fake,True)["expired"],1)
    def test_duplicate_ids(self):
        self.save(jobs=[self.job,self.job])
        with self.assertRaises(ValueError):tick(self.queue,self.db,"",self.now,self.fake,True)
if __name__=="__main__":unittest.main()
