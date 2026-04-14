import math
from typing import List

import numpy as np
from pathlib import Path

try:
    from .ByteIO import ByteIO, split
except ImportError:
    from ByteIO import ByteIO, split
bone_names = {}
armature_name = ''


class HeroGeomerty:
    def __init__(self):
        self.index = []
        self.positions = []
        self.normals = []
        self.uv = []
        self.uv2 = []
        self.vertex_colors = {}
        self.shape_key_data = {}
        self.skin_indices = np.array([])  # type:np.ndarray
        self.additional_skin_indices = np.array([])  # type:np.ndarray
        self.skin_weights = np.array([])  # type:np.ndarray
        self.additional_skin_weights = np.array([])  # type:np.ndarray
        self.original_indices = []
        self.main_skeleton = False
        self.has_geometry = False
        self.skinned = False
        self.bounds = []
        self.scale = []
        self.offset = []
        self.bones = []  # type: List[HeroBone]
        self.poses = []
        self.locations = []


class HeroBone:

    def __init__(self):
        self.name = ''
        self.parent_id = -1
        self.bone_id = -1
        self.pos = []
        self.scale = []
        self.quat = []
        self.rot = []


class HeroFile:
    MAX_UINT8 = (2 ** 8) - 1
    MAX_UINT16 = (2 ** 16) - 1

    def __init__(self, path):
        self.reader = ByteIO(path=path)
        self.name = Path(path).name
        self.version = 0
        self.i32_count = 0
        self.i16_count = 0
        self.i8_count = 0
        self.i1_count = 0
        self.export_time = 0

        self.i32_offset = 0
        self.i16_offset = 0
        self.i8_offset = 0
        self.i1_offset = 0
        self.bit_cursor = 0

        self._i1_array = []

        self.options = {}
        self.geometry = HeroGeomerty()
        self.vertex_count = 0

    def read_float(self, offset=0):
        self.reader.seek(self.i32_offset + offset)
        ret = self.reader.read_float()
        self.i32_offset += 4
        return ret

    def read_uint32(self, offset=0):
        self.reader.seek(self.i32_offset + offset)
        val = self.read_float()
        ret = round(val)
        return ret

    def read_uint16(self, offset=0, increment=True):
        self.reader.seek(self.i16_offset + offset)
        ret = self.reader.read_uint16()
        if increment:
            self.i16_offset += 2
        return ret

    def read_int8(self, offset=0):
        self.reader.seek(self.i8_offset + offset)
        ret = self.reader.read_uint8()
        self.i8_offset += 1
        return ret

    def read_string(self, offset=0):
        self.reader.seek(self.i8_offset + offset)
        l = self.read_int8()
        ret = self.reader.read_ascii_string(l)
        self.i8_offset += len(ret)
        return ret

    def read_bit(self):
        bit = self._i1_array[self.bit_cursor]
        self.bit_cursor += 1
        return bit

    def get_quaternion_array(self, count):
        count *= 4
        result = np.zeros(count)
        for i in range(count):
            result[i] = self.read_uint16() / self.MAX_UINT16 * 2 - 1
        return result

    def get_position_array(self, count, scale):
        result = np.zeros(count * 3)
        x = (self.MAX_UINT16 - 2) / 2
        for i in range(count):
            for j in range(3):
                result[3 * i + j] = (self.read_uint16() - x) / x * scale
        return result

    def get_scale_array(self, count, scale):
        result = np.zeros(count * 3)
        for i in range(count):
            for j in range(3):
                result[3 * i + j] = self.read_uint16() / self.MAX_UINT16 * scale
        return result

    def read(self):
        reader = self.reader
        self.version = round(reader.read_float(), 2)
        self.get_start_points()
        with reader.save_current_pos():
            reader.seek(self.i1_offset)
            for _ in range(math.ceil(self.i1_count / 8)):
                byte = reader.read_int8()
                for i in range(8):
                    self._i1_array.append(bool(byte & (1 << i)))
        self._init_settings()
        self._init_indices()
        self._init_points()
        self._init_normals()
        self._init_uvs()
        self._init_vertex_colors()
        self._init_blends()
        self._init_weights()
        self._init_parent()
        try:
            self._init_poses();
        except:
            pass

    def get_bit(self):
        self.bit_cursor += 1
        return self._i1_array[self.bit_cursor - 1]

    def get_start_points(self):
        reader = self.reader
        if self.version >= 1.8:
            self.i32_count = self.reader.read_uint32()
            self.i16_count = self.reader.read_uint32()
            self.i8_count = self.reader.read_uint32()
            self.i1_count = self.reader.read_uint32()
        else:
            self.i32_count = reader.read_float_int32()
            self.i16_count = reader.read_float_int32()
            self.i8_count = reader.read_float_int32()
            self.i1_count = reader.read_float_int32()

        e = 20
        if self.version >= 1.4:
            e += 4
            self.export_time = self.reader.read_float()
        self.i32_offset = e
        self.i16_offset = self.i32_offset + 4 * self.i32_count
        self.i8_offset = self.i16_offset + 2 * self.i16_count
        self.i1_offset = self.i8_offset + self.i8_count

    def _init_settings(self):
        default_attributes = ["mesh", "normals", "uv1", "uv2", "blendTargets", "blendNormals", "weights", "animations",
                              "jointScales", "addon", "paintMapping", "singleParent", "frameMappings", "indices32bit",
                              "originalIndices", "vertexColors"]
        if self.version >= 1.2:
            default_attributes.append('posGroups')
        if self.version >= 1.25:
            default_attributes.append('uvSeams')
            default_attributes.append('rivets')

        r = {}
        for attr in default_attributes:
            if self.bit_cursor < self.i1_count:
                r[attr] = self.get_bit()
            else:
                r[attr] = False

        self.options = r

        if self.version >= 1.8:
            self.options.update({
                'mesh': True, 'normals': True, 'uv1': True, 'weights': True, 'indices32bit': True
            })

        if 'addon' in self.options and 'weights' in self.options:
            self.geometry.main_skeleton = not self.options['addon'] and self.options['weights']

    def _init_indices(self):
        if self.options['mesh']:
            indices_count = self.read_uint32()
            if self.options['indices32bit']:
                self.geometry.index = [self.read_uint32() for _ in range(indices_count)]
            else:
                self.geometry.index = [self.read_uint16() for _ in range(indices_count)]
            if self.options['originalIndices']:
                if self.options['indices32bit']:
                    self.geometry.original_indices = [self.read_uint32() for _ in range(indices_count)]
                else:
                    self.geometry.original_indices = [self.read_uint16() for _ in range(indices_count)]

    def _init_points(self):
        if self.options['mesh']:
            vertex_count = self.read_uint32() if self.options['indices32bit'] else self.read_uint16()
            self.vertex_count = vertex_count
            self.geometry.has_geometry = True
            bbox = [self.read_float() for _ in range(6)]
            scale = [bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2]]
            self.geometry.offset = [bbox[0] * scale[0], bbox[1] * scale[1], bbox[2] * scale[2]]
            self.geometry.bounds = [bbox[0:3], bbox[3:6]]
            verts = []
            for _ in range(vertex_count):
                x = self.read_uint16() / self.MAX_UINT16 * scale[0] + bbox[0]
                y = self.read_uint16() / self.MAX_UINT16 * scale[1] + bbox[1]
                z = self.read_uint16() / self.MAX_UINT16 * scale[2] + bbox[2]
                verts.append((x, y, z))
            self.geometry.positions = verts

    def _init_normals(self):
        if self.options['normals'] and self.vertex_count > 0:
            normals = []
            for _ in range(self.vertex_count):
                x = self.read_int8() / self.MAX_UINT8 * 2 - 1
                y = self.read_int8() / self.MAX_UINT8 * 2 - 1
                z_sign = 2 * self.get_bit() - 1
                z = z_sign * (1 - x ** 2 - y ** 2)
                normals.extend([x, y, z])
            self.geometry.normals = split(normals, 3)

    def _init_uvs(self):
        if self.options['uv1']:
            uv_layers = ['uv', 'uv2'] if self.options['uv2'] else ['uv']
            for uv_layer in uv_layers:
                bbox = [self.read_float() for _ in range(4)]
                scale = [bbox[2] - bbox[0], bbox[3] - bbox[1]]
                uv_data = []
                for _ in range(self.vertex_count):
                    u = self.read_uint16() / self.MAX_UINT16 * scale[0] + bbox[0]
                    v = self.read_uint16() / self.MAX_UINT16 * scale[1] + bbox[1]
                    uv_data.append((u, v))
                setattr(self.geometry, uv_layer, uv_data)

    def _init_vertex_colors(self):
        if self.options['vertexColors']:
            layer_count = self.read_uint8()
            for _ in range(layer_count):
                layer_name = self.read_string()
                vertex_colors = []
                for _ in range(self.vertex_count):
                    gray_value = self.read_uint8() / self.MAX_UINT8
                    vertex_colors.extend([gray_value, gray_value, gray_value, 1.0])
                self.geometry.vertex_colors[layer_name] = np.array(vertex_colors).reshape((-1, 4))

    def _init_blends(self):
        if self.options['blendTargets']:
            shape_key_count = self.read_uint8()
            if shape_key_count > 0:
                shape_key_data = {}
                for _ in range(shape_key_count):
                    shape_key_name = self.read_string()
                    bbox = [self.read_float() for _ in range(6)]
                    scale = [bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2]]
                    blend_data = []
                    for _ in range(self.vertex_count):
                        x = self.read_uint8() / self.MAX_UINT8 * scale[0] + bbox[0]
                        y = self.read_uint8() / self.MAX_UINT8 * scale[1] + bbox[1]
                        z = self.read_uint8() / self.MAX_UINT8 * scale[2] + bbox[2]
                        blend_data.extend([x, y, z])
                    shape_key_data[shape_key_name] = split(blend_data, 3)
                    if self.options['blendNormals']:
                        for _ in range(self.vertex_count):
                            self.read_uint8(), self.read_uint8(), self.get_bit()
                self.geometry.shape_key_data = shape_key_data

    def _init_weights(self):
        if self.options['weights']:
            self.geometry.skinned = True
            weights_per_vertex = self.read_uint8()
            additional_weights = max(0, weights_per_vertex - 4)
            skin_indices = np.zeros(4 * self.vertex_count, dtype=np.uint16)
            additional_skin_indices = np.zeros(additional_weights * self.vertex_count, dtype=np.uint16)
            loop_count = 4 if weights_per_vertex < 4 else weights_per_vertex
            for i in range(loop_count):
                if weights_per_vertex > i:
                    if i < 4:
                        for j in range(self.vertex_count):
                            skin_indices[4 * j + i] = self.read_uint16(2 * (j * weights_per_vertex + i), False)
                    else:
                        for j in range(self.vertex_count):
                            additional_skin_indices[j * additional_weights + (i - 4)] = self.read_uint16(
                                2 * (j * additional_weights + i), False)
            self.geometry.skin_indices = skin_indices.reshape((-1, loop_count,))
            self.geometry.additional_skin_indices = additional_skin_indices.reshape((-1, loop_count,))
            self.i16_offset += weights_per_vertex * self.vertex_count * 2
            skin_weights = np.zeros(4 * self.vertex_count, dtype=np.float32)
            additional_skin_weights = np.zeros(additional_weights * self.vertex_count, dtype=np.float32)
            for i in range(loop_count):
                if weights_per_vertex > i:
                    if i < 4:
                        for j in range(self.vertex_count):
                            skin_weights[4 * j + i] = self.read_uint16(
                                2 * (j * weights_per_vertex + i), False) / self.MAX_UINT16
                    else:
                        for j in range(self.vertex_count):
                            additional_skin_weights[j * additional_weights + (i - 4)] = self.read_uint16(
                                2 * (j * weights_per_vertex + i), False) / self.MAX_UINT16
            self.geometry.skin_weights = skin_weights.reshape((-1, loop_count))
            self.geometry.additional_skin_weights = additional_skin_weights.reshape((-1, weights_per_vertex))
            self.i16_offset += weights_per_vertex * self.vertex_count * 2

    def _init_parent(self):
        if self.options['singleParent']:
            _ = self.read_string()
            parent_id = self.read_uint16()
            skin_indices = np.zeros(4 * self.vertex_count)
            skin_weights = np.zeros(4 * self.vertex_count)
            for i in range(self.vertex_count * 4):
                skin_indices[i] = parent_id if i % 4 == 0 else 0
                skin_weights[i] = 1 if i % 4 == 0 else 0
            self.geometry.skin_indices = skin_indices.reshape((-1, 4))
            self.geometry.skin_weights = skin_weights.reshape((-1, 4))

    def _init_poses(self):
        if self.options['animations']:
            bone_count = self.read_uint8()
            frame_mappings = {}
            if self.options['frameMappings']:
                count = self.read_uint16()
                frames = [self.read_uint16() for _ in range(count)]
                if count > 0:
                    for i in range(count):
                        frame_mappings[frames[i]] = i
            pos_scale = self.read_float()
            joint_scales = self.options['jointScales']
            scale_scale = self.read_float() if joint_scales else 1
            poses = {}
            locators = {}
            bones = []
            for _ in range(bone_count):
                name = self.read_string()
                l = self.read_uint16()
                u = self.read_uint16()

                def read_transforms():
                    return {
                        "pos": self.get_position_array(1, pos_scale) if self.get_bit() else self.get_position_array(u,
                                                                                                                  pos_scale),
                        "rot": self.get_quaternion_array(1) if self.get_bit() else self.get_quaternion_array(u),
                        "scl": self.get_scale_array(1, scale_scale) if self.get_bit() else self.get_scale_array(u,
                                                                                                               scale_scale) if joint_scales else [
                            1, 1, 1],
                        "frameMapping": frame_mappings if self.options["frameMappings"] else None
                    }

                if name == 'main':
                    for i in range(l):
                        parent_id = self.read_uint16()
                        bone = HeroBone()
                        bone.bone_id = i
                        bone.name = self.read_string()
                        if parent_id == 5e3:
                            self.geometry.main_skeleton = True
                            bone.parent_id = -1
                        else:
                            bone.parent_id = parent_id
                        transforms = read_transforms()
                        bone.pos = transforms['pos']
                        bone.quat = transforms['rot']
                        bone.scale = transforms['scl']
                        bones.append(bone)
                elif name == 'locators':
                    for _ in range(l):
                        bone = HeroBone()
                        bone.name = self.read_string()
                        transforms = read_transforms()
                        bone.pos = transforms['pos']
                        bone.scale = transforms['scl']
                        bone.quat = transforms['rot']
                        locators[bone.name] = bone
                else:
                    pose_data = {}
                    for _ in range(l):
                        pose_data[self.read_string()] = read_transforms()
                    poses[name] = pose_data
            self.geometry.bones = bones
            self.geometry.poses = poses
            self.geometry.locations = locators


