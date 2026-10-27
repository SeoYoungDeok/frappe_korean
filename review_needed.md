# 검토 필요 항목 (review_needed)

> 기준: frappe v16.53.0 (`e8d41dd0061a32ee781caefe5d0b0d2bb7c15362`), main.pot 7,909건 (POT-Creation-Date 2026-10-18 09:35+0000)
> 상태: 2026-10-27 R1~R6 결정 완료, `glossary_ko.csv`에 반영.

## 결정 요약 (2026-10-27)
| # | 결정 |
|---|---|
| R1 | 제안대로. A·B 26종은 `English (한국어)` 형식, C 18종은 일반 번역 (용어집 `translate`/`keep`으로 이동, A6 대상 제외) |
| R2 | 제안대로. 대화상자·prompt·이메일 계정 비밀번호 `Submit` → `확인`, 웹 폼 → `제출` (해당 항목 `validate-ignore: A5 R2`) |
| R3 | **`Document Type` 영문 유지** (`keep`). 제안했던 `DocType` 대신 원문 표기를 보존 |
| R4 | 제안대로. 역할·기본 사용자 이름 영문 유지 |
| R5 | 제안대로. 일반 개념 DocType 이름은 번역 |
| R6 | 제안대로. `App` → `앱`, `Site` → `사이트`, `Single`·`Patch`는 맥락 판단 |


---

## R1. fieldtype과 일반 문자열이 같은 msgid (msgctxt 없음)

필드 유형 44종은 모두 msgctxt가 없어서, 같은 msgid가 일반 라벨로도 쓰이면 번역을 하나만 고를 수 있다 (가이드 2장 주의).

| 분류 | 필드 유형 | 다른 사용처 |
|---|---|---|
| **A. fieldtype 전용** (15) | Autocomplete, Attach Image, Attachment Gallery, Button, Column Break, Geolocation, HTML Editor, Long Text, Markdown Editor, Percent, Rating, Small Text, Tab Break, Table MultiSelect, Text Editor | 없음 |
| **B. 다른 곳도 fieldtype 선택지** (11) | Attach, Barcode, Check, Datetime, Dynamic Link, Float, Fold, Int, Read Only, Section Break, Text | Report Column/Filter의 Fieldtype 옵션, 인쇄 형식 빌더 컨트롤, Attach 컨트롤 버튼, `Dynamic Link` DocType 이름, DocField의 `read_only` 체크 라벨, Sidebar Item 유형 |
| **C. 일반 라벨이 주된 용도** (18) | Code, Color, Currency, Data, Date, Duration, Heading, HTML, Icon, Image, JSON, Link, Password, Phone, Select, Signature, Table, Time | 예) `Password`: 로그인 화면(`www/login.html`), 사용자 비밀번호 변경 대화상자 / `Link`: 알림 로그·워크스페이스 링크 / `Icon`: 13개 DocType의 icon 필드 / `Phone`: 연락처·주소·사용자 / `Date`: 커뮤니케이션 날짜 / `Select`: DocPerm의 select 권한 체크 |

**제안**: A·B는 `English (한국어)` 형식, C는 일반 번역(예: `Password` → `비밀번호`, `Link` → `링크`, `Date` → `날짜`)을 쓴다. C 항목은 fieldtype 드롭다운에서 한국어만 보이며, 해당 항목에 `# validate-ignore: A6 R1 결정`을 단다.
(C도 형식을 적용하면 로그인 화면에 `Password (비밀번호)`가 나온다.)

## R2. 대화상자 기본 버튼 `Submit`

| msgctxt | 위치 | 제안 |
|---|---|---|
| (없음) | DocPerm/DocShare `submit` 권한 체크, 알림 발송 시점 옵션 | 확정 |
| Button in list view actions menu | list_view.js | 확정 |
| Button in web form | web_form.html | 제출 (가이드 4-1 웹 폼 예외) |
| **Primary action in dialog** | ui/dialog.js (버튼 라벨을 따로 지정하지 않은 대화상자의 기본값) | **확인** 제안 — docstatus와 무관 |
| **Primary action of prompt dialog** | ui/messages.js (`frappe.prompt`) | **확인** 제안 |
| **Submit password for Email Account** | desk.js | **확인** 제안 |

`확정`을 쓰면 라벨 없이 만든 대화상자와 `frappe.prompt`의 버튼이 모두 "확정"으로 보인다. 확인/제출 항목은 `# validate-ignore: A5 R2`로 예외 처리한다.

`Submitted`(msgctxt 없음)는 indicator·필터와 함께 `web_form.html`에서도 쓰인다 → 노출이 많은 데스크 기준 `확정됨`.

## R3. `Document Type` (단독 msgid 1개, 포함 문자열 33건)

28곳에서 DocType을 고르는 Link 필드의 라벨이다 (Assignment Rule, Data Import, DocShare 등). 가이드가 DocType의 번역어로 `문서 유형`을 금지하고 있다.

- **제안**: `DocType` (화면에서 DocType 필드와 표기 통일)
- 대안: `문서 종류` (금지어는 피하지만 DocType과 다른 단어처럼 보임)

## R4. 역할·기본 사용자 이름

`System Manager`, `Workspace Manager`(25건), `Website Manager`, `Administrator`, `Guest`는 Role/User 레코드 이름이다. 역할 목록과 권한 관리자에는 레코드 이름이 영문으로 표시된다.

- **제안**: 영문 유지(`keep`). 예: `Workspace Manager 역할이 필요합니다.`
- 대안: `시스템 관리자` 등으로 번역 (메시지와 역할 목록의 표기가 달라짐)

## R5. Frappe DocType 이름 중 일반 개념

가이드 1-3의 예약어 목록에 없는 DocType 이름(Web Form, Kanban Board, Number Card, Auto Repeat, Assignment Rule, Data Import, Prepared Report, User Permission, Role Profile 등)은 **번역**하는 것으로 제안했다 (용어집 R5 구역). 개발자 개념(Custom Field, Client Script, Print Format 등)만 영문을 유지한다.

특히 확인할 번역어:

| 원문 | 제안 | 비고 |
|---|---|---|
| Prepared Report | 사전 생성 보고서 | 대안: 준비된 보고서 |
| Number Card | 숫자 카드 | |
| Assign / Assignment | 배정 | `Assign To` → 담당자 지정(가이드 확정)과 별개 |
| Depends On | 표시 조건 | DocField 속성 |
| Fetch From | 값 가져오기 | DocField 속성 |
| Desk / Dock | 데스크 / 독 | v16 UI 영역 이름 |
| Label | 라벨 | 국어원 표기는 '레이블' |
| Event | 일정 | 캘린더 Event |
| Closed / Open (상태값) | 종료됨 / 진행 중 | ToDo·Event·Communication |

## R6. 가이드 1-3 예약어 중 `context`로 내린 항목

`Site`, `App`, `Single`, `Patch`는 가이드에서 영문 유지 대상이지만 "명령/설정 맥락"에 한정된다. 검증 A4는 `keep` 용어를 모든 문장에서 강제하므로 `context`로 분류했다.
- v16 main.pot에서 `App`은 24건. 데스크톱 아이콘·OAuth 클라이언트·OTP 앱 등 일반 UI와 `App {0} is not installed` 같은 앱 설치 메시지 → 모두 `앱`이 자연스러워 `앱` 제안 (`OTP App` → `OTP 앱`)
- `Site` 4건, 모두 일반 의미 → `사이트`
- `Single`은 단독 msgid가 없고 문장 안 8건 → DocType 유형을 가리킬 때만 `Single` 유지
- `Fixture`, `Hook`, `Bench`는 v16 main.pot에 출현하지 않음 (용어집에서 제외)

## 예약어 후보 (작업 중 발견, 확정 시 keep 추가)

- `Typst` (v16 인쇄 렌더러, 26건), `DuckDB`, `QZ Tray`: 제품·기술명이라 keep으로 넣었다.

## 검증 예외 목록 (validate-ignore)

자동 검증(6-1)에서 의도적으로 예외 처리한 항목입니다. ko.po의 번역자 주석 `# validate-ignore:`에 같은 사유가 있습니다.

| 원문 | 번역 | 제외 검사 | 사유 |
|---|---|---|---|
| `ALL` | ALL | A10 | IMAP 동기화 키워드(값 그대로 표시) |
| `Change` ‹Coins› | 잔돈 | A10 | 맥락(Coins)상 '거스름돈' 뜻으로 Change(변경)와 다름 |
| `DELAY` | DELAY | A10 | SMTP DSN 키워드(값 그대로 표시) |
| `DELETE` | DELETE | A5,A10 | HTTP 메서드 옵션(Recorder) |
| `FAILURE` | FAILURE | A10 | SMTP DSN 키워드(값 그대로 표시) |
| `HERE` | HERE | A10 | 지도 서비스 제공자 이름(HERE) |
| `M` ‹Number system› | M | A10 | 숫자 단위 약어(Million)로 분(m)과 다른 뜻 |
| `NEVER` | NEVER | A10 | SMTP DSN 키워드(값 그대로 표시) |
| `No Data...` | 데이터 없음... | A15 | 문장이 아닌 빈 상태 라벨 |
| `No.` | 번호 | A10,A12 | 번호 약어(No.)로 No(아니요)와 다른 뜻 |
| `No.` ‹Title of the 'row number' column› | 번호 | A10,A12 | 행 번호 열 제목(No.)으로 No(아니요)와 다른 뜻 |
| `Note:` | 참고: | A5,A10 | 안내 머리말(Note:)로 Note DocType(메모)과 다른 뜻 |
| `OPTIONS` | OPTIONS | A5,A10 | HTTP 메서드 옵션(Recorder) |
| `Open` | 열림 | A10 | 연락처 상태값(열림)으로 열기 버튼과 다른 뜻 |
| `PATCH` | PATCH | A10 | HTTP 메서드 옵션(Recorder) |
| `POST` | POST | A10 | HTTP 메서드 옵션(Recorder) |
| `Phone No.` | 전화번호 | A12 | 원문 마침표는 약어(No.) 표시 |
| `Read` | 읽음 | A10 | 전송 상태값(읽음)으로 읽기 권한과 다른 뜻 |
| `SUCCESS` | SUCCESS | A5,A10 | SMTP DSN 키워드(값 그대로 표시) |
| `SUCCESS` | SUCCESS | A5,A10 | SMTP DSN 키워드(값 그대로 표시) |
| `Set` ‹Field value is set› | 설정됨 | A10 | 필터의 '값이 설정됨' 상태로 Set(설정) 버튼과 다른 뜻 |
| `Sr No.` | 순번 | A12 | 약어 마침표(Sr No.) |
| `Submit` ‹Button in web form› | 제출 | A5,A10 | R2 웹 폼 제출 버튼(가이드 4-1 웹 폼 예외) |
| `Submit` ‹Primary action in dialog› | 확인 | A5,A10 | R2 대화상자 기본 버튼(docstatus와 무관) |
| `Submit` ‹Primary action of prompt dialog› | 확인 | A5,A10 | R2 prompt 대화상자 기본 버튼(docstatus와 무관) |
| `Submit` ‹Submit password for Email Account› | 확인 | A5,A10 | R2 이메일 계정 비밀번호 입력 대화상자 버튼(docstatus와 무관) |
| `Use % for any non empty value.` | 비어 있지 않은 모든 값에는 %를 사용하세요. | A3 | JSON 설명문의 '% f'가 python-format으로 오추출됨(플래그 제거) |
| `default` | default | A5,A10 | RQ 큐 이름(값 그대로 표시) |
| `e.g.` | 예: | A12 | 약어 마침표(e.g.)를 한국어 '예:'로 표기 |
| `event` | 이벤트 | A5,A10 | 자동화 엔진 이벤트(캘린더 일정 아님) |
| `fieldname on the document e.g.` | 문서의 필드명, 예: | A12 | 약어 마침표(e.g.)를 한국어 '예:'로 표기 |
| `long` | long | A10 | RQ 큐 이름(값 그대로 표시) |
| `plain` | plain | A10 | PKCE code_challenge_method 값(plain) |
| `short` | short | A10 | RQ 큐 이름(값 그대로 표시) |
| `wkhtmltopdf 0.12.x (with patched qt).` | wkhtmltopdf 0.12.x (패치된 qt 포함). | A15 | 문장이 아닌 버전 표기(포함은 명사) |
| `Discard?` | 폐기할까요? | A5,A10 | 대화상자 제목이라 의문형으로 표기 (리뷰 반영) |
| `Failed to import virtual doctype {}, is controller file present?` | …있는지 확인하세요. | A12 | 원문 의문문을 확인 안내문으로 변경 (리뷰 반영) |
| `Please visit https://frappecloud.com/…#encryption-key for more information.` | …참고하세요: https://… | A12 | URL 뒤에 마침표를 붙이면 링크 인식이 깨짐 (리뷰 반영) |

## LLM 리뷰 결과 (5단계, 2026-10-27)

별도 세션 4개가 표본 1,782건(모듈별 최대 50건)을 채점했다. 기준은 정확성(a)·자연스러움(n)·간결성(c)·일관성(s)·맥락 적합성(x)이다.

| 표본 | 건수 | a | n | c | s | x | 2점 이하 | 제안 |
|---|---|---|---|---|---|---|---|---|
| 1 | 446 | 4.98 | 4.93 | 4.99 | 4.98 | 4.99 | 1 | 28 |
| 2 | 446 | 4.98 | 4.92 | 4.99 | 4.97 | 4.98 | 1 | 10 |
| 3 | 445 | 4.98 | 4.94 | 5.00 | 4.98 | 4.98 | 3 | 18 |
| 4 | 445 | 4.99 | 4.91 | 5.00 | 4.98 | 4.99 | 1 | 32 |

- 전체 평균은 4.97이고, 2점 이하는 6건이다(`Create Child Doctype`, `Failed to get method {0} with {1}`, `Child DocTypes are not allowed`, `Good afternoon, {0}`, `Less`, `Discard?`). 6건 모두 수정했다.
- 실패율 5% 초과 모듈은 `api`(1/3)와 `public/js/frappe/web_form`(1/14)이다. 두 모듈은 표본이 모듈 전체여서 이미 전수 검토가 끝난 상태다.
- 제안 73건 중 다음은 반영하지 않았다.
  - `To use Google Indexing…`: 기존 표현을 유지했다.
  - OTP 메일의 `System Administrator`: 예약어(Administrator)라 유지했다.
  - `Deleted!` → `삭제되었습니다!`: `Deleted`와의 일관성(A10) 때문에 유지했다.
  - 문구를 조정한 4건: `Move to…`, `Select the label after which…`, `{0} {1} returned {2}: {3}`, `This Currency is disabled…`.
- 리뷰에서 나온 일괄 정리
  - 용어집 keep 항목인 `child table`·`Child Doctype`이 들어간 12건을 `Child Table`·`Child DocType`으로 통일했다.
  - 용어집(Table → 테이블)과 다르게 `표`로 쓴 20건을 `테이블`로 통일했다.
  - 공용 msgid 3건의 번역을 바꿨다: `Day` 요일 → 일(캘린더 보기 버튼), `Read` 읽음 → 읽기(권한 이름), `Reply` 답글 → 답장(이메일).

## 미해결: 공용 msgid로 인한 맥락 충돌

- **`Like` → 좋아요**
  - 이 msgid는 Comment 유형, 목록의 좋아요 필터, 필터 연산자(`filter.js`의 like)가 함께 쓴다.
  - 그래서 필터 조건 목록에 `좋아요`로 표시된다. 짝인 `Not Like`는 `패턴 불일치`다.
  - msgctxt가 없어 오버라이드 앱에서는 둘을 나눌 수 없다.
  - 사용 빈도가 높은 좋아요 쪽을 유지했다.
  - 근본 해결책은 업스트림에 msgctxt를 추가해 달라는 PR이다.
