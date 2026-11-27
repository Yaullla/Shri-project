import hashlib,hmac,json,tempfile,time,unittest,uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from pilot_api import Store,authenticate,ApiError

TOKEN="123:TEST_ONLY"
def signed(uid=1,age=0):
    d={"user":json.dumps({"id":uid}),"auth_date":str(int(time.time())-age),"start_param":"tg_hikka"}
    key=hmac.digest(b"WebAppData",TOKEN.encode(),"sha256")
    d["hash"]=hmac.new(key,"\n".join(f"{k}={v}" for k,v in sorted(d.items())).encode(),hashlib.sha256).hexdigest()
    return urlencode(d)
def request(q=1,**kwargs):
    return {"request_id":str(uuid.uuid4()),"items":{"buck":q},**kwargs}

class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.s=Store(str(Path(self.tmp.name)/"test.db"),1000)
    def tearDown(self): self.tmp.cleanup()
    def approve(self):
        with self.s.connection() as c:
            c.execute("UPDATE products SET approved=1,grams=500,price_kopecks=10000 WHERE id='buck'")
    def test_signed_identity(self):
        self.assertEqual(authenticate(signed(),TOKEN),(1,"tg_hikka"))
        for x in [signed(age=4000),signed()+"&start_param=bad",signed().replace("tg_hikka","tampered")]:
            with self.assertRaises(ApiError): authenticate(x,TOKEN)
    def test_unapproved_is_interest(self):
        o=self.s.submit(1,"direct",request())
        self.assertEqual((o["status"],o["grams"],o["amount"],o["parcel"]),("interest",0,0,None))
    def test_exact_capacity_and_idempotency(self):
        self.approve();r=request(2)
        o=self.s.submit(1,"direct",r)
        self.assertEqual(o["parcel"]["status"],"closed")
        self.assertEqual(self.s.catalog()["parcel"]["reserved"],0)
        self.assertEqual(self.s.submit(1,"direct",r)["id"],o["id"])
        self.assertEqual(len(self.s.orders(1)),1)
        with self.assertRaises(ApiError): self.s.submit(1,"direct",{**r,"items":{"buck":1}})
    def test_overweight_and_consent(self):
        self.approve();self.s.submit(1,"direct",request())
        with self.assertRaises(ApiError): self.s.submit(2,"direct",request(3,allow_next=True))
        with self.assertRaises(ApiError): self.s.submit(2,"direct",request(2))
        self.assertEqual(self.s.catalog()["parcel"]["reserved"],500)
        o=self.s.submit(2,"direct",request(2,allow_next=True))
        self.assertEqual(o["parcel"]["id"],2)
    def test_ownership_and_cancel(self):
        self.approve();o=self.s.submit(1,"direct",request())
        self.assertEqual(self.s.orders(2),[])
        with self.assertRaises(ApiError): self.s.cancel(2,o["id"])
        self.s.cancel(1,o["id"]);self.s.cancel(1,o["id"])
        self.assertEqual(self.s.catalog()["parcel"]["reserved"],0)
    def test_concurrent_capacity(self):
        self.approve()
        def place(i): return self.s.submit(i,"direct",request(1,allow_next=True))
        with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(place,range(1,17)))
        for p in self.s.summary()["parcels"]:
            self.assertLessEqual(p["reserved"],p["capacity"])
        self.assertEqual(self.s.summary()["totals"]["requests"],16)
if __name__=="__main__": unittest.main()
