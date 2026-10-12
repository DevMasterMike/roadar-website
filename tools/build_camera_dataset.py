#!/usr/bin/env python3
"""Build Roadar's nightly US camera file from OpenStreetMap data.

Every license-plate reader (ALPR), fixed speed camera and red-light camera in the US (and across the
Canadian and Mexican borders), as one small compressed file the Roadar app downloads once a day. Route
planning then looks cameras up on the phone instead of waiting on a busy public Overpass server.

    python3 tools/build_camera_dataset.py OUT_FILE

Sources (all OpenStreetMap, (c) OpenStreetMap contributors, ODbL):
  * ALPRs: DeFlock's published region tiles (cdn.deflock.me/regions), the daily cache behind the DeFlock
    map, built from man_made=surveillance + surveillance:type=ALPR. One polite fetch per region a night.
  * Speed and red-light cameras: one Overpass query (highway=speed_camera,
    enforcement=red_light|traffic_signals). If Overpass is down, last night's ones are kept.

Output: raw-DEFLATE-compressed JSON (the app inflates it with NSData's zlib decompressor):
    {"v": 1, "generated": "<ISO time>", "count": N,
     "cameras": [[node_id, lat, lon, "a"|"s"|"r", "direction" or null], ...]}

Classification matches SeededCamera.parse in the app. The build fails (publishing nothing, so the app
keeps yesterday's file) if the ALPR count looks wrong.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone

USER_AGENT = "Roadar camera dataset builder (https://devmastermike.github.io/roadar-website/)"
DEFLOCK_INDEX = "https://cdn.deflock.me/regions/index.json"
PREVIOUS = "https://github.com/DevMasterMike/roadar-website/releases/download/camera-data/cameras-v1.deflate"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
# The US with the border regions around it (Alaska and Hawaii included).
SOUTH, NORTH, WEST, EAST = 15.0, 72.0, -180.0, -60.0
MIN_ALPR = 50_000   # the US had ~128k mapped ALPRs in 2026; far fewer means a broken source


def get(url, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def retry(fn, attempts=4, wait=8):
    last = None
    for i in range(attempts):
        try:
            return fn(i)
        except Exception as e:
            last = e
            time.sleep(wait * (i + 1))
    raise RuntimeError(f"failed after {attempts} tries: {last}")


def in_area(lat, lon):
    return SOUTH <= lat <= NORTH and WEST <= lon <= EAST


def direction(tags):
    return tags.get("direction") or tags.get("camera:direction")


def alprs():
    """Every ALPR in the area, from DeFlock's region tiles."""
    index = json.loads(retry(lambda _: get(DEFLOCK_INDEX)))
    size, template = index["tile_size_degrees"], index["tile_url"]
    out = {}
    for region in index["regions"]:
        lat, lon = (int(v) for v in region.split("/"))
        if lat + size < SOUTH or lat > NORTH or lon + size < WEST or lon > EAST:
            continue
        url = template.replace("{lat}/{lon}", region)
        nodes = json.loads(retry(lambda _: get(url)))
        kept = 0
        for n in nodes:
            if in_area(n["lat"], n["lon"]):
                out[n["id"]] = [n["id"], round(n["lat"], 6), round(n["lon"], 6), "a", direction(n.get("tags", {}))]
                kept += 1
        print(f"DeFlock region {region}: {kept} ALPRs", flush=True)
        time.sleep(1)
    return out


def enforcement_cameras():
    """Speed and red-light cameras from Overpass: one query for the whole area (they're sparse, ~2.5k)."""
    box = f"({SOUTH},{WEST},{NORTH},{EAST})"
    q = (f'[out:json][timeout:180];(node["highway"="speed_camera"]{box};'
         f'node["enforcement"~"red_light|traffic_signals",i]{box};);out body;')
    body = urllib.parse.urlencode({"data": q}).encode()
    data = json.loads(retry(lambda i: get(OVERPASS[i % len(OVERPASS)], data=body, timeout=200), attempts=6))
    out = {}
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        enforcement = (tags.get("enforcement") or "").lower()
        if "red_light" in enforcement or "traffic_signals" in enforcement:
            kind = "r"
        elif tags.get("highway") == "speed_camera":
            kind = "s"
        else:
            continue
        out[el["id"]] = [el["id"], round(el["lat"], 6), round(el["lon"], 6), kind, direction(tags)]
    print(f"Overpass: {len(out)} speed / red-light cameras", flush=True)
    return out


def previous_enforcement_cameras():
    """Last night's speed and red-light cameras, for a night Overpass is down."""
    doc = json.loads(zlib.decompress(get(PREVIOUS), -15))
    kept = {row[0]: row for row in doc["cameras"] if row[3] in ("s", "r")}
    print(f"Overpass unavailable: keeping last night's {len(kept)} speed / red-light cameras", flush=True)
    return kept


def main(out_path):
    cameras = alprs()
    alpr_count = len(cameras)
    try:
        others = enforcement_cameras()
    except Exception as e:
        print(f"Overpass failed: {e}", flush=True)
        others = previous_enforcement_cameras()
    for node_id, row in others.items():
        cameras[node_id] = row   # a speed / red-light tag wins over ALPR on a combined device, as in the app
    print(f"total {len(cameras)} cameras ({alpr_count} ALPR)", flush=True)
    if alpr_count < MIN_ALPR:
        raise SystemExit(f"only {alpr_count} ALPR cameras - refusing to publish a partial map")
    rows = sorted(cameras.values(), key=lambda c: c[0])
    doc = {"v": 1, "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "count": len(rows), "cameras": rows}
    raw = json.dumps(doc, separators=(",", ":")).encode()
    deflater = zlib.compressobj(9, zlib.DEFLATED, -15)   # raw DEFLATE, what NSData's .zlib reads
    packed = deflater.compress(raw) + deflater.flush()
    with open(out_path, "wb") as f:
        f.write(packed)
    print(f"wrote {out_path}: {len(raw) / 1e6:.1f} MB json, {len(packed) / 1e6:.1f} MB compressed", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cameras-v1.deflate")
