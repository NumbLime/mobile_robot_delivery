#!/usr/bin/env python3
"""Online checkpoint for the frozen D2 path geometry; final audit still uses bag."""

import argparse
import json
import math
import sys
from pathlib import Path


def events(path):
    raw = Path(path).read_text(encoding="utf-8")
    if not raw.endswith("\n"):
        raw = raw.rsplit("\n", 1)[0] if "\n" in raw else ""
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def points(result):
    return [(item["position"]["x"], item["position"]["y"])
            for item in result["path"]["poses"]]


def length(polyline):
    return sum(math.dist(a, b) for a, b in zip(polyline, polyline[1:]))


def section_y(polyline):
    values = []
    for a, b in zip(polyline, polyline[1:]):
        if min(a[0], b[0]) <= 0.6 <= max(a[0], b[0]) and abs(b[0] - a[0]) > 1e-12:
            values.append(a[1] + (0.6 - a[0]) * (b[1] - a[1]) / (b[0] - a[0]))
    if len(values) != 1:
        raise ValueError(f"expected one x=0.6 crossing, found {len(values)}")
    return values[0]


def point_segment_distance(p, a, b):
    ux, uy = b[0] - a[0], b[1] - a[1]
    squared = ux * ux + uy * uy
    fraction = max(0, min(1, ((p[0] - a[0]) * ux + (p[1] - a[1]) * uy) / squared)) if squared else 0
    return math.hypot(p[0] - a[0] - fraction * ux, p[1] - a[1] - fraction * uy)


def max_nearest(a, b):
    def directed(source, target):
        return max(min(point_segment_distance(p, u, v) for u, v in zip(target, target[1:]))
                   for p in source)
    return max(directed(a, b), directed(b, a))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--compare", required=True)
    parser.add_argument("--mode", choices=("obstacle", "recovery", "postclear"), required=True)
    parser.add_argument("--t0", type=float)
    parser.add_argument("--after-sim", type=float)
    args = parser.parse_args()
    base_results = [e for e in events(args.baseline) if e.get("event") == "goal_result" and e.get("status") == 4]
    if len(base_results) < 2:
        raise ValueError("baseline lacks two successful paths")
    baselines = [points(e) for e in base_results]
    comparable = events(args.compare)
    successful = [e for e in comparable if e.get("event") == "goal_result" and e.get("status") == 4]
    results = {e["index"]: e for e in successful}
    if len(results) != len(successful):
        raise ValueError("duplicate result index; split concatenated sampler runs")
    requests = [e for e in comparable if e.get("event") == "goal_request"]
    good_indices = []
    for request in requests:
        index = request["index"]
        result = results.get(index)
        if args.mode in ("recovery", "postclear"):
            if args.mode == "recovery":
                if args.t0 is None:
                    raise ValueError("recovery mode needs t0")
                if not (args.t0 <= request.get("sim_sec", -1) <= args.t0 + 60.0):
                    continue
                if result is None or result.get("sim_sec") is None or result["sim_sec"] > args.t0 + 60.0:
                    print("window_request", index, "no in-window successful result")
                    continue
            else:
                if args.after_sim is None:
                    raise ValueError("postclear mode needs after-sim")
                if request.get("sim_sec") is None or request["sim_sec"] < args.after_sim:
                    continue
                if result is None:
                    print("postclear_request", index, "no successful result")
                    continue
        elif result is None:
            raise ValueError(f"obstacle request {index} lacks successful result")
        candidate = points(result)
        metrics = [(section_y(candidate) - section_y(baseline),
                    length(candidate) - length(baseline),
                    max_nearest(baseline, candidate)) for baseline in baselines]
        passed = all((dy <= -0.30 and dl >= 0.20) if args.mode == "obstacle"
                     else (abs(dy) <= 0.10 and abs(dl) <= 0.10 and nearest <= 0.10)
                     for dy, dl, nearest in metrics)
        print("index", index, "result_sim", result.get("sim_sec"),
              "vs_each_baseline_dy_dlen_max_nearest",
              [tuple(round(value, 4) for value in row) for row in metrics], "PASS", passed)
        if passed:
            good_indices.append(index)
        elif args.mode == "obstacle":
            raise ValueError("obstacle path fails frozen detour thresholds")
    if args.mode == "obstacle":
        if len(good_indices) < 2:
            raise ValueError("fewer than two detour paths")
    elif not any(b == a + 1 for a, b in zip(good_indices, good_indices[1:])):
        raise ValueError("no two consecutive in-window recovery results")
    print("PASS: frozen D2", args.mode, "path checkpoint")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
