#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Any, ClassVar, BinaryIO, Iterator
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
    def __init__(self, name: str, offset: int):
        self._name = name
        self.offset = offset

    def unpack(self, instance: Any) -> object:
        raise NotImplementedError("Subclass it")

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self.unpack(instance)


class FieldStr(Field):
    def __init__(self, name: str, fmt: str, offset: int):
        super().__init__(name, offset)
        self.fmt = fmt

    def unpack(self, instance):
        s = slice(
            self.offset,
            self.offset + struct.calcsize(self.fmt),
        )
        t = struct.unpack_from(self.fmt, instance.view[s])
        return t[0] if len(t) == 1 else t


class FieldType(Field):
    def __init__(self, name: str, factory: "ViewMeta", offset: int):
        super().__init__(name, offset)
        self.factory = factory

    def unpack(self, instance):
        s = slice(self.offset, self.offset + self.factory.data_size)
        return self.factory(instance.view[s])


class ViewMeta(type):
    data_size: ClassVar[int]

    def __new__(mcls, clsname, bases, ns):
        ns2 = dict(ns)
        format_merged = ""
        fields: list[str] = []
        offset: int = 0
        for name, val in ns.items():
            if name[:2] == "__" and name[-2:] == "__":
                continue
            if isinstance(val, str):
                if is_valid_struct_format(val):
                    fmt: str = val
                    ns2[name] = FieldStr(name, fmt, offset)
                    fields.append(name)
                    offset += struct.calcsize(fmt)
                    if format_merged == "":
                        format_merged = fmt
                    elif format_merged[0] == val[0]:
                        format_merged += fmt[1:]
                    else:
                        format_merged += fmt
                else:
                    raise TypeError(f"{val} Invalide struct format")
            elif isinstance(val, ViewMeta):
                factory: ViewMeta = val
                ns2[name] = FieldType(name, factory, offset)
                fields.append(name)
                offset += factory.data_size
            else:
                raise TypeError(f"{val!r} expected struct foramt or ViewMeta type")
        ns2["_format_merged"] = format_merged
        ns2["data_size"] = offset
        ns2["_fields"] = fields
        return super().__new__(mcls, clsname, bases, ns2)


class View(metaclass=ViewMeta):
    _fields: ClassVar[str]
    _format_merged: ClassVar[str]

    def __init__(self, bytesdata: bytes):
        self.view = memoryview(bytesdata)

    def __repr__(self):
        clsname = self.__class__.__name__
        args = ", ".join(str(getattr(self, f)) for f in self._fields)
        return f"{clsname}({args})"


class Point(View):
    x = "<d"
    y = "<d"


class Bbox(View):
    x1y1 = Point
    x2y2 = Point


class Header(View):
    magic = "<i"
    bbox = Bbox
    num_points = "<i"


def write_polygons():
    for poly in polygons:
        fmt: str = "<dd"
        sz = struct.calcsize(fmt)
        f.write(sz * len(poly))
        for pp in poly:
            f.write(struct.pack(fmt, pp))


class Polygon:
    def __init__(self, bytesdata: bytes):
        self.view = memoryview(bytesdata)

    @classmethod
    def from_file(cls):
        (sz,) = struct.unpack("<i", f.read(4))
        return cls(f.read(sz))


class PolygonStr(Polygon):
    def __init__(self, bytesdata, fmt):
        super().__init__(bytesdata)
        self.fmt = fmt

    def iter_as(self, fmt) -> Iterator[tuple[float, float]]:
        sz = struct.calcsize(fmt)
        for off in range(0, len(self.view), sz):
            s = slice(off, off + sz)
            yield struct.unpack_from(fmt, self.view[s])


class PolygonType(Polygon):
    def __init__(self, bytesdata: bytes, factory: ViewMeta):
        super().__init__(bytesdata)
        self.factory = factory

    def iter_as(self) -> Iterator[ViewMeta]:
        sz = self.factory.data_size
        for off in range(0, len(self.view), sz):
            s = slice(off, off + sz)
            yield self.factory(self.view[s])


def pack_header():
    magic = 0x1234
    x1 = min(x for x, _ in chain(*polygons))
    y1 = min(y for _, y in chain(*polygons))
    x2 = min(x for x, _ in chain(*polygons))
    y2 = min(y for _, y in chain(*polygons))
    num_points = len(polygons)
    print(Header._format_merged)
    return struct.pack(Header._format_merged, magic, x1, y1, x2, y2, num_points)


def write_read_header():
    with open("header.bin", "wb") as f:
        f.write(pack_header())
    with open("header.bin", "rb") as f:
        magic, x1, y1, x2, y2, num_points = struct.unpack(
            Header._format_merged, f.read()
        )
        print(magic, x1, y1, x2, y2, num_points)


if __name__ == "__main__":
    with open("header.bin", "rb") as f:
        # print(Header._format_merged)
        # print(Header.data_size)
        h = Header(f.read(Header.data_size))
        # print(h.magic)
        print(h)
