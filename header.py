#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO
from itertools import chain
import struct

polygons = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 6.3), (1.2, 0.5), (4.6, 9.2)],
]


def is_valid_struct_format(fmt: str) -> bool:
    try:
        struct.Struct(fmt)
    except struct.error:
        return False
    return True


class Field:
    def __init__(self, name: str, fmt: str):
        self._name = name
        self.fmt = fmt


class HeaderMeta(type):
    def __new__(mcls, clsname, bases, ns):
        ns2 = dict(ns)
        format_merged = ""
        for name, val in ns.items():
            if name[:2] == "__" and name[-2:] == "__":
                continue
            if isinstance(val, str):
                if is_valid_struct_format(val):
                    ns2[name] = Field(name, val)
                    if format_merged == "":
                        format_merged = val
                    elif format_merged[0] == val[0]:
                        format_merged += val[1:]
                    else:
                        format_merged += val
                else:
                    raise TypeError(f"{val} Invalide struct format")
        ns2["_format_merged"] = format_merged
        return super().__new__(mcls, clsname, bases, ns2)


class Header(metaclass=HeaderMeta):
    magic = "<i"
    x1 = "<d"
    y1 = "<d"
    x2 = "<d"
    y2 = "<d"
    num_points = "<i"


# def write_header(f: BinaryIO):
def pack_header():
    magic = 0x1234
    x1 = min(x for x, _ in chain(*polygons))
    y1 = min(y for _, y in chain(*polygons))
    x2 = min(x for x, _ in chain(*polygons))
    y2 = min(y for _, y in chain(*polygons))
    num_points = len(polygons)
    print(Header._format_merged)
    return struct.pack(Header._format_merged, magic, x1, y1, x2, y2, num_points)


if __name__ == "__main__":
    with open("header.bin", "wb") as f:
        f.write(pack_header())
    with open("header.bin", "rb") as f:
        magic, x1, y1, x2, y2, num_points = struct.unpack(
            Header._format_merged, f.read()
        )
        print(magic, x1, y1, x2, y2, num_points)
