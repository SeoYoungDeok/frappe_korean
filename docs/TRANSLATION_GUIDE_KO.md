# Frappe 한국어 번역 가이드 (Claude Code용)

> 이 문서는 **Frappe Framework v16**의 한국어 번역을 Claude Code로 진행할 때 따라야 하는 **구조·번역 기준·검증 기준**입니다.
> Claude Code는 번역 작업 전에 이 문서 전체를 읽고, 모든 번역에 이 기준을 적용해야 합니다.

## 확정 사항 요약
| 항목 | 결정 |
|---|---|
| 범위 | Frappe Framework만 (ERPNext, HRMS 제외) |
| 버전 | Frappe v16 최신 |
| 배포 | 공식 기여 아님. 별도 앱 `frappe_korean`이 frappe 번역을 덮어씀 |
| frappe 원본 | **frappe 앱의 파일은 절대 수정하지 않음** (업그레이드 시 merge conflict 방지) |
| docstatus 용어 | Submit = 확정, Amend = 수정본 |
| 문체 | 메시지는 합니다체 |
| 필드 유형 표기 | `Link (링크)` — 괄호 앞 한 칸 띄움 |

---

## 0. 구조: `frappe_korean` 오버라이드 앱

### 0-1. 동작 원리 (v16 `frappe/translate.py` 기준)
- `get_translations_from_apps()`는 **설치된 앱 순서대로** 각 앱의 번역(CSV → MO)을 읽어 dict에 `update()` 한다. 따라서 **나중에 설치된 앱의 번역이 앞선 앱을 덮어쓴다.** frappe는 항상 첫 번째 앱이므로 `frappe_korean`의 번역이 이긴다.
- 그 위에 사용자 번역(`Translation` DocType)이 마지막으로 덮어쓴다. 우선순위는 다음과 같다.
  ```
  frappe ko.po  <  frappe_korean ko.po  <  Translation DocType(DB)
  ```
- 번역 키는 `msgid` 또는 `msgid:msgctxt`이다. 따라서 **frappe_korean의 `msgid`와 `msgctxt`는 frappe의 `main.pot`과 글자 하나까지 같아야** 덮어쓰기가 된다.
- 병합 결과는 Redis 캐시(`merged_translations`)에 저장된다. 번역을 바꾼 뒤에는 반드시 캐시를 비운다.

### 0-2. 앱 구조
```
apps/frappe_korean/
├── frappe_korean/
│   ├── hooks.py
│   └── locale/
│       └── ko.po              ← 유일한 번역 산출물
├── tools/                     ← 번역 작업 도구 (Claude Code가 작성)
│   ├── sync_from_upstream.py  ← frappe main.pot → ko.po 동기화
│   ├── validate_ko.py         ← 자동 검증
│   └── report.py              ← 진행률·diff 리포트
├── upstream/
│   └── frappe_main.pot.snapshot  ← 마지막으로 동기화한 frappe 원문 스냅샷
├── glossary_ko.csv
├── review_needed.md
└── TRANSLATION_GUIDE_KO.md    ← 이 문서
```

설치:
```bash
bench new-app frappe_korean
bench --site <site> install-app frappe_korean
```

### 0-3. 반드시 지킬 규칙
1. **`apps/frappe/` 아래 파일은 읽기만 한다.** `ko.po`, `main.pot`, 소스 코드 모두 수정 금지.
2. **`bench update-po-files --app frappe_korean`과 `bench generate-pot-file --app frappe_korean`을 실행하지 않는다.** 이 명령들은 frappe_korean 자체 소스에서만 원문을 추출한다. 실행하면 frappe 원문이 전부 obsolete(`#~`)로 밀려 번역이 사라진다. 원문 동기화는 `tools/sync_from_upstream.py`로만 한다.
3. `ko.po`의 원문 출처는 `apps/frappe/frappe/locale/main.pot`이다. 각 항목의 `msgid`, `msgctxt`, `#:` 소스 위치 주석을 그대로 복사한다.
4. **빈 `msgstr`은 MO 파일에 들어가지 않는다.** 그러면 frappe의 기존 한국어(기계 번역투)가 그대로 나온다. 영문을 유지해야 하는 항목(예: `DocType`)도 반드시 `msgstr "DocType"`처럼 **명시적으로 채운다.** 그래야 frappe의 "문서 유형" 같은 기존 번역을 덮어쓴다.
5. CSV 형식(`translations/ko.csv`)은 쓰지 않는다. PO만 사용한다.

### 0-4. 반영 명령
```bash
bench compile-po-to-mo --app frappe_korean --locale ko
bench build --app frappe_korean   # 필요 시
bench --site <site> clear-cache
```
- 반영 후 브라우저 강력 새로고침. 부트 번역은 HTTP 캐시가 걸려 있다.
- `Translation` DocType에 같은 원문의 레코드가 남아 있으면 그것이 우선한다. 화면에 반영이 안 되면 먼저 이 레코드를 확인한다.

### 0-5. frappe 업그레이드 시 절차
1. `bench update`로 frappe 업그레이드 (frappe_korean은 frappe 파일을 건드리지 않았으므로 conflict 없음)
2. `tools/sync_from_upstream.py` 실행:
   - 새 `main.pot`과 `upstream/frappe_main.pot.snapshot`을 비교
   - **신규 원문**: `ko.po`에 빈 항목으로 추가
   - **변경된 원문**(같은 위치에서 문구 변경): 기존 번역을 `#, fuzzy`로 표시하고 재검토 대상에 올림
   - **삭제된 원문**: `ko.po`에서 obsolete(`#~`) 처리. 바로 삭제하지 않고 다음 업그레이드 때 제거
   - 소스 위치(`#:`) 주석 갱신
3. 신규 항목과 fuzzy 항목만 번역 → 검증 → 스냅샷 갱신 → 커밋

---

## 1. 번역하지 않는 단어 (영문 유지)

> 영문 유지 항목도 `msgstr`을 비우지 말고 영문 그대로 채운다 (0-3의 4번 규칙).

### 1-1. 기초 영단어로 그대로 써도 자연스러운 단어
한국 IT 사용자가 이미 영어 그대로 읽는 단어.
- 예: `ID`, `URL`, `API`, `PDF`, `CSV`, `Excel`, `OK`, `PIN`, `QR`, `SMS`, `OTP`, `JSON`, `HTML`, `CSS`, `SQL`
- 단, 문장 속에서는 한글이 더 자연스러우면 번역한다. (`Send Email` → `이메일 보내기`)

### 1-2. MES/ERP 업계 통용 용어
번역하면 오히려 실무자가 못 알아보는 단어. Frappe 코어에는 드물지만, 나올 경우 영문 유지.
- 예: `ERP`, `MES`, `KPI`, `SKU`, `UOM`, `Lot`, `Batch`, `FIFO`, `CRM`, `SLA`, `SSO`, `LDAP`, `OAuth`, `2FA`
- 판단 기준: "현장 담당자가 영어 그대로 말하는가?" → 그렇다면 영문 유지.

### 1-3. 프레임워크 예약어 (Frappe 고유 개념)

| 영문 유지 | 비고 |
|---|---|
| `DocType` | 절대 번역 금지 (문서 유형 X) |
| `Child Table`, `Child DocType` | |
| `Single` (DocType 유형) | `is_single` 맥락에서만 |
| `Submittable`, `Is Submittable` | |
| `Naming Series` | |
| `Custom Field`, `Property Setter` | |
| `Client Script`, `Server Script` | |
| `Print Format`, `Letter Head` | |
| `Workspace` | |
| `Webhook`, `Fixture`, `Patch`, `Hook` | |
| `Bench`, `Site`, `App`, `Module Def` | 명령/설정 맥락 |
| `DocField`, `DocPerm`, `Custom DocPerm` | 내부 DocType |
| `Report Builder`, `Query Report`, `Script Report` | |
| `Jinja`, `Socket.IO`, `Redis`, `MariaDB`, `PostgreSQL` 등 기술명 | |
| `docstatus`, `name`, `owner`, `modified`, `idx` 등 시스템 필드명 | 코드 식별자일 때 |

> 같은 단어라도 **일반 명사로 쓰인 경우**는 번역한다.
> 예: 예약어 `Single` ↔ 일반 의미 "단일" / bench의 `Site` ↔ 일반 의미 "사이트"
> 이 목록은 시작점이다. Claude Code는 작업 중 발견한 후보를 `review_needed.md`에 제안하고, 확정되면 `glossary_ko.csv`에 `keep`으로 추가한다.

### 1-4. 절대 손대지 않는 요소
- 플레이스홀더: `{0}`, `{1}`, `{name}`, `%s`, `%(doctype)s`
- HTML 태그와 속성: `<b>`, `<a href="...">`, `<br>`, `&nbsp;`
- 코드/식별자: `frappe.get_doc`, `fieldname`, 백틱 안 내용, 파일 경로, URL
- 키보드 단축키 표기: `Ctrl+S`, `Shift`
- 아이콘 이름, CSS 클래스

---

## 2. DocType 필드 유형 표기: `English (한국어)`

필드 유형은 `영어 (한국어)` 형식으로 번역한다. **괄호 앞 한 칸 띄움.**

> v16의 실제 필드 유형 목록은 `apps/frappe/frappe/core/doctype/docfield/docfield.json`의 `fieldtype` options에서 추출해 대조한다. 아래 표에 없는 유형이 있으면 같은 형식으로 추가하고 `review_needed.md`에 기록한다.

| 필드 유형 | 번역 |
|---|---|
| Data | Data (데이터) |
| Link | Link (링크) |
| Dynamic Link | Dynamic Link (동적 링크) |
| Select | Select (선택) |
| Check | Check (체크) |
| Int | Int (정수) |
| Float | Float (실수) |
| Currency | Currency (통화) |
| Percent | Percent (백분율) |
| Date | Date (날짜) |
| Datetime | Datetime (날짜시간) |
| Time | Time (시간) |
| Duration | Duration (기간) |
| Text | Text (텍스트) |
| Small Text | Small Text (짧은 텍스트) |
| Long Text | Long Text (긴 텍스트) |
| Text Editor | Text Editor (텍스트 편집기) |
| HTML Editor | HTML Editor (HTML 편집기) |
| Markdown Editor | Markdown Editor (마크다운 편집기) |
| Code | Code (코드) |
| JSON | JSON |
| Table | Table (테이블) |
| Table MultiSelect | Table MultiSelect (테이블 다중 선택) |
| Attach | Attach (첨부) |
| Attach Image | Attach Image (이미지 첨부) |
| Image | Image (이미지) |
| Signature | Signature (서명) |
| Color | Color (색상) |
| Barcode | Barcode (바코드) |
| Geolocation | Geolocation (위치) |
| Rating | Rating (평점) |
| Password | Password (비밀번호) |
| Phone | Phone (전화번호) |
| Autocomplete | Autocomplete (자동 완성) |
| Icon | Icon (아이콘) |
| Button | Button (버튼) |
| Read Only | Read Only (읽기 전용) |
| HTML | HTML |
| Heading | Heading (제목) |
| Section Break | Section Break (섹션 구분) |
| Column Break | Column Break (열 구분) |
| Tab Break | Tab Break (탭 구분) |
| Fold | Fold (접기) |

**적용 범위**: 이 형식은 "필드 유형 선택지(fieldtype)"로 쓰일 때만 적용한다.
- 일반 문장 속 `date` → `날짜`, 일반 버튼 `Attach` → `첨부`로 번역한다.
- 판별은 `msgctxt`와 소스 위치(`docfield`, `customize_form_field`, `custom_field`, 폼 빌더 등의 fieldtype 옵션)로 한다.
- **주의**: fieldtype 문자열과 일반 문자열이 같은 `msgid`이면서 `msgctxt`가 없으면 둘을 구분할 수 없다. 이런 경우 무리하게 하나로 정하지 말고 `review_needed.md`에 사용 위치 목록과 함께 기록한다. 그 뒤 어느 쪽 노출이 더 중요한지 사람이 결정한다.

---

## 3. 문체·어조 기준

### 3-1. UI 요소별 문체
| UI 요소 | 문체 | 예시 |
|---|---|---|
| 버튼·메뉴·액션 | 명사형 또는 "~하기" (짧게) | `Save` → `저장`, `Add Row` → `행 추가`, `Send Email` → `이메일 보내기` |
| 필드 라벨·열 제목 | 명사 | `Last Login` → `마지막 로그인` |
| 페이지/섹션 제목 | 명사구 | `Account Settings` → `계정 설정` |
| 안내·성공·에러 메시지 | **합니다체** | `저장되었습니다.`, `권한이 없습니다.` |
| 확인 질문 | "~하시겠습니까?" | `삭제하시겠습니까?` |
| 도움말·설명(description) | 합니다체, 간결하게 | |
| 입력 힌트(placeholder) | 명사형/짧은 구 | `Search...` → `검색...` |

### 3-2. 기계 번역투 금지 패턴
| 금지 | 개선 |
|---|---|
| 당신의 / 귀하의 | 생략 (`Your account` → `계정`) |
| ~을 가지고 있습니다 | ~이(가) 있습니다 |
| ~에 대한 (남용) | 구조 바꾸기 (`Settings for Email` → `이메일 설정`) |
| ~되어졌습니다, ~되어집니다 (이중 피동) | ~되었습니다 |
| ~하는 것이 가능합니다 | ~할 수 있습니다 |
| 복수형 "~들" 기계적 추가 | 대부분 생략 (`Users` → `사용자`) |
| 영어 어순 그대로 | 한국어 어순으로 재배열 |
| `Please ~` → `제발/부디` | `~하세요`, `~해 주세요` 또는 생략 |
| 불필요한 "그것", "이것" | 생략 |
| 해요체·반말 혼용 | 합니다체로 통일 |

### 3-3. 플레이스홀더와 조사
`{0}` 뒤 조사는 값에 따라 받침이 달라진다.
1. **1순위**: 조사가 필요 없도록 문장을 재구성
   - `{0} has been deleted` → `{0} 항목이 삭제되었습니다` 또는 `삭제되었습니다: {0}`
2. **2순위**: 뒤에 명사를 붙여 조사 고정 — `{0}이(가)` → `{0} 문서가`
3. **3순위**: 병기 조사 `을(를)`, `이(가)`, `은(는)`, `와(과)`, `(으)로`
- 플레이스홀더 순서는 한국어 어순에 맞게 바꿔도 된다. 단, 종류와 개수는 원문과 같아야 한다.

### 3-4. 표기 규칙
- 맞춤법·띄어쓰기는 국립국어원 기준.
- 외래어는 업계 관용 표기를 우선하고, 한 번 정하면 전체 통일 (예: `워크플로우`, `대시보드`, `템플릿`). 결정한 표기는 `glossary_ko.csv`에 등록.
- 문장 부호: 원문 끝에 마침표가 있으면 유지, 없으면 추가하지 않는다. `...`은 유지.
- 숫자 단위: `{0} items` → `{0}개 항목`, `{0} days` → `{0}일`.
- 원문 앞뒤 공백과 줄바꿈(`\n`)은 그대로 보존.
- 길이: 버튼/라벨은 원문 글자 수의 약 1.5배 이내 권장.

---

## 4. 용어집 (Glossary)

번역 시작 전에 `glossary_ko.csv`(`source,target,type,note`)를 만들고, 모든 번역은 용어집을 우선 적용한다.
`type`: `keep`(영문 유지) / `translate` / `fieldtype` / `context`(맥락 의존)

### 4-1. 문서 상태 (docstatus) — 확정
| 원문 | 번역 | 비고 |
|---|---|---|
| Draft | 임시저장 | docstatus 0 |
| Submit | 확정 | 버튼 |
| Submitted | 확정됨 | 상태 표시 |
| (문장 속 submit) | 확정하다 / 확정된 | 예: `Cannot edit submitted document` → `확정된 문서는 수정할 수 없습니다` |
| Cancel | 취소 | docstatus 2 액션, 대화상자 취소 버튼과 같은 단어 |
| Cancelled | 취소됨 | |
| Amend | 수정본 작성 | 버튼 |
| Amended From | 원본 문서 | 수정본이 참조하는 원본 필드 |
| Amendment | 수정본 | |
| Discard | 폐기 | |
| Approve / Reject | 승인 / 반려 | 워크플로우 |

> "submit"이 docstatus와 무관한 일반 의미(웹 폼 제출, 신청)로 쓰이면 `제출`로 번역한다. 소스 위치로 판별한다. 예: `www/`, `website/`, Web Form 관련 → 제출 / DocType 폼 → 확정.

### 4-2. 공통 UI 용어 기본안
| 원문 | 번역 | 원문 | 번역 |
|---|---|---|---|
| Save | 저장 | Delete | 삭제 |
| New | 새로 만들기 | Edit | 편집 |
| Duplicate | 복제 | Rename | 이름 변경 |
| Refresh / Reload | 새로고침 | Filter | 필터 |
| Sort | 정렬 | Group By | 그룹 기준 |
| Assign To | 담당자 지정 | Assigned To | 담당자 |
| Owner | 작성자 | Modified | 수정일 |
| Created On | 생성일 | Last Updated | 최근 수정 |
| Settings | 설정 | Customize | 사용자 정의 |
| Customize Form | 양식 사용자 정의 | Permission | 권한 |
| Role | 역할 | User | 사용자 |
| Report | 보고서 | Dashboard | 대시보드 |
| List View | 목록 보기 | Kanban | 칸반 |
| Mandatory | 필수 | Default | 기본값 |
| Enabled / Disabled | 사용 / 사용 안 함 | Attachment | 첨부 파일 |
| Comment | 댓글 | Timeline | 타임라인 |
| Workflow | 워크플로우 | Notification | 알림 |
| Module | 모듈 | Import / Export | 가져오기 / 내보내기 |

---

## 5. 맥락 판단 규칙

1. **동일 원문 다른 의미**: `Order`(순서/주문), `Post`(게시/전기), `Close`(닫기/마감), `Single`(예약어/단일), `Submit`(확정/제출). `msgctxt`와 `#:` 소스 위치로 구분한다.
2. **동사 vs 명사**: `Print`, `Export`, `Import` — 버튼이면 명사형 액션(`인쇄`), 섹션 제목이면 명사.
3. **Title Case 라벨**은 문장이 아니므로 명사구로 번역.
4. **의미가 모호하면** `#:` 주석의 소스 파일을 실제로 열어 어떤 UI 요소인지 확인한 뒤 번역한다.
5. 같은 `msgid`·`msgctxt`는 앱 전체에서 번역이 하나뿐이다. 여러 위치에서 다르게 읽히는 경우 가장 노출이 많은 위치 기준으로 번역하고 `review_needed.md`에 기록한다.

---

## 6. 검증 기준

### 6-1. 자동 검증 (`tools/validate_ko.py`, 100% 통과 필수)

| # | 검사 항목 | 실패 조건 | 등급 |
|---|---|---|---|
| A0 | 원문 정합성 | `ko.po`의 `msgid`+`msgctxt`가 frappe `main.pot`에 없음 (오타, 오버라이드 불가) | 치명 |
| A1 | 플레이스홀더 일치 | `{n}`, `{name}`, `%s`, `%(x)s`의 종류·개수가 원문과 다름 | 치명 |
| A2 | HTML 태그 일치 | 태그 종류·개수·중첩이 원문과 다름 | 치명 |
| A3 | PO 문법 | `msgfmt --check` 실패 | 치명 |
| A4 | 예약어 보존 | `keep` 용어가 원문에 있는데 번역문에서 사라지거나 번역됨 | 치명 |
| A5 | 용어집 준수 | `translate` 용어가 지정 번역어와 다름 (특히 Submit→확정, Amend→수정본) | 주요 |
| A6 | 필드 유형 형식 | fieldtype 맥락인데 `English (한국어)` 형식(괄호 앞 공백 1칸)이 아님 | 주요 |
| A7 | 미번역 | `msgstr`가 비어 있음 (영문 유지 항목도 채워야 함) | 주요 |
| A8 | 번역투 패턴 | 정규식 매칭: `당신`, `귀하`, `되어졌`, `되어집`, `하는 것이 가능`, `을 가지고 있`, `를 가지고 있` | 주요 |
| A9 | 앞뒤 공백·줄바꿈 | 원문과 다름 | 주요 |
| A10 | 일관성 | 같은 용어가 문자열마다 다르게 번역됨 (용어집 외 고빈도 단어 포함) | 주요 |
| A11 | frappe 파일 무수정 | `git -C apps/frappe status --porcelain`에 변경 사항 있음 | 치명 |
| A12 | 끝 문장 부호 | 원문의 마침표/콜론/물음표 유무와 불일치 | 경미 |
| A13 | 길이 비율 | 원문 20자 이하인데 번역이 원문의 2배 초과 | 경미 |
| A14 | 조사 오류 위험 | 플레이스홀더 바로 뒤에 병기 없는 받침 의존 조사 (`을`,`를`,`이`,`가`,`은`,`는`,`와`,`과`) | 경미 |
| A15 | 문체 | 메시지 문장이 합니다체가 아님 (`~해요`, `~한다.`, `~함.` 종결) | 경미 |

출력: 항목별 실패 목록(`msgid`, 현재 번역, 사유)과 요약 통계. 치명·주요가 1건이라도 있으면 종료 코드 1.

### 6-2. LLM 리뷰 (샘플링 검수)
자동 검증을 통과하면, 번역한 세션과 **다른 세션(서브에이전트)**이 원문/번역/소스 위치를 보고 채점한다. 각 1~5점.

| 기준 | 5점 기준 |
|---|---|
| 정확성 | 의미 누락·추가·왜곡 없음 |
| 자연스러움 | 한국 SaaS/ERP 제품 UI에서 실제로 볼 법한 문장 |
| 간결성 | 같은 의미를 더 짧게 쓸 수 없음 |
| 일관성 | 용어집·문체 규칙과 일치 |
| 맥락 적합성 | 버튼/라벨/메시지 위치에 맞는 형태 |

- 통과 기준: 모든 항목 평균 4.0 이상, 2점 이하 항목 없음.
- 샘플링: 소스 디렉터리(모듈)마다 최소 50건 또는 10% 중 큰 값. 실패율 5% 초과 시 해당 모듈 전체 재검토.
- 리뷰어는 수정안을 직접 반영하지 않고 제안만 한다. 반영은 원 작업 세션이 하고 다시 6-1을 돌린다.

### 6-3. 화면 검증
1. 0-4의 반영 명령 실행 후 사용자 언어를 한국어로 설정
2. 화면 체크리스트:
   - 데스크/워크스페이스, 사이드바, 검색 바(Awesome Bar)
   - 목록 보기, 필터·정렬·그룹 기준
   - 문서 폼: 저장 → **확정** → 취소 → **수정본 작성** 흐름 전체
   - DocType 편집 화면과 폼 빌더 (**필드 유형 드롭다운이 `Link (링크)` 형식인지**)
   - 양식 사용자 정의, Custom Field
   - 보고서 빌더, 인쇄 미리보기, 이메일 작성
   - 알림/토스트, 권한 오류, 필수값 누락 메시지
   - 사용자·역할·권한 관리자, 시스템 설정
   - 로그인 페이지(게스트 화면)
3. 확인 사항: 텍스트 잘림, 버튼 폭 넘침, 플레이스홀더 값이 들어간 실제 문장의 조사, 미번역 잔존, **frappe 기존 번역이 덮어써지지 않고 남아 있는 곳**

### 6-4. 완료 정의 (Definition of Done)
- [ ] 자동 검증 치명·주요 0건, 경미 항목은 사유 기록
- [ ] LLM 리뷰 통과 기준 충족
- [ ] 화면 체크리스트 확인
- [ ] `apps/frappe` 변경 없음 (A11)
- [ ] `glossary_ko.csv`, `review_needed.md`, `upstream/frappe_main.pot.snapshot` 갱신

---

## 7. Claude Code 작업 절차

1. **준비**
   - `apps/frappe/frappe/locale/main.pot`, `ko.po` 위치와 frappe 버전·커밋 해시 확인
   - 통계 출력: 전체 원문 수, frappe ko.po의 번역 수/미번역 수
2. **도구 작성**: `sync_from_upstream.py` → `validate_ko.py` → `report.py` 순서. 번역보다 먼저 만든다.
3. **초기 동기화**: `main.pot` 전체를 `frappe_korean/locale/ko.po`로 가져온다. `msgstr`은 비운 상태로 시작한다. frappe의 기존 ko.po 번역은 **참고용으로만** 보고 그대로 복사하지 않는다.
4. **용어 추출**: 고빈도 용어와 fieldtype 목록을 추출해 `glossary_ko.csv` 초안 작성 → **사람 확인 후 확정**
5. **배치 번역**: 소스 디렉터리(모듈) 단위로 200~300건씩. 우선순위:
   1. `core`, `desk`, `public/js/frappe/form`, `public/js/frappe/list` (가장 많이 노출)
   2. `custom`, `printing`, `email`, `workflow`
   3. 나머지
   - 매 배치 후 6-1 실행, 실패 건 즉시 수정
6. **리뷰**: 6-2를 별도 세션으로 수행
7. **반영**: 0-4 실행 후 6-3 화면 검증
8. **커밋**: frappe_korean 저장소에만 커밋. 커밋 메시지에 대상 frappe 커밋 해시 기록
9. **보고**: 모듈별 번역 수, 검증 결과, 미해결 항목 요약
