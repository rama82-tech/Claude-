// node shot.mjs  (serves the folder, opens viewer.html in Chromium, writes top.png and iso.png)
import http from "http"; import fs from "fs"; import { chromium } from "playwright-core";
const srv = http.createServer((q, s) => { const f = "." + (q.url.split("?")[0] === "/" ? "/viewer.html" : q.url.split("?")[0]);
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); } else { s.writeHead(200, {"Content-Type": f.endsWith(".glb") ? "model/gltf-binary" : f.endsWith(".html") ? "text/html" : f.endsWith(".js") ? "text/javascript" : "text/plain"}); s.end(d); } }); }).listen(8731);
const b = await chromium.launch({ executablePath: process.env.CHROME || undefined, args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"] });
const p = await b.newPage({ viewport: { width: 1200, height: 800 } });
p.on("console", m => console.log("page:", m.text())); p.on("pageerror", e => console.log("pageerror:", e.message));
await p.goto("http://localhost:8731/viewer.html?m=house.glb"); await p.waitForFunction("window.ready", null, { timeout: 30000 });
for (const v of ["top", "iso"]) { await p.evaluate(n => window.view(n), v); await p.waitForTimeout(300); await p.screenshot({ path: v + ".png" }); }
await b.close(); srv.close();
