"""Samobranka pilot API. Run with a private persistent database behind HTTPS."""
import hashlib, hmac, json, os, re, sqlite3, time, uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qsl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
PRODUCTS = [
 ("ejk","ЕЖК Провансаль 67%","400 мл","Соусы"),("ricco","Mr.Ricco Провансаль 67%","400 мл","Соусы"),
 ("sloboda","Слобода Провансаль 67%","400 мл","Соусы"),("sprats","За Родину — шпроты","160 г","Консервы"),
 ("cod","Беринг — печень трески","230 г","Консервы"),("saury","Доброфлот — сайра","245 г","Консервы"),
 ("buck","Мистраль — гречка","900 г","Крупы"),("mustard","Махеевъ — горчица","100 г","Соусы"),
 ("horseradish","Махеевъ — хрен","190 г","Соусы"),("milk","Алексеевское — сгущёнка","380 г","Молочные"),
 ("cheese","Сыр Российский","250 г","Молочные"),("roe","Тунгутун — икра","90 г","Деликатесы"),
 ("herring","Матиас — сельдь","250 г","Консервы")]
class ApiError(Exception):
    def __init__(self,status,message): self.status,self.message=status,message

def authenticate(raw,token,now=None):
    try:
        if not token or not raw or len(raw)>16384: raise ValueError()
        pairs=parse_qsl(raw,keep_blank_values=True,strict_parsing=True,max_num_fields=40)
        fields=dict(pairs)
        if len(fields)!=len(pairs): raise ValueError()
        signature=fields.pop("hash")
        check="\n".join(f"{k}={v}" for k,v in sorted(fields.items()))
        secret=hmac.digest(b"WebAppData",token.encode(),"sha256")
        expected=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,signature): raise ValueError()
        age=(time.time() if now is None else now)-int(fields["auth_date"])
        if not -30<=age<=3600: raise ValueError()
        uid=json.loads(fields["user"])["id"]
        if type(uid)!=int or not 0<uid<2**52: raise ValueError()
        source=fields.get("start_param","direct")
        return uid,source if re.fullmatch(r"[A-Za-z0-9_-]{1,64}",source) else "direct"
    except (ValueError,KeyError,TypeError,OverflowError):
        raise ApiError(401,"Откройте приложение заново через Telegram.") from None

SCHEMA="""
CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,name TEXT NOT NULL,size TEXT NOT NULL,category TEXT NOT NULL,grams INTEGER,price_kopecks INTEGER,approved INTEGER NOT NULL DEFAULT 0 CHECK(approved IN(0,1)),CHECK(approved=0 OR (grams IS NOT NULL AND grams>0 AND price_kopecks IS NOT NULL AND price_kopecks>0)));
CREATE TABLE IF NOT EXISTS parcels(id INTEGER PRIMARY KEY,capacity INTEGER NOT NULL CHECK(capacity>0),reserved INTEGER NOT NULL DEFAULT 0 CHECK(reserved>=0 AND reserved<=capacity),status TEXT NOT NULL CHECK(status IN('open','closed','sent','arrived','ready')),track TEXT, sent TEXT,eta_from TEXT,eta_to TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS one_open ON parcels(status) WHERE status='open';
CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,owner INTEGER NOT NULL,request_id TEXT NOT NULL,digest TEXT NOT NULL,source TEXT NOT NULL,created INTEGER NOT NULL,parcel INTEGER REFERENCES parcels(id),status TEXT NOT NULL CHECK(status IN('interest','requested','cancelled')),wish TEXT NOT NULL,notify INTEGER NOT NULL CHECK(notify IN(0,1)),grams INTEGER NOT NULL,amount INTEGER NOT NULL,UNIQUE(owner,request_id));
CREATE TABLE IF NOT EXISTS items(order_id TEXT NOT NULL REFERENCES orders(id),sku TEXT NOT NULL,name TEXT NOT NULL,size TEXT NOT NULL,qty INTEGER NOT NULL CHECK(qty>0),grams INTEGER,price_kopecks INTEGER,PRIMARY KEY(order_id,sku));
CREATE INDEX IF NOT EXISTS orders_owner ON orders(owner,created);
"""
class Store:
    def __init__(self,path,capacity=29000):
        self.path=path
        with self.connection() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript(SCHEMA)
            c.execute("BEGIN IMMEDIATE")
            c.executemany("INSERT OR IGNORE INTO products(id,name,size,category) VALUES(?,?,?,?)",PRODUCTS)
            c.execute("INSERT INTO parcels(capacity,status) SELECT ?,'open' WHERE NOT EXISTS(SELECT 1 FROM parcels WHERE status='open')",(capacity,))
            c.commit()
    @contextmanager
    def connection(self):
        c=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try: yield c
        finally: c.close()
    @staticmethod
    def open_parcel(c):
        return c.execute("SELECT id,capacity,reserved FROM parcels WHERE status='open'").fetchone()
    @staticmethod
    def rotate(c,p):
        c.execute("UPDATE parcels SET status='closed' WHERE id=?",(p["id"],))
        c.execute("INSERT INTO parcels(capacity,status) VALUES(?,'open')",(p["capacity"],))
        return Store.open_parcel(c)
    def catalog(self):
        with self.connection() as c:
            return {"products":[dict(r) for r in c.execute("SELECT * FROM products ORDER BY rowid")],
                    "parcel":dict(self.open_parcel(c))}
    @staticmethod
    def order_data(c,o):
        parcel=c.execute("SELECT id,status,track,sent,eta_from,eta_to FROM parcels WHERE id=?",(o["parcel"],)).fetchone()
        return {k:o[k] for k in ("id","created","status","wish","grams","amount","notify")} | {
            "items":[dict(r) for r in c.execute("SELECT sku,name,size,qty,grams,price_kopecks FROM items WHERE order_id=?",(o["id"],))],
            "parcel":dict(parcel) if parcel else None}
    def submit(self,owner,source,data):
        if not isinstance(data,dict): raise ApiError(400,"Неверная заявка.")
        key=data.get("request_id")
        if not isinstance(key,str) or not re.fullmatch(r"[a-f0-9-]{36}",key): raise ApiError(400,"Неверный идентификатор заявки.")
        wish=data.get("wish","")
        rows=data.get("items",{})
        move=data.get("allow_next",False)
        notify=data.get("notify",False)
        if not isinstance(wish,str) or len(wish)>1000 or not isinstance(rows,dict) or len(rows)>50 or type(move)!=bool or type(notify)!=bool:
            raise ApiError(400,"Проверьте заявку.")
        if any(not isinstance(k,str) or type(q)!=int or not 1<=q<=99 for k,q in rows.items()) or (not rows and not wish.strip()):
            raise ApiError(400,"Выберите товар или напишите пожелание.")
        digest=hashlib.sha256(json.dumps([rows,wish.strip(),notify],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with self.connection() as c:
            c.execute("BEGIN IMMEDIATE")
            previous=c.execute("SELECT * FROM orders WHERE owner=? AND request_id=?",(owner,key)).fetchone()
            if previous:
                if previous["digest"]!=digest: raise ApiError(409,"Изменённая заявка требует нового номера.")
                return self.order_data(c,previous)
            snapshots=[]; grams=amount=0
            for sku,qty in rows.items():
                p=c.execute("SELECT * FROM products WHERE id=?",(sku,)).fetchone()
                if not p: raise ApiError(400,"Товар не найден.")
                g=p["grams"] if p["approved"] else None
                price=p["price_kopecks"] if p["approved"] else None
                grams+=(g or 0)*qty; amount+=(price or 0)*qty
                snapshots.append((sku,p["name"],p["size"],qty,g,price))
            parcel=None
            if grams:
                p=self.open_parcel(c)
                if grams>p["capacity"]: raise ApiError(422,"Корзина тяжелее целой посылки.")
                if grams>p["capacity"]-p["reserved"]:
                    if not move: raise ApiError(409,"Недостаточно места. Подтвердите следующую партию.")
                    p=self.rotate(c,p)
                parcel=p["id"]
                c.execute("UPDATE parcels SET reserved=reserved+? WHERE id=?",(grams,parcel))
                remaining=p["capacity"]-p["reserved"]-grams
                minimum=c.execute("SELECT MIN(grams) FROM products WHERE approved=1").fetchone()[0]
                if remaining==0 or (minimum and remaining<minimum): self.rotate(c,p)
            oid=str(uuid.uuid4())
            c.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(oid,owner,key,digest,source,int(time.time()),parcel,"requested" if grams else "interest",wish.strip(),int(notify),grams,amount))
            c.executemany("INSERT INTO items VALUES(?,?,?,?,?,?,?)",[(oid,*x) for x in snapshots])
            result=self.order_data(c,c.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone())
            c.commit()
            return result
    def orders(self,owner):
        with self.connection() as c:
            return [self.order_data(c,r) for r in c.execute("SELECT * FROM orders WHERE owner=? ORDER BY created DESC LIMIT 100",(owner,))]
    def cancel(self,owner,oid):
        with self.connection() as c:
            c.execute("BEGIN IMMEDIATE")
            o=c.execute("SELECT * FROM orders WHERE id=? AND owner=?",(oid,owner)).fetchone()
            if not o: raise ApiError(404,"Заявка не найдена.")
            if o["status"]=="cancelled": return self.order_data(c,o)
            if o["parcel"]:
                p=c.execute("SELECT status FROM parcels WHERE id=?",(o["parcel"],)).fetchone()
                if p["status"]!="open": raise ApiError(409,"Партия закрыта. Согласуйте отмену с организатором.")
                c.execute("UPDATE parcels SET reserved=reserved-? WHERE id=?",(o["grams"],o["parcel"]))
            c.execute("UPDATE orders SET status='cancelled' WHERE id=?",(oid,))
            result=self.order_data(c,c.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone())
            c.commit(); return result
    def summary(self):
        with self.connection() as c:
            return {"totals":dict(c.execute("SELECT COUNT(*) requests,COUNT(DISTINCT owner) customers,COALESCE(SUM(grams),0) reserved_grams,COALESCE(SUM(amount),0) estimated_kopecks FROM orders WHERE status!='cancelled'").fetchone()),
             "sources":[dict(r) for r in c.execute("SELECT source,COUNT(*) requests,COUNT(DISTINCT owner) customers FROM orders WHERE status!='cancelled' GROUP BY source ORDER BY requests DESC")],
             "products":[dict(r) for r in c.execute("SELECT i.sku,i.name,SUM(i.qty) quantity FROM items i JOIN orders o ON o.id=i.order_id WHERE o.status!='cancelled' GROUP BY i.sku,i.name ORDER BY quantity DESC")],
             "parcels":[dict(r) for r in c.execute("SELECT id,status,capacity,reserved FROM parcels ORDER BY id DESC LIMIT 100")]}

def build_handler(store,token,admins,enabled):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def send(self,status,payload,media="application/json; charset=utf-8"):
            raw=json.dumps(payload,ensure_ascii=False).encode() if isinstance(payload,(dict,list)) else payload
            self.send_response(status); self.send_header("Content-Type",media)
            self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
            self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def identity(self): return authenticate(self.headers.get("X-Telegram-Init-Data",""),token)
        def body(self):
            n=int(self.headers.get("Content-Length","0"))
            if not 0<n<=16000: raise ApiError(400,"Неверный размер заявки.")
            return json.loads(self.rfile.read(n))
        def dispatch(self):
            path=self.path.split("?",1)[0]
            if self.command=="GET":
                if path in ("/","/miniapp"):
                    return self.send(200,(ROOT/"miniapp.html").read_bytes(),"text/html; charset=utf-8")
                if path=="/health": return self.send(200,{"ok":True})
                if path=="/api/catalog": return self.send(200,store.catalog() | {"accepting":enabled})
                if path=="/api/orders": return self.send(200,store.orders(self.identity()[0]))
                if path=="/api/admin/summary":
                    if self.identity()[0] not in admins: raise ApiError(403,"Доступ запрещён.")
                    return self.send(200,store.summary())
            if self.command=="POST":
                uid,source=self.identity()
                if path=="/api/orders":
                    if not enabled: raise ApiError(503,"Сбор заявок ещё не открыт.")
                    return self.send(200,store.submit(uid,source,self.body()))
                if path=="/api/cancel":
                    data=self.body()
                    if not isinstance(data,dict) or not isinstance(data.get("id"),str): raise ApiError(400,"Неверная заявка.")
                    return self.send(200,store.cancel(uid,data["id"]))
            raise ApiError(404,"Страница не найдена.")
        def handle_api(self):
            try: self.dispatch()
            except ApiError as e: self.send(e.status,{"error":e.message})
            except (ValueError,TypeError): self.send(400,{"error":"Неверные данные."})
            except sqlite3.Error: self.send(503,{"error":"База временно недоступна."})
        do_GET=do_POST=handle_api
    return Handler

if __name__=="__main__":
    token=os.environ.get("TELEGRAM_BOT_TOKEN","")
    admins={int(x) for x in os.environ.get("SAM_ADMIN_IDS","").split(",") if x.strip()}
    enabled=os.environ.get("SAM_ACCEPT_REQUESTS")=="1"
    if enabled and (not token or not admins): raise SystemExit("Configure bot token and admin IDs first")
    db=Store(os.environ.get("SAM_DB","samobranka.sqlite3"),int(os.environ.get("SAM_CAPACITY_GRAMS","29000")))
    ThreadingHTTPServer(("127.0.0.1",8081),build_handler(db,token,admins,enabled)).serve_forever()
