"""Russian Post SOAP tracking adapter. No browser credentials or synthetic scans."""
import os
import re
import time
import threading
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SOAP = "http://www.w3.org/2003/05/soap-envelope"
OP = "http://russianpost.org/operationhistory"
DATA = OP + "/data"
ENDPOINT = "https://tracking.russianpost.ru/rtm34"
MAX_XML = 2_000_000

class TrackingError(Exception):
    pass

def barcode(value):
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{9}[A-Z]{2}", value):
        raise ValueError("Invalid international postal tracking number")
    return value

def request_xml(track, login, password):
    root = ET.Element(f"{{{SOAP}}}Envelope")
    body = ET.SubElement(root, f"{{{SOAP}}}Body")
    method = ET.SubElement(body, f"{{{OP}}}getOperationHistory")
    for name, fields in (
        ("OperationHistoryRequest", {"Barcode": barcode(track), "MessageType": "0", "Language": "RUS"}),
        ("AuthorizationHeader", {"login": login, "password": password}),
    ):
        node = ET.SubElement(method, f"{{{DATA}}}{name}")
        for key, value in fields.items():
            ET.SubElement(node, f"{{{DATA}}}{key}").text = value
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)

def parse_history(payload):
    if len(payload) > MAX_XML or re.search(br"<!\s*(DOCTYPE|ENTITY)", payload, re.I):
        raise TrackingError("Unsafe or oversized XML")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        raise TrackingError("Invalid carrier response") from None
    for e in root.iter():
        e.tag = e.tag.rsplit("}", 1)[-1]
    if root.find(".//Fault") is not None or root.find(".//Error") is not None:
        raise TrackingError("Carrier returned an error")
    history = root.find(".//OperationHistoryData")
    if history is None:
        raise TrackingError("Missing carrier history")
    results = {}
    for record in history.findall("historyRecord"):
        def get(path):
            return (record.findtext(path) or "").strip()
        raw = get("OperationParameters/OperDate")
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        kind = get("OperationParameters/OperType/Name")
        attr = get("OperationParameters/OperAttr/Name")
        if not kind and not attr:
            continue
        place = get("AddressParameters/OperationAddress/Description")
        index = get("AddressParameters/OperationAddress/Index")
        # Do not return destination address, recipient, or declared value.
        event = {"date": dt.isoformat(), "kind": " · ".join(filter(None, (kind, attr))),
                 "place": place or index, "source": "russian_post"}
        key = (event["date"], event["kind"], event["place"])
        results[key] = event
    # For timestamps without a zone, preserve the carrier's local clock.
    def order_key(e):
        dt = datetime.fromisoformat(e["date"])
        return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt
    return sorted(results.values(), key=order_key, reverse=True)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def fetch_history(track):
    login = os.getenv("POCHTA_TRACK_LOGIN")
    password = os.getenv("POCHTA_TRACK_PASSWORD")
    if not login or not password:
        raise TrackingError("Tracking credentials not configured")
    req = urllib.request.Request(ENDPOINT, data=request_xml(track, login, password),
        headers={"Content-Type": "application/soap+xml; charset=utf-8", "SOAPAction": '""'}, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=15) as response:
            payload = response.read(MAX_XML + 1)
    except (OSError, ValueError):
        raise TrackingError("Carrier temporarily unavailable") from None
    return parse_history(payload)

class TrackingCache:
    """Per-process cache and cooldown; shared durable storage needed in production."""
    def __init__(self, fetch=fetch_history, ttl=900, clock=time.monotonic):
        self.fetch, self.ttl, self.clock = fetch, ttl, clock
        self.entries, self.attempts = {}, {}
        self.lock = threading.Lock()

    def get(self, track):
        track = barcode(track)
        with self.lock:
            now = self.clock()
            previous = self.entries.get(track)
            if previous and now - self.attempts[track] < self.ttl:
                return previous
            if track in self.attempts and now - self.attempts[track] < self.ttl:
                raise TrackingError("Retry later")
            self.attempts[track] = now
            try:
                events = self.fetch(track)
            except TrackingError:
                if previous:
                    stale = {**previous, "stale": True}
                    self.entries[track] = stale
                    return stale
                raise
            result = {"barcode": track, "events": events, "stale": False,
                      "checked_at": datetime.now(timezone.utc).isoformat(),
                      "eta": None, "source": "russian_post"}
            self.entries[track] = result
            return result
