#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator, Self, BinaryIO, cast, Generic, TypeVar
import os
import io
from itertools import chain
import struct
from pprint import pprint
import header as H


class Polygon:
    def __init__(self, bytesdata: bytes):
        self.view = memoryview(bytesdata)


class PolygonStr(Polygon):
    def __init__(self, bytesdata, fmt):
        super().__init__(bytesdata)
        self.fmt = fmt

    @classmethod
    def from_file(cls, f: BinaryIO, fmt: str) -> Self:
        (sz,) = struct.unpack("<i", f.read(4))
        return cls(f.read(sz), fmt)

    def __iter__(self) -> Iterator[tuple[float, float]]:
        sz = struct.calcsize(self.fmt)
        for off in range(0, len(self.view), sz):
            s = slice(off, off + sz)
            yield struct.unpack_from(self.fmt, self.view[s])


T = TypeVar("T", bound=H.View)


class PolygonType(Polygon, Generic[T]):
    def __init__(self, bytesdata: bytes, factory: type[T]):
        super().__init__(bytesdata)
        self.factory = factory

    @classmethod
    def from_file(cls, f: BinaryIO, factory: type[T]) -> Self:
        (sz,) = struct.unpack("<i", f.read(4))
        return cls(f.read(sz), factory)

    def __iter__(self) -> Iterator[T]:
        sz = self.factory.data_size
        for off in range(0, len(self.view), sz):
            s = slice(off, off + sz)
            yield self.factory(self.view[s])


def pack_header(polygons: H.PolygonType = H.polygons) -> bytes:
    magic = 0x1234
    x1 = min(x for x, _ in chain(*polygons))
    y1 = min(y for _, y in chain(*polygons))
    x2 = min(x for x, _ in chain(*polygons))
    y2 = min(y for _, y in chain(*polygons))
    num_points = len(polygons)
    return struct.pack("<iddddi", magic, x1, y1, x2, y2, num_points)


def write_polygons(f: BinaryIO, polygons: H.PolygonType = H.polygons) -> None:
    f.write(pack_header())
    for poly in polygons:
        fmt: str = "<dd"
        sz = struct.calcsize(fmt)
        f.write(struct.pack("<i", sz * len(poly)))
        for pp in poly:
            f.write(struct.pack(fmt, *pp))


if __name__ == "__main__":
    f: BinaryIO
    if not os.path.exists("polygons.bin"):
        with open("polygons.bin", "wb") as f:
            write_polygons(f)
            print("polygons.bin was written")
    with open("polygons.bin", "rb") as f:
        h: H.Header = H.Header(f.read(H.Header.data_size))
        _data = f.read()
        f1 = io.BytesIO(_data)
        f2 = io.BytesIO(_data)

        pprint(
            [
                [pp for pp in PolygonStr.from_file(f1, "<dd")]
                for _ in range(h.num_polygons)
            ]
        )
        pprint(
            [
                [pp for pp in PolygonType.from_file(f2, H.Point)]
                for _ in range(h.num_polygons)
            ]
        )
