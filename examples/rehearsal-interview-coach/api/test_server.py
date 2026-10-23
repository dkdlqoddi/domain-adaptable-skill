"""S0 뼈대 테스트. 실행: python3 -m unittest discover -s api -p 'test_*.py' — 포트 8765를 쓰지 않는다."""
import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

import server

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE = FIXTURES / "records.sample.json"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ServerTest(unittest.TestCase):
    def test_players_computed_from_sample(self):
        records = server.read_records(SAMPLE)
        self.assertEqual(server.list_players(records), fixture("players.response.json"))

    def test_http_round_trip(self):
        httpd = server.make_server(SAMPLE, 0)  # 0 = 임시 포트. S0은 읽기만 하므로 픽스처를 그대로 가리킨다
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)  # cleanup은 역순: shutdown → server_close
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        with urllib.request.urlopen(base + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), (server.UI_DIR / "index.html").read_bytes())  # 디렉터리 목록이 아니라 index.html
        with urllib.request.urlopen(base + "/api/players") as response:
            self.assertEqual(response.headers["Content-Type"], "application/json; charset=utf-8")
            body = response.read().decode("utf-8")
        self.assertIn("김민수", body)  # 한글 이스케이프 없음
        self.assertEqual(json.loads(body), fixture("players.response.json"))

    def test_broken_file_refuses_start(self):
        broken = ["{ not json", '{"version": 2, "records": []}', '{"version": 1, "records": {}}']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.json"
            for text in broken:
                with self.subTest(text=text):
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises(SystemExit) as caught:  # 검증이 바인드보다 먼저라 8765를 열지 않는다
                        server.main(["--data", str(path)])
                    self.assertIn(str(path), str(caught.exception.code))  # stderr로 나갈 문장에 경로 포함
                    self.assertEqual(path.read_text(encoding="utf-8"), text)  # 덮어쓰지 않음

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "없음.json"
            self.assertEqual(server.list_players(server.read_records(path)), {"players": []})
            self.assertFalse(path.exists())  # 만들지 않음
