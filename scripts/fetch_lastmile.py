"""제천역·봉양역·터미널 등 → 세명대 시내 구간을 ODsay 로 미리 받아 data/lastmile.json 에 저장한다.

ODSAY_KEY=... python3 scripts/fetch_lastmile.py
페이지가 길찾기 때마다 ODsay 를 부르지 않도록(무료 하루 한도) 고정 구간을 정적 파일로 둔다.
ODsay 웹 키는 등록 도메인에서만 동작하므로 Referer 를 localhost 로 보낸다.
"""
import json
import os
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAMPUS = (128.192822, 37.180875)
# ODsay 도시 간 검색 결과의 endName 그대로 (경도, 위도)
HUBS = {
    "제천": (128.205456, 37.127868),
    "봉양": (128.1338, 37.1574),
    "제천버스터미널": (128.210875, 37.142105),
    "제천고속버스터미널": (128.210982, 37.142964),
    "봉양정류소": (128.1350, 37.1590),
}


def search(sx, sy):
    q = urllib.parse.urlencode({"SX": sx, "SY": sy, "EX": CAMPUS[0], "EY": CAMPUS[1],
                                "SearchType": 0, "apiKey": os.environ["ODSAY_KEY"]})
    req = urllib.request.Request("https://api.odsay.com/v1/api/searchPubTransPathT?" + q,
                                 headers={"Referer": "http://localhost:8743/"})
    return json.load(urllib.request.urlopen(req, timeout=20))


def main():
    out = {}
    for name, (x, y) in HUBS.items():
        r = search(x, y)
        if "error" in r:
            print(name, "오류", r["error"])
            continue
        p = r["result"]["path"][0]
        keep = {"info": {k: p["info"][k] for k in ("totalTime", "payment", "totalWalk")},
                "subPath": [{k: s[k] for k in ("trafficType", "sectionTime", "distance", "startName", "endName", "stationCount", "lane") if k in s}
                            for s in p["subPath"]]}
        out[name] = keep
        buses = [l.get("busNo") for s in p["subPath"] for l in s.get("lane", [])]
        print(name, p["info"]["totalTime"], "분", buses[:3])
        time.sleep(0.5)
    path = ROOT / "data" / "lastmile.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(out)
    path.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
