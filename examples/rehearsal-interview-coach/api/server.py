"""인터뷰 연습 기록 서버 — CONTRACT B(API)·C(실행 명령)·D(기록 파일). Python 3 표준 라이브러리만.

실행: python3 api/server.py [--data <경로>]   (기본 data/records.json)
"""
import argparse
import datetime
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PORT = 8765
ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"
FIXTURES = ROOT / "fixtures"  # S0 stub 전용 — S1·S3에서 스텁과 함께 지운다


def read_records(path):
    """기록 파일의 records 배열. 파일이 없으면 [](빈 상태). 시작 검증과 요청 처리가 같이 쓴다. 파일에 쓰지 않는다."""
    try:
        data = json.loads(Path(path).read_bytes())
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as e:  # ValueError = JSON 파싱 오류·UTF-8 아님
        raise ValueError(f"기록 파일을 읽을 수 없습니다: {path} ({e})")
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("records"), list):
        raise ValueError(f"기록 파일 형식이 맞지 않습니다(version 1, records 배열이어야 합니다): {path}")
    # shortcut: records 원소의 모양은 검사하지 않는다(사람이 고쳐 player 키가 빠지면 요청이 끊김), S3 검증 함수가 생기면 여기서도 쓴다
    return data["records"]


def list_players(records):
    """GET /api/players 응답: 기록이 있는 선수 이름, 가나다순, 중복 없음."""
    return {"players": sorted({record["player"] for record in records})}


class Handler(SimpleHTTPRequestHandler):
    """/api/* 는 JSON. 나머지 GET은 ui/ 정적 파일(경로 탈출 차단·index.html·404는 표준 라이브러리가 처리)."""

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/api/players":
            # shortcut: 실행 중 파일이 손상되면 응답 없이 끊긴다(stderr에 traceback), GET 에러 형식이 계약에 생기면 바꾼다
            self.send_json(list_players(read_records(self.server.records_path)))  # 요청마다 읽는다(캐시 없음)
        elif url.path == "/api/compare":
            # S0 stub — S1에서 교체: 기록 파일을 보지 않고 픽스처를 돌려준다. 400 검증 없음
            query = parse_qs(url.query)
            player = query.get("player", [""])[0]
            date = query.get("date", [datetime.date.today().isoformat()])[0]
            stub = {"김민수": "compare.response.json", "박지훈": "compare.today.response.json"}
            if player in stub:
                self.send_json(json.loads((FIXTURES / stub[player]).read_bytes()))
            else:
                self.send_json({"player": player, "date": date, "today": None, "previous": []})
        else:
            super().do_GET()

    def do_PUT(self):
        if urlsplit(self.path).path != "/api/records":
            self.send_error(404)
            return
        # S0 stub — S3에서 교체: 본문은 읽어서 버린다. 검증·저장 없음
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self.send_json(json.loads((FIXTURES / "record.put.response.json").read_bytes()))

    def send_json(self, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(records_path, port):
    """127.0.0.1:<port>에 바인드한 서버(실패 = OSError). 테스트는 port=0(임시 포트)으로 띄운다."""
    # Threading: 브라우저가 미리 열어 두는 빈 연결에 단일 스레드 서버가 묶이지 않게(http.server 문서 권장)
    server = ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=str(UI_DIR)))
    server.records_path = records_path
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="인터뷰 연습 기록 서버")
    parser.add_argument("--data", default="data/records.json", help="기록 파일 경로 (기본 data/records.json)")
    args = parser.parse_args(argv)
    try:
        read_records(args.data)  # 바인드 전에 검증. 손상 파일은 만들지도 덮어쓰지도 않는다
    except ValueError as e:
        raise SystemExit(str(e))  # 문자열 SystemExit = stderr에 그 한 줄 + exit 1
    try:
        server = make_server(args.data, PORT)
    except OSError as e:
        raise SystemExit(f"포트 {PORT}를 열 수 없습니다(이미 사용 중인지 확인하세요): {e}")
    print(f"인터뷰 연습 기록 — http://localhost:{PORT}  (기록 파일: {args.data})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass  # Ctrl+C = 트레이스백 없이 exit 0
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
