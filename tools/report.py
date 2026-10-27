#!/usr/bin/env python
"""진행률·diff 리포트.

사용법:
    ../../env/bin/python tools/report.py                 # 모듈별 진행률
    ../../env/bin/python tools/report.py --upstream      # 스냅샷 대비 main.pot 변경(업그레이드 시)
    ../../env/bin/python tools/report.py --diff HEAD     # git 기준 ko.po 번역 변경 내역
    ../../env/bin/python tools/report.py --todo core --limit 300 --json batch.json
                                                         # 모듈의 미번역/fuzzy 항목 추출(배치 번역용)
"""

import argparse
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict

from babel.messages.pofile import read_po

from _common import (
	APP_ROOT,
	KO_PO,
	LOCALE,
	SNAPSHOT,
	UPSTREAM_KO,
	UPSTREAM_POT,
	key_of,
	load_catalog,
	messages,
	msgstr,
	primary_module,
)


def progress(po):
	rows = defaultdict(Counter)
	for m in messages(po):
		mod = primary_module(m)
		state = "fuzzy" if m.fuzzy else ("done" if msgstr(m) else "empty")
		rows[mod][state] += 1
		rows["(전체)"][state] += 1

	print(f"{'모듈':<32}{'전체':>7}{'완료':>7}{'fuzzy':>7}{'미번역':>7}{'진행률':>8}")
	order = sorted((k for k in rows if k != "(전체)"), key=lambda k: -sum(rows[k].values()))
	for mod in [*order, "(전체)"]:
		c = rows[mod]
		total = sum(c.values())
		print(f"{mod:<32}{total:>7}{c['done']:>7}{c['fuzzy']:>7}{c['empty']:>7}{c['done'] / total:>8.1%}")
	print(f"obsolete(#~): {len(po.obsolete)}")


def upstream_diff():
	if not SNAPSHOT.exists():
		print(f"스냅샷이 없습니다: {SNAPSHOT}")
		return
	old = {key_of(m): m for m in messages(load_catalog(SNAPSHOT))}
	new = {key_of(m): m for m in messages(load_catalog(UPSTREAM_POT))}
	added = [k for k in new if k not in old]
	removed = [k for k in old if k not in new]
	print(f"스냅샷 {len(old)}건 → main.pot {len(new)}건: 추가 {len(added)} / 삭제 {len(removed)}")
	for label, keys in (("+", added), ("-", removed)):
		for msgid, ctxt in keys:
			print(f"{label} {msgid!r}" + (f" [ctx={ctxt}]" if ctxt else ""))


def git_diff(rev):
	rel = KO_PO.relative_to(APP_ROOT)
	r = subprocess.run(["git", "-C", str(APP_ROOT), "show", f"{rev}:{rel}"], capture_output=True)
	if r.returncode:
		print(f"{rev}:{rel} 를 읽을 수 없습니다: {r.stderr.decode().strip()}")
		return
	old = {key_of(m): msgstr(m) for m in messages(read_po(io.BytesIO(r.stdout), locale=LOCALE))}
	cur = {key_of(m): (msgstr(m), m) for m in messages(load_catalog(KO_PO, LOCALE))}
	per_module = Counter()
	changes = []
	for k, (s, m) in cur.items():
		if s != old.get(k, ""):
			per_module[primary_module(m)] += 1
			changes.append((k, old.get(k, ""), s))
	print(f"{rev} 대비 번역 변경 {len(changes)}건")
	for mod, n in per_module.most_common():
		print(f"  {mod}: {n}")
	for (msgid, ctxt), before, after in changes:
		print(f"* {msgid!r}" + (f" [ctx={ctxt}]" if ctxt else "") + f"\n    {before!r} → {after!r}")


def todo(po, modules, limit, out):
	upstream = {key_of(m): msgstr(m) for m in messages(load_catalog(UPSTREAM_KO, LOCALE))}
	items = []
	for m in messages(po):
		if msgstr(m) and not m.fuzzy:
			continue
		if modules and primary_module(m) not in modules:
			continue
		items.append(
			{
				"msgid": m.id,
				"msgctxt": m.context,
				"msgstr": msgstr(m),
				"fuzzy": m.fuzzy,
				"previous_msgid": m.previous_id[0] if m.previous_id else None,
				"comments": list(m.auto_comments),
				"locations": [f"{p}:{n}" if n else p for p, n in m.locations],
				"frappe_ko(참고)": upstream.get(key_of(m), ""),
			}
		)
		if limit and len(items) >= limit:
			break
	if out:
		with open(out, "w", encoding="utf-8") as f:
			json.dump(items, f, ensure_ascii=False, indent=1)
		print(f"{len(items)}건 → {out}")
	else:
		for it in items:
			print(json.dumps(it, ensure_ascii=False))


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--upstream", action="store_true", help="스냅샷 대비 main.pot 변경")
	parser.add_argument("--diff", metavar="REV", help="git REV 대비 ko.po 번역 변경")
	parser.add_argument("--todo", nargs="*", metavar="MODULE", help="미번역/fuzzy 항목 추출 (모듈 생략 시 전체)")
	parser.add_argument("--limit", type=int, default=0)
	parser.add_argument("--json", help="--todo 결과 저장 경로")
	args = parser.parse_args()

	if args.upstream:
		upstream_diff()
	elif args.diff:
		git_diff(args.diff)
	elif args.todo is not None:
		todo(load_catalog(KO_PO, LOCALE), set(args.todo), args.limit, args.json)
	else:
		progress(load_catalog(KO_PO, LOCALE))
	return 0


if __name__ == "__main__":
	sys.exit(main())
