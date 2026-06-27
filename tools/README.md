# 색인(Indexing) 도구 모음

라곰 출장마사지(`https://lagom-massage.pages.dev`) 사이트의 **검색엔진 색인을 가장 빠르게** 만들기 위한 도구와 절차입니다.

---

## 📁 구성 파일

| 파일 | 역할 |
|---|---|
| `/b918cb81b5f890cf38dc4fd1779cfefa.txt` | **IndexNow 키 파일** (웹 루트에 위치 — 절대 삭제·이동 금지) |
| `tools/indexnow.py` | Bing·Naver 등에 **즉시 색인 통보** (표준 라이브러리만, 설치 불필요) |
| `tools/google_indexing.py` | Google Indexing API 통보 (보조 수단, 서비스 계정 필요) |

---

## 1. IndexNow — Bing·Naver 즉시 색인 (핵심)

IndexNow는 URL이 새로 생기거나 바뀌었을 때 **검색엔진에 즉시 알려주는** 프로토콜입니다.
**Bing, Naver, Seznam, Yandex** 등이 참여합니다. (구글은 미참여 → 아래 3번 참고)

### 키 파일
- 위치: `https://lagom-massage.pages.dev/b918cb81b5f890cf38dc4fd1779cfefa.txt`
- 내용: `b918cb81b5f890cf38dc4fd1779cfefa`
- 배포(Cloudflare Pages) 후 위 URL이 키 문자열을 그대로 보여주면 정상입니다.

### ① 첫 일괄 통보 (전체 URL 한 번에)
```bash
python tools/indexnow.py
```
→ `sitemap.xml`의 **전체 2,116개 URL**을 Bing·Naver에 즉시 통보합니다.

### ② 글 올릴 때마다 (변경분만)
```bash
python tools/indexnow.py https://lagom-massage.pages.dev/notices
# 여러 개 가능
python tools/indexnow.py https://.../a https://.../b
# 목록 파일에서
python tools/indexnow.py --from-file changed_urls.txt
```

> 의존성 없음 — 파이썬만 있으면 `python tools/indexnow.py` 바로 실행됩니다.

---

## 2. sitemap / robots — 기본 색인 토대

이미 설정 완료되어 있습니다:
- `robots.txt` → 모든 봇 허용 + `Sitemap:` 명시 + `Host:` 명시
- `sitemap.xml` → 2,116개 URL (lastmod·changefreq·priority 포함)
- `rss.xml` → 공지 피드

### ⚠️ sitemap "ping"은 더 이상 작동하지 않습니다
구글(2023.6)과 빙 모두 `/ping?sitemap=` **핑 엔드포인트를 폐지**했습니다.
따라서 sitemap은 **검색엔진 콘솔에 직접 제출**하는 것이 유일·정석 경로입니다(아래 4번).
즉시성은 **IndexNow(1번)** 가 담당합니다.

---

## 3. Google Indexing API (선택·보조)

구글은 IndexNow에 참여하지 않습니다. 일반 페이지의 가장 확실한 구글 색인 경로는
**Search Console + sitemap 제출**(4번)입니다. Indexing API는 보조 수단입니다.

```bash
pip install google-auth requests
export GOOGLE_APPLICATION_CREDENTIALS=/경로/service-account.json
python tools/google_indexing.py https://lagom-massage.pages.dev/notices
python tools/google_indexing.py --all     # sitemap 전체 (일일 할당량 200 주의)
```
사전 준비: Cloud에서 Indexing API 활성화 → 서비스 계정 JSON 발급 → Search Console에
그 서비스 계정 이메일을 **소유자**로 추가. (자세한 절차는 `google_indexing.py` 상단 주석)

---

## 4. 검색엔진 콘솔 등록 (한 번만, 가장 중요)

가장 빠르고 확실한 색인의 기반입니다. 배포 후 1회 진행하세요.

**구글 Search Console** — https://search.google.com/search-console
1. 속성 추가 → URL 접두어 → `https://lagom-massage.pages.dev/`
2. 소유확인: 이미 메인페이지에 `google-site-verification` 메타(`tLvzDmZ…`)가 있어 자동 확인됩니다.
3. 좌측 **Sitemaps** → `sitemap.xml` 제출
4. 핵심 페이지는 **URL 검사 → 색인 요청**으로 개별 가속

**네이버 서치어드바이저** — https://searchadvisor.naver.com
1. 사이트 등록 → `https://lagom-massage.pages.dev/`
2. 소유확인: 메인페이지의 `naver-site-verification`(`be2a661…`) 메타 + 루트의
   `naverbe2a66160a09c334890f73dd4f04a175d391a791.html` 로 자동 확인
3. **요청 → 사이트맵 제출** → `sitemap.xml`
4. **요청 → RSS 제출** → `rss.xml`
5. 네이버도 IndexNow를 지원하므로 `indexnow.py` 통보가 즉시 반영됩니다

**Bing Webmaster Tools** — https://www.bing.com/webmasters
- Search Console에서 가져오기(Import) 가능. sitemap 제출 + IndexNow 자동 인식

---

## 권장 운영 흐름

1. (최초) Cloudflare 배포 → 콘솔 3곳 등록 + sitemap/rss 제출
2. (최초) `python tools/indexnow.py` — 전체 URL 일괄 통보
3. (글 올릴 때마다) `python tools/indexnow.py <새 URL>` — 즉시 통보
4. (구글 가속이 필요할 때) Search Console URL 검사 → 색인 요청
