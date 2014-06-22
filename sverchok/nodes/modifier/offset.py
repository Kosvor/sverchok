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

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty

from utils.sv_bmesh_utils import bmesh_from_pydata
from node_tree import SverchCustomTreeNode
from data_structure import (changable_sockets, multi_socket,
                            fullList, dataCorrect,
                            SvSetSocketAnyType, SvGetSocketAnyType)
from mathutils import Vector, Matrix


class SvOffsetNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Doing offset of polygons '''
    bl_idname = 'SvOffsetNode'
    bl_label = 'Offset Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    offset = FloatProperty(name='opp', description='distance of offset',
                  default=0.04,
                  update=updateNode)
    nsides = IntProperty(name='n_', description='number of sides',
                  default=0,
                  update=updateNode)
    radius = FloatProperty(name='adj1', description='radius of inset',
                  default=0.04,
                  update=updateNode)
    keepface = BoolProperty(name='kp', description='to keep face inside',
                  default=True,
                  update=updateNode)


    def draw_buttons(self, context, layout):
        layout.prop(self, 'keepface', text='keepface')

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vers', 'Vers')
        self.inputs.new('StringsSocket', "Pols", "Pols")
        self.inputs.new('StringsSocket', "Offset", "Offset").prop_name = 'offset'
        self.inputs.new('StringsSocket', "N sides", "N sides").prop_name = 'nsides'
        self.inputs.new('StringsSocket', "Radius", "Radius").prop_name = 'radius'
        self.outputs.new('VerticesSocket', 'Vers', 'Vers')
        self.outputs.new('StringsSocket', "Edgs", "Edgs")
        self.outputs.new('StringsSocket', "Pols", "Pols")

    def update(self):
        
        if self.outputs['Vers'].links and self.inputs['Vers'].links:
                vertices = Vector_generate(SvGetSocketAnyType(self, self.inputs['Vers']))
                faces = SvGetSocketAnyType(self, self.inputs['Pols'])
                offset = SvGetSocketAnyType(self, self.inputs['Offset'])[0]
                nsides = SvGetSocketAnyType(self, self.inputs['N sides'])[0]
                radius = SvGetSocketAnyType(self, self.inputs['Radius'])[0]
                outv = []
                oute = []
                outp = []
                for verts_obj, faces_obj in zip(vertices, faces):
                    # this is for one object
                    bme = bmesh_from_pydata(verts_obj, [], faces_obj)
                    geom_in = bme.verts[:]+bme.edges[:]+bme.faces[:]
                    bmesh.ops.recalc_face_normals(bme, faces=bme.faces[:])
                    list_0 = [ f.index for f in bme.faces if f.select and f.is_valid ]
                    # calculation itself
                    result = \
                        self.Offset_pols(bme, list_0, offset, radius, nsides, self.keepface)
                    outv.append(result[0])
                    oute.append(result[1])
                    outp.append(result[2])
                if self.outputs['Vers'].links:
                    SvSetSocketAnyType(self, 'Vers', outv)
                if self.outputs['Edgs'].links:
                    SvSetSocketAnyType(self, 'Edgs', oute)
                if self.outputs['Pols'].links:
                    SvSetSocketAnyType(self, 'Pols', outp)
    
    
    # #################
    #   part from ofset operator in extra tools
    #   that in own place based completely on addon by zmj100
    #   in russian is called "Круговая порука", Various artists
    # #################
    
    def a_rot(self, ang, rp, axis, q):
        return (Matrix.Rotation(ang, 3, axis) * (q - rp)) + rp

    # #################
    # opp -     offset amount
    # n_ -      number of sides
    # adj1 -    radius 
    # en0 -     corner type bmesh or triangle, we need bmesh opt0
    # kp -      keep face, not delete it.
    # #################
    
    def Offset_pols(self, bme, list_0, opp, adj1, n_, kp):

        list_del = [] # what for?
        for fi in list_0:
            f = bme.faces[fi]
            f.select_set(0)
            list_del.append(f)
            f.normal_update()
            list_2 = [v.index for v in f.verts]
            dict_0 = {}
            list_1 = []
            n = len(list_2)
            for i in range(n):
                dict_0[i] = []
                p = (bme.verts[ list_2[i] ].co).copy()
                p1 = (bme.verts[ list_2[(i - 1) % n] ].co).copy()
                p2 = (bme.verts[ list_2[(i + 1) % n] ].co).copy()
                dict_0[i].append(bme.verts[list_2[i]])
                vec1 = p - p1
                vec2 = p - p2
                ang = vec1.angle(vec2)
                adj = opp / tan(ang * 0.5)
                h = (adj ** 2 + opp ** 2) ** 0.5
                if round(degrees(ang)) == 180 or round(degrees(ang)) == 0.0:
                    p6 = a_rot(radians(90), p, vec1, p - \
                                ((f.normal).normalized() * opp))
                    list_1.append(p6)
                else:
                    p6 = a_rot(-radians(90), p, ((p - (vec1.normalized() * adj)) - \
                                (p - (vec2.normalized() * adj))), p - \
                                ((f.normal).normalized() * h))
                    list_1.append(p6)

            list_2 = []
            n1_ = len(list_1)
            for j in range(n1_):
                q = list_1[j]
                q1 = list_1[(j - 1) % n1_]
                q2 = list_1[(j + 1) % n1_]
                vec1_ = q - q1
                vec2_ = q - q2
                ang_ = vec1_.angle(vec2_)
                if round(degrees(ang_)) == 180 or round(degrees(ang_)) == 0.0:
                    bme.verts.new(q)
                    bme.verts.index_update()
                    list_2.append(bme.verts[-1])
                    dict_0[j].append(bme.verts[-1])
                else:
                    opp_ = adj1
                    # radius flag deleted - have to depennd on n_. if 0 no radius
                    if not n_:
                        h_ = adj1 * (1 / cos(ang_ * 0.5))
                        d = adj1
                    elif n_:
                        h_ = opp_ / sin(ang_ * 0.5)
                        d = opp_ / tan(ang_ * 0.5)

                    q3 = q - (vec1_.normalized() * d)
                    q4 = q - (vec2_.normalized() * d)
                    rp_ = q - ((q - ((q3 + q4) * 0.5)).normalized() * h_)
                    axis_ = vec1_.cross(vec2_)
                    vec3_ = rp_ - q3
                    vec4_ = rp_ - q4
                    rot_ang = vec3_.angle(vec4_)
                    list_3 = []
                    
                    for o in range(n_ + 1):
                        q5 = a_rot((rot_ang * o / n_), rp_, axis_, q4)
                        bme.verts.new(q5)
                        bme.verts.index_update()
                        dict_0[j].append(bme.verts[-1])
                        list_3.append(bme.verts[-1])
                    list_3.reverse()
                    list_2.extend(list_3)

            
            # if kp == True: #not solved
            bme.faces.new(list_2)
            bme.faces.index_update()
            bme.faces[-1].select_set(1)

            n2_ = len(dict_0)
            for o in range(n2_):
                list_a = dict_0[o]
                list_b = dict_0[(o + 1) % n2_]
                bme.faces.new( [ list_a[0], list_b[0], list_b[-1], list_a[1] ] )
                bme.faces.index_update()
            
            # keeping triangulation of polygons commented
            #if en0 == 'opt0':
            for k in dict_0:
                if len(dict_0[k]) > 2:
                    bme.faces.new(dict_0[k])
                    bme.faces.index_update()
            #if en0 == 'opt1':
            #    for k_ in dict_0:
            #        q_ = dict_0[k_][0]
            #        dict_0[k_].pop(0)
            #        n3_ = len(dict_0[k_])
            #        for kk in range(n3_ - 1):
            #            bme.faces.new( [ dict_0[k_][kk], dict_0[k_][(kk + 1) % n3_], q_ ] )
            #            bme.faces.index_update()
        
        # this is old
        del_ = [bme.faces.remove(f) for f in list_del]
        del del_
        # i think, it deletes doubling faces
        
        # from Linus Yng solidify example
        edges = []
        faces = []
        # clean and assign
        bme.verts.index_update()
        bme.edges.index_update()
        bme.faces.index_update()
        for edge in bm.edges[:]:
            edges.append([v.index for v in edge.verts[:]])
        verts = [vert.co[:] for vert in bm.verts[:]]
        for face in bme.faces:
            faces.append([v.index for v in face.verts[:]])
        bme.clear()
        bme.free()
        return (verts, edges, faces)




def register():
    bpy.utils.register_class(SvOffsetNode)


def unregister():
    bpy.utils.unregister_class(SvOffsetNode)
if __name__ == '__main__':
    register()