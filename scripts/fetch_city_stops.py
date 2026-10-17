"""제천 시내버스 정류장·노선 목록 → docs/jecheon_stops.json (실시간 도착 칸의 정류장·버스 번호 고르기용).

TAGO 버스노선정보(노선 목록 → 노선별 경유 정류장 순서)로 정류장마다 지나는 버스 번호와
'다음 정류장'(어느 방향인지 구별용)을 모은다. 노선 수만큼만 호출(수백 건, 하루 한도 10,000).
키: AutoSNS 암호화 저장소 DATA_GO_KR_KEY.  실행: python3 scripts/fetch_city_stops.py
"""
import json, os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, "/Volumes/USB256/devAPP/AutoSNS")
from shared.secret_get import get

KEY = get("DATA_GO_KR_KEY")
CITY = 33030
API = "https://apis.data.go.kr/1613000/BusRouteInfoInqireService/"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "jecheon_stops.json")


def items(op, **p):
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode(dict(serviceKey=KEY, cityCode=CITY, _type="json", numOfRows=500, pageNo=page, **p))
        for t in range(3):
            try:
                j = json.load(urllib.request.urlopen(API + op + "?" + q, timeout=30)); break
            except Exception:
                time.sleep(2)
        else:
            raise SystemExit(f"{op} 실패")
        b = j["response"]["body"]; it = (b.get("items") or {}).get("item") or []
        out += it if isinstance(it, list) else [it]
        if len(out) >= b.get("totalCount", 0): return out
        page += 1


routes = items("getRouteNoList")
print("노선", len(routes))
stops = {}
for n, r in enumerate(routes):
    seq = sorted(items("getRouteAcctoThrghSttnList", routeId=r["routeid"]), key=lambda s: int(s["nodeord"]))
    no = str(r["routeno"])
    for i, s in enumerate(seq):
        st = stops.setdefault(s["nodeid"], {"id": s["nodeid"], "name": s["nodenm"], "no": s.get("nodeno"),
                                            "lat": round(float(s["gpslati"]), 6), "lng": round(float(s["gpslong"]), 6),
                                            "buses": set(), "next": set()})
        st["buses"].add(no)
        if i + 1 < len(seq) and seq[i + 1]["nodenm"] != s["nodenm"]:
            st["next"].add(seq[i + 1]["nodenm"])
    if n % 20 == 0: print(n, no, len(stops))
key = lambda b: (int("".join(c for c in b if c.isdigit()) or 0), b)
data = sorted(({**s, "buses": sorted(s["buses"], key=key), "next": sorted(s["next"])[:3]} for s in stops.values()),
              key=lambda s: s["name"])
json.dump({"built": time.strftime("%Y-%m-%d"), "source": "국토교통부 TAGO 버스노선정보", "stops": data},
          open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
print("정류장", len(data), os.path.getsize(OUT) // 1024, "KB")
