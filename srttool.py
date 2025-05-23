#!/usr/bin/env python3

import re
import codecs
import argparse
from decimal import Decimal

parser = argparse.ArgumentParser(description="options")
parser.add_argument("file", help="File to process")
parser.add_argument('-i', '--in-place', action="store_true", help="Edit file in place")
parser.add_argument('-f', '--fps', nargs=2, type=Decimal, help="Convert [FPS] to [FPS]")
parser.add_argument('-s', '--shift', nargs=1, type=Decimal, help="Shift time by [seconds]")
parser.add_argument('-c', '--clear', action="store_true", help="Clear hearing impaired text")

args = parser.parse_args()


def srt_generator(file):
    try:
        fh = open(file, "r")
        fh.read()
        fh.seek(0)
    except UnicodeDecodeError:
        fh = codecs.open(file, "r", encoding="iso-8859-15")
    for _item in fh.read().split("\n\n"):
        if _item.strip():
            yield _item.strip()
    fh.close()


def timestamp_to_ms(timestamp: str) -> int:
    # Convert HH:MM:SS,mmm to milliseconds
    hours, minutes, seconds = timestamp.split(":")
    seconds, milliseconds = seconds.split(",")
    return int(hours) * 3600000 + int(minutes) * 60000 + int(seconds) * 1000 + int(milliseconds)


def ms_to_timestamp(ms: int) -> str:
    # Convert milliseconds to HH:MM:SS,mmm
    hours = ms // 3600000
    if hours > 99:
        raise ValueError("Timestamp exceeds 100 hours")
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def change_fps(fps_from: Decimal, fps_to: Decimal, time_stamp: str) -> str:
    # Convert time from one FPS to another
    ms = timestamp_to_ms(time_stamp)
    new_ms = timestamp_to_ms(time_stamp) * (fps_from / fps_to)
    return ms_to_timestamp(round(new_ms))


def clear_hearing_impaired(text: list) -> list:
    # Remove hearing impaired text
    return [line for line in text if not re.search(r"\[.*?\]", line)]


if __name__ == "__main__":
    new_lines = []

    for index, srt_item in enumerate(srt_generator(args.file), start=1):
        lines = srt_item.splitlines()
        old_index = lines.pop(0)
        if not old_index.isdigit():
            raise ValueError(f"Invalid SRT index: {old_index}")
        timestamps = lines.pop(0)
        start, end = timestamps.split(" --> ")

        if args.fps:
            start = change_fps(args.fps[0], args.fps[1], start)
            end = change_fps(args.fps[0], args.fps[1], end)

        if args.shift:
            shift_seconds = args.shift[0] * 1000
            start_ms = timestamp_to_ms(start) + int(shift_seconds)
            end_ms = timestamp_to_ms(end) + int(shift_seconds)
            if start_ms < 0:
                start_ms = 0
            if end_ms < 0:
                end_ms = 0
            start = ms_to_timestamp(start_ms)
            end = ms_to_timestamp(end_ms)

        if args.clear:
            lines = clear_hearing_impaired(lines)

        text_lines = "\n".join(lines)

        output = f"{index}\n{start} --> {end}\n{text_lines}\n"

        if not args.in_place:
            print(output)
        else:
            new_lines.append(output + "\n")

    if args.in_place:
        with open(args.file, "w") as f:
            f.writelines(new_lines)
