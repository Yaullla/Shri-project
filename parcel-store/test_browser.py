"""Real Chromium regression test, synthetic users and local API only."""
import contextlib
import json
import tempfile
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from pilot_api import Store, build_handler
from test_pilot import signed, TOKEN

ROOT=Path(__file__).resolve().parent

@contextlib.contextmanager
def server(handler):
    srv=ThreadingHTTPServer(("127.0.0.1",0),handler)
    worker=threading.Thread(target=srv.serve_forever,daemon=True)
    worker.start()
    try: yield "http://127.0.0.1:"+str(srv.server_port)
    finally: srv.shutdown();srv.server_close();worker.join()

class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start()
        cls.browser=cls.p.chromium.launch()
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.p.stop()
    def context(self,width=390,auth=None,reduced="reduce"):
        c=self.browser.new_context(viewport={"width":width,"height":844},reduced_motion=reduced)
        c.route("**/*",lambda route:route.continue_() if route.request.url.startswith("http://127.0.0.1:") else route.abort())
        if auth:
            c.add_init_script("window.Telegram={WebApp:{initData:"+json.dumps(auth)+",ready(){},expand(){},setHeaderColor(){},setBackgroundColor(){}}}")
        return c
    def no_overflow(self,page):
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"))
    def test_storefront_responsive(self):
        with server(partial(SimpleHTTPRequestHandler,directory=str(ROOT))) as url:
            for width in (390,768,1440):
                with self.subTest(width=width),self.context(width) as c:
                    page=c.new_page();errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(url+"/index.html")
                    expect(page.locator(".hero")).to_be_visible()
                    self.no_overflow(page)
                    page.evaluate("go('catalog')")
                    expect(page.locator(".card.product")).to_have_count(13)
                    self.no_overflow(page)
                    page.evaluate("productDetails('buck')")
                    expect(page.locator("#productDialog")).to_be_visible()
                    expect(page.locator("#productDialog")).to_contain_text("Состав")
                    page.locator("#productDialog").evaluate("(d)=>d.close()")
                    page.evaluate("change('buck',1);go('cart')")
                    expect(page.locator("#app")).to_contain_text("Ваша заявка")
                    self.no_overflow(page)
                    page.evaluate("go('admin')")
                    for tab in ("Обзор","Заявки","Товары","Поставки"):
                        page.evaluate("(t)=>setTab(t)",tab)
                        self.assertGreater(len(page.locator("#app").inner_text()),20)
                    self.assertEqual(errors,[])
    def test_pilot_signed_checkout_and_owner_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Store(str(Path(tmp)/"test.db"),1000)
            with db.connection() as conn:
                conn.execute("UPDATE products SET approved=1,grams=500,price_kopecks=10000 WHERE id='buck'")
            with server(build_handler(db,TOKEN,{1},True)) as url:
                with self.context(auth=signed(1)) as c:
                    page=c.new_page();errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(url+"/miniapp")
                    expect(page.locator(".card")).to_have_count(13)
                    page.get_by_role("textbox",name="Поиск").fill("гречка")
                    expect(page.locator(".card")).to_have_count(1)
                    page.get_by_role("button",name="Характеристики").click()
                    expect(page.locator("dialog")).to_be_visible()
                    page.get_by_role("button",name="Добавить в заявку").click()
                    page.locator("nav").get_by_role("button",name="Заявка · 1").click()
                    page.get_by_role("button",name="Отправить заявку").click()
                    expect(page.locator("#app")).to_contain_text("Заявка получена")
                    page.locator("nav").get_by_role("button",name="CRM").click()
                    expect(page.locator("#app")).to_contain_text("Аналитика")
                    self.no_overflow(page);self.assertEqual(errors,[])
                with self.context(auth=signed(2)) as c:
                    page=c.new_page();page.goto(url+"/miniapp")
                    expect(page.locator(".card")).to_have_count(13)
                    page.locator("nav").get_by_role("button",name="Мои заявки").click()
                    expect(page.locator("#app")).to_contain_text("Заявок пока нет")
                    self.assertEqual(page.locator("nav").get_by_role("button",name="CRM").count(),0)
                self.assertEqual(len(db.orders(1)),1)
                self.assertEqual(db.catalog()["parcel"]["reserved"],500)
if __name__=="__main__": unittest.main()
