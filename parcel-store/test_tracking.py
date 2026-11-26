import unittest
import xml.etree.ElementTree as ET
from tracking import TrackingCache, TrackingError, request_xml, parse_history, barcode

TRACK = "EE123456789RU"  # synthetic, not submitted to carrier
RECORD = """<historyRecord><AddressParameters><OperationAddress><Description>Москва</Description></OperationAddress></AddressParameters><OperationParameters><OperDate>2026-11-25T12:00:00+03:00</OperDate><OperType><Name>Приём</Name></OperType></OperationParameters><ItemParameters><Recipient>PRIVATE</Recipient></ItemParameters></historyRecord>"""
XML = ("<Envelope><Body><OperationHistoryData>"+RECORD+RECORD+"</OperationHistoryData></Body></Envelope>").encode()

class TrackingTests(unittest.TestCase):
    def test_parse_deduplicates_and_omits_private_data(self):
        events = parse_history(XML)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["place"], "Москва")
        self.assertNotIn("PRIVATE", str(events))
    def test_invalid_response(self):
        for payload in (b"<Fault/>", b"<invalid>", b"<!DOCTYPE x><x/>", b"<x/>"):
            with self.assertRaises(TrackingError):
                parse_history(payload)
    def test_empty_history(self):
        self.assertEqual(parse_history(b"<OperationHistoryData/>"), [])
    def test_xml_escapes_credentials(self):
        xml = request_xml(TRACK, "<user>", "a&b")
        self.assertIn(b"&amp;", xml)
        ET.fromstring(xml)
    def test_invalid_barcode(self):
        with self.assertRaises(ValueError):
            barcode("../not-a-track")
    def test_cache_and_stale(self):
        t, calls = [0], []
        def fetch(track):
            calls.append(track)
            if len(calls)>1:
                raise TrackingError("Offline")
            return parse_history(XML)
        cache = TrackingCache(fetch=fetch, ttl=10, clock=lambda: t[0])
        self.assertFalse(cache.get(TRACK)["stale"])
        cache.get(TRACK)
        self.assertEqual(len(calls),1)
        t[0]=11
        self.assertTrue(cache.get(TRACK)["stale"])
        self.assertTrue(cache.get(TRACK)["stale"])
        self.assertEqual(len(calls),2)
        self.assertIsNone(cache.get(TRACK)["eta"])

if __name__ == "__main__":
    unittest.main()
