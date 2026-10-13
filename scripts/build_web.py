"""⑤ 정적 데이터: stops.json(좌표) + routes.json(시간표) → docs/shuttle.json

python3 scripts/build_web.py
docs/ 는 GitHub Pages 로 공개된다.
"""
import json
import pathlib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    stops = {s["area"]: s for s in json.loads((ROOT / "data" / "stops.json").read_text())}
    meta = json.loads((ROOT / "data" / "routes.json").read_text())
    routes = []
    for r in meta["routes"]:
        if "city" in r:
            city = stops[r["city"]]["route"]
            out = [{"name": s["place"], "lat": s["lat"], "lng": s["lng"], "times": s["times"],
                    "approx": s.get("approx", False)} for s in city if s["place"] != "학교 도착"]
        else:
            out = []
            for s in r["stops"]:
                src = stops[s["area"]]
                out.append({"name": s["area"], "place": src["place"], "lat": src["lat"],
                            "lng": src["lng"], "times": s["times"]})
        item = {k: v for k, v in r.items() if k not in ("stops", "city")}
        item["stops"] = out
        routes.append(item)
    data = {k: v for k, v in meta.items() if k not in ("routes", "_source", "transit")}
    data.update(routes=routes, source=meta["_source"], built=date.today().isoformat())
    transit = ROOT / "data" / "transit.json"
    if transit.exists():
        data["transit"] = json.loads(transit.read_text())
        data["transit"].update(meta["transit"])
    (ROOT / "docs" / "shuttle.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n = sum(len(r["stops"]) for r in routes)
    print(f"노선 {len(routes)}개, 정류장 {n}곳 → docs/shuttle.json")


if __name__ == "__main__":
    main()
