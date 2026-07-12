#!/usr/bin/env python3
"""
show_graph.py — 直接读 graph.json 渲染图谱（支持多 session 切换）
- 起 HTTP server 暴露 graph.json + serve 自带 HTML（5s 拉一次）
- URL ?session=SESSION_ID 切换 session
- 自动开浏览器
"""
import http.server
import json
import os
import socketserver
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path("D:/xiaoke/CogniFold/sessions")
PORT = 9201

# Auto-discover sessions
def list_sessions():
    sessions = []
    if SESSIONS_DIR.exists():
        for d in sorted(SESSIONS_DIR.iterdir()):
            if d.is_dir() and (d / "graph.json").exists():
                sessions.append(d.name)
    return sessions

KNOWN_SESSIONS = list_sessions()

HTML = """<!doctype html>
<html><head><meta charset="utf-8">
<title>CogniFold Direct</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body { font: 14px/1.4 -apple-system, sans-serif; margin: 0; padding: 16px; background: #fafafa; }
  h1 { margin: 0 0 8px; font-size: 18px; }
  .meta { color: #555; margin-bottom: 8px; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-left: 8px; }
  .connected { background: #d1fae5; color: #065f46; }
  .stale { background: #fef3c7; color: #92400e; }
  .session-bar { margin-bottom: 12px; }
  .session-bar select { font: 14px -apple-system, sans-serif; padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; }
  .session-bar label { font-weight: 600; margin-right: 8px; }
  .log { font: 12px/1.4 ui-monospace, Consolas, monospace; max-height: 120px; overflow-y: auto; background: #1e293b; color: #e2e8f0; padding: 8px; border-radius: 4px; margin-top: 12px; }
  .log div { margin: 0; }
  #graph { width: 100%; height: 70vh; border: 1px solid #ddd; background: white; border-radius: 6px; }
  .legend { margin-top: 8px; font-size: 12px; color: #555; }
  .legend span { display: inline-block; margin-right: 16px; }
  .legend .swatch { display: inline-block; width: 12px; height: 12px; border-radius: 50%; vertical-align: middle; margin-right: 4px; }
</style>
</head><body>
<h1>🧠 CogniFold Direct
  <span id="status" class="status stale">loading…</span>
</h1>
<div class="session-bar">
  <label>Session:</label>
  <select id="sessionSelect" onchange="switchSession()">
    __SESSION_OPTIONS__
  </select>
</div>
<div class="meta">
  Nodes: <b id="nodeCount">0</b> &middot;
  Edges: <b id="edgeCount">0</b> &middot;
  Concepts: <b id="conceptCount">0</b> &middot;
  Intents: <b id="intentCount">0</b> &middot;
  Last disk update: <span id="lastUpdate">—</span>
</div>
<div id="graph"></div>
<div class="legend">
  <span><i class="swatch" style="background:#3B82F6"></i>event</span>
  <span><i class="swatch" style="background:#059669"></i>concept</span>
  <span><i class="swatch" style="background:#F59E0B"></i>intent</span>
  <span><i class="swatch" style="background:#9CA3AF"></i>time</span>
</div>
<div class="log" id="log"></div>
<script>
const COLOR = { event: "#3B82F6", concept: "#059669", intent: "#F59E0B", time: "#9CA3AF" };
const nodesDS = new vis.DataSet();
const edgesDS = new vis.DataSet();
const container = document.getElementById("graph");
const data = { nodes: nodesDS, edges: edgesDS };
const options = {
  physics: { stabilization: { iterations: 100 } },
  nodes: { shape: "dot", size: 14, font: { size: 11 } },
  edges: { arrows: "to", font: { size: 9, align: "middle" } },
};
const network = new vis.Network(container, data, options);

let currentSession = new URLSearchParams(location.search).get("session") || "__DEFAULT__";
let sseSource = null;

function connectSSE() {
  if (sseSource) sseSource.close();
  const sseUrl = `http://127.0.0.1:9001/api/v1/sessions/${currentSession}/stream`;
  sseSource = new EventSource(sseUrl);
  sseSource.onopen = () => {
    document.getElementById("status").textContent = "live (SSE)";
    document.getElementById("status").className = "status connected";
  };
  sseSource.addEventListener("graph_updated", (ev) => {
    fetchGraph();
  });
  sseSource.onerror = () => {
    document.getElementById("status").textContent = "SSE reconnecting…";
    document.getElementById("status").className = "status stale";
    sseSource.close();
    setTimeout(connectSSE, 3000);
  };
}

function switchSession() {
  const sel = document.getElementById("sessionSelect");
  currentSession = sel.value;
  const url = new URL(location);
  url.searchParams.set("session", currentSession);
  history.replaceState(null, "", url);
  nodesDS.clear(); edgesDS.clear();
  fetchGraph();
  connectSSE();
}

async function fetchGraph() {
  try {
    const r = await fetch(`/graph.json?session=${currentSession}&ts=${Date.now()}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const raw = await r.json();
    const g = raw.graph;
    const mtime = raw._mtime || "?";

    const newNodes = g.nodes.filter(n => !nodesDS.get(n.id));
    const newEdges = g.edges.filter(e => !edgesDS.get(e.id));
    const newNodeIds = new Set(newNodes.map(n => n.id));
    const newEdgeIds = new Set(newEdges.map(e => e.id || ""));

    const vNodes = g.nodes.map(n => {
      const nt = (n.node_type || n.type || "event").toLowerCase();
      const isNew = newNodeIds.has(n.id);
      return {
        id: n.id,
        label: (n.data?.title || n.id).slice(0, 30),
        color: { background: COLOR[nt] || COLOR.event, border: COLOR[nt] || COLOR.event },
        title: `${nt}: ${n.data?.title || n.id}\\n${n.data?.description || ""}`,
      };
    });
    const vEdges = g.edges.map((e, i) => {
      const eid = e.id || `e-${i}`;
      return {
        id: eid,
        from: e.source_id || e.source,
        to: e.target_id || e.target,
        label: e.edge_type || e.type || "",
      };
    });
    nodesDS.clear(); nodesDS.add(vNodes);
    edgesDS.clear(); edgesDS.add(vEdges);

    // ✨ Flash new nodes + edges: white glow blink 5 times over 3s
    if (newNodeIds.size > 0 || newEdgeIds.size > 0) {
      let blinks = 0;
      const maxBlinks = 5;
      const flashOn = () => {
        // Flash ON — bright white ring + enlarged
        for (const nid of newNodeIds) {
          const node = nodesDS.get(nid);
          if (!node) continue;
          nodesDS.update({ id: nid, color: { background: "#FFFFFF", border: "#FF0000" }, font: { size: 14, strokeColor: "#FF0000" } });
        }
        for (const eid of newEdgeIds) {
          edgesDS.update({ id: eid, color: { color: "#FF0000", highlight: "#FF0000" }, width: 4 });
        }
      };
      const flashOff = () => {
        // Restore original colors
        for (const nid of newNodeIds) {
          const rawNode = g.nodes.find(n => n.id === nid);
          if (!rawNode) continue;
          const nt = (rawNode.node_type || rawNode.type || "event").toLowerCase();
          nodesDS.update({ id: nid, color: { background: COLOR[nt] || COLOR.event, border: COLOR[nt] || COLOR.event }, font: { size: 11 } });
        }
        for (const eid of newEdgeIds) {
          edgesDS.update({ id: eid, color: {}, width: 1 });
        }
      };
      const blinkInterval = setInterval(() => {
        if (blinks >= maxBlinks) {
          clearInterval(blinkInterval);
          flashOff();
          return;
        }
        if (blinks % 2 === 0) { flashOn(); } else { flashOff(); }
        blinks++;
      }, 1000); // 1s × 5 blinks = 5s
    }

    document.getElementById("nodeCount").textContent = g.nodes.length;
    document.getElementById("edgeCount").textContent = g.edges.length;
    document.getElementById("conceptCount").textContent = g.nodes.filter(n => (n.node_type || n.type || "").toLowerCase() === "concept").length;
    document.getElementById("intentCount").textContent = g.nodes.filter(n => (n.node_type || n.type || "").toLowerCase() === "intent").length;
    document.getElementById("lastUpdate").textContent = mtime;
    document.getElementById("status").textContent = "live (SSE push)";
    document.getElementById("status").className = "status connected";
    if (newNodes.length || newEdges.length) {
      const msg = `[${new Date().toLocaleTimeString()}] ✨ +${newNodes.length} nodes, +${newEdges.length} edges (total ${g.nodes.length}/${g.edges.length})`;
      const log = document.getElementById("log");
      log.innerHTML = `<div>${msg}</div>` + log.innerHTML;
    }
  } catch (err) {
    document.getElementById("status").textContent = "error: " + err.message;
    document.getElementById("status").className = "status stale";
  }
}

// Set dropdown to current session
document.getElementById("sessionSelect").value = currentSession;

fetchGraph();
connectSSE();
</script>
</body></html>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse query string
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path.startswith("/graph.json"):
            session_id = params.get("session", [KNOWN_SESSIONS[0] if KNOWN_SESSIONS else ""])[0]
            graph_path = SESSIONS_DIR / session_id / "graph.json"
            try:
                if not graph_path.exists():
                    raise FileNotFoundError(f"graph.json not found for session {session_id}")
                stat = graph_path.stat()
                mtime = stat.st_mtime
                with open(graph_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                raw["_mtime"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                raw["_session"] = session_id
                body = json.dumps(raw, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f"[show_graph] served {session_id} nodes={len(raw.get('graph',{}).get('nodes',[]))} edges={len(raw.get('graph',{}).get('edges',[]))}", flush=True)
            except Exception as e:
                err = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)
            return

        if parsed.path == "/" or parsed.path == "/index.html":
            # Build session dropdown options
            options = ""
            default_session = params.get("session", [KNOWN_SESSIONS[0] if KNOWN_SESSIONS else ""])[0]
            for sid in KNOWN_SESSIONS:
                label = sid
                if sid == "7ea0a35153f64f0a":
                    label = f"{sid} (小柯)"
                elif sid == "86028fda52774069":
                    label = f"{sid} (小媒)"
                selected = " selected" if sid == default_session else ""
                options += f'<option value="{sid}"{selected}>{label}</option>\\n'

            html = HTML.replace("__SESSION_OPTIONS__", options).replace("__DEFAULT__", default_session)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def main():
    if not KNOWN_SESSIONS:
        print(f"[show_graph] no sessions found in {SESSIONS_DIR}")
        sys.exit(1)
    print(f"[show_graph] serving at http://127.0.0.1:{PORT}/", flush=True)
    print(f"[show_graph] sessions: {KNOWN_SESSIONS}", flush=True)
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/")).start()
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
