"""
Skill: normalize_patent_fields — 专利号规范化
"""
from __future__ import annotations

import re


def normalize_patent_fields(record: dict) -> dict:
    normalized = {}

    raw_no = record.get("patent_no_raw") or record.get("patent_no_normalized") or ""
    norm_no = _normalize_patent_no(raw_no)
    normalized["patent_no_normalized"] = norm_no
    normalized["application_no"] = norm_no

    pub_no = record.get("publication_no_raw") or record.get("publication_no") or ""
    normalized["publication_no"] = _normalize_publication_no(pub_no)

    normalized["patent_title"] = _normalize_text(record.get("patent_title"))
    normalized["inventors"] = _normalize_names(record.get("inventors", []))
    normalized["patentee"] = _normalize_names(record.get("patentee", []))
    normalized["patent_type"] = record.get("patent_type")
    normalized["application_date"] = record.get("application_date")
    normalized["grant_announcement_date"] = record.get("grant_announcement_date")

    return {"status": "success", "normalized_record": normalized}


def _normalize_patent_no(value: str | None) -> str | None:
    if not value:
        return None
    s = value.upper().strip()
    s = s.replace("ＺＬ", "ZL").replace("ＣＮ", "CN")
    s = s.replace("ZL", "").replace("CN", "")
    s = re.sub(r"[\s\.\-_/]", "", s)
    s = re.sub(r"[^0-9X]", "", s)
    if 9 <= len(s) <= 13:
        return s
    return None


def _normalize_publication_no(value: str | None) -> str | None:
    if not value:
        return None
    s = value.upper().strip()
    s = s.replace("ＣＮ", "CN")
    s = re.sub(r"[\s\.\-_]", "", s)
    if re.match(r"CN\d{7,13}[A-Z]?$", s):
        return s
    digits = re.sub(r"[^0-9A-Z]", "", s)
    if len(digits) >= 7:
        return f"CN{digits}"
    return None


def _normalize_text(s: str | None) -> str | None:
    if not s:
        return None
    return s.replace(" ", "").replace("　", "").strip()


def _normalize_names(names: list[str]) -> list[str]:
    result = []
    for name in names or []:
        n = name.replace(" ", "").replace("　", "").strip()
        if n and len(n) > 1:
            result.append(n)
    return result
