#!/usr/bin/env python
"""frappe_korean ko.po 자동 검증 (가이드 6-1, A0~A15).

치명·주요 실패가 1건이라도 있으면 종료 코드 1.
항목별 예외는 번역자 주석으로 남긴다:  # validate-ignore: A12,A13 사유

사용법:
    ../../env/bin/python tools/validate_ko.py
    ../../env/bin/python tools/validate_ko.py --module core --skip A7     # 배치 검증
    ../../env/bin/python tools/validate_ko.py --only A1,A2 --limit 0      # 전체 목록
    ../../env/bin/python tools/validate_ko.py --json /tmp/result.json
"""

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from _common import (
	FRAPPE_ROOT,
	KO_PO,
	LOCALE,
	UPSTREAM_POT,
	ignored_checks,
	key_of,
	load_catalog,
	load_glossary,
	messages,
	module_of,
	msgstr,
)

CRITICAL, MAJOR, MINOR = "치명", "주요", "경미"
CHECKS = {
	"A0": ("원문 정합성", CRITICAL),
	"A1": ("플레이스홀더 일치", CRITICAL),
	"A2": ("HTML 태그 일치", CRITICAL),
	"A3": ("PO 문법", CRITICAL),
	"A4": ("예약어 보존", CRITICAL),
	"A5": ("용어집 준수", MAJOR),
	"A6": ("필드 유형 형식", MAJOR),
	"A7": ("미번역", MAJOR),
	"A8": ("번역투 패턴", MAJOR),
	"A9": ("앞뒤 공백·줄바꿈", MAJOR),
	"A10": ("일관성", MAJOR),
	"A11": ("frappe 파일 무수정", CRITICAL),
	"A12": ("끝 문장 부호", MINOR),
	"A13": ("길이 비율", MINOR),
	"A14": ("조사 오류 위험", MINOR),
	"A15": ("문체", MINOR),
}

PLACEHOLDER_RE = re.compile(
	r"\{\{[\s\w].*?\}\}"  # jinja ({{ 뒤가 공백/식별자일 때만. '{{' 같은 문자 그대로의 중괄호는 제외)
	r"|\{\d*\}|\{[A-Za-z_][\w.]*\}"  # {0} {} {name}
	r"|%\(\w+\)[#0\- +]*\d*(?:\.\d+)?[sdifr]"  # %(x)s
	r"|%[sdifr]"
)
TAG_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s[^<>]*?)?/?>")
ENTITY_RE = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z]+);")
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "wbr", "col", "source"}

TRANSLATIONESE_RE = re.compile(r"당신|귀하|되어졌|되어집|하는 것이 가능|을 가지고 있|를 가지고 있")
PARTICLE_RISK_RE = re.compile(rf"(?:{PLACEHOLDER_RE.pattern})([을를이가은는와과])(?!\()")

FIELDTYPE_COMMENT_RE = re.compile(
	r"Option for the '(?:Type|Field Type|Fieldtype)' \(Select\) field in DocType "
	r"'(?:DocField|Custom Field|Customize Form Field|Web Form Field|Web Template Field)'"
)
FIELDTYPE_FORMAT_RE = re.compile(r"^(?P<en>.+) \((?P<ko>[^()]+)\)$")

SUBMIT_RE = re.compile(r"\bsubmit(?:s|ted|ting|table|tion)?\b", re.I)
AMEND_RE = re.compile(r"\bamend(?:s|ed|ing|ment|ments)?\b", re.I)
WEB_CONTEXT_PREFIXES = ("frappe/www/", "frappe/website/", "frappe/templates/")


def placeholders(s: str) -> Counter:
	return Counter(PLACEHOLDER_RE.findall(s))


def tags(s: str) -> Counter:
	return Counter(TAG_RE.findall(s)) + Counter(ENTITY_RE.findall(s))


def well_nested(s: str) -> bool:
	stack = []
	for tag in TAG_RE.findall(s):
		name = re.match(r"</?([A-Za-z][\w-]*)", tag).group(1).lower()
		if name in VOID_TAGS or tag.endswith("/>"):
			continue
		if tag.startswith("</"):
			if not stack or stack.pop() != name:
				return False
		else:
			stack.append(name)
	return not stack


def end_class(s: str) -> str:
	s = s.rstrip()
	if s.endswith(("...", "…")):
		return "..."
	return s[-1] if s and s[-1] in ".:?!" else ""


def lead_trail(s: str) -> tuple[str, str]:
	return re.match(r"^\s*", s).group(), re.search(r"\s*$", s).group()


def norm_label(s: str) -> str:
	return re.sub(r"[\s.:?!…]+$", "", s.strip()).lower()


def is_fieldtype_context(m) -> bool:
	return any(FIELDTYPE_COMMENT_RE.search(c) for c in m.auto_comments)


def is_web_context(m) -> bool:
	return bool(m.locations) and all(
		p.startswith(WEB_CONTEXT_PREFIXES) or "web_form" in p for p, _ in m.locations
	)


def word_re(term: str) -> re.Pattern:
	# \w는 한글도 포함하므로 영문·숫자로만 경계를 판단한다 (예: "URL을"도 URL로 인식)
	return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])")


class Validator:
	def __init__(self, args):
		self.args = args
		self.failures = defaultdict(list)  # code -> [(msgid, ctxt, msgstr, reason)]
		self.glossary = load_glossary()
		self.keep = [(g["source"], word_re(g["source"])) for g in self.glossary if g["type"] == "keep"]
		self.keep_terms = {term for term, _ in self.keep}
		self.translate = {
			g["source"].lower(): [t.strip() for t in g["target"].split("|")]
			for g in self.glossary
			if g["type"] == "translate"
		}
		self.fieldtype = {g["source"]: g["target"] for g in self.glossary if g["type"] == "fieldtype"}

	def fail(self, code, m, reason=""):
		if code in self.skip or (m is not None and code in ignored_checks(m)):
			return
		if m is None:
			self.failures[code].append(("", None, "", reason))
		else:
			self.failures[code].append((m.id, m.context, msgstr(m), reason))

	@property
	def skip(self):
		return self.args.skip

	def in_scope(self, m) -> bool:
		if not self.args.module and not self.args.path:
			return True
		locs = [p for p, _ in m.locations]
		if self.args.module and any(module_of(p) in self.args.module for p in locs):
			return True
		if self.args.path and any(p.startswith(tuple(self.args.path)) for p in locs):
			return True
		return False

	def run(self):
		self.check_a3_syntax()
		self.check_a11_frappe_clean()

		pot_keys = {key_of(m) for m in messages(load_catalog(UPSTREAM_POT))}
		self.po = load_catalog(KO_PO, LOCALE)
		entries = [m for m in messages(self.po) if self.in_scope(m)]
		self.total = len(entries)

		for m in entries:
			if key_of(m) not in pot_keys:
				self.fail("A0", m, "main.pot에 없는 msgid/msgctxt")
			src, tgt = m.id, msgstr(m)
			if not tgt or m.fuzzy:
				self.fail("A7", m, "fuzzy" if tgt else "빈 msgstr")
				continue
			self.check_entry(m, src, tgt)

		self.check_a10_consistency(entries)

	def check_entry(self, m, src, tgt):
		if placeholders(src) != placeholders(tgt):
			self.fail("A1", m, f"원문 {sorted(placeholders(src).elements())} ≠ 번역 {sorted(placeholders(tgt).elements())}")

		if tags(src) != tags(tgt):
			diff = (tags(src) - tags(tgt)) + (tags(tgt) - tags(src))
			self.fail("A2", m, f"태그/엔티티 차이 {sorted(diff.elements())}")
		elif well_nested(src) and not well_nested(tgt):
			self.fail("A2", m, "태그 중첩 오류")

		for term, rx in self.keep:
			if rx.search(src) and len(rx.findall(tgt)) < len(rx.findall(src)):
				self.fail("A4", m, f"예약어 '{term}' 누락/번역됨")

		self.check_a5_glossary(m, src, tgt)

		general = src.lower() in self.translate or src in self.keep_terms  # R1: 일반 라벨 용도로 결정된 공용 msgid
		if is_fieldtype_context(m) and not general:
			expected = self.fieldtype.get(src)
			if expected is not None:
				if tgt != expected:
					self.fail("A6", m, f"용어집 기준 '{expected}'")
			elif src not in ("JSON", "HTML") and not FIELDTYPE_FORMAT_RE.match(tgt):
				self.fail("A6", m, "'English (한국어)' 형식 아님")
			elif (fm := FIELDTYPE_FORMAT_RE.match(tgt)) and fm.group("en") != src:
				self.fail("A6", m, "괄호 앞 영문이 원문과 다름")

		if hit := TRANSLATIONESE_RE.findall(tgt):
			self.fail("A8", m, f"번역투: {', '.join(hit)}")

		if lead_trail(src) != lead_trail(tgt):
			self.fail("A9", m, f"원문 {lead_trail(src)!r} ≠ 번역 {lead_trail(tgt)!r}")

		se, te = end_class(src), end_class(tgt)
		if se != te and not (se == "!" and te == "."):
			self.fail("A12", m, f"원문 끝 '{se}' ≠ 번역 끝 '{te}'")

		if len(src) <= 20 and len(tgt) > 2 * len(src) and not is_fieldtype_context(m):
			self.fail("A13", m, f"{len(src)}자 → {len(tgt)}자")

		if hit := PARTICLE_RISK_RE.findall(tgt):
			self.fail("A14", m, f"플레이스홀더 뒤 조사 '{''.join(hit)}'")

		self.check_a15_style(m, src, tgt)

	def check_a5_glossary(self, m, src, tgt):
		if is_fieldtype_context(m) and src in self.fieldtype:
			return  # A6에서 검사
		expected = self.translate.get(norm_label(src))
		if expected is not None:
			if norm_label(tgt) not in {norm_label(e) for e in expected}:
				self.fail("A5", m, f"용어집 기준 '{' | '.join(expected)}'")
			return
		if is_web_context(m):
			return
		if SUBMIT_RE.search(src) and "제출" in tgt:
			self.fail("A5", m, "docstatus submit은 '확정' (웹 폼 맥락이면 validate-ignore)")
		if AMEND_RE.search(src) and "수정본" not in tgt:
			self.fail("A5", m, "amend는 '수정본'")

	def check_a15_style(self, m, src, tgt):
		if not re.search(r"[.!?]\s*$", src) or " " not in src.strip():
			return
		body = re.sub(r"(<[^>]+>|[\s.!?…\"')\]]|" + PLACEHOLDER_RE.pattern + r")+$", "", tgt)
		ended_with_period = bool(re.search(r"[.]\s*$", tgt))
		if re.search(r"(?<!세)요$", body):
			self.fail("A15", m, "해요체")
		elif re.search(r"(?<!니)다$", body):
			self.fail("A15", m, "~다. 평서형(합니다체 아님)")
		elif ended_with_period and re.search(r"(함|됨|음)$", body):
			self.fail("A15", m, "~함. 명사형 종결")

	def check_a10_consistency(self, entries):
		groups = defaultdict(list)
		for m in entries:
			tgt = msgstr(m)
			if not tgt or m.fuzzy or is_fieldtype_context(m) or PLACEHOLDER_RE.search(m.id):
				continue
			if len(m.id.split()) > 4:
				continue
			groups[norm_label(m.id)].append(m)
		for src, ms in groups.items():
			variants = {norm_label(msgstr(m)) for m in ms if "A10" not in ignored_checks(m)}
			if len(variants) > 1:
				for m in ms:
					self.fail("A10", m, f"'{src}' 번역 {len(variants)}종: {sorted(variants)}")

	def check_a3_syntax(self):
		if "A3" in self.skip:
			return
		if msgfmt := shutil.which("msgfmt"):
			r = subprocess.run([msgfmt, "--check", "-o", "/dev/null", str(KO_PO)], capture_output=True, text=True)
			if r.returncode:
				self.fail("A3", None, r.stderr.strip())
			return
		# msgfmt가 없으면 babel로 대체 검사 (파싱 + python-format 검사 + MO 생성)
		try:
			with open(KO_PO, "rb") as f:
				catalog = read_po(f, locale=LOCALE, abort_invalid=True)
			for message, errors in catalog.check():
				for e in errors:
					self.fail("A3", message, str(e))
			write_mo(io.BytesIO(), catalog)
		except Exception as e:
			self.fail("A3", None, f"{type(e).__name__}: {e}")

	def check_a11_frappe_clean(self):
		r = subprocess.run(
			["git", "-C", str(FRAPPE_ROOT), "status", "--porcelain"], capture_output=True, text=True
		)
		if r.returncode:
			self.fail("A11", None, f"git status 실패: {r.stderr.strip()}")
		elif r.stdout.strip():
			self.fail("A11", None, "apps/frappe 변경 사항:\n" + r.stdout.rstrip())

	def report(self) -> int:
		limit = self.args.limit
		for code, (name, severity) in CHECKS.items():
			items = self.failures.get(code, [])
			if not items or (self.args.only and code not in self.args.only):
				continue
			print(f"\n=== {code} {name} [{severity}] {len(items)}건 ===")
			for msgid, ctxt, tgt, reason in items[: limit or None]:
				label = f"{msgid!r}" + (f" [ctx={ctxt}]" if ctxt else "")
				print(f"- {label}\n    번역: {tgt!r}\n    사유: {reason}")
			if limit and len(items) > limit:
				print(f"  ... 외 {len(items) - limit}건 (--limit 0 으로 전체 표시)")

		print(f"\n요약 (검사 대상 {self.total}건)")
		counts = Counter()
		for code, (name, severity) in CHECKS.items():
			n = len(self.failures.get(code, []))
			counts[severity] += n
			mark = "skip" if code in self.skip else n
			print(f"  {code:<4} {name:<12} {severity}  {mark}")
		print(f"  치명 {counts[CRITICAL]} / 주요 {counts[MAJOR]} / 경미 {counts[MINOR]}")

		if self.args.json:
			data = {
				code: [dict(zip(("msgid", "msgctxt", "msgstr", "reason"), item)) for item in items]
				for code, items in self.failures.items()
			}
			with open(self.args.json, "w", encoding="utf-8") as f:
				json.dump(data, f, ensure_ascii=False, indent=1)
			print(f"JSON: {self.args.json}")

		return 1 if counts[CRITICAL] or counts[MAJOR] else 0


def codes(value: str) -> set[str]:
	return {c.strip().upper() for c in value.split(",") if c.strip()}


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--module", action="append", help="모듈 단위 검사 (예: core, public/js/frappe/form)")
	parser.add_argument("--path", action="append", help="소스 경로 접두어로 검사 (예: frappe/core/doctype/user/)")
	parser.add_argument("--skip", type=codes, default=set(), help="건너뛸 검사 (예: A7,A13)")
	parser.add_argument("--only", type=codes, default=set(), help="출력할 검사만 (집계는 전체)")
	parser.add_argument("--limit", type=int, default=20, help="검사별 출력 건수 (0=전체)")
	parser.add_argument("--json", help="실패 목록을 JSON으로 저장")
	args = parser.parse_args()

	v = Validator(args)
	v.run()
	return v.report()


if __name__ == "__main__":
	sys.exit(main())
