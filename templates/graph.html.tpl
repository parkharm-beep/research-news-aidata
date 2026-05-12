<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{DATE}} Ontology Graph</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
  /* ── 기본 레이아웃 ── */
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; height: 100vh; overflow: hidden; }
  #graph-area { flex: 1; position: relative; }
  #detail-panel { width: 300px; background: #161b22; border-left: 1px solid #30363d; padding: 16px; overflow-y: auto; }
  #detail-panel h2 { font-size: 14px; color: #8b949e; margin-bottom: 12px; }
  #detail-title { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
  #detail-body { font-size: 13px; line-height: 1.6; color: #8b949e; }
  #detail-body a { color: #58a6ff; text-decoration: none; }
  #detail-body .tag { display: inline-block; background: #21262d; border-radius: 4px; padding: 2px 6px; margin: 2px; font-size: 11px; }
  /* ── 줌 컨트롤 ── */
  #zoom-controls { position: absolute; bottom: 16px; right: 16px; display: flex; flex-direction: column; gap: 4px; }
  #zoom-controls button { width: 32px; height: 32px; background: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; cursor: pointer; font-size: 16px; }
  /* ── 노드 색상 ── */
  .node-report  circle { fill: #0d1117; stroke: #c9d1d9; stroke-width: 2; }
  .node-news    circle { fill: #58a6ff; }
  .node-topic   circle { fill: #3fb950; }
  .node-company circle { fill: #f78166; }
  .node-trend   circle { fill: #d2a8ff; }
  .node text { font-size: 10px; fill: #c9d1d9; text-anchor: middle; pointer-events: none; }
  /* ── 엣지 스타일 ── */
  .link { fill: none; stroke-opacity: 0.6; }
  .link-contains  { stroke: #c9d1d9; stroke-width: 1.5; }
  .link-about     { stroke: #3fb950; stroke-dasharray: 4,2; stroke-width: 1; }
  .link-mentions  { stroke: #f78166; stroke-dasharray: 4,2; stroke-width: 1; }
  .link-signals   { stroke: #d2a8ff; stroke-dasharray: 4,2; stroke-width: 1; }
  .link-relates   { stroke: #8b949e; stroke-dasharray: 2,4; stroke-width: 1; }
  svg { width: 100%; height: 100%; }
</style>
</head>
<body>

<div id="graph-area">
  <svg id="svg"></svg>
  <div id="zoom-controls">
    <button id="btn-in">+</button>
    <button id="btn-reset">⊞</button>
    <button id="btn-out">−</button>
  </div>
</div>

<div id="detail-panel">
  <h2>{{DATE}} · 노드 상세</h2>
  <div id="detail-title">노드를 클릭하세요</div>
  <div id="detail-body"></div>
</div>

<script>
// ── 데이터 (INGEST 시 이 부분을 채운다) ──────────────────────────
const nodes = {{NODES_JSON}};
const edges = {{EDGES_JSON}};
// ─────────────────────────────────────────────────────────────────

const svg = d3.select("#svg");
const g   = svg.append("g");
const W   = () => document.getElementById("graph-area").clientWidth;
const H   = () => document.getElementById("graph-area").clientHeight;

// 줌
const zoom = d3.zoom().scaleExtent([0.2, 4]).on("zoom", e => g.attr("transform", e.transform));
svg.call(zoom);
document.getElementById("btn-in").onclick    = () => svg.transition().call(zoom.scaleBy, 1.4);
document.getElementById("btn-out").onclick   = () => svg.transition().call(zoom.scaleBy, 0.7);
document.getElementById("btn-reset").onclick = () => svg.transition().call(zoom.transform, d3.zoomIdentity);

// 시뮬레이션
const sim = d3.forceSimulation(nodes)
  .force("link",   d3.forceLink(edges).id(d => d.id).distance(d => d.type === "contains" ? 100 : 60))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(W() / 2, H() / 2))
  .force("collide", d3.forceCollide(30));

// 엣지
const link = g.append("g").selectAll("line")
  .data(edges).join("line")
  .attr("class", d => `link link-${d.type}`);

// 노드
const nodeSize = { report: 22, news: 16, topic: 12, company: 12, trend: 14 };
const node = g.append("g").selectAll("g")
  .data(nodes).join("g")
  .attr("class", d => `node node-${d.type}`)
  .call(d3.drag()
    .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
    .on("end",   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
  )
  .on("click", (e, d) => showDetail(d));

node.append("circle").attr("r", d => nodeSize[d.type] ?? 12);
node.append("text").attr("dy", d => (nodeSize[d.type] ?? 12) + 12)
  .selectAll("tspan").data(d => (d.label || "").split("\n")).join("tspan")
  .attr("x", 0).attr("dy", (_, i) => i ? "1.1em" : 0)
  .text(t => t);

sim.on("tick", () => {
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${d.x},${d.y})`);
});

// 상세 패널
function showDetail(d) {
  document.getElementById("detail-title").textContent = d.label?.replace("\n", " ") || d.id;
  const related = edges
    .filter(e => e.source.id === d.id || e.target.id === d.id)
    .map(e => e.source.id === d.id ? e.target : e.source);
  document.getElementById("detail-body").innerHTML = `
    ${d.outlet ? `<p><strong>출처</strong>: ${d.url ? `<a href="${d.url}" target="_blank">${d.outlet}</a>` : d.outlet}</p>` : ""}
    ${d.summary ? `<p style="margin-top:8px">${d.summary}</p>` : ""}
    ${d.insight ? `<p style="margin-top:8px;color:#e3b341"><strong>인사이트</strong>: ${d.insight}</p>` : ""}
    ${d.tags?.length ? `<p style="margin-top:8px">${d.tags.map(t => `<span class="tag">${t}</span>`).join("")}</p>` : ""}
    ${related.length ? `<p style="margin-top:12px;font-size:12px;color:#8b949e">연결: ${related.map(r => r.label?.replace("\n"," ")||r.id).join(", ")}</p>` : ""}
  `;
}
</script>
</body>
</html>
