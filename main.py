bl_info = {
    "name": "Block Instancer from Position Data",
    "blender": (3, 0, 0),
    "category": "Object",
}

import bpy
import re


class OBJECT_OT_instance_blocks(bpy.types.Operator):
    bl_idname = "object.instance_blocks_from_text"
    bl_label = "Instance Blocks from Position Data"
    bl_options = {'REGISTER', 'UNDO'}

    position_data: bpy.props.StringProperty(
        name="Position Data",
        description="Paste position data here",
        default=""
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "position_data")

    def execute(self, context):
        # Find the Block mesh
        if "Block" not in bpy.data.objects:
            self.report({'ERROR'}, "No object named 'Block' found in scene")
            return {'CANCELLED'}

        block_obj = bpy.data.objects["Block"]

        # Parse positions - handles multiple formats
        positions = self.parse_positions(self.position_data)

        if not positions:
            self.report({'ERROR'}, "No valid positions found in data")
            return {'CANCELLED'}

        # Create instances
        created = 0
        for pos in positions:
            new_obj = block_obj.copy()
            new_obj.location = pos
            context.collection.objects.link(new_obj)
            created += 1

        self.report({'INFO'}, f"Created {created} instances")
        return {'FINISHED'}

    def parse_positions(self, data):
        positions = []

        # Try different formats
        # Format 1: (x, y, z) or [x, y, z]
        tuple_pattern = r'[\(\[]?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*[\)\]]?'

        # Format 2: x y z (space separated)
        space_pattern = r'(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)'

        # Format 3: x,y,z (comma only, no spaces required)
        csv_pattern = r'(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)'

        # Try tuple/bracket format first
        matches = re.findall(tuple_pattern, data)
        if matches:
            for m in matches:
                positions.append((float(m[0]), float(m[1]), float(m[2])))
            return positions

        # Try space-separated
        matches = re.findall(space_pattern, data)
        if matches:
            for m in matches:
                positions.append((float(m[0]), float(m[1]), float(m[2])))
            return positions

        # Try CSV
        matches = re.findall(csv_pattern, data)
        if matches:
            for m in matches:
                positions.append((float(m[0]), float(m[1]), float(m[2])))
            return positions

        return positions


class OBJECT_PT_block_instancer_panel(bpy.types.Panel):
    bl_label = "Block Instancer"
    bl_idname = "OBJECT_PT_block_instancer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.instance_blocks_from_text")


def register():
    bpy.utils.register_class(OBJECT_OT_instance_blocks)
    bpy.utils.register_class(OBJECT_PT_block_instancer_panel)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_instance_blocks)
    bpy.utils.unregister_class(OBJECT_PT_block_instancer_panel)


if __name__ == "__main__":
    register()