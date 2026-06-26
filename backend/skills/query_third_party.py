"""
Skill: query_third_party_api — 第三方 API 查询（框架预留，暂隐藏）

支持接入天眼查、企查查等商业专利 API。
当前版本仅定义接口结构，不实际调用。
"""

from ..config import THIRD_PARTY_API_KEY, THIRD_PARTY_API_URL


def query_third_party_api(publication_no: str) -> dict:
    """
    通过第三方 API 查询专利信息。

    参数:
        publication_no: 专利公开号（如 CN202210001234.5）

    返回:
        与 query_cnipa_official_record 相同格式的结果
    """
    if not THIRD_PARTY_API_KEY or not THIRD_PARTY_API_URL:
        return {
            "query_status": "not_configured",
            "record_count": 0,
            "official_record": None,
            "need_manual": False,
            "fail_reason": "第三方 API 未配置",
        }

    try:
        import requests
        resp = requests.get(
            THIRD_PARTY_API_URL,
            params={"publication_no": publication_no},
            headers={"Authorization": f"Bearer {THIRD_PARTY_API_KEY}"},
            timeout=15,
        )
        if resp.status_code != 200:
            return _failed(f"第三方 API 返回 {resp.status_code}")

        data = resp.json()
        if not data.get("data"):
            return _failed("第三方 API 无记录")

        item = data["data"][0] if isinstance(data["data"], list) else data["data"]
        record = {
            "application_no": item.get("application_no"),
            "patent_no": item.get("patent_no"),
            "patent_title": item.get("title"),
            "patent_type": item.get("patent_type"),
            "inventors": item.get("inventors", []),
            "patentee": item.get("patentee", []),
            "application_date": item.get("application_date"),
            "grant_announcement_date": item.get("grant_date"),
            "legal_status": item.get("legal_status"),
            "publication_no": item.get("publication_no"),
        }

        return {
            "query_status": "success",
            "record_count": 1,
            "official_record": record,
            "need_manual": False,
            "source": "third_party",
        }

    except Exception as e:
        return _failed(f"第三方 API 查询异常: {e}")


def _failed(reason: str) -> dict:
    return {
        "query_status": "failed",
        "record_count": 0,
        "official_record": None,
        "need_manual": True,
        "fail_reason": reason,
        "source": "third_party",
    }
