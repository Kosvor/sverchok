# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import itertools
import random
import re

import bpy
from bpy.props import (
    BoolProperty,
    StringProperty,
    FloatProperty,
    IntProperty)

from mathutils import Matrix, Vector

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

from sverchok.node_tree import (
    SverchCustomTreeNode,
    VerticesSocket,
    MatrixSocket,
    StringsSocket)

from sverchok.data_structure import (
    dataCorrect,
    fullList,
    updateNode,
    SvGetSocketAnyType)

from sverchok.nodes.basic_view.viewer_bmesh import (
    matrix_sanitizer,
    natural_plus_one,
    get_random_init)


def live_curve(curve_name, verts, edges, matrix, node):
    curves = bpy.data.curves
    objects = bpy.data.objects
    scene = bpy.context.scene

    # if curve data exists, pick it up else make new curve
    cu = curves.get(curve_name)
    if not cu:
        cu = curves.new(name=curve_name, type='CURVE')

    # if object reference exists, pick it up else make a new one
    obj = objects.get(curve_name)
    if not obj:
        obj = objects.new(curve_name, cu)
        scene.objects.link(obj)

    # break down existing splines entirely.
    if cu.splines:
        cu.splines.clear()

    cu.bevel_depth = node.depth
    cu.bevel_resolution = node.resolution
    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'

    # and rebuild
    for edge in edges:
        v0, v1 = verts[edge[0]], verts[edge[1]]
        full_flat = [v0[0], v0[1], v0[2], 0.0, v1[0], v1[1], v1[2], 0.0]

        # each spline has a default first coordinate but we need two.
        segment = cu.splines.new('POLY')
        segment.points.add(1)
        segment.points.foreach_set('co', full_flat)
        # print(cu.name)

    # print(curves[:])
    return obj


def make_curve_geometry(node, context, name, verts, *topology):
    edges, matrix = topology

    sv_object = live_curve(name, verts, edges, matrix, node)
    sv_object.hide_select = False

    if matrix:
        matrix = matrix_sanitizer(matrix)
        sv_object.matrix_local = matrix
    else:
        sv_object.matrix_local = Matrix.Identity(4)


# could be imported from bmeshviewr directly, it's almost identical
class SvCurveViewOp(bpy.types.Operator):

    bl_idname = "node.showhide_svcurve"
    bl_label = "Sverchok curve showhide"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')
    # obj_type = StringProperty(default='MESH')

    def hide_unhide(self, context, type_op):
        n = context.node
        k = n.basemesh_name + "_"

        # maybe do hash+(obj_name + treename)
        child = lambda obj: obj.type == "CURVE" and obj.name.startswith(k)
        objs = list(filter(child, bpy.data.objects))

        if type_op == 'hide_view':
            for obj in objs:
                obj.hide = n.state_view
            n.state_view = not n.state_view

        elif type_op == 'hide_render':
            for obj in objs:
                obj.hide_render = n.state_render
            n.state_render = not n.state_render

        elif type_op == 'hide_select':
            for obj in objs:
                obj.hide_select = n.state_select
            n.state_select = not n.state_select

        elif type_op == 'mesh_select':
            for obj in objs:
                obj.select = n.select_state_mesh
            n.select_state_mesh = not n.select_state_mesh

        elif type_op == 'random_mesh_name':
            n.basemesh_name = get_random_init()

    def execute(self, context):
        self.hide_unhide(context, self.fn_name)
        return {'FINISHED'}


# should inherit from bmeshviewer, many of these methods are largely identical.
class SvCurveViewerNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvCurveViewerNode'
    bl_label = 'SvCurve Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        name='Show',
        description='When enabled this will process incoming data',
        default=True,
        update=updateNode)

    basemesh_name = StringProperty(
        default='Alpha',
        update=updateNode,
        description='sets which base name the object will use, \
        use N-panel to pick alternative random names')

    material = StringProperty(default='', update=updateNode)
    grouping = BoolProperty(default=False)
    state_view = BoolProperty(default=True)
    state_render = BoolProperty(default=True)
    state_select = BoolProperty(default=True)
    select_state_mesh = BoolProperty(default=False)

    depth = FloatProperty(min=0.0, default=0.2, update=updateNode)
    resolution = IntProperty(min=0, default=3, update=updateNode)

    def sv_init(self, context):
        self.use_custom_color = True
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')

    def draw_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')
        sh = 'node.showhide_svcurve'

        def icons(button_type):
            icon = 'WARNING'
            if button_type == 'v':
                icon = 'RESTRICT_VIEW_' + ['ON', 'OFF'][self.state_view]
            elif button_type == 'r':
                icon = 'RESTRICT_RENDER_' + ['ON', 'OFF'][self.state_render]
            elif button_type == 's':
                icon = 'RESTRICT_SELECT_' + ['ON', 'OFF'][self.state_select]
            return icon

        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, "activate", text="UPD", toggle=True, icon=view_icon)

        row.operator(sh, text='', icon=icons('v')).fn_name = 'hide_view'
        row.operator(sh, text='', icon=icons('s')).fn_name = 'hide_select'
        row.operator(sh, text='', icon=icons('r')).fn_name = 'hide_render'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "grouping", text="Group", toggle=True)

        row = col.row(align=True)
        row.scale_y = 1
        row.prop(self, "basemesh_name", text="", icon='OUTLINER_OB_MESH')

        row = col.row(align=True)
        row.scale_y = 2
        row.operator(sh, text='Select / Deselect').fn_name = 'mesh_select'
        row = col.row(align=True)
        row.scale_y = 1

        row.prop_search(
            self, 'material', bpy.data, 'materials', text='',
            icon='MATERIAL_DATA')

        col = layout.column()
        col.prop(self, 'depth', text='depth radius')
        col.prop(self, 'resolution', text='surface resolution')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.separator()

        row = layout.row(align=True)
        sh = 'node.showhide_svcurve'
        row.operator(sh, text='Random Name').fn_name = 'random_mesh_name'

    def get_geometry_from_sockets(self):

        def get(socket_name):
            data = self.inputs[socket_name].sv_get(default=[])
            return dataCorrect(data)

        mverts = get('vertices')
        medges = get('edges')
        mmtrix = get('matrix')
        return mverts, medges, mmtrix

    def get_structure(self, stype, sindex):
        if not stype:
            return []

        try:
            j = stype[sindex]
        except IndexError:
            j = []
        finally:
            return j

    def process(self):
        if not (self.inputs['vertices'].is_linked and self.inputs['edges'].is_linked):
            # possible remove any potential existing geometry here too
            return

        # perhaps if any of mverts is [] this should already fail.
        mverts, *mrest = self.get_geometry_from_sockets()

        def get_edges_faces_matrices(obj_index):
            for geom in mrest:
                yield self.get_structure(geom, obj_index)

        # extend all non empty lists to longest of mverts or *mrest
        maxlen = max(len(mverts), *(map(len, mrest)))
        fullList(mverts, maxlen)
        for idx in range(2):
            if mrest[idx]:
                fullList(mrest[idx], maxlen)

        for obj_index, Verts in enumerate(mverts):
            if not Verts:
                continue

            data = get_edges_faces_matrices(obj_index)
            mesh_name = self.basemesh_name + "_" + str(obj_index)
            make_curve_geometry(self, bpy.context, mesh_name, Verts, *data)

        # print('object index:', obj_index)
        self.remove_non_updated_objects(obj_index)

        objs = self.get_children()
        # print('objs:', objs)

        if self.grouping:
            self.to_group(objs)

        # truthy if self.material is in .materials
        if bpy.data.materials.get(self.material):
            self.set_corresponding_materials(objs)

    def get_children(self):
        objects = bpy.data.objects
        objs = [obj for obj in objects if obj.type == 'CURVE']
        return [o for o in objs if o.name.startswith(self.basemesh_name + "_")]

    def remove_non_updated_objects(self, obj_index):
        objs = self.get_children()
        objs = [obj.name for obj in objs if int(obj.name.split("_")[-1]) > obj_index]
        if not objs:
            return

        curves = bpy.data.curves
        objects = bpy.data.objects
        scene = bpy.context.scene

        # remove excess objects
        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False
            scene.objects.unlink(obj)
            objects.remove(obj)

        # delete associated meshes
        for object_name in objs:
            curves.remove(curves[object_name])

    def to_group(self, objs):
        groups = bpy.data.groups
        named = self.basemesh_name

        # alias group, or generate new group and alias that
        group = groups.get(named, groups.new(named))

        for obj in objs:
            if obj.name not in group.objects:
                group.objects.link(obj)

    def set_corresponding_materials(self, objs):
        for obj in objs:
            obj.active_material = bpy.data.materials[self.material]


def register():
    bpy.utils.register_class(SvCurveViewerNode)
    bpy.utils.register_class(SvCurveViewOp)


def unregister():
    bpy.utils.unregister_class(SvCurveViewerNode)
    bpy.utils.unregister_class(SvCurveViewOp)