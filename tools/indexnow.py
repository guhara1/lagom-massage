#!/usr/bin/env python3
"""
IndexNow 즉시 색인 통보 스크립트 (Bing / Naver 등 IndexNow 참여 검색엔진)

표준 라이브러리만 사용 — 별도 설치(pip) 불필요. Python 3.7+

사용법
------
1) 전체 URL 일괄 통보 (sitemap.xml 의 모든 URL):
       python tools/indexnow.py

2) 특정 URL만 통보 (글 새로 올렸을 때):
       python tools/indexnow.py https://lagom-massage.pages.dev/notices \\
                                https://lagom-massage.pages.dev/regions/seoul

3) 변경된 URL 목록 파일에서 읽기 (한 줄에 하나):
       python tools/indexnow.py --from-file changed_urls.txt

동작
----
- IndexNow 한 곳(api.indexnow.org)에 제출하면 참여 엔진(Bing, Naver, Seznam, Yandex 등)에
  전파되지만, 즉시성·확실성을 위해 Bing·Naver 엔드포인트에도 직접 통보합니다.
- 한 번에 최대 10,000 URL 까지 묶어서 전송(IndexNow 제한), 초과 시 자동 분할.
"""

import json
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

# ─────────────────────────── 설정 ───────────────────────────
HOST = "lagom-massage.pages.dev"
KEY = "b918cb81b5f890cf38dc4fd1779cfefa"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP_PATH = Path(__file__).resolve().parent.parent / "sitemap.xml"

# IndexNow 참여 엔드포인트 (아무 곳에나 한 번 보내면 공유되지만, 확실히 하려고 복수 전송)
ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://searchadvisor.naver.com/indexnow",  # Naver IndexNow
]

BATCH_SIZE = 10000  # IndexNow 1회 최대 URL 수
# ────────────────────────────────────────────────────────────


def urls_from_sitemap(path: Path) -> list[str]:
    """sitemap.xml(또는 sitemap index)에서 모든 <loc> URL을 수집."""
    if not path.exists():
        sys.exit(f"[오류] sitemap을 찾을 수 없습니다: {path}")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(path)
    root = tree.getroot()
    locs = [el.text.strip() for el in root.findall(".//sm:loc", ns) if el.text]
    # sitemap index 인 경우(<sitemap><loc>...) 하위 맵까지는 로컬 파일 기준으로만 처리
    return locs


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def submit(urls: list[str]) -> None:
    if not urls:
        print("[정보] 통보할 URL이 없습니다.")
        return
    print(f"[정보] 통보 대상 URL: {len(urls)}개")
    for batch in chunked(urls, BATCH_SIZE):
        payload = json.dumps(
            {
                "host": HOST,
                "key": KEY,
                "keyLocation": KEY_LOCATION,
                "urlList": batch,
            }
        ).encode("utf-8")

        for endpoint in ENDPOINTS:
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "lagom-massage-indexnow/1.0",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    print(f"  ✓ {endpoint}  →  HTTP {resp.status} ({len(batch)} URL)")
            except urllib.error.HTTPError as e:
                # 200/202 외의 코드도 IndexNow에서는 의미가 있음(예: 200 OK, 202 Accepted)
                body = e.read().decode("utf-8", "ignore")[:200]
                print(f"  ✗ {endpoint}  →  HTTP {e.code}  {body}")
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ {endpoint}  →  실패: {e}")


def main(argv: list[str]) -> None:
    args = argv[1:]
    if args and args[0] == "--from-file":
        if len(args) < 2:
            sys.exit("사용법: python tools/indexnow.py --from-file <파일경로>")
        urls = [
            line.strip()
            for line in Path(args[1]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    elif args:
        urls = args
    else:
        # 인자 없음 → sitemap 전체 일괄 통보
        urls = urls_from_sitemap(SITEMAP_PATH)

    submit(urls)


if __name__ == "__main__":
    main(sys.argv)
