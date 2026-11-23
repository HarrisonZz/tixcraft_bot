#!/usr/bin/env python3
# encoding=utf-8
import http.server
import json
import os
import socketserver
import tempfile
import threading
import unittest

import chrome_tixcraft as bot
import settings


class MockTicketingHandler(http.server.BaseHTTPRequestHandler):
    refresh_hits = 0

    def log_message(self, format, *args):
        # Silence HTTP request logs during tests.
        pass

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/activity/detail/26_demo":
            self._send_html("<html><body><h1>Event Detail</h1></body></html>")
            return

        if path == "/activity/game/26_demo":
            self._send_html(
                """
                <html><body>
                  <div id="gameList">
                    <table>
                      <tbody>
                        <tr>
                          <td>2026/12/01 (Tue)</td>
                          <td><button class="btn-next" onclick="window.location='/ticket/area/26_demo/1'">Buy 1</button></td>
                        </tr>
                        <tr>
                          <td>2026/12/02 (Wed)</td>
                          <td><button class="btn-next" onclick="window.location='/ticket/area/26_demo/2'">Buy 2</button></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </body></html>
                """
            )
            return

        if path == "/activity/game/26_modern":
            self._send_html(
                """
                <html><body>
                  <header>
                    <button class="search-btn" data-href="/activity" onclick="window.location=this.getAttribute('data-href')"></button>
                  </header>
                  <div id="gameList">
                    <div class="table-wrap">
                      <table>
                        <tbody>
                          <tr>
                            <td>2026/12/10 VIP</td>
                            <td><button class="btn btn-primary" data-href="/ticket/area/26_modern/10" onclick="window.location=this.getAttribute('data-href')">Find tickets</button></td>
                          </tr>
                          <tr>
                            <td>2026/12/11 Regular</td>
                            <td><button class="btn btn-primary" data-href="/ticket/area/26_modern/11" onclick="window.location=this.getAttribute('data-href')">Find tickets</button></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </body></html>
                """
            )
            return

        if path.startswith("/ticket/area/26_demo/"):
            self._send_html(
                """
                <html><body>
                  <div class="zone">
                    <ul class="area-list">
                      <li><a href="/ticket/ticket/26_demo/a1">A1 Zone $3800</a></li>
                      <li><a href="/ticket/ticket/26_demo/b1">B1 Zone $2800</a></li>
                      <li><a href="/ticket/ticket/26_demo/b2">B2 Zone $2800</a></li>
                    </ul>
                  </div>
                </body></html>
                """
            )
            return

        if path == "/ticket/area/26_refresh":
            MockTicketingHandler.refresh_hits += 1
            self._send_html(
                """
                <html><body>
                  <div class="area-list">
                    <a href="/ticket/ticket/26_demo/c1">C1 Zone $1800</a>
                  </div>
                </body></html>
                """
            )
            return

        if path.startswith("/ticket/area/26_modern/"):
            self._send_html("<html><body><div class='area-list'><a href='/ticket/ticket/26_modern/1'>Floor $4800</a></div></body></html>")
            return

        if path == "/ticket/ticket/26_demo/a1":
            self._send_html(
                """
                <html><body>
                  <form id="TicketForm">
                    <select class="mobile-select" id="TicketForm_ticketPrice_01">
                      <option value="0" selected>0</option>
                      <option value="1">1</option>
                      <option value="2">2</option>
                      <option value="3">3</option>
                    </select>
                    <input type="checkbox" id="TicketForm_agree" />
                    <input type="text" id="TicketForm_verifyCode" />
                  </form>
                </body></html>
                """
            )
            return

        if path == "/ticket/ticket/26_demo/limited":
            self._send_html(
                """
                <html><body>
                  <form id="TicketForm">
                    <select id="TicketForm_ticketPrice_02">
                      <option value="0" selected>0</option>
                      <option value="1">1</option>
                    </select>
                    <input type="checkbox" id="TicketForm_agree" checked />
                    <input type="text" id="TicketForm_verifyCode" />
                  </form>
                </body></html>
                """
            )
            return

        if path == "/fami":
            self._send_html(
                """
                <html><body>
                  <div id="game_page">
                    <table><tbody>
                      <tr><td>h1</td></tr>
                      <tr><td>h2</td></tr>
                      <tr><td>h3</td></tr>
                      <tr><td>
                        <table><tbody>
                          <tr><td>2026/12/01</td><td><img id="d1" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" onclick="document.body.setAttribute('data-clicked','d1')" /></td></tr>
                          <tr><td>2026/12/02</td><td><img id="d2" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" onclick="document.body.setAttribute('data-clicked','d2')" /></td></tr>
                        </tbody></table>
                      </td></tr>
                    </tbody></table>
                  </div>
                </body></html>
                """
            )
            return

        if path == "/urbtix":
            self._send_html(
                """
                <html><body>
                  <table id="ticket-price-tbl">
                    <tbody>
                      <tr><td>Zone A</td><td><input type="radio" name="pz" class="pricezone-radio-input" value="A" /></td></tr>
                      <tr><td>Zone B</td><td><input type="radio" name="pz" class="pricezone-radio-input" value="B" /></td></tr>
                    </tbody>
                  </table>
                </body></html>
                """
            )
            return

        if path == "/cityline":
            self._send_html(
                """
                <html><body>
                  <table>
                    <tbody>
                      <tr class="menubar_text"><td>Header</td></tr>
                      <tr><td>Price 1</td><td><input type="radio" name="cl" value="1" /></td></tr>
                      <tr><td>Price 2</td><td><input type="radio" name="cl" value="2" /></td></tr>
                    </tbody>
                  </table>
                </body></html>
                """
            )
            return

        self.send_response(404)
        self.end_headers()


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


class UnitTests(unittest.TestCase):
    def test_load_config_from_repo(self):
        cfg = bot.load_config()
        self.assertIsNotNone(cfg)
        self.assertEqual(bot.homepage, "https://tixcraft.com")
        self.assertEqual(bot.browser, "chrome")
        self.assertEqual(bot.ticket_number, "2")

    def test_load_config_missing_file(self):
        cfg = bot.load_config("/nonexistent/settings.json")
        self.assertIsNone(cfg)

    def test_settings_load_json_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = os.path.join(tmpdir, "settings.json")
            cfg = settings.load_json(missing)
            self.assertEqual(cfg["homepage"], "https://tixcraft.com")
            self.assertEqual(cfg["browser"], "chrome")
            self.assertEqual(cfg["ticket_number"], 2)

    def test_helper_functions(self):
        self.assertEqual(bot.find_between("abc【XYZ】def", "【", "】"), "XYZ")
        self.assertEqual(bot.find_between("no markers", "【", "】"), "")
        self.assertEqual(bot.convert_string_to_pattern("AB12", dynamic_length=False), r"[A-Z][A-Z][\d][\d]")
        self.assertEqual(bot.convert_string_to_pattern("AB12", dynamic_length=True), r"[A-Z]+[\d]+")

    def test_get_answer_list_no_unbound_local_error(self):
        # Short trailing options previously triggered UnboundLocalError on maybe_delimitor.
        question = "測試題目？（範例：1A）1A"
        ans_list, delim = bot.get_answer_list_by_question(question)
        self.assertIsInstance(ans_list, list)
        self.assertEqual(delim, "")

    def test_select_target_index(self):
        self.assertEqual(bot._select_target_index(0, bot.CONST_FROM_TOP_TO_BOTTOM), -1)
        self.assertEqual(bot._select_target_index(3, bot.CONST_FROM_TOP_TO_BOTTOM), 0)
        self.assertEqual(bot._select_target_index(3, bot.CONST_FROM_BOTTOM_TO_TOP), 2)
        idx = bot._select_target_index(3, bot.CONST_RANDOM)
        self.assertIn(idx, (0, 1, 2))

    def test_driver_closed_error_detection(self):
        self.assertTrue(bot._is_driver_closed_error(Exception("invalid session id")))
        self.assertTrue(bot._is_driver_closed_error(Exception("chrome not reachable")))
        self.assertFalse(bot._is_driver_closed_error(Exception("some unrelated error")))

    def test_unsupported_browser_raises(self):
        with self.assertRaises(ValueError):
            bot.create_driver("safari")


class SeleniumIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingTCPServer(("127.0.0.1", 0), MockTicketingHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        bot.load_config()
        cls.driver = bot.create_driver(browser_name="chrome", headless=True)
        bot.driver = cls.driver

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None) is not None:
            cls.driver.quit()
            bot.driver = None
        cls.server.shutdown()
        cls.server.server_close()

    def test_tixcraft_redirect(self):
        url = f"{self.base_url}/activity/detail/26_demo"
        self.driver.get(url)
        redirected = bot.tixcraft_redirect(self.driver.current_url)
        self.assertTrue(redirected)
        self.assertTrue(self.driver.current_url.endswith("/activity/game/26_demo"))

    def test_tixcraft_date_auto_select_modes_and_keyword(self):
        # Top-to-bottom without keyword
        bot.date_keyword = ""
        bot.date_auto_select_mode = bot.CONST_FROM_TOP_TO_BOTTOM
        self.driver.get(f"{self.base_url}/activity/game/26_demo")
        self.assertTrue(bot.date_auto_select(self.driver.current_url))
        self.assertTrue(self.driver.current_url.endswith("/ticket/area/26_demo/1"))

        # Bottom-to-top without keyword
        bot.date_auto_select_mode = bot.CONST_FROM_BOTTOM_TO_TOP
        self.driver.get(f"{self.base_url}/activity/game/26_demo")
        self.assertTrue(bot.date_auto_select(self.driver.current_url))
        self.assertTrue(self.driver.current_url.endswith("/ticket/area/26_demo/2"))

        # Modern button[data-href] without keyword must ignore header search-btn
        bot.date_keyword = ""
        bot.date_auto_select_mode = bot.CONST_FROM_TOP_TO_BOTTOM
        self.driver.get(f"{self.base_url}/activity/game/26_modern")
        self.assertTrue(bot.date_auto_select(self.driver.current_url))
        self.assertTrue(self.driver.current_url.endswith("/ticket/area/26_modern/10"))

        # Modern button[data-href] + keyword matching
        bot.date_keyword = "2026/12/11"
        bot.date_auto_select_mode = bot.CONST_FROM_TOP_TO_BOTTOM
        self.driver.get(f"{self.base_url}/activity/game/26_modern")
        self.assertTrue(bot.date_auto_select(self.driver.current_url))
        self.assertTrue(self.driver.current_url.endswith("/ticket/area/26_modern/11"))

    def test_tixcraft_area_auto_select_and_refresh(self):
        # Keyword match with bottom-to-top picks B2
        bot.area_keyword = "$2800"
        bot.area_auto_select_mode = bot.CONST_FROM_BOTTOM_TO_TOP
        self.driver.get(f"{self.base_url}/ticket/area/26_demo/1")
        self.assertTrue(bot.area_auto_select(self.driver.current_url))
        self.assertTrue(self.driver.current_url.endswith("/ticket/ticket/26_demo/b2"))

        # Non-matching keyword triggers refresh
        MockTicketingHandler.refresh_hits = 0
        bot.area_keyword = "$9999"
        self.driver.get(f"{self.base_url}/ticket/area/26_refresh")
        hits_before = MockTicketingHandler.refresh_hits
        self.assertFalse(bot.area_auto_select(self.driver.current_url))
        self.assertGreater(MockTicketingHandler.refresh_hits, hits_before)

    def test_tixcraft_ticket_fill_agree_and_focus_verify_code(self):
        bot.ticket_number = "2"
        self.driver.get(f"{self.base_url}/ticket/ticket/26_demo/a1")
        editing = bot.tixcraft_ticket_main(self.driver.current_url, False)
        self.assertTrue(editing)

        selected_val = self.driver.execute_script(
            'return document.getElementById("TicketForm_ticketPrice_01").value;'
        )
        agree_checked = self.driver.execute_script(
            'return document.getElementById("TicketForm_agree").checked;'
        )
        active_id = self.driver.execute_script("return document.activeElement.id;")

        self.assertEqual(selected_val, "2")
        self.assertTrue(agree_checked)
        self.assertEqual(active_id, "TicketForm_verifyCode")

        # Fallback to "1" when requested ticket_number exceeds available options,
        # and do not uncheck an already-checked agree checkbox.
        bot.ticket_number = "4"
        self.driver.get(f"{self.base_url}/ticket/ticket/26_demo/limited")
        editing = bot.tixcraft_ticket_main(self.driver.current_url, False)
        self.assertTrue(editing)
        self.assertEqual(
            self.driver.execute_script('return document.getElementById("TicketForm_ticketPrice_02").value;'),
            "1",
        )
        self.assertTrue(
            self.driver.execute_script('return document.getElementById("TicketForm_agree").checked;')
        )

    def test_fami_bottom_to_top(self):
        bot.date_keyword = ""
        bot.date_auto_select_mode = bot.CONST_FROM_BOTTOM_TO_TOP
        self.driver.get(f"{self.base_url}/fami")
        bot.fami_date_auto_select(self.driver.current_url)
        clicked = self.driver.execute_script("return document.body.getAttribute('data-clicked');")
        self.assertEqual(clicked, "d2")

    def test_urbtix_and_cityline_area_select_modes(self):
        bot.kktix_area_keyword = ""
        bot.kktix_area_auto_select_mode = bot.CONST_FROM_BOTTOM_TO_TOP

        self.driver.get(f"{self.base_url}/urbtix")
        self.assertTrue(bot.urbtix_area_auto_select(self.driver.current_url))
        selected = self.driver.execute_script(
            'return document.querySelector("input[name=pz]:checked").value;'
        )
        self.assertEqual(selected, "B")

        self.driver.get(f"{self.base_url}/cityline")
        self.assertTrue(bot.cityline_area_auto_select(self.driver.current_url))
        selected = self.driver.execute_script(
            'return document.querySelector("input[name=cl]:checked").value;'
        )
        self.assertEqual(selected, "2")


if __name__ == "__main__":
    unittest.main()
