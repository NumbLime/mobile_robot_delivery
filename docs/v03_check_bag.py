#!/usr/bin/env python3
"""Read-only closeout check for a stopped V0.3 rosbag2 SQLite bag."""

import argparse
import sqlite3
import sys
from pathlib import Path

import rosbag2_py
import yaml
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from rosgraph_msgs.msg import Clock

REQUIRED = {"/clock", "/tf", "/tf_static", "/scan", "/map",
            "/global_costmap/costmap", "/local_costmap/costmap", "/plan",
            "/compute_path_to_pose/_action/status"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag_dir")
    args = parser.parse_args()
    bag = Path(args.bag_dir)
    meta_path = bag / "metadata.yaml"
    if not meta_path.is_file() or meta_path.stat().st_size == 0:
        raise ValueError("nonempty metadata.yaml missing")
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))["rosbag2_bagfile_information"]
    if meta["storage_identifier"] != "sqlite3" or len(meta["relative_file_paths"]) != 1:
        raise ValueError("unexpected metadata storage/file layout")
    database = bag / meta["relative_file_paths"][0]
    if not database.is_file() or database.stat().st_size == 0:
        raise ValueError("database missing or empty")
    connection = sqlite3.connect("file:" + str(database) + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        counts = dict(connection.execute("SELECT t.name, COUNT(*) FROM messages m "
                                         "JOIN topics t ON t.id=m.topic_id GROUP BY t.name"))
    finally:
        connection.close()
    if integrity != "ok" or sum(counts.values()) != meta["message_count"]:
        raise ValueError("SQLite integrity or metadata count mismatch")
    missing = sorted(name for name in REQUIRED if counts.get(name, 0) == 0)
    if missing:
        raise ValueError("missing required messages: " + ", ".join(missing))
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(bag), storage_id="sqlite3"),
                rosbag2_py.ConverterOptions("", ""))
    types = {item.name: item.type for item in reader.get_all_topics_and_types()}
    seen = set()
    read_counts = {}
    first_clock = last_clock = None
    while reader.has_next():
        name, blob, _ = reader.read_next()
        read_counts[name] = read_counts.get(name, 0) + 1
        if name not in seen:
            deserialize_message(blob, get_message(types[name]))
            seen.add(name)
        if name == "/clock":
            msg = deserialize_message(blob, Clock)
            value = msg.clock.sec + msg.clock.nanosec / 1e9
            if first_clock is None:
                first_clock = value
            last_clock = value
    if read_counts != counts or not REQUIRED.issubset(seen):
        raise ValueError("sequential readback differs from SQLite counts")
    if first_clock is None or last_clock <= first_clock:
        raise ValueError("/clock did not advance")
    if counts["/global_costmap/costmap"] < 3:
        raise ValueError("fewer than 3 global costmap messages")
    print("PASS: metadata, SQLite integrity, sequential readback, required topics, advancing clock")
    print("database", database)
    print("messages", sum(counts.values()), "global_maps", counts["/global_costmap/costmap"])
    print("clock_range", first_clock, last_clock)
    for name in sorted(REQUIRED):
        print(name, counts[name], types[name])


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, sqlite3.DatabaseError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
