#!/usr/bin/env python3
"""Read-only live costmap snapshots and D2 window gate for operator-run V0.3.

This helper never calls a ROS service, changes Gazebo state, or opens a bag.
It writes only the operator-selected JSON/JSONL evidence files.
"""

import argparse
import ast
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path


def write_jsonl(path, item):
    with path.open("a", encoding="utf-8", buffering=1) as stream:
        stream.write(json.dumps(item, separators=(",", ":")) + "\n")


def sec(stamp):
    return stamp.sec + stamp.nanosec / 1e9


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def compose(a, b):
    x, y, theta = a
    u, v, phi = b
    return (x + math.cos(theta) * u - math.sin(theta) * v,
            y + math.sin(theta) * u + math.cos(theta) * v,
            theta + phi)


def inverse(a):
    x, y, theta = a
    return (-math.cos(theta) * x - math.sin(theta) * y,
            math.sin(theta) * x - math.cos(theta) * y, -theta)


def model_pose(name):
    before = time.time()
    result = subprocess.run(["gz", "model", "-m", name, "-p"],
                            capture_output=True, text=True, timeout=10, check=False)
    after = time.time()
    fields = result.stdout.strip().split()
    if len(fields) != 6:
        raise RuntimeError(f"gz model {name!r} invalid pose; rc={result.returncode}, "
                           f"stdout={result.stdout!r}, stderr={result.stderr!r}")
    values = [float(x) for x in fields]
    if not all(math.isfinite(x) for x in values):
        raise RuntimeError(f"gz model {name!r} returned non-finite pose")
    return {"name": name, "pose_xyz_rpy": values, "wall_before": before,
            "wall_after": after, "returncode": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def locate(args):
    import rclpy
    from rclpy.time import Time
    from tf2_ros import Buffer, TransformListener

    rclpy.init()
    node = rclpy.create_node("v03_costmap_alignment")
    buffer = Buffer()
    listener = TransformListener(buffer, node)
    try:
        deadline = time.monotonic() + args.timeout_wall
        while not buffer.can_transform("map", "base_footprint", Time()) and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if not buffer.can_transform("map", "base_footprint", Time()):
            raise RuntimeError("map -> base_footprint TF unavailable")
        robot = model_pose("delivery_robot")
        box = model_pose("c3_temporary_box")
        if any(abs(a - b) > 0.02 for a, b in zip(box["pose_xyz_rpy"][:3], (0.6, -1.4, 0.25))) or abs(box["pose_xyz_rpy"][5]) > 0.02:
            raise RuntimeError("box pose differs from frozen D2 input")
        tf_before = time.time()
        transform = buffer.lookup_transform("map", "base_footprint", Time())
        tf_after = time.time()
        map_base = (transform.transform.translation.x,
                    transform.transform.translation.y,
                    yaw(transform.transform.rotation))
        world_base = (robot["pose_xyz_rpy"][0], robot["pose_xyz_rpy"][1],
                      robot["pose_xyz_rpy"][5])
        world_map = compose(map_base, inverse(world_base))
        box_map = compose(world_map, (box["pose_xyz_rpy"][0],
                                      box["pose_xyz_rpy"][1],
                                      box["pose_xyz_rpy"][5]))
        output = {"robot": robot, "box": box, "tf_header_sim_sec": sec(transform.header.stamp),
                  "tf_wall_before": tf_before, "tf_wall_after": tf_after,
                  "map_base_xyyaw": map_base, "world_to_map_xyyaw": world_map,
                  "box_map_xyyaw": box_map,
                  "limit": "gz pose has no simulation header; this is near-time alignment"}
        Path(args.out).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        print("box_map_xyyaw", *[round(x, 5) for x in box_map])
    finally:
        node.destroy_node()
        rclpy.shutdown()


def clock_once(args):
    import rclpy
    from rclpy.qos import QoSProfile, ReliabilityPolicy
    from rosgraph_msgs.msg import Clock

    rclpy.init()
    node = rclpy.create_node("v03_clock_once")
    samples = []
    node.create_subscription(Clock, "/clock", lambda msg: samples.append(sec(msg.clock)),
                             QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT))
    try:
        deadline = time.monotonic() + args.timeout_wall
        while not samples and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if not samples:
            raise RuntimeError("/clock unavailable")
        print(f"{samples[-1]:.9f}")
    finally:
        node.destroy_node()
        rclpy.shutdown()


def model_list_stamp(args):
    raw = Path(args.file).read_text(encoding="utf-8")
    match = re.search(r"GetModelList_Response\(header=.*?stamp=builtin_interfaces\.msg\.Time\(sec=(\d+), nanosec=(\d+)\).*?model_names=(\[[^\]]*\]).*?success=True", raw, re.S)
    if not match:
        raise RuntimeError("successful GetModelList response with header stamp not found")
    names = ast.literal_eval(match.group(3))
    if not isinstance(names, list):
        raise RuntimeError("model_names is not a list")
    present = "c3_temporary_box" in names
    if present != (args.expect == "present"):
        raise RuntimeError(f"box presence={present}, expected={args.expect}")
    print(f"{int(match.group(1)) + int(match.group(2)) / 1e9:.9f}")


def capture(args):
    import rclpy
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
    from nav_msgs.msg import OccupancyGrid
    from rosgraph_msgs.msg import Clock

    path = Path(args.out)
    if path.exists():
        raise RuntimeError(f"refusing to append or overwrite: {path}")
    rclpy.init()
    node = rclpy.create_node("v03_costmap_capture")
    state = {"clock": None, "count": 0, "first_clock": None}
    qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT,
                     durability=DurabilityPolicy.VOLATILE)

    def on_clock(msg):
        value = sec(msg.clock)
        if state["clock"] is not None and value + 0.01 < state["clock"]:
            raise RuntimeError("/clock moved backwards during capture")
        state["clock"] = value
        if state["first_clock"] is None:
            state["first_clock"] = value

    def on_map(msg):
        if state["clock"] is None:
            return
        if msg.header.frame_id != "map":
            raise RuntimeError(f"unexpected global costmap frame: {msg.header.frame_id}")
        info = msg.info
        write_jsonl(path, {"event": "map", "wall_unix": time.time(),
                           "stamp_sim": sec(msg.header.stamp),
                           "clock_sim": state["clock"], "frame": msg.header.frame_id,
                           "width": info.width, "height": info.height,
                           "resolution": info.resolution,
                           "origin": [info.origin.position.x, info.origin.position.y],
                           "data": list(msg.data)})
        state["count"] += 1

    node.create_subscription(Clock, "/clock", on_clock, qos)
    node.create_subscription(OccupancyGrid, "/global_costmap/costmap", on_map, qos)
    start = time.monotonic()
    try:
        while time.monotonic() - start < args.timeout_wall:
            rclpy.spin_once(node, timeout_sec=0.1)
            if args.count is not None and state["count"] >= args.count:
                break
            if args.until_sim is not None and state["clock"] is not None and state["clock"] >= args.until_sim:
                break
        else:
            raise RuntimeError("wall timeout before capture condition")
        if state["count"] < 3:
            raise RuntimeError(f"only {state['count']} maps captured")
        if state["first_clock"] is None or state["clock"] <= state["first_clock"]:
            raise RuntimeError("/clock did not advance")
        print(f"maps={state['count']} first_clock={state['first_clock']:.3f} "
              f"last_clock={state['clock']:.3f} out={path}")
    finally:
        node.destroy_node()
        rclpy.shutdown()


def load_maps(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    maps = [row for row in rows if row.get("event") == "map"]
    if not maps:
        raise RuntimeError(f"no maps: {path}")
    return maps


def grid_value(m, x, y):
    gx = math.floor((x - m["origin"][0]) / m["resolution"])
    gy = math.floor((y - m["origin"][1]) / m["resolution"])
    if not (0 <= gx < m["width"] and 0 <= gy < m["height"]):
        raise RuntimeError("target cell outside map")
    return m["data"][gy * m["width"] + gx]


def marked_targets(baseline_path, with_box_path, alignment_path):
    base = load_maps(baseline_path)[-1]
    box = load_maps(with_box_path)[-1]
    alignment = json.loads(Path(alignment_path).read_text(encoding="utf-8"))
    cx, cy, theta = alignment["box_map_xyyaw"]
    target = []
    for gy in range(box["height"]):
        y = box["origin"][1] + (gy + 0.5) * box["resolution"]
        for gx in range(box["width"]):
            x = box["origin"][0] + (gx + 0.5) * box["resolution"]
            dx, dy = x - cx, y - cy
            u = math.cos(theta) * dx + math.sin(theta) * dy
            v = -math.sin(theta) * dx + math.cos(theta) * dy
            distance = math.hypot(max(abs(u) - 0.175, 0), max(abs(v) - 0.175, 0))
            if distance <= 0.55 and grid_value(base, x, y) <= 10 and grid_value(box, x, y) >= 90:
                target.append((x, y))
    if not target:
        raise RuntimeError("no baseline<=10 / with-box>=90 target cells")
    return target


def mark(args):
    target = marked_targets(args.baseline, args.with_box, args.alignment)
    print("PASS: baseline<=10 and with-box>=90 target cells", len(target))


def gate(args):
    target = marked_targets(args.baseline, args.with_box, args.alignment)
    window = load_maps(args.window)
    if args.period == "original":
        window = [m for m in window if args.t0 <= m["stamp_sim"] <= args.t0 + 60.0]
    if len(window) < 3:
        raise RuntimeError("fewer than three maps in original 60 s window")
    stamps = [m["stamp_sim"] for m in window]
    if any(b <= a for a, b in zip(stamps, stamps[1:])):
        raise RuntimeError("costmap header stamps did not advance")
    if args.period == "original" and args.t0 + 60.0 - stamps[-1] > 3.0:
        raise RuntimeError("last map is too far before original window deadline")
    summaries = []
    for m in window:
        values = [grid_value(m, x, y) for x, y in target]
        summaries.append({"stamp_sim": m["stamp_sim"], "max_target_cost": max(values),
                          "all_le10": all(v <= 10 for v in values),
                          "ge90_count": sum(v >= 90 for v in values),
                          "ge90_indices": {i for i, v in enumerate(values) if v >= 90}})
    last = summaries[-3:]
    residual = set.intersection(*(row["ge90_indices"] for row in last))
    cleared = any(all(row["all_le10"] for row in summaries[i:i + 3])
                  for i in range(len(summaries) - 2))
    if args.period == "original":
        print("original_window", round(args.t0, 3), round(args.t0 + 60.0, 3))
    else:
        print("current_preclear_maps")
    print("window_maps", len(window), "last_three_stamps", [round(row["stamp_sim"], 3) for row in last])
    print("target_cells", len(target), "last_three_max_cost", [row["max_target_cost"] for row in last])
    print("cleared_three_maps_in_window", cleared)
    print("same_target_cells_ge90_on_last_three", len(residual))
    if len(residual):
        print("GATE: residual condition met; save pre-clear map and plan before any explicit clear")
    else:
        print("GATE: no residual condition; do not call clear service")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("locate")
    one.add_argument("--out", required=True)
    one.add_argument("--timeout-wall", type=float, default=20)
    zero = sub.add_parser("clock")
    zero.add_argument("--timeout-wall", type=float, default=10)
    models = sub.add_parser("model-list-stamp")
    models.add_argument("--file", required=True)
    models.add_argument("--expect", required=True, choices=("present", "absent"))
    two = sub.add_parser("capture")
    two.add_argument("--out", required=True)
    group = two.add_mutually_exclusive_group(required=True)
    group.add_argument("--count", type=int)
    group.add_argument("--until-sim", type=float)
    two.add_argument("--timeout-wall", type=float, default=180)
    three = sub.add_parser("gate")
    marker = sub.add_parser("mark")
    marker.add_argument("--baseline", required=True)
    marker.add_argument("--with-box", required=True)
    marker.add_argument("--alignment", required=True)
    three.add_argument("--baseline", required=True)
    three.add_argument("--with-box", required=True)
    three.add_argument("--window", required=True)
    three.add_argument("--alignment", required=True)
    three.add_argument("--t0", type=float, required=True)
    three.add_argument("--period", choices=("original", "current"), default="original")
    args = parser.parse_args()
    try:
        {"locate": locate, "clock": clock_once, "model-list-stamp": model_list_stamp,
         "capture": capture, "gate": gate, "mark": mark}[args.command](args)
    except Exception as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
