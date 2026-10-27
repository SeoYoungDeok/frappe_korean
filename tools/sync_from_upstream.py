#!/usr/bin/env python
"""frappe main.pot → frappe_korean/locale/ko.po 동기화.

`bench update-po-files` / `bench generate-pot-file`을 대신한다 (가이드 0-3, 0-5).

- 신규 원문: 빈 msgstr로 추가
- 변경된 원문(같은 소스 파일에서 사라진 번역된 원문과 유사도 0.5 초과): 기존 번역을 옮기고
  `#, fuzzy` + `#| msgid` 이전 원문 표시. 스냅샷과 main.pot의 차이는 report.py로 확인
- 삭제된 원문: obsolete(`#~`) 처리. 이전 동기화에서 obsolete가 된 항목은
  main.pot의 POT-Creation-Date가 바뀐(=다음 업그레이드) 시점에 제거
- `#:` 소스 위치, `#.` 추출 주석, 플래그를 main.pot 기준으로 갱신

사용법:
    ../../env/bin/python tools/sync_from_upstream.py            # 동기화
    ../../env/bin/python tools/sync_from_upstream.py --dry-run  # 변경 통계만
    ../../env/bin/python tools/sync_from_upstream.py --update-snapshot  # 번역·검증 완료 후 스냅샷 갱신
"""

import argparse
import difflib
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone

from babel.messages.catalog import Catalog, Message

from _common import (
	KO_PO,
	LOCALE,
	drop_false_format_flag,
	SNAPSHOT,
	UPSTREAM_POT,
	key_of,
	load_catalog,
	messages,
	msgstr,
	save_catalog,
)

OBSOLETE_STAMP = "obsolete-since:"
SIMILARITY_THRESHOLD = 0.5


def new_header_catalog(pot: Catalog, po: Catalog | None) -> Catalog:
	catalog = Catalog(
		locale=LOCALE,
		project="frappe_korean",
		msgid_bugs_address="developers@frappe.io",
		language_team="Korean",
		last_translator="frappe_korean",
		creation_date=pot.creation_date,
		revision_date=datetime.now(timezone.utc),
		fuzzy=False,
	)
	if po is not None:
		catalog.last_translator = po.last_translator
	return catalog


def obsolete_stamp(message) -> str | None:
	for c in message.user_comments:
		if c.startswith(OBSOLETE_STAMP):
			return c[len(OBSOLETE_STAMP) :].strip()
	return None


def pot_stamp(pot: Catalog) -> str:
	return pot.creation_date.strftime("%Y-%m-%d %H:%M%z") if pot.creation_date else "unknown"


def find_changed_source(message, removed_by_file) -> Message | None:
	"""같은 소스 파일에서 사라진 원문 중 가장 비슷한 번역된 항목."""
	best, best_ratio = None, SIMILARITY_THRESHOLD
	seen = set()
	for filename, _line in message.locations:
		for old in removed_by_file.get(filename, ()):
			if id(old) in seen or old.context != message.context:
				continue
			seen.add(id(old))
			ratio = difflib.SequenceMatcher(None, old.id, message.id).ratio()
			if ratio > best_ratio:
				best, best_ratio = old, ratio
	return best


def sync(dry_run: bool) -> int:
	pot = load_catalog(UPSTREAM_POT)
	po = load_catalog(KO_PO, LOCALE) if KO_PO.exists() else None
	stamp = pot_stamp(pot)

	pot_keys = {key_of(m) for m in messages(pot)}

	# 번역이 있는 기존 항목(활성 + obsolete) 중 main.pot에서 사라진 것 → 변경 원문 후보
	removed_by_file = defaultdict(list)
	if po is not None:
		old_pool = list(messages(po)) + list(po.obsolete.values())
		for old in old_pool:
			if key_of(old) in pot_keys or not msgstr(old):
				continue
			for filename, _line in old.locations:
				removed_by_file[filename].append(old)

	out = new_header_catalog(pot, po)
	stats = defaultdict(int)
	changed = []

	for m in messages(pot):
		existing = po.get(m.id, m.context) if po is not None else None
		if existing is not None:
			string = existing.string
			flags = set(m.flags) | ({"fuzzy"} if existing.fuzzy else set())
			user_comments = [c for c in existing.user_comments if not c.startswith(OBSOLETE_STAMP)]
			previous_id = existing.previous_id
			stats["kept"] += 1
		else:
			string, flags, user_comments, previous_id = "", set(m.flags), [], ()
			if po is not None and (old := find_changed_source(m, removed_by_file)):
				string = old.string
				flags.add("fuzzy")
				previous_id = (old.id,)
				user_comments = [c for c in old.user_comments if not c.startswith(OBSOLETE_STAMP)]
				changed.append((old.id, m.id))
				stats["changed→fuzzy"] += 1
			else:
				stats["new"] += 1

		message = out.add(
			m.id,
			string,
			locations=m.locations,
			flags=flags,
			auto_comments=m.auto_comments,
			user_comments=user_comments,
			previous_id=previous_id,
			context=m.context,
		)
		drop_false_format_flag(message)

	if po is not None:
		for old in messages(po):
			if key_of(old) in pot_keys:
				continue
			if not msgstr(old):
				stats["removed(빈 항목 삭제)"] += 1
				continue
			old.user_comments = [*old.user_comments, f"{OBSOLETE_STAMP} {stamp}"]
			out.obsolete[out._key_for(old.id, old.context)] = old
			stats["removed→obsolete"] += 1

		for k, old in po.obsolete.items():
			if key_of(old) in pot_keys:
				continue  # 원문이 되살아남: 위에서 신규로 처리됨
			if obsolete_stamp(old) == stamp:
				out.obsolete[k] = old
				stats["obsolete 유지"] += 1
			else:
				stats["obsolete 제거(이전 업그레이드분)"] += 1

	print(f"main.pot: {UPSTREAM_POT} ({len(pot_keys)}건, POT-Creation-Date {stamp})")
	print(f"ko.po:    {KO_PO} ({'신규 생성' if po is None else '기존 파일 갱신'})")
	for k, v in stats.items():
		print(f"  {k}: {v}")
	for old_id, new_id in changed[:30]:
		print(f"  fuzzy: {old_id!r}\n      → {new_id!r}")
	if len(changed) > 30:
		print(f"  ... 외 {len(changed) - 30}건")

	if dry_run:
		print("(dry-run: 파일을 쓰지 않음)")
		return 0

	save_catalog(KO_PO, out)
	print(f"작성 완료: {KO_PO}")

	if po is None and not SNAPSHOT.exists():
		update_snapshot()
	return 0


def update_snapshot() -> int:
	SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
	shutil.copyfile(UPSTREAM_POT, SNAPSHOT)
	print(f"스냅샷 갱신: {SNAPSHOT}")
	return 0


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--dry-run", action="store_true", help="파일을 쓰지 않고 통계만 출력")
	parser.add_argument("--update-snapshot", action="store_true", help="main.pot을 스냅샷으로 복사만 한다")
	args = parser.parse_args()
	if args.update_snapshot:
		return update_snapshot()
	return sync(args.dry_run)


if __name__ == "__main__":
	sys.exit(main())
