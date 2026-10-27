"""번역 도구 공용 모듈. bench 가상환경의 Python(babel 포함)으로 실행한다.

    ../../env/bin/python tools/<script>.py
"""

import csv
import io
import re
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po

APP_ROOT = Path(__file__).resolve().parent.parent
BENCH_ROOT = APP_ROOT.parent.parent
FRAPPE_ROOT = BENCH_ROOT / "apps" / "frappe"

UPSTREAM_POT = FRAPPE_ROOT / "frappe" / "locale" / "main.pot"
UPSTREAM_KO = FRAPPE_ROOT / "frappe" / "locale" / "ko.po"
KO_PO = APP_ROOT / "frappe_korean" / "locale" / "ko.po"
SNAPSHOT = APP_ROOT / "upstream" / "frappe_main.pot.snapshot"
GLOSSARY = APP_ROOT / "glossary_ko.csv"

LOCALE = "ko"


def load_catalog(path: Path, locale: str | None = None) -> Catalog:
	with open(path, "rb") as f:
		return read_po(f, locale=locale)


def save_catalog(path: Path, catalog: Catalog) -> None:
	"""frappe의 write_catalog와 같은 형식(width=None, 정렬)으로 쓰되 obsolete 항목은 남긴다."""
	path.parent.mkdir(parents=True, exist_ok=True)
	buf = io.BytesIO()
	write_po(buf, catalog, sort_output=True, ignore_obsolete=False, include_previous=True, width=None)
	path.write_bytes(buf.getvalue())


def key_of(message) -> tuple[str, str | None]:
	return (message.id, message.context)


def messages(catalog: Catalog):
	"""헤더를 제외한 항목."""
	return [m for m in catalog if m.id]


def msgstr(message) -> str:
	s = message.string
	if isinstance(s, (tuple, list)):
		return s[0] if s else ""
	return s or ""


def module_of(location_path: str) -> str:
	"""소스 위치를 리포트·배치 단위 모듈로 묶는다.

	frappe/core/doctype/user/user.json      -> core
	frappe/public/js/frappe/form/form.js    -> public/js/frappe/form
	"""
	parts = location_path.split("/")
	if parts and parts[0] == "frappe":
		parts = parts[1:]
	if parts[:3] == ["public", "js", "frappe"] and len(parts) > 4:
		return "/".join(parts[:4])
	if parts[:2] == ["public", "js"] and len(parts) > 3:
		return "/".join(parts[:3])
	return parts[0] if len(parts) > 1 else "(root)"


def primary_module(message) -> str:
	if not message.locations:
		return "(none)"
	return module_of(message.locations[0][0])


def load_glossary(path: Path = GLOSSARY) -> list[dict]:
	if not path.exists():
		return []
	with open(path, newline="", encoding="utf-8") as f:
		return [
			{k: (v or "").strip() for k, v in row.items()}
			for row in csv.DictReader(f)
			if (row.get("source") or "").strip() and not row["source"].lstrip().startswith("#")
		]


IGNORE_RE = re.compile(r"validate-ignore:\s*((?:A\d+\s*,\s*)*A\d+)")


def ignored_checks(message) -> set[str]:
	"""번역자 주석 `# validate-ignore: A12,A13 사유`로 검사를 예외 처리한다."""
	codes = set()
	for c in message.user_comments:
		if m := IGNORE_RE.search(c):
			codes |= set(re.findall(r"A\d+", m.group(1)))
	return codes


def drop_false_format_flag(message) -> None:
	"""`validate-ignore: A3`이 달린 항목은 babel이 잘못 붙인 python-format 플래그를 지운다.

	예: JSON 설명문 "Use % for any non empty value."의 `% f`를 포맷 지정자로 오인한다.
	플래그가 남으면 번역문에도 `% f`가 있어야 A3(msgfmt --check)를 통과한다.
	"""
	if "A3" in ignored_checks(message):
		message.flags.discard("python-format")
