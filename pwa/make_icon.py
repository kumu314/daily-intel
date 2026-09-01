# -*- coding: utf-8 -*-
"""零依赖生成 512x512 纯色图标（PWA 占位图标）。后续可换成真图标。"""
import zlib
import struct
from pathlib import Path

ROOT = Path(__file__).parent


def write_png(path, size=512, color=(18, 58, 51)):
    w = h = size
    raw = bytearray()
    for _ in range(h):
        raw.append(0)  # 每行过滤字节：无
        for _ in range(w):
            raw += bytes(color)
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        return (struct.pack('>I', len(data)) + typ + data +
                struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff))

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)  # 8bit, RGB
    png = sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', comp) + chunk(b'IEND', b'')
    Path(path).write_bytes(png)


if __name__ == '__main__':
    out = ROOT / 'icon.png'
    write_png(out)
    print(f"图标已生成：{out}  ({out.stat().st_size} bytes)")
