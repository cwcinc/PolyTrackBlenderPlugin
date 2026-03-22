import zlib
from dataclasses import dataclass
from typing import Optional, List, Tuple
from track_parts import *

# Custom Base62 encoding table (matches the TypeScript)
ENCODE_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

# Decode table: maps ASCII code to value (-1 = invalid)
DECODE_TABLE = [
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
    -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
    -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
]

COMPACT_MASK = 0b00011110  # 30


def base62_decode(encoded: str) -> Optional[bytes]:
    """Decode the custom base62 bit-packed string to bytes."""
    if not encoded:
        return None

    data = []
    bit_index = 0
    length = len(encoded)

    for i, char in enumerate(encoded):
        char_code = ord(char)
        if char_code >= len(DECODE_TABLE):
            return None

        bits = DECODE_TABLE[char_code]
        if bits == -1:
            return None

        is_last = (i == length - 1)

        # Determine if this is a 5-bit or 6-bit value
        if (bits & COMPACT_MASK) == COMPACT_MASK:
            write_bits(data, bit_index, 5, bits, is_last)
            bit_index += 5
        else:
            write_bits(data, bit_index, 6, bits, is_last)
            bit_index += 6

    return bytes(data)


def write_bits(data: list, bit_index: int, num_bits: int, bits: int, is_last: bool):
    """Write bits to the data array at the given bit index."""
    byte_index = bit_index // 8

    # Extend data array if needed
    while byte_index >= len(data):
        data.append(0)

    local_bit_index = bit_index - byte_index * 8
    data[byte_index] |= (bits << local_bit_index) & 0xff

    # Handle overflow to next byte
    if local_bit_index > 8 - num_bits and not is_last:
        next_byte_index = byte_index + 1
        if next_byte_index >= len(data):
            data.append(0)
        data[next_byte_index] |= bits >> (8 - local_bit_index)


def decompress_zlib(data: bytes, to_string: bool = False) -> Optional[bytes | str]:
    """Decompress zlib/deflate data."""
    try:
        # Try raw deflate first (pako default)
        decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        try:
            # Try with zlib header
            decompressed = zlib.decompress(data)
        except zlib.error:
            return None

    if to_string:
        try:
            return decompressed.decode('utf-8')
        except UnicodeDecodeError:
            return None
    return decompressed


@dataclass
class TrackPart:
    x: int
    y: int
    z: int
    part_type: int
    rotation: int
    rotation_axis: int
    color: int
    checkpoint_order: Optional[int] = None
    start_order: Optional[int] = None


@dataclass
class TrackMetadata:
    name: str
    author: Optional[str]


@dataclass
class TrackData:
    environment: int
    sun_direction: int
    parts: List[TrackPart]

    def __init__(self, environment: int, sun_direction: int):
        self.environment = environment
        self.sun_direction = sun_direction
        self.parts = []

    def add_part(self, x: int, y: int, z: int, part_type: int, rotation: int,
                 rotation_axis: int, color: int, checkpoint_order: Optional[int],
                 start_order: Optional[int]):
        self.parts.append(TrackPart(
            x=x, y=y, z=z,
            part_type=part_type,
            rotation=rotation,
            rotation_axis=rotation_axis,
            color=color,
            checkpoint_order=checkpoint_order,
            start_order=start_order
        ))


def read_int32_le(data: bytes, offset: int) -> int:
    """Read a signed 32-bit little-endian integer."""
    val = data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)
    if val >= 0x80000000:
        val -= 0x100000000
    return val


def read_uint32_le(data: bytes, offset: int) -> int:
    """Read an unsigned 32-bit little-endian integer."""
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)


def from_byte_array(offset: int, data: bytes,
                    checkpoint_types: List[int],
                    start_types: List[int]) -> Optional[TrackData]:
    """Parse track data from byte array."""
    i = offset

    if len(data) - i < 1:
        return None
    environment = data[i]
    i += 1

    if len(data) - i < 1:
        return None
    sun_direction = data[i]
    i += 1

    if sun_direction < 0 or sun_direction >= 180:
        return None

    track_data = TrackData(environment, sun_direction)

    if len(data) - i < 4 + 4 + 4 + 1:
        return None

    min_x = read_int32_le(data, i)
    i += 4
    min_y = read_int32_le(data, i)
    i += 4
    min_z = read_int32_le(data, i)
    i += 4

    width_bytes = data[i] & 0x03
    height_bytes = (data[i] >> 2) & 0x03
    length_bytes = (data[i] >> 4) & 0x03
    i += 1

    if not (1 <= width_bytes <= 4 and 1 <= height_bytes <= 4 and 1 <= length_bytes <= 4):
        return None

    while i < len(data):
        if len(data) - i < 1:
            return None
        part_type = data[i]
        i += 1

        if len(data) - i < 4:
            return None
        amount = read_uint32_le(data, i)
        i += 4

        for _ in range(amount):
            if len(data) - i < width_bytes:
                return None
            x = 0
            for k in range(width_bytes):
                x |= data[i + k] << (8 * k)
            x += min_x
            i += width_bytes

            if len(data) - i < height_bytes:
                return None
            y = 0
            for k in range(height_bytes):
                y |= data[i + k] << (8 * k)
            y += min_y
            i += height_bytes

            if len(data) - i < length_bytes:
                return None
            z = 0
            for k in range(length_bytes):
                z |= data[i + k] << (8 * k)
            z += min_z
            i += length_bytes

            if len(data) - i < 1:
                return None
            rotation = data[i]
            i += 1
            if rotation > 3:
                return None

            if len(data) - i < 1:
                return None
            rotation_axis = data[i]
            i += 1

            if len(data) - i < 1:
                return None
            color = data[i]
            i += 1

            checkpoint_order = None
            if part_type in checkpoint_types:
                if len(data) - i < 2:
                    return None
                checkpoint_order = data[i] | (data[i + 1] << 8)
                i += 2

            start_order = None
            if part_type in start_types:
                if len(data) - i < 4:
                    return None
                start_order = read_uint32_le(data, i)
                i += 4

            track_data.add_part(x, y, z, part_type, rotation, rotation_axis,
                                color, checkpoint_order, start_order)

    return track_data


def decode_track_with_metadata(export_string: str,
                               checkpoint_types: Optional[List[int]] = None,
                               start_types: Optional[List[int]] = None
                               ) -> Optional[Tuple[TrackMetadata, TrackData]]:
    """Decode a PolyTrack1 export string."""
    if checkpoint_types is None:
        checkpoint_types = get_checkpoint_types()
    if start_types is None:
        start_types = get_start_types()

    if not export_string.startswith("PolyTrack1"):
        print("Invalid export string prefix")
        return None

    # First base62 decode
    compressed_data = base62_decode(export_string[10:])
    if compressed_data is None:
        print("Failed to decode base62")
        return None

    # First decompress (to string)
    base62_data = decompress_zlib(compressed_data, to_string=True)
    if base62_data is None or not isinstance(base62_data, str):
        print("Failed first decompression")
        return None

    # Second base62 decode
    compressed_data2 = base62_decode(base62_data)
    if compressed_data2 is None:
        print("Failed second base62 decode")
        return None

    # Second decompress (to bytes)
    data = decompress_zlib(compressed_data2, to_string=False)
    if data is None or not isinstance(data, bytes):
        print("Failed second decompression")
        return None

    # Parse track name
    if len(data) < 1:
        return None
    track_name_length = data[0]

    if len(data) < 1 + track_name_length:
        return None
    track_name = data[1:1 + track_name_length].decode('utf-8')

    # Parse author
    author_offset = 1 + track_name_length
    if len(data) < author_offset + 1:
        return None
    author_length = data[author_offset]

    if len(data) < author_offset + 1 + author_length:
        return None

    author = None
    if author_length > 0:
        author = data[author_offset + 1:author_offset + 1 + author_length].decode('utf-8')

    # Parse track data
    track_data_offset = author_offset + 1 + author_length
    track_data = from_byte_array(track_data_offset, data, checkpoint_types, start_types)

    if track_data is None:
        print("Failed to parse track data")
        return None

    return (TrackMetadata(name=track_name, author=author), track_data)


def decode_track_positions(export_string: str,
                           checkpoint_types: Optional[List[int]] = None,
                           start_types: Optional[List[int]] = None
                           ) -> Optional[List[Tuple[int, int, int, int]]]:
    """Decode a track and return positions and types."""
    result = decode_track_with_metadata(export_string, checkpoint_types, start_types)
    if result is None:
        return None

    metadata, track_data = result
    return [(p.x, p.y, p.z, p.part_type) for p in track_data.parts]


if __name__ == "__main__":
    test = "PolyTrack14pdbUlssjiDE8XysDHtBDY2Nm9bgQiNzqBEWf6He6unY6DDRFESiSVWkVGZqdplHTH485um228HYBjDUfNd5n5GPxe7qwVVVXT7nGyqu3Ne5TDTfmcPeJhLoSeiTf8aldchk7OeSJLmRB1xGU5pCd5tRxKyY9OxlvmLf0i4QX8QD8bCKo3eETg6ILEBFARXQ7egtoxgztrwdvHcUzzCSb0eCaFRw15MGrS3JebeBvo98lGRJOQ3NhLLfsI40DHruZ3YY3qSKFpXp9xX1Ou3f4Fpw4WQ6dlxK4oQMdH1HjfXqXFQXFCqkMwwfdcQefP8BtfLgex9LzXTYZtsGe4EpsfkuqdlvdNHJVBZTfpdlMvfEiixtf6cKg3L8VzR9yeKb6NxI90cF71b90XDKqmcY38kqOr1jeYbeuNuevpkeegUagFTrj0vhlsW6dcp93ZJGwaxfQkq22xLgQuIa7gsjzDgvtzCfzffdcubL2fzVtRmwILobGefcd7YsJdtUP0x4gMBvMNUwlJDfTxoJLscqFoSBeLrO7KCH3IrmM5xrSgF3P665bd3fRZxBp2VJxWxhxEHhD3P50RonEXCUSP31eTH66IyKY8PET2nUt5iiTQZrmsvkR3Wmu2CRPP41PhIYCGSeT1tVoou4R3q0foWtXKVP2RYRXfn9HEUrHLYb9NDryWZ3egyCOSEzrYfSyUjix7jwijdfOGMelSW06SWMLEXw7hU7HFGTcJVIAwhZlzEYQA3TG3eGGT3D0LeNphpickB4jmVe9N7C2Cn0M0uX5iknRgZvbIbxJ2hjJvbeiXTgpiPEDiEG3CgPeCep4Te7c3YVwGsSHSTkeMKMtcXAJvy3UkYAFUVQrIQD0iSMX0UMiVdGynMzxxahJsXCOGaHqCOaxnItg1r1b0r8uOUxozovPkfJDgUeo8pwW53KvHKvuRSlVmhNSLjSpfhKfu1MVLY2z8khmLuIAyYicHCBEKHWGIyvVlJLP7abqMxRq7cgU9KoGYXZYzcR6lo8ZL9uRi1ZXee41tjMWA4mbjVGTc9KvP4WBc5IrzeQegaOLxY59NcfHfE1IAEVnLrXo27CT3y74zZfa2rFQOFjaG3aTnjGG1Ip3UL79pOJ2jk6kq97eScC8y4zewm8OcYZLK9H4OiYzpSZ125yBqbhO31OUn5tXFHpyMyOV9aJ1LcXiGjSadSqteYn7xWXxa3065XW78dX5kfKG7ihdZatWeXGGRmHGGHfUxxa635arn0QwcsygwImMgB9r4fM5ZpmpccVGatwePPEuZd4D0yZWfwKTRfh6JdoBzhR2np0yKfyWREj4IfHb02VQ6kSqaINwM9CB8NQ9Q9QuvgyYexdtCj6pGi65qn3sOaXhnMOttv8p70SsLdvi2xVzVxrcpXJfeOP6fG6KfZI1OFX2lb3cLEfF8O9sxn6g0iBcfWQuMJ9zzz6ID7PNODhCanmj76QIWKClIQps89gfWy7hmAVSAOIqtQ8eTRcoYqEC6tOlUGIxHL0b2PMSW5d9Rli90B7rEIok9acIKrkue26nr6HbwHO8mpqkT30Zkis3M76VyAfs48Pi70DMhsldXLxqr8vO9t0sSVFwweTjlLhnN6tlUd6C4eCrgG9JcrY7HbFXDTk0C1XI1eggFKGer68FSxSMVMTn2EUMjI8l7ixUb8J1MPf1cO5p0pMdebHIQMUkDwTwDPby2gHseP5mQrQvKhGBfeEITMD8KGo20cUe93IKYMsYCecpXj1jM3B4Paeh7O1nufI4J2D2B8qbHvBL8xEnb3l2oeBn9iaJvi26x92h0lYx7DReiAbo154ey6P8TMAVe4ftWBkiFv5Yk9KwhrClL9SlZfRvK96E07VJZXH5KKx6dfnCJJWBMT7KQIW1bgnL8Xv2LzVFoZ9qsz43bFoNcM8ZDrdV7vGTfRQPMcEpuVU2urggjUcIvlglZgyfBe3nqaM"  # your string here
    result = decode_track_with_metadata(test)
    if result:
        meta, data = result
        print(f"Track: {meta.name}, Author: {meta.author}")
        print(f"Parts: {len(data.parts)}")