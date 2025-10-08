"""
This is a tutorial and standalone script to parse a Hero Forge file.

This repository is designed to parse and import 3D models from Hero Forge,
a popular online character creator. The files work together to read the
binary data, reconstruct the 3D geometry, and import it into Blender.

Here's a breakdown of how the different files work together:

ByteIO.py: This is a utility for handling binary data. It provides a set of
tools for reading and writing different data types, such as integers, floats,
and strings. It also provides a way to seek to different parts of a file,
which is essential for parsing binary data.

HeroForge.py: This is the core of the parser. It uses ByteIO.py to read a
Hero Forge file and reconstruct the 3D geometry. It also provides a set of
classes for representing the different parts of a 3D model, such as the
vertices, faces, and skeleton.

bl_loader.py: This is a Blender addon that uses HeroForge.py to import a
Hero Forge file into Blender. It provides a user interface for selecting a
file and importing it into the current scene.

To use this script, run it from the command line and pass the path to your
.ckb file as an argument:

python tutorial.py path/to/your/file.ckb
"""

import argparse
import sys
from HeroForge import HeroFile

def main():
    """
    Main function to parse the Hero Forge file.
    """
    parser = argparse.ArgumentParser(
        description="Parse a Hero Forge .ckb file and print its contents."
    )
    parser.add_argument("file_path", help="The path to the .ckb file to parse.")
    args = parser.parse_args()

    file_path = args.file_path

    try:
        # Create a new HeroFile object and pass it the path to your .ckb file.
        hf = HeroFile(file_path)
        # The read() method parses the file and populates the geometry properties.
        hf.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while parsing the file: {e}")
        sys.exit(1)

    # Once the file is parsed, you can access the different parts of the 3D model
    # from the HeroFile object. Here are some of the most important properties:
    #
    # hf.geometry.positions: A list of the vertices in the model. Each vertex is a
    # tuple of three floats (x, y, z).
    #
    # hf.geometry.index: A list of the faces in the model. Each face is a tuple of
    # three integers, which are the indices of the vertices that make up the face.
    #
    # hf.geometry.normals: A list of the normals in the model. Each normal is a
    # tuple of three floats (x, y, z).
    #
    # hf.geometry.uv: A list of the UV coordinates in the model. Each UV coordinate
    # is a tuple of two floats (u, v).
    #
    # hf.geometry.bones: A list of the bones in the model's skeleton. Each bone is
    # a HeroBone object, which has properties for the bone's name, parent, and
    # transformation matrix.

    # Print the number of vertices, faces, and bones in the model.
    print(f"Successfully parsed '{file_path}'")
    print(f"Vertices: {len(hf.geometry.positions)}")
    print(f"Faces: {len(hf.geometry.index) // 3}")
    print(f"Bones: {len(hf.geometry.bones)}")

    if hf.geometry.positions:
        # Print the first 10 vertices.
        print("\nFirst 10 vertices:")
        for i in range(min(10, len(hf.geometry.positions))):
            print(hf.geometry.positions[i])

    if hf.geometry.index:
        # Print the first 10 faces.
        print("\nFirst 10 faces:")
        for i in range(0, min(30, len(hf.geometry.index)), 3):
            print(hf.geometry.index[i:i+3])

    if hf.geometry.bones:
        # Print the names of all the bones.
        print("\nBones:")
        for bone in hf.geometry.bones:
            print(bone.name)

if __name__ == "__main__":
    main()