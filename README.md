### Frappe Korean

Frappe Framework v16 한국어(ko) 오버라이드 번역 앱입니다. frappe 저장소를 수정하지 않고, 이 앱의 `frappe_korean/locale/ko.po`가 frappe 기본 번역을 덮어씁니다.

- 기준 버전: frappe v16.53.0 (commit `e8d41dd0061a32ee781caefe5d0b0d2bb7c15362`)
- 번역: `main.pot` 7,909건 전부

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/SeoYoungDeok/frappe_korean --branch version-16
bench --site $SITE install-app frappe_korean
bench compile-po-to-mo --app frappe_korean --locale ko
bench --site $SITE clear-cache
```

사용자 또는 System Settings의 언어를 `ko`로 설정하면 적용됩니다.

### 구성

| 경로 | 내용 |
|---|---|
| `frappe_korean/locale/ko.po` | 번역 파일 |
| `glossary_ko.csv` | 용어집 (translate / keep / fieldtype) |
| `review_needed.md` | 번역 결정 사항, 검증 예외 목록, 리뷰 결과 |
| `docs/TRANSLATION_GUIDE_KO.md` | 번역 절차와 규칙 |
| `tools/` | 업스트림 동기화(`sync_from_upstream.py`), 검증(`validate_ko.py`), 진행 현황(`report.py`), 일괄 반영(`apply_batch.py`) |
| `upstream/frappe_main.pot.snapshot` | 마지막으로 동기화한 frappe `main.pot` (변경분 비교 기준) |

도구는 bench 가상환경의 Python으로 실행합니다.

```bash
cd apps/frappe_korean
../../env/bin/python tools/validate_ko.py
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/frappe_korean
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

MIT. 원문 문자열과 `upstream/frappe_main.pot.snapshot`은 Frappe Framework(MIT, © Frappe Technologies Pvt. Ltd.)에서 가져왔습니다. 자세한 내용은 [license.txt](license.txt)를 참고하세요.
