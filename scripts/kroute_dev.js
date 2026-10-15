// 로컬 확인용: AutoSNS/geoai-functions 의 Netlify 함수(kroute·busarr·alerts)를 http://localhost:8899/<이름> 으로 띄운다.
//   KAKAO_REST_KEY=... DATA_GO_KR_KEY=... node scripts/kroute_dev.js
const http = require("http");
const FN = { kroute: require("../../AutoSNS/geoai-functions/kroute.js"), busarr: require("../../AutoSNS/geoai-functions/busarr.js"),
  alerts: require("../../AutoSNS/geoai-functions/alerts.js") };
http.createServer(async (req, res) => {
  const u = new URL(req.url, "http://localhost");
  const f = FN[u.pathname.slice(1)];
  if (!f) { res.writeHead(404); return res.end(); }
  const r = await f.handler({ httpMethod: req.method, headers: req.headers, queryStringParameters: Object.fromEntries(u.searchParams) });
  res.writeHead(r.statusCode, r.headers); res.end(r.body || "");
}).listen(8899, () => console.log("함수 로컬 서버: http://localhost:8899/kroute · /busarr · /alerts"));
