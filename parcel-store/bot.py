"""Private-chat Telegram entry point. Run only after HTTPS deployment."""
import json, os, re, sys, time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def call(token,method,params):
    req=Request("https://api.telegram.org/bot"+token+"/"+method,
        data=json.dumps(params,ensure_ascii=False).encode(),
        headers={"Content-Type":"application/json"})
    try:
        with build_opener(NoRedirect()).open(req,timeout=45) as r:
            data=json.load(r)
        if not data.get("ok"): raise ValueError()
        return data["result"]
    except Exception:
        raise RuntimeError("Telegram API unavailable: "+method) from None

def main():
    token=os.environ.get("TELEGRAM_BOT_TOKEN","")
    url=os.environ.get("SAM_MINIAPP_URL","")
    parsed=urlsplit(url)
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+",token) or parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and public HTTPS SAM_MINIAPP_URL")
    if "--configure" in sys.argv:
        call(token,"setMyCommands",{"commands":[{"command":"start","description":"Открыть Самобранку"},{"command":"help","description":"Как заказать"},{"command":"id","description":"Мой Telegram ID"}]})
        call(token,"setChatMenuButton",{"menu_button":{"type":"web_app","text":"Самобранка","web_app":{"url":url}}})
        print("Commands and menu configured.")
        return
    offset=None
    while True:
        try:
            args={"timeout":25,"allowed_updates":["message"]}
            if offset is not None: args["offset"]=offset
            for update in call(token,"getUpdates",args):
                msg=update.get("message",{})
                chat=msg.get("chat",{})
                command=msg.get("text","").split(maxsplit=1)[0].split("@")[0] if msg.get("text","").strip() else ""
                if chat.get("type")=="private" and command in ("/start","/help","/id"):
                    if command=="/id":
                        payload={"chat_id":chat["id"],"text":str(msg["from"]["id"])}
                    else:
                        payload={"chat_id":chat["id"],"text":"Самобранка — всё, по чему скучали. Русские продукты по предварительным заявкам. Самовывоз в Хиккадуве. Без оплаты до согласования поставки.",
                                 "reply_markup":{"inline_keyboard":[[{"text":"Открыть каталог","web_app":{"url":url}}]]}}
                    call(token,"sendMessage",payload)
                offset=update["update_id"]+1
        except RuntimeError as e:
            print(str(e),flush=True);time.sleep(5)
if __name__=="__main__": main()
