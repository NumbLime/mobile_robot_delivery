#!/usr/bin/env python3
"""Render V0.3 D7 figures from a stopped D5 bag and its plan JSONL files.

Offline only: opens SQLite read-only, never calls ROS services or starts nodes.
Run after sourcing ROS 2 Humble so message deserialization is available.
"""

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/v03_d7_matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon
from nav_msgs.msg import OccupancyGrid, Path as NavPath
from rclpy.serialization import deserialize_message
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import LaserScan

from v03_compare_paths import length, max_nearest, points, section_y
from v03_live_costmap import marked_targets


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def sim_stamp(message):
    stamp = message.header.stamp
    return stamp.sec + stamp.nanosec / 1e9


def cost(message, x, y):
    info = message.info
    col = math.floor((x - info.origin.position.x) / info.resolution)
    row = math.floor((y - info.origin.position.y) / info.resolution)
    if not (0 <= col < info.width and 0 <= row < info.height):
        raise ValueError("target point outside a global costmap")
    return message.data[row * info.width + col]


def results(path):
    events = [json.loads(line) for line in path.read_text().splitlines() if line]
    return [event for event in events
            if event.get("event") == "goal_result" and event.get("status") == 4]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir.resolve(strict=True)
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    db = run / "bag/recovery/recovery_0.db3"
    metadata = run / "bag/recovery/metadata.yaml"
    if not db.is_file() or not metadata.is_file():
        raise ValueError("stopped D5 bag and metadata are required")
    t0 = float((run / "t0_first_absence_sim.txt").read_text())
    deadline = float((run / "deadline_sim.txt").read_text())
    if not math.isclose(deadline - t0, 60.0, abs_tol=1e-8):
        raise ValueError("original D2 window is not 60 simulation seconds")
    model_after = (run / "model_list_after_delete.log").read_text()
    match = re.search(r"stamp=builtin_interfaces\.msg\.Time\(sec=(\d+), nanosec=(\d+)\)",
                      model_after)
    if not match or "'c3_temporary_box'" in model_after:
        raise ValueError("first absent model-list response missing")
    model_stamp = int(match.group(1)) + int(match.group(2)) / 1e9
    if not math.isclose(model_stamp, t0, abs_tol=1e-8):
        raise ValueError("t0 differs from first absent model-list stamp")

    target = marked_targets(run / "baseline_maps.jsonl",
                            run / "with_box_maps.jsonl", run / "box_alignment.json")
    if len(target) != 179:
        raise ValueError(f"D5 accepted target set changed: {len(target)}")
    baseline = results(run / "plans_baseline.jsonl")
    with_box = results(run / "plans_with_box.jsonl")
    predelete = results(run / "plans_predelete.jsonl")
    continuous = results(run / "plans_continuous.jsonl")
    if [len(baseline), len(with_box), len(predelete), len(continuous)] != [2, 2, 1, 59]:
        raise ValueError("plan result counts differ from the accepted D5 run")
    base_path = points(baseline[0])
    if any(max_nearest(base_path, points(item)) > 1e-6 for item in baseline):
        raise ValueError("baseline paths are not identical")

    connection = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    try:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        topics = dict(connection.execute("SELECT name,id FROM topics"))
        for name in ("/clock", "/scan", "/global_costmap/costmap", "/plan"):
            if name not in topics:
                raise ValueError(f"missing bag topic: {name}")
        maps = []
        for (blob,) in connection.execute(
                "SELECT data FROM messages WHERE topic_id=? ORDER BY timestamp",
                (topics["/global_costmap/costmap"],)):
            message = deserialize_message(blob, OccupancyGrid)
            maps.append((sim_stamp(message), message))
        scans = []
        for (blob,) in connection.execute(
                "SELECT data FROM messages WHERE topic_id=? ORDER BY timestamp",
                (topics["/scan"],)):
            message = deserialize_message(blob, LaserScan)
            stamp = sim_stamp(message)
            if t0 - 30 <= stamp <= deadline + 1:
                ranges = [value for index, value in enumerate(message.ranges)
                          if -1.18 <= message.angle_min + index * message.angle_increment <= -0.85
                          and math.isfinite(value)]
                scans.append((stamp, min(ranges)))
        clocks = []
        for wall_ns, blob in connection.execute(
                "SELECT timestamp,data FROM messages WHERE topic_id=? ORDER BY timestamp",
                (topics["/clock"],)):
            message = deserialize_message(blob, Clock)
            clocks.append((wall_ns / 1e9,
                           message.clock.sec + message.clock.nanosec / 1e9))
        bag_paths = [deserialize_message(blob, NavPath)
                     for (blob,) in connection.execute(
                         "SELECT data FROM messages WHERE topic_id=? ORDER BY timestamp",
                         (topics["/plan"],))]
    finally:
        connection.close()

    all_results = baseline + with_box + predelete + continuous
    if len(bag_paths) != len(all_results):
        raise ValueError("bag /plan and JSONL result counts differ")
    for result, path in zip(all_results, bag_paths):
        coordinates = points(result)
        if len(coordinates) != len(path.poses):
            raise ValueError("bag and JSONL path lengths differ")
        if any(abs(x - pose.pose.position.x) > 1e-6 or
               abs(y - pose.pose.position.y) > 1e-6
               for (x, y), pose in zip(coordinates, path.poses)):
            raise ValueError("bag and JSONL path geometry differ")

    map_series = []
    for stamp, message in maps:
        if t0 - 30 <= stamp <= deadline:
            map_series.append((stamp, max(cost(message, x, y) for x, y in target)))
    window = [(stamp, max(cost(message, x, y) for x, y in target))
              for stamp, message in maps if t0 <= stamp <= deadline]
    if len(window) < 3 or window[-3:] != [(stamp, 0) for stamp, _ in window[-3:]]:
        raise ValueError("original-window last three maps are not zero")
    third_clear_stamp = next(
        window[index + 2][0] for index in range(len(window) - 2)
        if all(value <= 10 for _, value in window[index:index + 3]))
    recovered = next((item for item in continuous
                      if t0 <= item["sim_sec"] <= deadline
                      and item["sim_sec"] > third_clear_stamp
                      and abs(section_y(points(item)) - section_y(base_path)) <= .10
                      and abs(length(points(item)) - length(base_path)) <= .10
                      and max_nearest(points(item), base_path) <= .10), None)
    if recovered is None:
        raise ValueError("no qualifying recovery plan after three clear maps")

    def sim_near_wall(filename):
        wall = float((run / filename).read_text())
        received, sim = min(clocks, key=lambda row: abs(row[0] - wall))
        if abs(received - wall) > .2:
            raise ValueError("bag /clock too far from a service wall time")
        return sim

    delete_before = sim_near_wall("delete_wall_before.txt")
    delete_after = sim_near_wall("delete_wall_after.txt")

    # Figure 1: original deletion window, all x values are simulation time relative to t0.
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 120})
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(10, 7),
                             constrained_layout=True)
    fig.suptitle("V0.3 D5 | Deletion and recovery (offline evidence)", fontsize=14)
    axes[0].plot([stamp - t0 for stamp, _ in scans], [value for _, value in scans],
                 color="#2271b2", lw=1.3)
    axes[0].set_ylabel("Scan sector min (m)")
    axes[0].set_ylim(0, 4)
    axes[0].text(.99, .93, "Laser angles -1.18 to -0.85 rad", ha="right",
                 va="top", transform=axes[0].transAxes, fontsize=8)
    axes[1].step([stamp - t0 for stamp, _ in map_series],
                 [value for _, value in map_series], where="post",
                 color="#d55e00", lw=1.7)
    axes[1].set_ylabel("Max target cost")
    axes[1].set_ylim(-5, 110)
    near_results = [item for item in continuous if t0 - 30 <= item["sim_sec"] <= deadline]
    axes[2].plot([item["sim_sec"] - t0 for item in near_results],
                 [section_y(points(item)) - section_y(base_path) for item in near_results],
                 "o-", color="#009e73", lw=1.2, ms=3.5)
    axes[2].axhspan(-.10, .10, color="#009e73", alpha=.1)
    axes[2].axhline(0, color="#666666", lw=.7)
    axes[2].set_ylabel("Path delta y at x=0.6 (m)")
    axes[2].set_xlabel("Simulation seconds from first confirmed box absence (t0)")
    for axis in axes:
        axis.axvspan(delete_before - t0, delete_after - t0,
                     color="#999999", alpha=.2)
        axis.axvline(0, color="#333333", ls="--", lw=1)
        axis.axvline(60, color="#333333", ls=":", lw=1)
        axis.grid(alpha=.2)
        axis.set_xlim(-30, 61)
    axes[0].text(delete_before - t0, 3.65, "first delete call", fontsize=8,
                 ha="left", va="top")
    axes[2].text(0, -.78, "t0", ha="left", va="bottom", fontsize=8)
    axes[2].text(60, -.78, "60 s", ha="right", va="bottom", fontsize=8)
    fig.savefig(out / "v03_d7_deletion_timeline.png", dpi=190)
    fig.savefig(out / "v03_d7_deletion_timeline.svg")
    plt.close(fig)

    # Figure 2: same map coordinates and same requested start/goal in three phases.
    stages = [("No box", baseline[0], "#2271b2"),
              ("Box present", with_box[0], "#d55e00"),
              ("After removal", recovered, "#009e73")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.8), sharex=True, sharey=True,
                             constrained_layout=True)
    fig.suptitle("V0.3 D5 | Same map start and goal in three phases", fontsize=14)
    image = None
    for axis, (label, result, color) in zip(axes, stages):
        stamp, message = min(maps, key=lambda row: abs(row[0] - result["sim_sec"]))
        info = message.info
        grid = np.asarray(message.data, dtype=float).reshape(info.height, info.width)
        grid = np.ma.masked_less(grid, 0)
        cmap = plt.get_cmap("YlOrRd").copy()
        cmap.set_bad("#dddddd")
        image = axis.imshow(grid, origin="lower", cmap=cmap, norm=Normalize(0, 100),
                            extent=(info.origin.position.x,
                                    info.origin.position.x + info.width * info.resolution,
                                    info.origin.position.y,
                                    info.origin.position.y + info.height * info.resolution),
                            interpolation="nearest")
        xy = points(result)
        axis.plot([p[0] for p in xy], [p[1] for p in xy],
                  color=color, lw=2.4, label="observed plan")
        if label == "Box present":
            axis.plot([p[0] for p in base_path], [p[1] for p in base_path],
                      color="#2271b2", ls="--", lw=1.3, label="no-box reference")
            box = json.loads((run / "box_alignment.json").read_text())["box_map_xyyaw"]
            corners = []
            for u, v in ((-.175, -.175), (.175, -.175), (.175, .175), (-.175, .175)):
                corners.append((box[0] + math.cos(box[2]) * u - math.sin(box[2]) * v,
                                box[1] + math.sin(box[2]) * u + math.cos(box[2]) * v))
            axis.add_patch(Polygon(corners, closed=True, fill=False,
                                   ls=":", lw=1.2, ec="#333333"))
        axis.scatter([1.4], [-1.0], marker="o", s=48, c="white", edgecolors="#222222", zorder=5)
        axis.scatter([-.2], [-1.8], marker="*", s=95, c="white", edgecolors="#222222", zorder=5)
        axis.annotate("S", (1.4, -1.0), xytext=(5, 5), textcoords="offset points", fontsize=9)
        axis.annotate("G", (-.2, -1.8), xytext=(5, 5), textcoords="offset points", fontsize=9)
        axis.set_title(f"{label}\nmap {stamp:.1f} s | plan {result['sim_sec']:.1f} s")
        axis.set_xlim(-.5, 1.6)
        axis.set_ylim(-2.6, -.55)
        axis.set_aspect("equal")
        axis.set_xlabel("map x (m)")
        axis.grid(alpha=.12)
        axis.legend(loc="lower left", fontsize=7, framealpha=.9)
    axes[0].set_ylabel("map y (m)")
    fig.colorbar(image, ax=axes, shrink=.76, label="Published global costmap cost")
    fig.savefig(out / "v03_d7_maps_paths.png", dpi=190)
    fig.savefig(out / "v03_d7_maps_paths.svg")
    plt.close(fig)

    provenance = {
        "kind": "offline rendering, not Gazebo/RViz footage",
        "run_dir": str(run),
        "bag": str(db),
        "bag_sha256": digest(db),
        "plan_jsonl_sha256": {name: digest(run / name) for name in
                              ("plans_baseline.jsonl", "plans_with_box.jsonl",
                               "plans_predelete.jsonl", "plans_continuous.jsonl")},
        "t0_sim": t0,
        "deadline_sim": deadline,
        "delete_call_sim_approx": [delete_before, delete_after],
        "target_cells": len(target),
        "bag_plan_count": len(bag_paths),
        "third_clear_map_sim": third_clear_stamp,
        "recovery_plan_sim": recovered["sim_sec"],
        "map_snapshot_sim": [min(maps, key=lambda row: abs(row[0] - item["sim_sec"]))[0]
                             for _, item, _ in stages],
    }
    (out / "v03_d7_provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print("PASS: offline figures and provenance written to", out)
    print("t0", t0, "deadline", deadline, "targets", len(target),
          "bag_paths", len(bag_paths), "first_postclear_plan", recovered["sim_sec"])


if __name__ == "__main__":
    main()
