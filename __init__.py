bl_info = {
    "name": "Combine Animations",
    "blender": (3, 3, 0),
    "category": "Animation",
    "author": "JonasM2705",
    "description": "Combina animaciones de un Armature a otro en el frame actual."
}

import bpy
import os

class CombineAnimationsOperator(bpy.types.Operator):
    """Combina animaciones desde un Armature en escena o archivo FBX"""
    bl_idname = "animation.combine_animations"
    bl_label = "Combinar Animaciones"

    def execute(self, context):
        target_armature = context.object
        source_armature = context.scene.source_armature
        fbx_path = context.scene.fbx_filepath
        imported_objects = []

        if not target_armature or target_armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Selecciona un Armature objetivo válido.")
            return {'CANCELLED'}

        # Si se especifica una ruta FBX, importar el archivo y buscar un Armature
        if fbx_path and os.path.isfile(bpy.path.abspath(fbx_path)):
            before_import = set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=bpy.path.abspath(fbx_path))
            after_import = set(bpy.data.objects)
            imported_objects = list(after_import - before_import)

            source_armature = next((obj for obj in imported_objects if obj.type == 'ARMATURE'), None)
            if not source_armature:
                self.report({'ERROR'}, "No se encontró un Armature en el archivo FBX.")
                return {'CANCELLED'}

        elif not source_armature:
            self.report({'ERROR'}, "Debes seleccionar un Armature fuente o un archivo FBX.")
            return {'CANCELLED'}

        if not source_armature.animation_data or not source_armature.animation_data.action:
            self.report({'ERROR'}, "El Armature fuente no tiene animaciones.")
            return {'CANCELLED'}

        # Crear acción si no existe en el armature destino
        if not target_armature.animation_data:
            target_armature.animation_data_create()
        if not target_armature.animation_data.action:
            target_armature.animation_data.action = bpy.data.actions.new(name=f"{target_armature.name}_action")

        source_action = source_armature.animation_data.action
        target_action = target_armature.animation_data.action
        target_frame = context.scene.frame_current

        for fcurve in source_action.fcurves:
            data_path = fcurve.data_path
            array_index = fcurve.array_index

            # Buscar o crear fcurve correspondiente en destino
            target_fcurve = next((fc for fc in target_action.fcurves
                                  if fc.data_path == data_path and fc.array_index == array_index), None)
            if not target_fcurve:
                target_fcurve = target_action.fcurves.new(data_path, index=array_index)

            for keyframe in fcurve.keyframe_points:
                original_frame = keyframe.co[0]
                new_frame = target_frame + (original_frame - fcurve.range()[0])
                new_key = target_fcurve.keyframe_points.insert(frame=new_frame, value=keyframe.co[1], options={'FAST'})
                new_key.interpolation = keyframe.interpolation

        # Limpiar objetos importados
        for obj in imported_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        self.report({'INFO'}, "Animación copiada correctamente.")
        return {'FINISHED'}

class CombineAnimationsPanel(bpy.types.Panel):
    bl_label = "Combine Animations"
    bl_idname = "ANIMATION_PT_combine_animations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animations"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "source_armature")
        layout.prop(context.scene, "fbx_filepath")
        layout.operator("animation.combine_animations", text="Combinar Animaciones")

classes = [
    CombineAnimationsOperator,
    CombineAnimationsPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.source_armature = bpy.props.PointerProperty(
        name="Armature1",
        type=bpy.types.Object,
        description="Selecciona el Armature con las animaciones a copiar"
    )
    bpy.types.Scene.fbx_filepath = bpy.props.StringProperty(
        name="Archivo FBX",
        description="Ruta al archivo FBX que contiene la animación",
        subtype='FILE_PATH'
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.source_armature
    del bpy.types.Scene.fbx_filepath

if __name__ == "__main__":
    register()
