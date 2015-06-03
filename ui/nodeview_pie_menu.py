import bpy
from bpy.types import Menu, Operator


class NODEVIEW_PE_SV_ops(Operator):

    bl_idname = "nodes.pie_menu_enum"
    bl_label = "Add Quick Node"

    mode_options = [
        ("option1", "option1", "", "CURVE_DATA", 0),
        ("option2", "option2", "", "", 1),
        ("option3", "option3", "", "", 2)
    ]

    selected_mode = bpy.props.EnumProperty(
        items=mode_options,
        description="offers....",
        default="option1"
    )

    def execute(self, context):
        print('added ', self.selected_mode)
        return {'FINISHED'}


class NODEVIEW_MT_PIE_Menu(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Select Mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator_enum("nodes.pie_menu_enum", "selected_mode")


def register():
    bpy.utils.register_class(NODEVIEW_PE_SV_ops)
    bpy.utils.register_class(NODEVIEW_MT_PIE_Menu)


def unregister():
    bpy.utils.unregister_class(NODEVIEW_MT_PIE_Menu)
    bpy.utils.unregister_class(NODEVIEW_PE_SV_ops)
