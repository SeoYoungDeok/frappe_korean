#!/usr/bin/env python
"""배치 번역 결과를 ko.po에 반영한다.

1. report.py --todo <모듈> --limit 250 --json batch.json   (원문 목록, 순번 = 배열 인덱스)
2. 번역 파일 작성 (JSON 객체, 키 = 순번):
       {"0": "저장", "1": ["확인", "validate-ignore: A5 R2"]}
   값이 배열이면 두 번째 이후 요소는 번역자 주석(`# ...`)으로 추가한다.
3. ../../env/bin/python tools/apply_batch.py batch.json translations.json

원문은 batch.json에서 가져오므로 msgid를 다시 입력하지 않는다(A0 오타 방지).
반영한 항목은 fuzzy 플래그를 지운다. `validate-ignore: A3` 주석이 있으면 잘못 추출된
python-format 플래그도 지운다 (예: JSON 설명문의 "Use % for ..."가 `% f` 포맷으로 오인됨).
"""

import argparse
import json
import sys

from _common import KO_PO, LOCALE, drop_false_format_flag, load_catalog, save_catalog


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("batch", help="report.py --todo 결과 JSON")
	parser.add_argument("translations", help="순번 → 번역 JSON")
	args = parser.parse_args()

	with open(args.batch, encoding="utf-8") as f:
		batch = json.load(f)
	with open(args.translations, encoding="utf-8") as f:
		translations = json.load(f)

	po = load_catalog(KO_PO, LOCALE)
	applied, errors = 0, []
	for idx, value in translations.items():
		i = int(idx)
		if not 0 <= i < len(batch):
			errors.append(f"{idx}: 범위 밖 순번")
			continue
		item = batch[i]
		string, *comments = value if isinstance(value, list) else [value]
		m = po.get(item["msgid"], item["msgctxt"])
		if m is None:
			errors.append(f"{idx}: ko.po에 없음 {item['msgid']!r}")
			continue
		m.string = string
		m.flags.discard("fuzzy")
		m.previous_id = ()
		if any(c.startswith("validate-ignore:") for c in comments):
			# 예외 주석은 누적하지 않고 새 사유로 교체한다
			m.user_comments = [c for c in m.user_comments if not c.startswith("validate-ignore:")]
		for c in comments:
			if c not in m.user_comments:
				m.user_comments.append(c)
		drop_false_format_flag(m)
		applied += 1

	missing = len(batch) - len(translations)
	save_catalog(KO_PO, po)
	print(f"반영 {applied}건 / 배치 {len(batch)}건 (번역 없음 {missing}건)")
	for e in errors:
		print("오류:", e)
	return 1 if errors else 0


if __name__ == "__main__":
	sys.exit(main())
