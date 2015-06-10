import bpy
import bpy.utils.previews
from bpy.types import Menu, Operator
import os
import time

preview_collections = {}


class NODEVIEW_PE_SV_ops(Operator):

    bl_idname = "nodes.pie_menu_enum"
    bl_label = "Add Quick Node"

    mode_options = [
        ("option1", "option1", "", 'CURVE_DATA', 0),
        ("option2", "option2", "", "", 1),
        ("Prefs", "Prefs", "", "PREFERENCES", 2)
    ]

    selected_mode = bpy.props.EnumProperty(
        items=mode_options,
        description="offers....",
        default="option1"
    )

    def execute(self, context):
        print('added ', self.selected_mode)
        import bpy

        if self.selected_mode == 'Prefs':
            import addon_utils

            module_name = "sverchok"
            addon_utils.modules_refresh()

            bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
            bpy.context.user_preferences.active_section = "ADDONS"
            bpy.data.window_managers['WinMan'].addon_search = "sverch"

            try:
                mod = addon_utils.addons_fake_modules.get(module_name)
                info = addon_utils.module_bl_info(mod)
                if not info["show_expanded"]:
                    info["show_expanded"] = True
            except:
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

        return {'FINISHED'}


class NODEVIEW_MT_PIE_Menu(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Select Mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator_enum("nodes.pie_menu_enum", "selected_mode")
        pie.operator("object.add", icon='CURVE_DATA').type = 'EMPTY'
        pie.menu("NODEVIEW_MT_AddGeneratorsExt", icon='PLUGIN')


def register():
    bpy.utils.register_class(NODEVIEW_PE_SV_ops)
    bpy.utils.register_class(NODEVIEW_MT_PIE_Menu)


def unregister():
    bpy.utils.unregister_class(NODEVIEW_MT_PIE_Menu)
    bpy.utils.unregister_class(NODEVIEW_PE_SV_ops)
