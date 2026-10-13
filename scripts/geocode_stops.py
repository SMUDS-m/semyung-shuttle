"""③ 좌표 붙이기: 원주·충주 경유지를 카카오 장소검색으로 지오코딩한다.

KAKAO_REST_KEY=... python3 scripts/geocode_stops.py
data/overrides.json 에 같은 이름이 있으면 검색 대신 그 좌표를 쓴다.
"""
import json
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://dapi.kakao.com/v2/local/search/keyword.json"
# 시 경계를 대략 감싸는 사각형 (경도1, 위도1, 경도2, 위도2)
RECT = {"원주": "127.85,37.25,128.05,37.45", "충주": "127.80,36.90,128.02,37.08"}


def clean(name):
    name = re.sub(r"\(구\)", "", name)
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"(앞|옆|건너편|입구)?\s*(버스정류장)?\s*$", "", name.strip())
    return re.sub(r"\s+(앞|옆|건너편)$", "", name).strip()


def search(key, query, rect):
    q = urllib.parse.urlencode({"query": query, "rect": rect, "size": 5})
    req = urllib.request.Request(f"{API}?{q}", headers={"Authorization": f"KakaoAK {key}"})
    return json.load(urllib.request.urlopen(req, timeout=10))["documents"]


def candidates(name):
    """정류장 이름에서 검색어 후보를 만든다: 전체 → 마지막 상호 → 첫 상호."""
    base = clean(name)
    parts = re.split(r"\s+(?:옆|건너편|앞)\s+", base)
    out = [base] + parts[::-1]
    return list(dict.fromkeys(p for p in out if p))


def main():
    key = os.environ["KAKAO_REST_KEY"]
    overrides_path = ROOT / "data" / "overrides.json"
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    stops = json.loads((ROOT / "data" / "stops.json").read_text())
    for s in stops:
        city = s["area"]
        for r in s.get("route", []):
            if r["place"] == "학교 도착":
                continue
            if r["place"] in overrides:
                r.update(overrides[r["place"]], source="override")
                continue
            for q in candidates(r["place"]):
                docs = search(key, q, RECT[city])
                time.sleep(0.1)
                if docs:
                    d = docs[0]
                    r.update(lat=float(d["y"]), lng=float(d["x"]), source="kakao",
                             matched=d["place_name"], query=q)
                    break
            else:
                r.update(lat=None, lng=None, source="missing")
            print(f'{city} | {r["place"]} → {r.get("matched")} ({r.get("query")})')
    (ROOT / "data" / "stops.json").write_text(json.dumps(stops, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
