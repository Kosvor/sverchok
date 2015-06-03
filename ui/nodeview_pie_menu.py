import bpy
import bpy.utils.previews
from bpy.types import Menu, Operator
import os

preview_collections = {}


class NODEVIEW_PE_SV_ops(Operator):

    bl_idname = "nodes.pie_menu_enum"
    bl_label = "Add Quick Node"

    pcoll = preview_collections.get("main")
    if pcoll:
        ICON = pcoll["vec_icon"].icon_id
    else:
        ICON = 'CURVE_DATA'

    mode_options = [
        ("option1", "option1", "", ICON, 0),
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

        pcoll = preview_collections.get("main")
        if pcoll:
            ICON = pcoll["vec_icon"].icon_id
        else:
            ICON = 'CURVE_DATA'

        pie = layout.menu_pie()
        pie.operator_enum("nodes.pie_menu_enum", "selected_mode")
        pie.operator("object.add", icon_value=ICON).type = 'EMPTY'


def register():
    pcoll = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    # load a preview thumbnail of a file and store in the previews collection
    pcoll.load("vec_icon", os.path.join(my_icons_dir, "VEC_IMG.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    bpy.utils.register_class(NODEVIEW_PE_SV_ops)
    bpy.utils.register_class(NODEVIEW_MT_PIE_Menu)


def unregister():
    bpy.utils.unregister_class(NODEVIEW_MT_PIE_Menu)
    bpy.utils.unregister_class(NODEVIEW_PE_SV_ops)
