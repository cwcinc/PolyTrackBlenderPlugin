bl_info = {
    "name": "PolyTrack Importer",
    "author": "cwcinc",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > PolyTrack",
    "description": "Import PolyTrack track strings and instance parts",
    "category": "Import-Export",
}

import bpy
import zlib
import math
from bpy.props import StringProperty, FloatProperty, BoolProperty
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import IntEnum
from mathutils import Matrix, Euler, Quaternion

# =============================================================================
# Track Part ID Enum
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
    SlopePillar = 40
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
    SlopePillarShort = 84
    BlockSlopeUp = 85
    BlockSlopeDown = 86
    BlockSlopeVerticalTop = 87
    BlockSlopeVerticalBottom = 88
    PlaneSlopeVerticalBottom = 90
    StartWide = 91
    PlaneStart = 92
    PlaneStartWide = 93
    TurnShortLeftWide = 94
    TurnShortRightWide = 95
    TurnLongLeftWide = 96
    TurnLongRightWide = 97
    SlopeUpVertical = 98
    PlaneSlopePillar = 99
    PlaneSlopePillarShort = 100
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
                start_order = _read_uint32_le(data, i)
                i += 4

            track_data.add_part(x, y, z, part_type, rotation, rotation_axis,
                                color, checkpoint_order, start_order)

    return track_data


def decode_track(export_string: str) -> Optional[Tuple[TrackMetadata, TrackData]]:
    if not export_string.startswith("PolyTrack1"):
        return None

    compressed_data = base62_decode(export_string[10:])
    if compressed_data is None:
        return None

    base62_data = decompress_zlib(compressed_data, to_string=True)
    if base62_data is None or not isinstance(base62_data, str):
        return None

    compressed_data2 = base62_decode(base62_data)
    if compressed_data2 is None:
        return None

    data = decompress_zlib(compressed_data2, to_string=False)
    if data is None or not isinstance(data, bytes):
        return None

    if len(data) < 1:
        return None
    track_name_length = data[0]

    if len(data) < 1 + track_name_length:
        return None
    track_name = data[1:1 + track_name_length].decode('utf-8')

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
    track_data = _from_byte_array(track_data_offset, data, CHECKPOINT_TYPES, START_TYPES)

    if track_data is None:
        return None

    return (TrackMetadata(name=track_name, author=author), track_data)


# =============================================================================
# Blender Instancing
# =============================================================================

def quaternion_from_axis_angle(axis: tuple[float, float, float], angle: float) -> Quaternion:
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
    Create a quaternion that:
    1. Starts with "up" (Z+)
    2. Rotates around the up axis by rotation * pi/2 radians
    3. Applies an axis rotation to orient toward the specified axis

    rotation_axis:
        0: Z+ (no additional rotation)
        1: Z- (flip 180° around X)
        2: X+ (rotate 90° around Y)
        3: X- (rotate -90° around Y)
        4: Y+ (rotate -90° around X)
        5: Y- (rotate 90° around X)
    """
    if (rotation_axis % 2 == 0) or (rotation % 2 == 1):
        rotation += 2

    if (rotation_axis % 2 == 1) and (rotation_axis >= 3):
        rotation += 2

    # Step 1: Rotation around up axis (Z) by rotation * pi/2
    up_rotation = quaternion_from_axis_angle((0, 0, 1), (rotation) * math.pi / 2)

    # Step 2: Axis rotation based on rotation_axis
    axis_rotations = {
        0: Quaternion((1, 0, 0, 0)),  # Z+: identity (no rotation)
        1: quaternion_from_axis_angle((1, 0, 0), math.pi),  # Z-: 180° around X
        2: quaternion_from_axis_angle((0, 1, 0), -math.pi / 2),  # X+: 90° around Y
        3: quaternion_from_axis_angle((0, 1, 0), math.pi / 2),  # X-: -90° around Y
        4: quaternion_from_axis_angle((1, 0, 0), -math.pi / 2),  # Y+: -90° around X
        5: quaternion_from_axis_angle((1, 0, 0), math.pi / 2),  # Y-: 90° around X
    }

    axis_rotation = axis_rotations[rotation_axis]

    # Apply axis rotation first, then up rotation
    # (axis_rotation orients the direction, up_rotation spins around that direction)
    return axis_rotation @ up_rotation

TRACK_COLORS = {
    0: (100, 100, 100),     # Default
    1: (100, 100, 100),     # Summer
    2: (80, 119, 178),      # Winter
    3: (153, 114, 64),      # Desert

    32: (19, 19, 19),       # Custom0 (Black)
    33: (80, 27, 27),       # Custom1 (Red)
    34: (127, 77, 43),      # Custom2 (Orange)
    35: (147, 134, 45),     # Custom3 (Yellow)
    36: (42, 94, 48),       # Custom4 (Green)
    37: (35, 99, 99),       # Custom5 (Blue)
    38: (32, 36, 75),       # Custom6 (Purple)
    39: (89, 39, 89),       # Custom7 (Pink)
    40: (48, 35, 24)        # Custom8 (Brown)
}

def norm_color(color: int) -> tuple[float, float, float]:
    col = TRACK_COLORS[color]
    return (col[0] / 255, col[1] / 255, col[2] / 255)

def instance_track_part(
        part_type: int,
        x: int,
        y: int,
        z: int,
        rotation: int,
        rotation_axis: int,
        color: int,
        scale: float = 5.0,
        collection: bpy.types.Collection = None
) -> Optional[bpy.types.Object]:
    try:
        part_name = TrackPartId(part_type).name
    except ValueError:
        return None

    if part_name not in bpy.data.objects:
        return None

    source_obj = bpy.data.objects[part_name]

    # Get quaternion from lookup table
    effective_rotation = round(rotation) % 4
    track_quat = quaternion_from_rotation_axis(effective_rotation, rotation_axis).copy()

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
        -x * scale + rotated_source_location.x,
        z * scale + rotated_source_location.y,
        y * scale + rotated_source_location.z
    )

    target_collection = collection if collection else bpy.context.collection

    # Copy parent
    new_obj = source_obj.copy()
    if source_obj.data:
        new_obj.data = source_obj.data

    new_obj.location = final_position
    new_obj.rotation_mode = 'QUATERNION'
    new_obj.rotation_quaternion = quat

    new_obj["block_color"] = norm_color(color)

    target_collection.objects.link(new_obj)

    # Copy children
    for child in source_obj.children:
        new_child = child.copy()
        if child.data:
            new_child.data = child.data
        new_child.parent = new_obj
        new_child.matrix_parent_inverse = child.matrix_parent_inverse.copy()
        new_child["block_color"] = norm_color(color)
        target_collection.objects.link(new_child)

    return new_obj


# =============================================================================
# Operators
# =============================================================================

class POLYTRACK_OT_import(bpy.types.Operator):
    bl_idname = "polytrack.import_track"
    bl_label = "Import Track"
    bl_description = "Import a PolyTrack track string"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.polytrack_props
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

        # Instance all parts
        created = 0
        missing_parts = set()

        for part in track_data.parts:
            obj = instance_track_part(
                part.part_type,
                part.x,
                part.y,
                part.z,
                part.rotation,
                part.rotation_axis,
                part.color,
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
        msg = f"Imported '{metadata.name}': {created}/{len(track_data.parts)} parts"
        if metadata.author:
            msg += f" by {metadata.author}"

        if missing_parts:
            self.report({'WARNING'}, f"{msg}. Missing models: {', '.join(sorted(missing_parts))}")
        else:
            self.report({'INFO'}, msg)

        return {'FINISHED'}


class POLYTRACK_OT_list_missing(bpy.types.Operator):
    bl_idname = "polytrack.list_missing"
    bl_label = "List Missing Parts"
    bl_description = "List all track part names that don't have models in the scene"

    def execute(self, context):
        missing = []
        for part_id in TrackPartId:
            if part_id.name not in bpy.data.objects:
                missing.append(part_id.name)

        if missing:
            self.report({'INFO'},
                        f"Missing {len(missing)} models: {', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}")
            # Print full list to console
            print("Missing track part models:")
            for name in missing:
                print(f"  - {name}")
        else:
            self.report({'INFO'}, "All track part models are present!")

        return {'FINISHED'}


# =============================================================================
# Panel & Properties
# =============================================================================

class PolyTrackProperties(bpy.types.PropertyGroup):
    track_string: StringProperty(
        name="Track String",
        description="PolyTrack export string (starts with PolyTrack1)",
        default=""
    )

    scale: FloatProperty(
        name="Scale",
        description="Scale multiplier for part positions",
        default=1.0,
        min=0.001,
        max=1000.0
    )

    create_collection: BoolProperty(
        name="Create Collection",
        description="Create a new collection for imported parts",
        default=True
    )


class POLYTRACK_PT_main_panel(bpy.types.Panel):
    bl_label = "PolyTrack Importer"
    bl_idname = "POLYTRACK_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyTrack'

    def draw(self, context):
        layout = self.layout
        props = context.scene.polytrack_props

        layout.label(text="Track String:")
        layout.prop(props, "track_string", text="")

        layout.separator()

        layout.prop(props, "scale")
        layout.prop(props, "create_collection")

        layout.separator()

        layout.operator("polytrack.import_track", icon='IMPORT')
        layout.operator("polytrack.list_missing", icon='QUESTION')


# =============================================================================
# Registration
# =============================================================================

classes = (
    PolyTrackProperties,
    POLYTRACK_OT_import,
    POLYTRACK_OT_list_missing,
    POLYTRACK_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.polytrack_props = bpy.props.PointerProperty(type=PolyTrackProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.polytrack_props


if __name__ == "__main__":
    register()