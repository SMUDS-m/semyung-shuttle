"""다른 교통편: 제천역 열차, 제천버스터미널 시외버스 시간표를 모아 data/transit.json 에 저장한다.

python3 scripts/fetch_transit.py
자료: 아사마루(코레일·시외버스 공공데이터를 매일 갱신해 보여 주는 사이트).
"""
import html
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
JECHEON_STN = "제천역-중앙선"
JECHEON_BUS = "제천버스터미널"
STATIONS = {"청량리": "청량리역-강릉선-고속철도", "서울": "서울역-경부선-고속철도"}
TERMINALS = {
    "동서울": "동서울종합터미널", "성남": "성남종합버스터미널",
    "인천": "인천종합터미널", "원주": "원주시외버스터미널", "충주": "충주공용버스터미널",
    "청주": "청주시외버스터미널", "동대구": "동대구터미널",
}


def page(host, path):
    url = f"https://{host}/" + urllib.parse.quote(path)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (semyung-shuttle)"})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    s = html.unescape(re.sub(r"<[^>]+>", "|", raw))
    return re.sub(r"\s*\|[\s|]*", "|", s)


def trains(src, dst):
    s = page("train.asamaru.net", f"시간표/{src}/출발/{dst}/도착/")
    start = s.find("|출발|도착|열차|")
    s = s[start:s.find("돌아오는 시간표", start)]
    rows = re.findall(r"\|[\d-]+\|(\d\d:\d\d)\|[\d-]+\|(\d\d:\d\d)\|([^|]+)\|(\d+)\|([\d,]+)\|원\|.*?\|(\d\d:\d\d)(?=\||$)", s)
    return [{"dep": d, "arr": a, "kind": k, "no": n, "fare": int(f.replace(",", "")), "dur": u}
            for d, a, k, n, f, u in rows]


def buses(src, dst):
    try:
        s = page("transportation.asamaru.net", f"시외버스/시간표/{src}/출발/{dst}/도착/")
    except urllib.error.HTTPError as e:
        print(f"  {src} → {dst}: {e.code}")
        return []
    start = s.find("|요금(어른)|소요시간|")
    s = s[start:s.find("돌아오는 시간표", start)]
    rows = re.findall(r"\|(\d\d:\d\d)\|(\d\d:\d\d)\|([^|]+)\|([\d,]+)\|원\|(\d\d:\d\d)", s)
    return [{"dep": d, "arr": a, "kind": k, "fare": int(f.replace(",", "")), "dur": u} for d, a, k, f, u in rows]


def main():
    out = {"fetched": date.today().isoformat(), "train": [], "bus": []}
    for name, code in STATIONS.items():
        out["train"].append({"from": name, "to_jecheon": trains(code, JECHEON_STN),
                             "from_jecheon": trains(JECHEON_STN, code)})
        time.sleep(1)
    for name, code in TERMINALS.items():
        out["bus"].append({"from": name, "terminal": code, "to_jecheon": buses(code, JECHEON_BUS),
                           "from_jecheon": buses(JECHEON_BUS, code)})
        time.sleep(1)
    for kind in ("train", "bus"):
        for r in out[kind]:
            print(kind, r["from"], len(r["to_jecheon"]), len(r["from_jecheon"]))
    (ROOT / "data" / "transit.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
