#!/usr/bin/env python3
"""Validate the actual JSONL fields written by the frozen-input plan_sampler.py."""

import argparse
import json
import sys
from pathlib import Path


def fixed(request):
    if request.get("use_start") is not True or request.get("planner_id") != "":
        return False
    for key, x, y in (("start", 1.4, -1.0), ("goal", -0.2, -1.8)):
        item = request.get(key, {})
        if item.get("header", {}).get("frame_id") != "map":
            return False
        if item.get("position") != {"x": x, "y": y, "z": 0.0}:
            return False
        if item.get("orientation") != {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}:
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--min-results", type=int, default=2)
    parser.add_argument("--ongoing", action="store_true")
    parser.add_argument("--require-duration", action="store_true")
    parser.add_argument("--t0", type=float)
    parser.add_argument("--after-sim", type=float)
    parser.add_argument("--min-after-results", type=int, default=0)
    args = parser.parse_args()
    raw = Path(args.file).read_text(encoding="utf-8")
    if args.ongoing and not raw.endswith("\n"):
        raw = raw.rsplit("\n", 1)[0] if "\n" in raw else ""
    events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not events or events[0].get("event") != "sampler_start":
        raise ValueError("missing first sampler_start")
    if sum(e.get("event") == "sampler_start" for e in events) != 1:
        raise ValueError("expected exactly one sampler_start; preserve concatenated runs separately")
    start = events[0]
    if not fixed(start.get("request", {})):
        raise ValueError("sampler_start fixed request differs from D2")
    actual_args = start.get("args", {})
    if args.require_duration and (actual_args.get("start_sim") is None or actual_args.get("duration_sim") is None):
        raise ValueError("continuous sampler lacks explicit start_sim/duration_sim")
    requests = {}
    responses = {}
    results = {}
    fatal = []
    ends = []
    for event in events:
        kind = event.get("event")
        if "wall_unix" not in event or "sim_sec" not in event:
            raise ValueError("event lacks actual wall_unix/sim_sec fields")
        if kind == "goal_request":
            idx = event.get("index")
            if idx in requests or not fixed(event.get("request", {})):
                raise ValueError("duplicate index or changed goal_request")
            requests[idx] = event
        elif kind == "goal_response":
            idx = event.get("index")
            if idx in responses or not event.get("accepted") or not event.get("uuid"):
                raise ValueError("duplicate/rejected/missing-UUID goal_response")
            responses[idx] = event
        elif kind == "goal_result":
            idx = event.get("index")
            if idx in results or event.get("status") != 4 or not event.get("path", {}).get("poses"):
                raise ValueError("duplicate/failed/empty goal_result")
            results[idx] = event
        elif kind == "fatal":
            fatal.append(event)
        elif kind == "sampler_end":
            ends.append(event)
    if fatal:
        raise ValueError("fatal event: " + ", ".join(str(e.get("reason")) for e in fatal))
    if len(results) < args.min_results:
        raise ValueError(f"only {len(results)} successful results, need {args.min_results}")
    for idx, result in results.items():
        if idx not in requests or idx not in responses or responses[idx]["uuid"] != result.get("uuid"):
            raise ValueError(f"request/response/result UUID or index mismatch at {idx}")
    if len({e["uuid"] for e in responses.values()}) != len(responses):
        raise ValueError("duplicate UUID")
    if args.ongoing:
        if len(ends) > 1:
            raise ValueError("multiple sampler_end events")
    else:
        if len(ends) != 1 or ends[0].get("count") != len(results):
            raise ValueError("missing/incorrect sampler_end count")
        if set(requests) != set(responses) or set(requests) != set(results):
            raise ValueError("incomplete request/response/result sequence")
        if ends[0].get("deadline_reached"):
            raise ValueError("sampler wall deadline reached")
    in_window = []
    if args.t0 is not None:
        in_window = [e for e in results.values() if e.get("sim_sec") is not None
                     and args.t0 <= e["sim_sec"] <= args.t0 + 60.0]
    after = []
    if args.after_sim is not None:
        after = [e for e in results.values() if e.get("sim_sec") is not None
                 and e["sim_sec"] >= args.after_sim]
        if len(after) < args.min_after_results:
            raise ValueError(f"only {len(after)} results after {args.after_sim}, need {args.min_after_results}")
    print("PASS fixed schema, status, UUID and result paths")
    print("requests", len(requests), "responses", len(responses), "results", len(results))
    print("args", json.dumps(actual_args, sort_keys=True))
    if args.t0 is not None:
        print("original_window_successful_results", len(in_window),
              "sim_secs", [round(e["sim_sec"], 3) for e in sorted(in_window, key=lambda e: e["sim_sec"])])
    if args.after_sim is not None:
        print("after_sim_successful_results", len(after),
              "sim_secs", [round(e["sim_sec"], 3) for e in sorted(after, key=lambda e: e["sim_sec"])])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
