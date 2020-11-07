import bpy, bmesh, random, mathutils


def build_bottle():
    bpy.ops.mesh.primitive_circle_add(radius=1,
                                      enter_editmode=False,
                                      location=(0, 0, 0))
    bottle_shell = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].render_levels = 6
    bpy.context.object.modifiers["Subdivision"].levels = 3

    body_length = random.uniform(1, 7)
    body_taper = random.uniform(.1, .4)

    neck_length = random.uniform(.5, 3)
    neck_taper_out = body_taper + random.uniform(1, 2)

    top_length = random.uniform(.3, .9)

    print('body length:', body_length)
    print('body taper:', body_taper)
    print('neck length:', neck_length)
    print('neck taper out:', neck_taper_out)
    print('top length:', top_length)

    bpy.context.scene.eevee.use_ssr = True
    bpy.context.scene.eevee.use_ssr_refraction = True

    # Body length
    bpy.ops.object.mode_set(mode='EDIT')
    bmesh.from_edit_mesh(bpy.context.object.data)
    extrude(0, 0, body_length)

    cleanup_bottom()

    liquid = make_liquid(body_length)

    # re-select first mesh
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bottle_shell

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    for v in mesh.verts:
        if v.co[2] > body_length * .99:
            v.select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    # continue extruding

    # body taper to neck
    extrude(0, 0, 0)
    transform_resize(body_taper, body_taper, body_taper)

    # extrude neck
    extrude(0, 0, 0)
    transform_translate(0, 0, neck_length)

    # lip for bottle top
    extrude(0, 0, 0)
    transform_resize(neck_taper_out, neck_taper_out, neck_taper_out)

    # length of top piece
    extrude(0, 0, top_length)
    extrude(0, 0, 0)

    # shrink down, make last extrusion, seal shut
    transform_resize(0.586486, 0.586486, 0.586486)
    extrude(0, 0, 0)
    bpy.ops.mesh.merge(type='CENTER')
    bpy.ops.object.mode_set(mode='OBJECT')

    set_up_glass_shader()

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = liquid
    set_up_liquid_shader()

    # bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bottle_shell
    # bpy.data.objects[bottle_shell.name].select_set(True)
    bpy.data.objects[liquid.name].select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)


def make_liquid(body_length):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.duplicate()
    liquid = bpy.context.active_object
    transform_resize(0.9, 0.9, 0.9)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    for v in mesh.verts:
        if v.co[2] >= (body_length * .98):
            v.select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    extrude(0, 0, 0)
    transform_resize(0.5, 0.5, 0.5)
    extrude(0, 0, 0)
    bpy.ops.mesh.merge(type='CENTER')
    bpy.ops.object.mode_set(mode='OBJECT')
    transform_translate(0, 0, .08)
    return liquid


def set_up_liquid_shader():
    # Get material
    liquid_mat = bpy.data.materials.get("liquid_xyz")
    if liquid_mat is None:
        # create material
        liquid_mat = bpy.data.materials.new(name="liquid_xyz")
    liquid_mat.use_nodes = True
    ob = bpy.context.object
    if ob.data.materials:
        ob.data.materials[0] = liquid_mat
    else:
        ob.data.materials.append(liquid_mat)

    nodes = liquid_mat.node_tree.nodes
    node = nodes.get('Principled BSDF')
    if node:
        nodes.remove(node)
    if not bpy.data.materials['liquid_xyz'].node_tree.nodes.get('Glass BSDF'):
        # bpy.data.materials['liquid_xyz'].node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        bpy.data.materials['liquid_xyz'].node_tree.nodes.new('ShaderNodeBsdfGlass')
        bpy.data.materials['liquid_xyz'].node_tree.nodes.new("ShaderNodeBsdfTransparent")
        bpy.data.materials['liquid_xyz'].node_tree.nodes.new("ShaderNodeMixShader")

        glass_bsdf_output = bpy.data.materials['liquid_xyz'].node_tree.nodes["Glass BSDF"].outputs['BSDF']
        transparent_bsdf_output = bpy.data.materials['liquid_xyz'].node_tree.nodes["Transparent BSDF"].outputs['BSDF']
        mix_shader_output = bpy.data.materials['liquid_xyz'].node_tree.nodes["Mix Shader"].outputs['Shader']
        mix_shader_input1 = bpy.data.materials['liquid_xyz'].node_tree.nodes["Mix Shader"].inputs[1]
        mix_shader_input2 = bpy.data.materials['liquid_xyz'].node_tree.nodes["Mix Shader"].inputs[2]
        mat_output_surface_input = bpy.data.materials['liquid_xyz'].node_tree.nodes["Material Output"].inputs['Surface']

        bpy.data.materials['liquid_xyz'].node_tree.links.new(glass_bsdf_output, mix_shader_input1)
        bpy.data.materials['liquid_xyz'].node_tree.links.new(transparent_bsdf_output, mix_shader_input2)
        bpy.data.materials['liquid_xyz'].node_tree.links.new(mix_shader_output, mat_output_surface_input)

        bpy.data.materials["liquid_xyz"].node_tree.nodes["Glass BSDF"].inputs[0].default_value = (
        0.39959, 0.000400819, 0, 1)
        bpy.data.materials["liquid_xyz"].node_tree.nodes["Glass BSDF"].inputs[2].default_value = 1.333
        bpy.data.materials["liquid_xyz"].node_tree.nodes["Transparent BSDF"].inputs[0].default_value = (
            0.076476, 0.0854893, 0.0803021, 1)

        # set factor value
        bpy.data.materials["liquid_xyz"].node_tree.nodes["Mix Shader"].inputs[0].default_value = 0.8

    bpy.context.object.active_material.use_backface_culling = True
    bpy.context.object.active_material.use_screen_refraction = True
    bpy.context.object.active_material.use_sss_translucency = True
    bpy.context.object.active_material.blend_method = 'HASHED'


def set_up_glass_shader():
    # Get material
    glass_mat = bpy.data.materials.get("glass")
    if glass_mat is None:
        # create material
        glass_mat = bpy.data.materials.new(name="glass")
    glass_mat.use_nodes = True
    ob = bpy.context.object
    if ob.data.materials:
        ob.data.materials[0] = glass_mat
    else:
        ob.data.materials.append(glass_mat)

    nodes = glass_mat.node_tree.nodes
    node = nodes.get('Principled BSDF')
    if node:
        nodes.remove(node)
    if not bpy.data.materials['glass'].node_tree.nodes.get('Glass BSDF'):
        bpy.data.materials['glass'].node_tree.nodes.new('ShaderNodeBsdfGlass')
        # bpy.data.materials['glass'].node_tree.nodes["Glass BSDF"]
        # bpy.data.materials['glass'].node_tree.nodes["Material Output"]
        # bpy.data.materials['glass'].node_tree.nodes["Glass BSDF"].inputs.keys()
        # bpy.data.materials['glass'].node_tree.nodes["Glass BSDF"].outputs.keys()
        glass_bsdf_output = bpy.data.materials['glass'].node_tree.nodes["Glass BSDF"].outputs['BSDF']
        mat_output_surface_output = bpy.data.materials['glass'].node_tree.nodes["Material Output"].inputs['Surface']
        bpy.data.materials['glass'].node_tree.links.new(glass_bsdf_output, mat_output_surface_output)
    bpy.context.object.active_material.use_backface_culling = True
    bpy.context.object.active_material.use_screen_refraction = True
    bpy.context.object.active_material.use_sss_translucency = True
    bpy.data.materials["glass"].node_tree.nodes["Glass BSDF"].inputs[0].default_value = (
        0.0880155, 0.0856212, 0.0863521, 1)


def cleanup_bottom():
    # look at all of the faces of the cube, find the one that is 'facing' the positive direction on the y axis
    # bpy.ops.object.mode_set(mode='EDIT')
    mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in mesh.verts:
        if v.co[2] == 0.0:
            v.select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    # go back and clean up the bottom
    extrude(0, 0, 0)
    transform_resize(0.794349, 0.794349, 0.794349)
    extrude(0, 0, 0)
    bpy.ops.mesh.merge(type='CENTER')


def extrude(x, y, z):
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip": False, "mirror": False},
                                     TRANSFORM_OT_translate={"value": (x, y, z),
                                                             "orient_type": 'GLOBAL',
                                                             "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                             "orient_matrix_type": 'GLOBAL',
                                                             "constraint_axis": (False, False, False), "mirror": False,
                                                             "use_proportional_edit": False,
                                                             "proportional_edit_falloff": 'SMOOTH',
                                                             "proportional_size": 1,
                                                             "use_proportional_connected": False,
                                                             "use_proportional_projected": False, "snap": False,
                                                             "snap_target": 'CLOSEST', "snap_point": (0, 0, 0),
                                                             "snap_align": False, "snap_normal": (0, 0, 0),
                                                             "gpencil_strokes": False, "cursor_transform": False,
                                                             "texture_space": False, "remove_on_cancel": False,
                                                             "release_confirm": False, "use_accurate": False})


def transform_resize(x, y, z):
    bpy.ops.transform.resize(value=(x, y, z), orient_type='GLOBAL',
                             orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True,
                             use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1,
                             use_proportional_connected=False, use_proportional_projected=False)


def transform_translate(x, y, z):
    bpy.ops.transform.translate(value=(x, y, z), orient_type='GLOBAL',
                                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False,
                                proportional_edit_falloff='SMOOTH', proportional_size=1,
                                use_proportional_connected=False, use_proportional_projected=False)



# delete everything in the scene
def clear_scene():
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)


if __name__ == "__main__":
    build_bottle()
