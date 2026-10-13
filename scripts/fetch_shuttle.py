"""① 수집 + ② 정리: 세명대 통학버스 공지에서 정류장·시간을 뽑아 data/ 에 저장한다.

python3 scripts/fetch_shuttle.py
"""
import html
import json
import pathlib
import re
import urllib.request

BASE = "https://www.semyung.ac.kr"
STOPS_URL = BASE + "/prog/atdBusGuide/kor/sub01_06_03_02/list.do?pageIndex={}"
GUIDE_URL = BASE + "/kor/sub05_04_01.do"
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")


def text(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse_stops(pages):
    """출발장소 목록: 지역, 승차위치, 좌표, (원주·충주) 상세노선 원문."""
    stops = []
    for page in pages:
        body = page[page.find("col-bigo"):page.find("담당부서")]
        for tr in re.findall(r"<tr.*?</tr>", body, re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(tds) < 2:
                continue
            raw = html.unescape(tr)
            ll = re.search(r"lng=([\d.]+).*?lat=([\d.]+)", raw)
            pop = re.search(r'data-cont="(.*?)"', tr, re.S)
            stops.append({
                "area": text(tds[0]),
                "place": text(tds[1]),
                "lat": float(ll.group(2)) if ll else None,
                "lng": float(ll.group(1)) if ll else None,
                "detail": html.unescape(pop.group(1)).strip() if pop else None,
            })
    return stops


def parse_city_route(detail):
    """원주·충주 팝업에서 등교 경유지와 1·2호차 시각을 뽑는다."""
    board = detail.split("■ 하교차량")[0]
    times = {}
    for name, ts in re.findall(r"(?:^|→|•)[ \t]*([^\[\]→•\n]+?)\s*\[([\d:, ]+)\]", board, re.M):
        name = name.strip()
        times.setdefault(name, []).extend(t.strip() for t in ts.split(","))
    return [{"place": k, "times": v} for k, v in times.items()]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    pages = []
    for i in (1, 2, 3):
        page = get(STOPS_URL.format(i))
        (RAW / f"stops_p{i}.html").write_text(page, encoding="utf-8")
        pages.append(page)
    (RAW / "guide.html").write_text(get(GUIDE_URL), encoding="utf-8")

    stops = parse_stops(pages)
    for s in stops:
        if s["detail"]:
            s["route"] = parse_city_route(s["detail"])
        s.pop("detail")
    out = ROOT / "data" / "stops.json"
    out.write_text(json.dumps(stops, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(stops)}곳 → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
