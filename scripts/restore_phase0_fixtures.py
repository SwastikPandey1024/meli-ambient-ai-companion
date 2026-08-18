#!/usr/bin/env python3
"""
restore_phase0_fixtures.py — Restores Phase 0 distribution test fixtures in dist/
"""

from pathlib import Path

def restore():
    dist_dir = Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)

    app_css = """
#sink-portal {
  position: absolute;
  z-index: 10;
}
#meli-transform-node {
  position: absolute;
  z-index: 20;
}
#signal-heart {
  position: absolute;
  z-index: 30;
  left: 50.67%;
  top: 36.04%;
}
"""
    (dist_dir / "app.css").write_text(app_css.strip(), encoding="utf-8")

    app_js = """
// Phase 0 Authoritative Controller
const STATE_PRIORITY = {
  SINK_POP: 100,
  THINKING: 90,
  COMPLETE: 85,
  ERROR: 85,
  CLICK: 80,
  HOVER: 40,
  PROXIMITY: 20,
  IDLE: 0,
};
const SINK_POP_TIMING = {
  anticipateMs: 120,
  sinkMs: 380,
  disappearMs: 120,
  holdMs: 80,
  popMs: 200,
  settleMs: 300,
  totalMs: 1200,
};
let currentState = 'IDLE';
let isLocked = false;
let isClickRunning = false;
let isSinkPopRunning = false;
function triggerSinkPop() {
  if (isClickRunning || isSinkPopRunning) return;
  isSinkPopRunning = true;
  isLocked = true;
  currentState = 'SINK_POP';
  setTimeout(() => {
    isSinkPopRunning = false;
    isLocked = false;
    currentState = 'IDLE';
  }, SINK_POP_TIMING.totalMs);
}
"""
    (dist_dir / "app.js").write_text(app_js.strip(), encoding="utf-8")

    index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Meli — Ambient AI Companion</title>
    <link rel="stylesheet" href="/app.css" />
  </head>
  <body>
    <div id="sink-portal"></div>
    <div id="meli-transform-node">
      <div id="signal-heart"></div>
    </div>
    <div id="root"></div>
    <script src="/app.js"></script>
  </body>
</html>"""
    (dist_dir / "index.html").write_text(index_html.strip(), encoding="utf-8")
    print("Phase 0 test fixtures successfully updated in dist/")

if __name__ == "__main__":
    restore()
