"""④ 검증: 좌표 누락, 이웃 정류장 간 거리, 시각 순서를 확인한다. 문제가 있으면 종료 코드 1."""
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_HOP_KM = 6


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def main():
    problems = []
    for s in json.loads((ROOT / "data" / "stops.json").read_text()):
        if s["lat"] is None:
            problems.append(f'{s["area"]}: 좌표 없음')
        route = [r for r in s.get("route", []) if r["place"] != "학교 도착"]
        for r in route:
            if r.get("lat") is None:
                problems.append(f'{s["area"]} {r["place"]}: 좌표 없음')
        for a, b in zip(route, route[1:]):
            if a.get("lat") and b.get("lat") and km(a, b) > MAX_HOP_KM:
                problems.append(f'{s["area"]} {a["place"]} → {b["place"]}: {km(a, b):.1f}km')
            if b["times"] < a["times"]:
                problems.append(f'{s["area"]} {b["place"]}: 시각이 앞 정류장보다 빠름')
    print("\n".join(problems) or "검증 통과")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
