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

from math import radians

import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, IntProperty
import bmesh
from bmesh.ops import spin

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (dataCorrect, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


def get_lathed_geometry(node, verts, edges, cent, axis, dvec, angle, steps):

    bm = bmesh_from_pydata(verts, edges, [])
    geom = bm.verts[:] + bm.edges[:]

    spin(bm, geom=geom, cent=cent, axis=axis, dvec=dvec, angle=angle, steps=steps, use_duplicate=0)

    if node.remove_doubles:
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=node.dist)

    v = [v.co[:] for v in bm.verts]
    p = [[i.index for i in p.verts] for p in bm.faces[:]]
    bm.free()
    return v, p


class SvLatheNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SvLatheNode'
    bl_label = 'Sv Lathe Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    remove_doubles = BoolProperty(name='merge', description='Remove doubles', update=updateNode)
    dist = FloatProperty(name="merge distance", default=0.0001, update=updateNode)
    Degrees = FloatProperty(name="Degrees", default=360.0, update=updateNode)
    Steps = IntProperty(name="Steps", default=20, min=0, update=updateNode)
    cent = FloatVectorProperty(name='cent', size=3, update=updateNode)
    dvec = FloatVectorProperty(name='dvec', size=3, update=updateNode)
    axis = FloatVectorProperty(name='axis', size=3, update=updateNode, default=(0, 0, 1))

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Verts', 'Verts')
        self.inputs.new('StringsSocket', 'Edges', 'Edges')
        self.inputs.new('VerticesSocket', 'cent', 'cent').prop_name = 'cent'
        self.inputs.new('VerticesSocket', 'axis', 'axis').prop_name = 'axis'
        self.inputs.new('VerticesSocket', 'dvec', 'dvec').prop_name = 'dvec'
        self.inputs.new('StringsSocket', 'Degrees', 'Degrees').prop_name = 'Degrees'
        self.inputs.new('StringsSocket', 'Steps', 'Steps').prop_name = 'Steps'

        self.outputs.new('VerticesSocket', 'Verts', 'Verts')
        self.outputs.new('StringsSocket', 'Poly', 'Poly')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "remove_doubles", text="merge")

    def nothing_to_process(self):

        if not (self.inputs['Verts'].links and self.outputs['Verts'].links):
            return True

    def process(self):

        if self.nothing_to_process():
            return

        inputs = self.inputs

        def get_socket(x):
            r = inputs[x].sv_get()
            r = dataCorrect(r)
            return r

        socket_names = ['Verts', 'Edges', 'cent', 'axis', 'dvec', 'Degrees', 'Steps']
        data = list(map(get_socket, socket_names))
        mverts, medges, mcent, maxis, mdvec, mDegrees, mSteps = data
        
        verts_match_edges = medges and (len(medges) == len(mverts))

        verts_out, faces_out = [], []
        for idx, verts in enumerate(mverts):

            if not verts:
                continue

            # here we find defaults if the node gets incongruent input
            final_values = {
                'verts': verts,
                'edges': [],
                'cent': [0, 0, 0],
                'axis': [0, 0, 1],
                'dvec': [0, 0, 0],
                'angle': radians(self.Degrees),
                'steps': self.Steps
            }

            ''' [], or by idx, if idx present'''
            if medges:
                if verts_match_edges or (idx <= len(medges)-1):
                    final_values['edges'] = medges[idx]

            ''' by idx, if idx present, else last. if none then default'''
            if mcent:
                idxr = idx if (idx <= len(mcent[0])-1) else -1
                final_values['cent'] = mcent[0][idxr]

            if maxis:
                idxr = idx if (idx <= len(maxis[0])-1) else -1
                final_values['axis'] = maxis[0][idxr]

            if mdvec:
                idxr = idx if (idx <= len(mdvec[0])-1) else -1
                final_values['dvec'] = mdvec[0][idxr]

            if mDegrees:
                if isinstance(mDegrees, list):
                    neatList = mDegrees[0][0]
                    idxr = min(len(neatList)-1, idx)
                    angle = neatList[idxr]
                    final_values['angle'] = radians(float(angle))

            if mSteps:
                if isinstance(mSteps, list):
                    neatList = mSteps[0][0]
                    idxr = min(len(neatList)-1, idx)
                    steps = neatList[idxr]
                    final_values['steps'] = max(0, int(steps))

            v, p = get_lathed_geometry(self, **final_values)
            verts_out.append(v)
            faces_out.append(p)

        SvSetSocketAnyType(self, 'Verts', verts_out)
        SvSetSocketAnyType(self, 'Poly', faces_out)


