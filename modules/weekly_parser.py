import re


def parse_week(text):

    week = {}

    days = [
        "月曜日",
        "火曜日",
        "水曜日",
        "木曜日",
        "金曜日",
        "土曜日",
        "日曜日"
    ]

    current = None

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line in days:

            current = line

            week[current] = []

            continue

        if current:

            week[current].append(line)

    return week