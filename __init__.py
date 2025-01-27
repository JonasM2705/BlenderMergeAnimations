bl_info = {
    "name": "Combine Animations",
    "blender": (3, 3, 0),
    "category": "Animation",
    "author": "JonasM2705",
    "description": "Combina animaciones de un Armature a otro en el frame actual."
}

import bpy

class CombineAnimationsOperator(bpy.types.Operator):
    """Operador para combinar animaciones de un armature a otro"""
    bl_idname = "animation.combine_animations"
    bl_label = "Combinar Animaciones"

    def execute(self, context):
        source_armature = context.scene.source_armature
        target_armature = context.object

        if not source_armature or target_armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Selecciona un Armature válido.")
            return {'CANCELLED'}

        # Verificar que el armature fuente tiene animaciones
        if not source_armature.animation_data or not source_armature.animation_data.action:
            self.report({'ERROR'}, "El Armature1 no tiene animaciones para copiar.")
            return {'CANCELLED'}

        # Crear acción en el armature objetivo si no tiene
        if not target_armature.animation_data:
            target_armature.animation_data_create()
        if not target_armature.animation_data.action:
            target_armature.animation_data.action = bpy.data.actions.new(name=f"{target_armature.name}_action")

        source_action = source_armature.animation_data.action
        target_action = target_armature.animation_data.action

        # Copiar todos los fotogramas clave de la animación
        target_frame = context.scene.frame_current
        for fcurve in source_action.fcurves:
            data_path = fcurve.data_path
            array_index = fcurve.array_index

            # Buscar o crear un fcurve correspondiente en el armature objetivo
            target_fcurve = None
            for t_fcurve in target_action.fcurves:
                if t_fcurve.data_path == data_path and t_fcurve.array_index == array_index:
                    target_fcurve = t_fcurve
                    break

            if not target_fcurve:
                target_fcurve = target_action.fcurves.new(data_path, index=array_index)

            # Copiar keyframes al frame actual
            for keyframe in fcurve.keyframe_points:
                original_frame = keyframe.co[0]
                new_frame = target_frame + (original_frame - fcurve.range()[0])
                new_keyframe = target_fcurve.keyframe_points.insert(frame=new_frame, value=keyframe.co[1], options={'FAST'})
                new_keyframe.interpolation = keyframe.interpolation

        self.report({'INFO'}, "Animación copiada correctamente.")
        return {'FINISHED'}

class CombineAnimationsPanel(bpy.types.Panel):
    """Panel de la interfaz para combinar animaciones"""
    bl_label = "Combine Animations"
    bl_idname = "ANIMATION_PT_combine_animations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Merge Animations"

    def draw(self, context):
        layout = self.layout

        layout.prop(context.scene, "source_armature")
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
        description="Selecciona el Armature con las animaciones a copiar",
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.source_armature

if __name__ == "__main__":
    register()