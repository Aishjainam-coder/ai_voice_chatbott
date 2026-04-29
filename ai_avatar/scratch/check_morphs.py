import pygltflib
import sys
import os

def list_morphs(glb_path):
    try:
        gltf = pygltflib.GLTF2().load(glb_path)
        morph_targets = set()
        for mesh in gltf.meshes:
            for primitive in mesh.primitives:
                if primitive.targets:
                    # The names of morph targets are usually in the extras or extras/targetNames
                    if mesh.extras and "targetNames" in mesh.extras:
                        for name in mesh.extras["targetNames"]:
                            morph_targets.add(name)
        
        if not morph_targets:
            print("No named morph targets found in metadata. Checking primitives...")
            # Some models don't have names in extras, but three.js might find them elsewhere
            # or they are just indexed.
        
        print("Found Morph Targets:")
        for name in sorted(list(morph_targets)):
            print(f" - {name}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    glb = "static/avatar.glb"
    if os.path.exists(glb):
        list_morphs(glb)
    else:
        print(f"File {glb} not found")
