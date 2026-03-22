bl_info = {
    "name": "PolyTrack v2 Importer",
    "author": "cwcinc",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > PolyTrack v2",
    "description": "Import PolyTrack track strings (v1 & v2) with proper materials and model generation",
    "category": "Import-Export",
}

import bpy
import zlib
import math
import bmesh
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import IntEnum
from mathutils import Matrix, Euler, Quaternion, Vector

# =============================================================================
# Track Part ID Enum (updated from main.js line 7560)
# =============================================================================

class TrackPartId(IntEnum):
    Straight = 0
    TurnSharp = 1
    SlopeUp = 2
    SlopeDown = 3
    Slope = 4
    Start = 5
    Finish = 6
    ToWideMiddle = 7
    ToWideLeft = 8
    ToWideRight = 9
    StraightWide = 10
    InnerCornerWide = 11
    OuterCornerWide = 12
    SlopeUpLeftWide = 13
    SlopeUpRightWide = 14
    SlopeDownLeftWide = 15
    SlopeDownRightWide = 16
    SlopeLeftWide = 17
    SlopeRightWide = 18
    PillarTop = 19
    PillarMiddle = 20
    PillarBottom = 21
    PillarShort = 22
    PlanePillarBottom = 23
    PlanePillarShort = 24
    Plane = 25
    PlaneWall = 26
    PlaneWallCorner = 27
    PlaneWallInnerCorner = 28
    Block = 29
    WallTrackTop = 30
    WallTrackMiddle = 31
    WallTrackBottom = 32
    PlaneSlopeUp = 33
    PlaneSlopeDown = 34
    PlaneSlope = 35
    TurnShort = 36
    TurnLong = 37
    SlopeUpLong = 38
    SlopeDownLong = 39
    # 40 is removed in current version (was SlopePillar)
    TurnSLeft = 41
    TurnSRight = 42
    IntersectionT = 43
    IntersectionCross = 44
    PillarBranch1 = 45
    PillarBranch2 = 46
    PillarBranch3 = 47
    PillarBranch4 = 48
    WallTrackBottomCorner = 49
    WallTrackMiddleCorner = 50
    WallTrackTopCorner = 51
    Checkpoint = 52
    HalfBlock = 53
    QuarterBlock = 54
    HalfPlane = 55
    QuarterPlane = 56
    PlaneBridge = 57
    SignArrowLeft = 58
    SignArrowRight = 59
    # 60 is skipped
    SignArrowUp = 61
    SignArrowDown = 62
    SignWarning = 63
    SignWrongWay = 64
    CheckpointWide = 65
    WallTrackCeiling = 66
    WallTrackFloor = 67
    BlockSlopedDown = 68
    BlockSlopedDownInnerCorner = 69
    BlockSlopedDownOuterCorner = 70
    BlockSlopedUp = 71
    BlockSlopedUpInnerCorner = 72
    BlockSlopedUpOuterCorner = 73
    FinishWide = 74
    PlaneCheckpoint = 75
    PlaneFinish = 76
    PlaneCheckpointWide = 77
    PlaneFinishWide = 78
    WallTrackBottomInnerCorner = 79
    WallTrackInnerCorner = 80
    WallTrackTopInnerCorner = 81
    TurnLong2 = 82
    TurnLong3 = 83
    # 84 is removed in current version (was SlopePillarShort)
    BlockSlopeUp = 85
    BlockSlopeDown = 86
    BlockSlopeVerticalTop = 87
    BlockSlopeVerticalBottom = 88
    # 89 is skipped
    PlaneSlopeVerticalBottom = 90
    StartWide = 91
    PlaneStart = 92
    PlaneStartWide = 93
    TurnShortLeftWide = 94
    TurnShortRightWide = 95
    TurnLongLeftWide = 96
    TurnLongRightWide = 97
    SlopeUpVertical = 98
    IntersectionY = 99
    IntersectionYLong = 100
    PillarBranch1Top = 101
    PillarBranch1Bottom = 102
    PillarBranch1Middle = 103
    PillarBranch2Top = 104
    PillarBranch2Middle = 105
    PillarBranch2Bottom = 106
    PillarBranch3Top = 107
    PillarBranch3Middle = 108
    PillarBranch3Bottom = 109
    PillarBranch4Top = 110
    PillarBranch4Middle = 111
    PillarBranch4Bottom = 112
    PillarBranch5 = 113
    PillarBranch5Top = 114
    PillarBranch5Middle = 115
    PillarBranch5Bottom = 116
    ToWideDouble = 117
    ToWideDiagonal = 118
    StraightPillarBottom = 119
    StraightPillarShort = 120
    TurnSharpPillarBottom = 121
    TurnSharpPillarShort = 122
    IntersectionTPillarBottom = 123
    IntersectionTPillarShort = 124
    IntersectionCrossPillarBottom = 125
    IntersectionCrossPillarShort = 126
    PlaneBridgeCorner = 127
    PlaneBridgeIntersectionT = 128
    PlaneBridgeIntersectionCross = 129
    BlockBridge = 130
    BlockBridgeCorner = 131
    BlockBridgeIntersectionT = 132
    BlockBridgeIntersectionCross = 133
    WallTrackCeilingCorner = 134
    WallTrackCeilingPlaneCorner = 135
    WallTrackFloorCorner = 136
    WallTrackFloorPlaneCorner = 137
    SlopeUpVerticalLeftWide = 138
    SlopeUpVerticalRightWide = 139
    BlockSlopeVerticalCornerTop = 140
    BlockSlopeVerticalCornerBottom = 141
    WallTrackSlopeToVertical = 142
    PlaneSlopeToVertical = 143
    BlockSlopeToVertical = 144
    PlaneSlopeUpLong = 145
    PlaneSlopeDownLong = 146
    SlopeUpLongLeftWide = 147
    SlopeUpLongRightWide = 148
    SlopeDownLongLeftWide = 149
    SlopeDownLongRightWide = 150
    BlockSlopeUpLong = 151
    BlockSlopeDownLong = 152
    BlockSlopeVerticalInnerCornerBottom = 153
    BlockSlopeVerticalInnerCornerTop = 154
    BlockInnerCorner = 155
    SlopeToVertical = 156
    SlopeToVerticalLeftWide = 157
    SlopeToVerticalRightWide = 158
    StraightTilted = 159
    TurnShortTilted = 160
    TurnLongTilted = 161
    TurnLong2Tilted = 162
    TurnLong3Tilted = 163
    TurnSLongLeft = 164
    TurnSLongRight = 165
    ToTiltedLeft = 166
    ToTiltedRight = 167
    PillarTopSlope = 168
    PillarShortSlope = 169
    HalfPlaneSlopeBottomLeft = 170
    HalfPlaneSlopeBottomRight = 171
    HalfPlaneSlopeTopLeft = 172
    HalfPlaneSlopeTopRight = 173
    HalfBlockSlopeBottomLeft = 174
    HalfBlockSlopeBottomRight = 175
    HalfBlockSlopeTopLeft = 176
    HalfBlockSlopeTopRight = 177
    PlaneWallSlopeLeft = 178
    PlaneWallSlopeRight = 179
    PlaneWallSlopeUpLeft = 180
    PlaneWallSlopeUpRight = 181
    PlaneWallSlopeDownLeft = 182
    PlaneWallSlopeDownRight = 183
    PlaneWallSlopeUpLongLeft = 184
    PlaneWallSlopeUpLongRight = 185
    PlaneWallSlopeDownLongLeft = 186
    PlaneWallSlopeDownLongRight = 187
    BlockOuterCorner = 188
    PlaneCorner = 189


# Checkpoint and start part types
CHECKPOINT_TYPES = [
    int(TrackPartId.Checkpoint),
    int(TrackPartId.CheckpointWide),
    int(TrackPartId.PlaneCheckpoint),
    int(TrackPartId.PlaneCheckpointWide),
]

START_TYPES = [
    int(TrackPartId.Start),
    int(TrackPartId.StartWide),
    int(TrackPartId.PlaneStart),
    int(TrackPartId.PlaneStartWide),
]

# =============================================================================

# Map theme ID to a dictionary of material name -> hex color
ENVIRONMENT_OVERRIDES = {
    1: {}, # Summer has no overrides, uses default FBX colors
    2: { # Winter
        "road": "#5077b2",
        "roadbarrier": "#898989",
        "roadedgewhite": "#ffffff",
        "roadedgered": "#1f3d6b",
        "blocksurface": "#878787",
        "pillar": "#2b4d7f",
        "pillaredge": "#071428",
        "walltrack": "#5077b2",
        "walltrackbottom": "#878787",
        "walltracksides": "#ffffff",
        "planewall": "#1f3d6b",
        "planewalldetail": "#878787",
        "signyellow": "#1b2a89",
        "signred": "#841901",
        "signblack": "#5077b2",
    },
    3: { # Desert
        "road": "#997240",
        "roadbarrier": "#211001",
        "roadedgered": "#5b2424",
        "roadedgewhite": "#510808",
        "blocksurface": "#b78f5b",
        "pillar": "#99713d",
        "pillaredge": "#1c1105",
        "walltrack": "#260b0b",
        "walltrackbottom": "#160606",
        "walltracksides": "#75562e",
        "planewall": "#633030",
        "planewalldetail": "#aa8a53",
        "signyellow": "#997240",
        "signred": "#d80202",
        "signblack": "#601d1d",
    }
}

CUSTOM_COLORS = {
    32: "#131313",
    33: "#501b1b",
    34: "#7f4d2b",
    35: "#93862d",
    36: "#2a5e30",
    37: "#236363",
    38: "#20244b",
    39: "#592759",
    40: "#302318",
}

ENVIRONMENT_NAMES = {
    0: "Summer",
    1: "Summer",
    2: "Winter",
    3: "Desert",
}

def srgb_to_linear(c: float) -> float:
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def hex_to_rgba(hex_str: str) -> tuple:
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return (1.0, 1.0, 1.0, 1.0)
    r = srgb_to_linear(int(hex_str[0:2], 16) / 255.0)
    g = srgb_to_linear(int(hex_str[2:4], 16) / 255.0)
    b = srgb_to_linear(int(hex_str[4:6], 16) / 255.0)
    return (r, g, b, 1.0)

MATERIAL_CACHE = {}

def get_override_material(original_mat: bpy.types.Material, hex_color: str) -> bpy.types.Material:
    cache_key = (original_mat.name, hex_color)
    if cache_key in MATERIAL_CACHE:
        return MATERIAL_CACHE[cache_key]
        
    # Duplicate existing material so we retain its shader settings (like roughness)
    new_mat = original_mat.copy()
    new_mat.name = f"{original_mat.name}_{hex_color}"
    
    # Change Principled BSDF base color
    if new_mat.use_nodes:
        for node in new_mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs['Base Color'].default_value = hex_to_rgba(hex_color)
                break
                
    MATERIAL_CACHE[cache_key] = new_mat
    return new_mat


# =============================================================================
# Base62 Decoding
# =============================================================================

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

COMPACT_MASK = 0b00011110


def base62_decode(encoded: str) -> Optional[bytes]:
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

        if (bits & COMPACT_MASK) == COMPACT_MASK:
            _write_bits(data, bit_index, 5, bits, is_last)
            bit_index += 5
        else:
            _write_bits(data, bit_index, 6, bits, is_last)
            bit_index += 6

    return bytes(data)


def _write_bits(data: list, bit_index: int, num_bits: int, bits: int, is_last: bool):
    byte_index = bit_index // 8

    while byte_index >= len(data):
        data.append(0)

    local_bit_index = bit_index - byte_index * 8
    data[byte_index] |= (bits << local_bit_index) & 0xff

    if local_bit_index > 8 - num_bits and not is_last:
        next_byte_index = byte_index + 1
        if next_byte_index >= len(data):
            data.append(0)
        data[next_byte_index] |= bits >> (8 - local_bit_index)


# =============================================================================
# Decompression
# =============================================================================

def decompress_zlib(data: bytes, to_string: bool = False) -> Optional[bytes | str]:
    try:
        decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        try:
            decompressed = zlib.decompress(data)
        except zlib.error:
            return None

    if to_string:
        try:
            return decompressed.decode('utf-8')
        except UnicodeDecodeError:
            return None
    return decompressed


# =============================================================================
# Data Classes
# =============================================================================

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
    last_modified: Optional[int] = None  # Unix timestamp (PolyTrack2 only)


class TrackData:
    def __init__(self, environment: int, sun_direction: int):
        self.environment = environment
        self.sun_direction = sun_direction
        self.parts: List[TrackPart] = []

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


# =============================================================================
# Track Decoding
# =============================================================================

def _read_int32_le(data: bytes, offset: int) -> int:
    val = data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)
    if val >= 0x80000000:
        val -= 0x100000000
    return val


def _read_uint32_le(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)


def _from_byte_array(offset: int, data: bytes,
                     checkpoint_types: List[int],
                     start_types: List[int]) -> Optional[TrackData]:
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

    min_x = _read_int32_le(data, i)
    i += 4
    min_y = _read_int32_le(data, i)
    i += 4
    min_z = _read_int32_le(data, i)
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
        amount = _read_uint32_le(data, i)
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
            rot_byte = data[i]
            i += 1
            rotation = rot_byte & 0x03
            if rotation > 3:
                return None

            rotation_axis = (rot_byte >> 2) & 0x07

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
                start_order = _read_uint32_le(data, i)
                i += 4

            track_data.add_part(x, y, z, part_type, rotation, rotation_axis,
                                color, checkpoint_order, start_order)

    return track_data


def _decode_common(data: bytes, version: int) -> Optional[Tuple[TrackMetadata, TrackData]]:
    """Common decoding for the inner decompressed binary data (after double base62+zlib)."""
    if len(data) < 1:
        return None

    # Parse track name
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

    track_data_offset = author_offset + 1 + author_length

    # PolyTrack2: parse lastModified timestamp after author
    last_modified = None
    if version >= 2:
        if len(data) < track_data_offset + 1:
            return None
        has_timestamp = data[track_data_offset]
        track_data_offset += 1
        if has_timestamp == 1:
            if len(data) < track_data_offset + 4:
                return None
            last_modified = _read_uint32_le(data, track_data_offset)
            track_data_offset += 4

    # Parse track data
    track_data = _from_byte_array(track_data_offset, data, CHECKPOINT_TYPES, START_TYPES)

    if track_data is None:
        return None

    return (TrackMetadata(name=track_name, author=author, last_modified=last_modified), track_data)


def decode_track(export_string: str) -> Optional[Tuple[TrackMetadata, TrackData]]:
    """Decode a PolyTrack1 or PolyTrack2 export string."""
    export_string = export_string.strip()

    if export_string.startswith("PolyTrack1"):
        return _decode_versioned(export_string[10:], version=1)
    elif export_string.startswith("PolyTrack2"):
        return _decode_versioned(export_string[10:], version=2)
    else:
        return None


def _decode_versioned(encoded_payload: str, version: int) -> Optional[Tuple[TrackMetadata, TrackData]]:
    """Decode the payload after the version prefix."""
    # First base62 decode
    compressed_data = base62_decode(encoded_payload)
    if compressed_data is None:
        return None

    # First decompress (to string for base62)
    base62_data = decompress_zlib(compressed_data, to_string=True)
    if base62_data is None or not isinstance(base62_data, str):
        return None

    # Second base62 decode
    compressed_data2 = base62_decode(base62_data)
    if compressed_data2 is None:
        return None

    # Second decompress (to binary)
    data = decompress_zlib(compressed_data2, to_string=False)
    if data is None or not isinstance(data, bytes):
        return None

    return _decode_common(data, version)


# =============================================================================
# Rotation System (copied from existing plugin)
# =============================================================================

def quaternion_from_axis_angle(axis: tuple, angle: float) -> Quaternion:
    """Create a quaternion from an axis and angle (in radians)."""
    half_angle = angle / 2
    s = math.sin(half_angle)
    return Quaternion((
        math.cos(half_angle),
        axis[0] * s,
        axis[1] * s,
        axis[2] * s
    ))


def quaternion_from_rotation_axis(rotation: int, rotation_axis: int) -> Quaternion:
    """
    Create a quaternion from rotation and rotation_axis values.

    rotation_axis:
        0: Z+ (no additional rotation)
        1: Z- (flip 180 around X)
        2: X+ (rotate 90 around Y)
        3: X- (rotate -90 around Y)
        4: Y+ (rotate -90 around X)
        5: Y- (rotate 90 around X)
    """
    if (rotation_axis % 2 == 0) or (rotation % 2 == 1):
        rotation += 2

    if (rotation_axis % 2 == 1) and (rotation_axis >= 3):
        rotation += 2

    # Rotation around up axis (Z) by rotation * pi/2
    up_rotation = quaternion_from_axis_angle((0, 0, 1), rotation * math.pi / 2)

    # Axis rotation based on rotation_axis
    axis_rotations = {
        0: Quaternion((1, 0, 0, 0)),                            # Z+: identity
        1: quaternion_from_axis_angle((1, 0, 0), math.pi),      # Z-: 180 around X
        2: quaternion_from_axis_angle((0, 1, 0), -math.pi / 2), # X+: 90 around Y
        3: quaternion_from_axis_angle((0, 1, 0), math.pi / 2),  # X-: -90 around Y
        4: quaternion_from_axis_angle((1, 0, 0), -math.pi / 2), # Y+: -90 around X
        5: quaternion_from_axis_angle((1, 0, 0), math.pi / 2),  # Y-: 90 around X
    }

    axis_rotation = axis_rotations[rotation_axis]
    return axis_rotation @ up_rotation


# =============================================================================
# Blender Instancing
# =============================================================================

def instance_track_part(
        part: TrackPart,
        environment: int,
        scale: float = 1.0,
        collection: bpy.types.Collection = None
) -> Optional[bpy.types.Object]:
    try:
        part_name = TrackPartId(part.part_type).name
    except ValueError:
        return None

    if part_name not in bpy.data.objects:
        return None

    source_obj = bpy.data.objects[part_name]

    # Get quaternion from the rotation system
    effective_rotation = round(part.rotation) % 4
    track_quat = quaternion_from_rotation_axis(effective_rotation, part.rotation_axis).copy()

    # Get the source object's existing rotation
    if source_obj.rotation_mode == 'QUATERNION':
        source_quat = source_obj.rotation_quaternion.copy()
    else:
        source_quat = source_obj.rotation_euler.to_quaternion()

    # Combine: first apply source rotation, then track rotation
    quat = track_quat @ source_quat

    # Get the source object's location (the pivot point)
    source_location = source_obj.location.copy()

    # Rotate the source location around world origin
    rotated_source_location = track_quat @ source_location

    # Final position: track position + rotated offset from origin
    final_position = (
        -part.x * scale + rotated_source_location.x,
        part.z * scale + rotated_source_location.y,
        part.y * scale + rotated_source_location.z
    )

    target_collection = collection if collection else bpy.context.collection

    # The environment context is deferred directly into _apply_material

    # Copy parent
    new_obj = source_obj.copy()
    if source_obj.data:
        new_obj.data = source_obj.data.copy()

    new_obj.location = final_position
    new_obj.rotation_mode = 'QUATERNION'
    new_obj.rotation_quaternion = quat

    # Store track data as custom properties for model generation
    new_obj["pt_part_type"] = part.part_type
    new_obj["pt_x"] = part.x
    new_obj["pt_y"] = part.y
    new_obj["pt_z"] = part.z
    new_obj["pt_rotation"] = part.rotation
    new_obj["pt_rotation_axis"] = part.rotation_axis
    new_obj["pt_color"] = part.color

    # Apply material
    _apply_material(new_obj, part.color, environment)

    target_collection.objects.link(new_obj)

    # Copy children
    for child in source_obj.children:
        new_child = child.copy()
        if child.data:
            new_child.data = child.data.copy()
        new_child.parent = new_obj
        new_child.matrix_parent_inverse = child.matrix_parent_inverse.copy()

        # Apply material to children too
        _apply_material(new_child, part.color, environment)

        target_collection.objects.link(new_child)

    return new_obj


def resolve_theme(part_color: int, map_environment: int) -> int:
    """Determines the active environment palette for the mesh."""
    if part_color in (1, 2, 3):
        return part_color
    
    # Map index 0->1, 1->2, 2->3
    return map_environment + 1


def _apply_material(obj: bpy.types.Object, part_color: int, map_environment: int):
    """Dynamically caches overriding materials and maps them perfectly into mesh slots."""
    theme = resolve_theme(part_color, map_environment)
    
    if obj.data is not None and hasattr(obj.data, 'materials'):
        for i, mat in enumerate(obj.data.materials):
            if mat is None:
                continue
                
            mat_base_name = mat.name.lower().split('.')[0]
            target_hex = None
            
            # Custom block color?
            if part_color in CUSTOM_COLORS and mat_base_name == "blocksurface":
                target_hex = CUSTOM_COLORS[part_color]
            # Environment theme override?
            elif theme in ENVIRONMENT_OVERRIDES and mat_base_name in ENVIRONMENT_OVERRIDES[theme]:
                target_hex = ENVIRONMENT_OVERRIDES[theme][mat_base_name]
                
            if target_hex is not None:
                obj.data.materials[i] = get_override_material(mat, target_hex)


# =============================================================================
# Operators
# =============================================================================

class POLYTRACKV2_OT_import(bpy.types.Operator):
    bl_idname = "polytrack_v2.import_track"
    bl_label = "Import Track"
    bl_description = "Import a PolyTrack track string (supports PolyTrack1 and PolyTrack2)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.polytrack_v2_props
        export_string = props.track_string.strip()

        if not export_string:
            self.report({'ERROR'}, "No track string provided")
            return {'CANCELLED'}

        result = decode_track(export_string)
        if result is None:
            self.report({'ERROR'}, "Failed to decode track string")
            return {'CANCELLED'}

        metadata, track_data = result

        # Create a new collection for the track
        if props.create_collection:
            collection_name = metadata.name or "Imported Track"
            track_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(track_collection)
        else:
            track_collection = bpy.context.collection

        # Store environment on the collection for model generation
        track_collection["pt_environment"] = track_data.environment

        # Instance all parts
        created = 0
        missing_parts = set()
        self.report({'INFO'}, str(track_data.environment))
        for part in track_data.parts:
            obj = instance_track_part(
                part,
                track_data.environment,
                props.scale,
                track_collection
            )
            if obj:
                created += 1
            else:
                try:
                    missing_parts.add(TrackPartId(part.part_type).name)
                except ValueError:
                    missing_parts.add(f"Unknown({part.part_type})")

        # Report results
        version = "v2" if export_string.startswith("PolyTrack2") else "v1"
        msg = f"Imported '{metadata.name}' ({version}): {created}/{len(track_data.parts)} parts"
        if metadata.author:
            msg += f" by {metadata.author}"

        if missing_parts:
            self.report({'WARNING'}, f"{msg}. Missing models: {', '.join(sorted(missing_parts))}")
        else:
            self.report({'INFO'}, msg)

        return {'FINISHED'}


class POLYTRACKV2_OT_list_missing(bpy.types.Operator):
    bl_idname = "polytrack_v2.list_missing"
    bl_label = "List Missing Parts"
    bl_description = "List all track part names that don't have models in the scene"

    def execute(self, context):
        missing = []
        for part_id in TrackPartId:
            if part_id.name not in bpy.data.objects:
                missing.append(part_id.name)

        if missing:
            self.report({'INFO'},
                        f"Missing {len(missing)} models: {', '.join(missing)}")
            print("Missing track part models:")
            for name in missing:
                print(f"  - {name}")
        else:
            self.report({'INFO'}, "All track part models are present!")

        return {'FINISHED'}



# ---------------------------------------------------------------------------
# Model definitions  (transcribed from the game's JS track-part config)
# Each entry: (TrackPartId enum name, [(scene_name, mesh_name, opts), ...])
# scene_name is kept for readability only — lookup is by mesh_name alone.
# opts keys: flipX, flipY, flipZ, offset=(x,y,z), scale=(x,y,z),
#            euler=(rx,ry,rz) in radians XYZ order
# ---------------------------------------------------------------------------

MISSING_MODEL_DEFS = [
    # ── RoadWide ──────────────────────────────────────────────────────────
    ("ToWideLeft",               [("RoadWide", "ToWideSide",            {"flipX": True})]),
    ("ToWideRight",              [("RoadWide", "ToWideSide",            {})]),
    ("SlopeUpLeftWide",          [("RoadWide", "SlopeUpWide",           {"flipX": True})]),
    ("SlopeUpRightWide",         [("RoadWide", "SlopeUpWide",           {})]),
    ("SlopeDownLeftWide",        [("RoadWide", "SlopeDownWide",         {"flipX": True})]),
    ("SlopeDownRightWide",       [("RoadWide", "SlopeDownWide",         {})]),
    ("SlopeUpLongLeftWide",      [("RoadWide", "SlopeUpLongWide",       {"flipX": True})]),
    ("SlopeUpLongRightWide",     [("RoadWide", "SlopeUpLongWide",       {})]),
    ("SlopeDownLongLeftWide",    [("RoadWide", "SlopeDownLongWide",     {"flipX": True})]),
    ("SlopeDownLongRightWide",   [("RoadWide", "SlopeDownLongWide",     {})]),
    ("SlopeLeftWide",            [("RoadWide", "SlopeWide",             {"flipX": True})]),
    ("SlopeRightWide",           [("RoadWide", "SlopeWide",             {})]),
    ("SlopeUpVerticalLeftWide",  [("RoadWide", "SlopeUpVerticalWide",   {})]),
    ("SlopeUpVerticalRightWide", [("RoadWide", "SlopeUpVerticalWide",   {"flipX": True})]),
    ("SlopeToVerticalLeftWide",  [("RoadWide", "SlopeToVerticalWide",   {"flipX": True})]),
    ("SlopeToVerticalRightWide", [("RoadWide", "SlopeToVerticalWide",   {})]),

    # ── Road turns / tilted ───────────────────────────────────────────────
    ("TurnSLeft",                [("Road", "TurnS",                     {"flipX": True})]),
    ("TurnSRight",               [("Road", "TurnS",                     {})]),
    ("TurnSLongLeft",            [("Road", "TurnSLong",                 {"flipX": True})]),
    ("TurnSLongRight",           [("Road", "TurnSLong",                 {})]),
    ("StraightTilted",           [("Road", "Straight",                  {
                                      "offset": (0, 5, 0),
                                      "scale":  (1, 0.894425810573391, 1),
                                      "euler":  (0, 0, -0.46364760900081),
                                  })]),
    ("ToTiltedLeft",             [("Road", "ToTilted",                  {"flipX": True, "offset": (0, 5, 0)})]),
    ("ToTiltedRight",            [("Road", "ToTilted",                  {"offset": (0, 5, 0)})]),

    # ── Pillar composites ─────────────────────────────────────────────────
    ("PlanePillarBottom",        [("Planes", "Plane",                   {}),
                                  ("Pillar", "SurfacePillarBottom",     {})]),
    ("PlanePillarShort",         [("Planes", "Plane",                   {}),
                                  ("Pillar", "SurfacePillarShort",      {})]),
    ("StraightPillarBottom",     [("Road",   "Straight",                {}),
                                  ("Pillar", "SurfacePillarBottom",     {})]),
    ("StraightPillarShort",      [("Road",   "Straight",                {}),
                                  ("Pillar", "SurfacePillarShort",      {})]),
    ("TurnSharpPillarBottom",    [("Road",   "TurnSharp",               {}),
                                  ("Pillar", "SurfacePillarBottom",     {})]),
    ("TurnSharpPillarShort",     [("Road",   "TurnSharp",               {}),
                                  ("Pillar", "SurfacePillarShort",      {})]),
    ("IntersectionTPillarBottom",    [("Road",   "IntersectionT",       {}),
                                      ("Pillar", "SurfacePillarBottom", {})]),
    ("IntersectionTPillarShort",     [("Road",   "IntersectionT",       {}),
                                      ("Pillar", "SurfacePillarShort",  {})]),
    ("IntersectionCrossPillarBottom",[("Road",   "IntersectionCross",   {}),
                                      ("Pillar", "SurfacePillarBottom", {})]),
    ("IntersectionCrossPillarShort", [("Road",   "IntersectionCross",   {}),
                                      ("Pillar", "SurfacePillarShort",  {})]),

    # ── WallTrack flipY variants ──────────────────────────────────────────
    ("WallTrackTop",             [("WallTrack", "WallTrackBottom",            {"flipY": True})]),
    ("WallTrackTopCorner",       [("WallTrack", "WallTrackBottomCorner",      {"flipY": True})]),
    ("WallTrackTopInnerCorner",  [("WallTrack", "WallTrackBottomInnerCorner", {"flipY": True})]),

    # ── Block flipY variants ──────────────────────────────────────────────
    ("BlockSlopeVerticalTop",             [("Blocks", "BlockSlopeVertical",             {"flipY": True})]),
    ("BlockSlopeVerticalCornerTop",       [("Blocks", "BlockSlopeVerticalCornerBottom", {"flipY": True})]),
    ("BlockSlopeVerticalInnerCornerTop",  [("Blocks", "BlockSlopeVerticalInnerCorner",  {"flipY": True})]),

    # ── Block normal ──────────────────────────────────────────────────────
    ("BlockSlopeVerticalBottom",          [("Blocks", "BlockSlopeVertical",             {})]),
    ("BlockSlopeVerticalInnerCornerBottom",[("Blocks","BlockSlopeVerticalInnerCorner",  {})]),

    # ── Plane slope vertical ──────────────────────────────────────────────
    ("PlaneSlopeVerticalBottom",          [("Planes", "PlaneSlopeVertical",             {})]),

    # ── Half-block / half-plane slopes ───────────────────────────────────
    ("HalfBlockSlopeBottomLeft",  [("Blocks", "HalfBlockSlopeBottom", {})]),
    ("HalfBlockSlopeBottomRight", [("Blocks", "HalfBlockSlopeBottom", {"flipX": True})]),
    ("HalfBlockSlopeTopLeft",     [("Blocks", "HalfBlockSlopeTop",    {"flipX": True})]),
    ("HalfBlockSlopeTopRight",    [("Blocks", "HalfBlockSlopeTop",    {})]),
    ("HalfPlaneSlopeBottomLeft",  [("Planes", "HalfPlaneSlopeBottom", {})]),
    ("HalfPlaneSlopeBottomRight", [("Planes", "HalfPlaneSlopeBottom", {"flipX": True})]),
    ("HalfPlaneSlopeTopLeft",     [("Planes", "HalfPlaneSlopeTop",    {"flipX": True})]),
    ("HalfPlaneSlopeTopRight",    [("Planes", "HalfPlaneSlopeTop",    {})]),

    # ── PlaneWall slopes ──────────────────────────────────────────────────
    ("PlaneWallSlopeLeft",         [("Planes", "PlaneWallSlope",         {})]),
    ("PlaneWallSlopeRight",        [("Planes", "PlaneWallSlope",         {"flipX": True})]),
    ("PlaneWallSlopeUpLeft",       [("Planes", "PlaneWallSlopeUp",       {})]),
    ("PlaneWallSlopeUpRight",      [("Planes", "PlaneWallSlopeUp",       {"flipX": True})]),
    ("PlaneWallSlopeDownLeft",     [("Planes", "PlaneWallSlopeDown",     {})]),
    ("PlaneWallSlopeDownRight",    [("Planes", "PlaneWallSlopeDown",     {"flipX": True})]),
    ("PlaneWallSlopeUpLongLeft",   [("Planes", "PlaneWallSlopeUpLong",   {})]),
    ("PlaneWallSlopeUpLongRight",  [("Planes", "PlaneWallSlopeUpLong",   {"flipX": True})]),
    ("PlaneWallSlopeDownLongLeft", [("Planes", "PlaneWallSlopeDownLong", {})]),
    ("PlaneWallSlopeDownLongRight",[("Planes", "PlaneWallSlopeDownLong", {"flipX": True})]),

    # ── Signs ─────────────────────────────────────────────────────────────
    ("SignArrowLeft",             [("Signs", "SignArrowRight", {"flipX": True})]),
    ("SignArrowDown",             [("Signs", "SignArrowUp",    {"flipY": True})]),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_mesh_object(scene_name: str, mesh_name: str):
    """
    Find a mesh object by name from the current Blender scene.
    scene_name is unused but kept for readability of the definitions above.
    Falls back to prefix match to handle Blender's .001 suffixes.
    """
    obj = bpy.data.objects.get(mesh_name)
    if obj and obj.type == 'MESH':
        return obj
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name.startswith(mesh_name + "."):
            return obj
    return None

def _apply_opts_to_bm(bm: bmesh.types.BMesh, opts: dict):
    # Game axes in Blender space: X→X, Y→Z, Z→-Y

    # 1. Non-uniform scale: remap game (sx, sy, sz) → Blender (sx, sz, sy)
    if "scale" in opts:
        gx, gy, gz = opts["scale"]
        bmesh.ops.transform(bm,
                            matrix=Matrix.Diagonal((gx, gz, gy, 1.0)),
                            verts=bm.verts)

    # 2. Euler rotation: game XYZ euler → remap axes
    #    game X-axis = Blender X, game Y-axis = Blender Z, game Z-axis = Blender -Y
    if "euler" in opts:
        rx, ry, rz = opts["euler"]
        rot_mat = Euler((rx, -rz, ry), 'XYZ').to_quaternion().to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=rot_mat, verts=bm.verts)

    # 3. Flip axes: remap game flips to Blender space
    flip_x = opts.get("flipX", False)
    flip_y = opts.get("flipY", False)
    flip_z = opts.get("flipZ", False)

    if flip_x or flip_y or flip_z:
        bx = -1.0 if flip_x else 1.0
        by = -1.0 if flip_z else 1.0
        bz = -1.0 if flip_y else 1.0

        # Capture max Z (game Y) BEFORE flipping
        if flip_y:
            max_z = max(v.co.z for v in bm.verts)

        bmesh.ops.transform(bm,
                            matrix=Matrix.Diagonal((bx, by, bz, 1.0)),
                            verts=bm.verts)
        if flip_x ^ flip_y ^ flip_z:
            for face in bm.faces:
                face.normal_flip()

        # Translate back up by the pre-flip max so it sits at Z=0..max
        # instead of -max..0
        if flip_y:
            bmesh.ops.translate(bm, vec=Vector((0, 0, max_z)), verts=bm.verts)

    # 4. Offset: game (ox, oy, oz) → Blender (ox, -oz, oy), scaled by 5
    # 4. Offset: game (ox, oy, oz) → Blender (ox, -oz, oy), NO scaling
    #    The offset is already in world units, not grid units
    if "offset" in opts:
        ox, oy, oz = opts["offset"]
        bmesh.ops.translate(bm,
                            vec=Vector((ox, -oz, oy)),
                            verts=bm.verts)

def _build_model(part_name: str, sources: list,
                 target_collection: bpy.types.Collection) -> bool:
    """
    Build one composite model object from one or more source meshes,
    add it to target_collection named exactly after part_name.
    Returns True on success.
    """
    combined_bm = bmesh.new()

    for (scene_name, mesh_name, opts) in sources:
        src_obj = _find_mesh_object(scene_name, mesh_name)
        if src_obj is None:
            combined_bm.free()
            return False

        # Pull geometry into a temp bmesh, bake local transform, apply opts
        tmp_bm = bmesh.new()
        tmp_bm.from_mesh(src_obj.data)
        bmesh.ops.transform(tmp_bm,
                            matrix=src_obj.matrix_local,
                            verts=tmp_bm.verts)
        _apply_opts_to_bm(tmp_bm, opts)

        # Merge into combined
        tmp_mesh = bpy.data.meshes.new("_pt_tmp")
        tmp_bm.to_mesh(tmp_mesh)
        tmp_bm.free()
        combined_bm.from_mesh(tmp_mesh)
        bpy.data.meshes.remove(tmp_mesh)

    combined_bm.normal_update()

    final_mesh = bpy.data.meshes.new(part_name)
    combined_bm.to_mesh(final_mesh)
    combined_bm.free()
    final_mesh.update()

    obj = bpy.data.objects.new(part_name, final_mesh)
    target_collection.objects.link(obj)

    # Copy materials from the first source so colours work on import
    first_src = _find_mesh_object(sources[0][0], sources[0][1])
    if first_src:
        for mat in first_src.data.materials:
            obj.data.materials.append(mat)

    return True


# ---------------------------------------------------------------------------
# Operator execute() — drop this into POLYTRACKV2_OT_generate_merged
# ---------------------------------------------------------------------------

def execute_generate_missing(self, context):
    out_col_name = "PolyTrack_GeneratedModels"

    if out_col_name in bpy.data.collections:
        out_col = bpy.data.collections[out_col_name]
    else:
        out_col = bpy.data.collections.new(out_col_name)
        bpy.context.scene.collection.children.link(out_col)

    generated     = 0
    skipped       = 0
    skipped_names = []

    for (part_name, sources) in MISSING_MODEL_DEFS:
        if part_name in bpy.data.objects:
            continue  # already exists, nothing to do

        ok = _build_model(part_name, sources, out_col)
        if ok:
            generated += 1
        else:
            skipped += 1
            skipped_names.append(part_name)

    msg = f"Generated {generated} model(s) into '{out_col_name}'."
    if skipped:
        self.report({'WARNING'},
                    msg + f" Skipped {skipped} (source mesh not found in scene): "
                    + ", ".join(skipped_names[:8])
                    + ("..." if len(skipped_names) > 8 else ""))
    else:
        self.report({'INFO'}, msg)

    return {'FINISHED'}

class POLYTRACKV2_OT_generate_merged(bpy.types.Operator):
    bl_idname = "polytrack_v2.generate_merged"
    bl_label = "Generate Merged Models"
    bl_description = "Generate filler block models by merging overlapping track parts (like the game does)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return execute_generate_missing(self, context)


# =============================================================================
# Panel & Properties
# =============================================================================

class PolyTrackV2Properties(bpy.types.PropertyGroup):
    track_string: StringProperty(
        name="Track String",
        description="PolyTrack export string (starts with PolyTrack1 or PolyTrack2)",
        default=""
    )

    scale: FloatProperty(
        name="Scale",
        description="Scale multiplier for part positions",
        default=5.0,
        min=0.001,
        max=1000.0
    )

    create_collection: BoolProperty(
        name="Create Collection",
        description="Create a new collection for imported parts",
        default=True
    )


class POLYTRACKV2_PT_main_panel(bpy.types.Panel):
    bl_label = "PolyTrack v2 Importer"
    bl_idname = "POLYTRACKV2_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyTrack v2'

    def draw(self, context):
        layout = self.layout
        props = context.scene.polytrack_v2_props

        # Import section
        box = layout.box()
        box.label(text="Import", icon='IMPORT')
        box.prop(props, "track_string", text="")
        box.prop(props, "scale")
        box.prop(props, "create_collection")
        box.operator("polytrack_v2.import_track", icon='IMPORT')

        layout.separator()

        # Tools section
        box = layout.box()
        box.label(text="Tools", icon='TOOL_SETTINGS')
        box.operator("polytrack_v2.list_missing", icon='QUESTION')
        box.operator("polytrack_v2.generate_merged", icon='MOD_BUILD')


# =============================================================================
# Registration
# =============================================================================

classes = (
    PolyTrackV2Properties,
    POLYTRACKV2_OT_import,
    POLYTRACKV2_OT_list_missing,
    POLYTRACKV2_OT_generate_merged,
    POLYTRACKV2_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.polytrack_v2_props = bpy.props.PointerProperty(type=PolyTrackV2Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.polytrack_v2_props


if __name__ == "__main__":
    register()
