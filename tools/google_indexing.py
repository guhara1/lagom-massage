#!/usr/bin/env python3
"""
Google Indexing API 즉시 색인 통보 스크립트

⚠️ 참고: 구글은 IndexNow에 참여하지 않습니다. 또한 Indexing API는 공식적으로
   JobPosting / BroadcastEvent 구조화 데이터 페이지를 위한 것입니다. 일반 페이지는
   '제출은 되지만 색인은 보장되지 않음'에 가깝습니다. 가장 확실한 일반 색인 경로는
   Google Search Console 에 사이트를 등록하고 sitemap.xml 을 제출하는 것입니다.
   (이 스크립트는 보조 수단입니다.)

사전 준비
--------
1) Google Cloud 프로젝트에서 "Indexing API" 활성화
2) 서비스 계정 생성 → JSON 키 다운로드
3) Search Console 에서 해당 서비스 계정 이메일을 '소유자(Owner)'로 추가
4) 라이브러리 설치:
       pip install google-auth requests

사용법
------
    export GOOGLE_APPLICATION_CREDENTIALS=/경로/service-account.json
    python tools/google_indexing.py https://lagom-massage.pages.dev/notices
    # 또는 sitemap 전체:
    python tools/google_indexing.py --all
"""

import os
import sys
from pathlib import Path

try:
    import requests
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
except ImportError:
    sys.exit(
        "필수 라이브러리가 없습니다. 먼저 설치하세요:\n"
        "    pip install google-auth requests"
    )

ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPES = ["https://www.googleapis.com/auth/indexing"]
SITEMAP_PATH = Path(__file__).resolve().parent.parent / "sitemap.xml"


def get_session() -> AuthorizedSession:
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not Path(cred_path).exists():
        sys.exit(
            "서비스 계정 키를 찾을 수 없습니다.\n"
            "    export GOOGLE_APPLICATION_CREDENTIALS=/경로/service-account.json"
        )
    creds = service_account.Credentials.from_service_account_file(
        cred_path, scopes=SCOPES
    )
    return AuthorizedSession(creds)


def urls_from_sitemap() -> list[str]:
    import xml.etree.ElementTree as ET

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.parse(SITEMAP_PATH).getroot()
    return [el.text.strip() for el in root.findall(".//sm:loc", ns) if el.text]


def publish(session: AuthorizedSession, url: str, kind: str = "URL_UPDATED") -> None:
    resp = session.post(ENDPOINT, json={"url": url, "type": kind}, timeout=30)
    if resp.status_code == 200:
        print(f"  ✓ {url}")
    else:
        print(f"  ✗ {url}  →  HTTP {resp.status_code}  {resp.text[:200]}")


def main(argv: list[str]) -> None:
    args = argv[1:]
    if not args:
        sys.exit(
            "사용법:\n"
            "    python tools/google_indexing.py <url> [<url> ...]\n"
            "    python tools/google_indexing.py --all   # sitemap 전체"
        )
    urls = urls_from_sitemap() if args == ["--all"] else args
    # Indexing API 할당량: 기본 하루 200건. 대량은 분할/요청 증대 필요.
    if len(urls) > 200:
        print(f"[경고] {len(urls)}개 — Indexing API 기본 일일 할당량(200)을 초과합니다.")
    session = get_session()
    print(f"[정보] 통보 대상 URL: {len(urls)}개")
    for u in urls:
        publish(session, u)


if __name__ == "__main__":
    main(sys.argv)
