"""Минимальный сборщик 3D-моделей в формат glTF 2.0 (.glb) и OBJ.

Без внешних зависимостей: только стандартная библиотека Python.
Модель собирается из примитивов (box, cylinder, sphere, prism), узлы образуют
иерархию (кости персонажей, башня танка, крышка сундука), а анимации пишутся
как ключевые кадры вращения / смещения / масштаба узлов.
"""
import json
import math
import struct

# ---------------------------------------------------------------- математика

def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_norm(a):
    l = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def q_euler(x=0.0, y=0.0, z=0.0):
    """Эйлер в градусах (порядок XYZ, как в three.js) -> кватернион [x, y, z, w]."""
    x, y, z = (math.radians(a) / 2 for a in (x, y, z))
    c1, c2, c3 = math.cos(x), math.cos(y), math.cos(z)
    s1, s2, s3 = math.sin(x), math.sin(y), math.sin(z)
    return (
        s1 * c2 * c3 + c1 * s2 * s3,
        c1 * s2 * c3 - s1 * c2 * s3,
        c1 * c2 * s3 + s1 * s2 * c3,
        c1 * c2 * c3 - s1 * s2 * s3,
    )


def q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def q_rot(q, v):
    x, y, z, w = q
    p = q_mul(q_mul(q, (v[0], v[1], v[2], 0.0)), (-x, -y, -z, w))
    return (p[0], p[1], p[2])


def srgb(hex_color):
    """'#RRGGBB' -> линейный RGB (glTF хранит цвета в линейном пространстве)."""
    h = hex_color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


# ---------------------------------------------------------------- геометрия
# Геометрия = (positions, normals, indices)


def poly(verts, faces):
    """Выпуклый многогранник с плоским затенением; нормали наружу по центроиду."""
    cen = [sum(v[i] for v in verts) / len(verts) for i in range(3)]
    P, N, I = [], [], []
    for f in faces:
        pts = [verts[i] for i in f]
        # нормаль методом Ньюэлла (устойчива к вырожденным граням)
        n = [0.0, 0.0, 0.0]
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            n[0] += (a[1] - b[1]) * (a[2] + b[2])
            n[1] += (a[2] - b[2]) * (a[0] + b[0])
            n[2] += (a[0] - b[0]) * (a[1] + b[1])
        fc = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
        if sum(n[i] * (fc[i] - cen[i]) for i in range(3)) < 0:
            pts = pts[::-1]
            n = [-c for c in n]
        n = v_norm(n)
        base = len(P)
        for p in pts:
            P.append(tuple(p))
            N.append(n)
        for i in range(1, len(pts) - 1):
            I += [base, base + i, base + i + 1]
    return P, N, I


BOX_FACES = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]


def prism(corners):
    """8 углов: низ (-x-z, +x-z, +x+z, -x+z), затем верх в том же порядке."""
    return poly(corners, BOX_FACES)


def box(sx, sy, sz):
    x, y, z = sx / 2, sy / 2, sz / 2
    return prism([(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z),
                  (-x, y, -z), (x, y, -z), (x, y, z), (-x, y, z)])


def tbox(wb, db, wt, dt, h, top_dz=0.0, top_dx=0.0):
    """Усечённая коробка: нижнее основание wb*db, верхнее wt*dt, высота h."""
    a, b, c, d, y = wb / 2, db / 2, wt / 2, dt / 2, h / 2
    return prism([(-a, -y, -b), (a, -y, -b), (a, -y, b), (-a, -y, b),
                  (-c + top_dx, y, -d + top_dz), (c + top_dx, y, -d + top_dz),
                  (c + top_dx, y, d + top_dz), (-c + top_dx, y, d + top_dz)])


def wedge(sx, sy, sz):
    """Клин (пандус): высокая сторона сзади (-z), низкая спереди (+z)."""
    x, y, z = sx / 2, sy / 2, sz / 2
    v = [(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z), (-x, y, -z), (x, y, -z)]
    return poly(v, [[0, 1, 2, 3], [0, 1, 5, 4], [3, 2, 5, 4], [0, 3, 4], [1, 2, 5]])


def _axis(g, axis):
    if axis == "y":
        return g
    if axis == "z":
        f = lambda p: (p[0], -p[2], p[1])
    else:  # x
        f = lambda p: (p[1], -p[0], p[2])
    P, N, I = g
    return [f(p) for p in P], [f(n) for n in N], I


def cyl(r_top, r_bot=None, h=1.0, seg=16, axis="y", caps=True):
    """Цилиндр / конус по оси Y (затем повёрнутый к axis), центр в начале координат."""
    r_bot = r_top if r_bot is None else r_bot
    P, N, I = [], [], []
    hy = h / 2
    slope = (r_bot - r_top) / h
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        n = v_norm((c, slope, s))
        P += [(c * r_bot, -hy, s * r_bot), (c * r_top, hy, s * r_top)]
        N += [n, n]
    for i in range(seg):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        I += [a, b, d, a, d, c]
    if caps:
        for y, r, ny in ((hy, r_top, 1.0), (-hy, r_bot, -1.0)):
            if r <= 0:
                continue
            base = len(P)
            P.append((0.0, y, 0.0))
            N.append((0.0, ny, 0.0))
            for i in range(seg + 1):
                a = 2 * math.pi * i / seg
                P.append((math.cos(a) * r, y, math.sin(a) * r))
                N.append((0.0, ny, 0.0))
            for i in range(seg):
                if ny > 0:
                    I += [base, base + i + 2, base + i + 1]
                else:
                    I += [base, base + i + 1, base + i + 2]
    return _axis((P, N, I), axis)


def sphere(rx, ry=None, rz=None, seg=16, rings=10, phi_max=math.pi):
    """Эллипсоид. phi_max = pi/2 даёт верхнюю полусферу (купол парашюта)."""
    ry = rx if ry is None else ry
    rz = rx if rz is None else rz
    P, N, I = [], [], []
    for j in range(rings + 1):
        ph = phi_max * j / rings
        for i in range(seg + 1):
            th = 2 * math.pi * i / seg
            u = (math.sin(ph) * math.cos(th), math.cos(ph), math.sin(ph) * math.sin(th))
            P.append((u[0] * rx, u[1] * ry, u[2] * rz))
            N.append(v_norm((u[0] / rx, u[1] / ry, u[2] / rz)))
    w = seg + 1
    for j in range(rings):
        for i in range(seg):
            a, b = j * w + i, j * w + i + 1
            c, d = a + w, b + w
            I += [a, b, d, a, d, c]
    return P, N, I


def xf(g, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1)):
    """Запечь масштаб, поворот (градусы) и смещение в геометрию."""
    q = q_euler(*r)
    P, N, I = g
    P2 = [v_add(q_rot(q, (p[0] * s[0], p[1] * s[1], p[2] * s[2])), t) for p in P]
    N2 = [v_norm(q_rot(q, v_norm((n[0] / s[0], n[1] / s[1], n[2] / s[2])))) for n in N]
    if s[0] * s[1] * s[2] < 0:
        I = [I[k + o] for k in range(0, len(I), 3) for o in (0, 2, 1)]
    return P2, N2, list(I)


def merge(*gs):
    P, N, I = [], [], []
    for g in gs:
        base = len(P)
        P += g[0]
        N += g[1]
        I += [i + base for i in g[2]]
    return P, N, I


# ---------------------------------------------------------------- модель

class Model:
    def __init__(self, name):
        self.name = name
        self.nodes = []      # dict(name, t, r(quat), s, mesh, children, parent, export_obj)
        self.by_name = {}
        self.materials = []
        self.mat_index = {}
        self.meshes = []
        self.anims = []

    # материалы ----------------------------------------------------------
    def mat(self, name, color, metal=0.0, rough=0.7, emissive=None, alpha=1.0, double=False):
        rgb = srgb(color)
        m = {"name": name,
             "pbrMetallicRoughness": {"baseColorFactor": rgb + [alpha],
                                      "metallicFactor": metal, "roughnessFactor": rough}}
        if emissive:
            m["emissiveFactor"] = srgb(emissive)
        if alpha < 1.0:
            m["alphaMode"] = "BLEND"
        if double or alpha < 1.0:
            m["doubleSided"] = True
        self.mat_index[name] = len(self.materials)
        self.materials.append(m)
        return name

    # узлы ---------------------------------------------------------------
    def node(self, name, parent=None, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1), obj=True):
        assert name not in self.by_name, name
        idx = len(self.nodes)
        self.nodes.append({"name": name, "t": tuple(t), "r": q_euler(*r), "s": tuple(s),
                           "mesh": None, "children": [], "parent": None, "obj": obj})
        self.by_name[name] = idx
        if parent is not None:
            p = self.by_name[parent]
            self.nodes[p]["children"].append(idx)
            self.nodes[idx]["parent"] = p
        return name

    def part(self, name, geom, material, parent=None, t=(0, 0, 0), r=(0, 0, 0), s=(1, 1, 1), obj=True):
        self.node(name, parent, t, r, s, obj)
        self.meshes.append((name, geom, self.mat_index[material]))
        self.nodes[self.by_name[name]]["mesh"] = len(self.meshes) - 1
        return name

    # анимации -----------------------------------------------------------
    def anim(self, name, tracks):
        """tracks: [(узел, 'rotation'|'translation'|'scale', [(время, значение), ...])]

        rotation   — эйлер в градусах, добавляется к позе покоя узла;
        translation — смещение относительно позы покоя;
        scale      — абсолютный масштаб.
        """
        self.anims.append((name, tracks))

    # экспорт glTF ---------------------------------------------------------
    def to_glb(self, path):
        buf = bytearray()
        views, accs = [], []

        def add(data, fmt, ctype, typ, count, target=None, mn=None, mx=None):
            while len(buf) % 4:
                buf.append(0)
            off = len(buf)
            buf.extend(struct.pack("<%d%s" % (len(data), fmt), *data))
            v = {"buffer": 0, "byteOffset": off, "byteLength": len(buf) - off}
            if target:
                v["target"] = target
            views.append(v)
            a = {"bufferView": len(views) - 1, "componentType": ctype, "count": count, "type": typ}
            if mn is not None:
                a["min"], a["max"] = mn, mx
            accs.append(a)
            return len(accs) - 1

        meshes_json = []
        for name, (P, N, I), mi in self.meshes:
            flatP = [c for p in P for c in p]
            flatN = [c for n in N for c in n]
            mn = [min(p[i] for p in P) for i in range(3)]
            mx = [max(p[i] for p in P) for i in range(3)]
            pa = add(flatP, "f", 5126, "VEC3", len(P), 34962, mn, mx)
            na = add(flatN, "f", 5126, "VEC3", len(N), 34962)
            if len(P) < 65536:
                ia = add(I, "H", 5123, "SCALAR", len(I), 34963)
            else:
                ia = add(I, "I", 5125, "SCALAR", len(I), 34963)
            meshes_json.append({"name": name, "primitives": [
                {"attributes": {"POSITION": pa, "NORMAL": na}, "indices": ia, "material": mi}]})

        nodes_json = []
        for n in self.nodes:
            j = {"name": n["name"]}
            if any(n["t"]):
                j["translation"] = list(n["t"])
            if n["r"] != (0.0, 0.0, 0.0, 1.0):
                j["rotation"] = list(n["r"])
            if n["s"] != (1, 1, 1):
                j["scale"] = list(n["s"])
            if n["mesh"] is not None:
                j["mesh"] = n["mesh"]
            if n["children"]:
                j["children"] = n["children"]
            nodes_json.append(j)

        anims_json = []
        for aname, tracks in self.anims:
            samplers, channels = [], []
            for node_name, prop, keys in tracks:
                n = self.nodes[self.by_name[node_name]]
                times = [k[0] for k in keys]
                out = []
                prev = None
                for _, val in keys:
                    if prop == "rotation":
                        q = q_mul(n["r"], q_euler(*val))
                        if prev and sum(a * b for a, b in zip(prev, q)) < 0:
                            q = tuple(-c for c in q)
                        prev = q
                        out += list(q)
                    elif prop == "translation":
                        out += list(v_add(n["t"], val))
                    else:
                        out += list(val)
                ta = add(times, "f", 5126, "SCALAR", len(times), None, [min(times)], [max(times)])
                oa = add(out, "f", 5126, "VEC4" if prop == "rotation" else "VEC3", len(keys))
                samplers.append({"input": ta, "output": oa, "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1,
                                 "target": {"node": self.by_name[node_name], "path": prop}})
            anims_json.append({"name": aname, "samplers": samplers, "channels": channels})

        while len(buf) % 4:
            buf.append(0)
        gltf = {
            "asset": {"version": "2.0", "generator": "block-royale gltf_builder"},
            "scene": 0,
            "scenes": [{"name": self.name,
                        "nodes": [i for i, n in enumerate(self.nodes) if n["parent"] is None]}],
            "nodes": nodes_json,
            "meshes": meshes_json,
            "materials": self.materials,
            "accessors": accs,
            "bufferViews": views,
            "buffers": [{"byteLength": len(buf)}],
        }
        if anims_json:
            gltf["animations"] = anims_json
        js = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        js += b" " * ((4 - len(js) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(buf)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, total))
            f.write(struct.pack("<II", len(js), 0x4E4F534A))
            f.write(js)
            f.write(struct.pack("<II", len(buf), 0x004E4942))
            f.write(buf)

    # экспорт OBJ (статичная поза покоя) -----------------------------------------
    def _world(self, idx):
        n = self.nodes[idx]
        if n["parent"] is None:
            return n["t"], n["r"], n["s"], n["obj"]
        pt, pr, ps, pobj = self._world(n["parent"])
        ls = (n["t"][0] * ps[0], n["t"][1] * ps[1], n["t"][2] * ps[2])
        t = v_add(pt, q_rot(pr, ls))
        s = (ps[0] * n["s"][0], ps[1] * n["s"][1], ps[2] * n["s"][2])
        return t, q_mul(pr, n["r"]), s, pobj and n["obj"]

    def to_obj(self, path, mtl_name):
        lines = ["# %s — block-royale" % self.name, "mtllib %s" % mtl_name]
        base = 1
        for idx, n in enumerate(self.nodes):
            if n["mesh"] is None:
                continue
            t, q, s, ok = self._world(idx)
            if not ok:
                continue
            _, (P, N, I), mi = self.meshes[n["mesh"]]
            lines.append("o %s" % n["name"])
            lines.append("usemtl %s" % self.materials[mi]["name"])
            for p in P:
                w = v_add(q_rot(q, (p[0] * s[0], p[1] * s[1], p[2] * s[2])), t)
                lines.append("v %.5f %.5f %.5f" % w)
            for nn in N:
                w = v_norm(q_rot(q, nn))
                lines.append("vn %.4f %.4f %.4f" % w)
            for k in range(0, len(I), 3):
                a, b, c = (I[k] + base, I[k + 1] + base, I[k + 2] + base)
                lines.append("f %d//%d %d//%d %d//%d" % (a, a, b, b, c, c))
            base += len(P)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        mtl = []
        for m in self.materials:
            def to_srgb(c):
                return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
            col = m["pbrMetallicRoughness"]["baseColorFactor"]
            mtl += ["newmtl %s" % m["name"],
                    "Kd %.4f %.4f %.4f" % tuple(to_srgb(c) for c in col[:3]),
                    "Ka 0 0 0", "Ks 0.2 0.2 0.2", "d %.2f" % col[3], "illum 2"]
            if "emissiveFactor" in m:
                mtl.append("Ke %.4f %.4f %.4f" % tuple(to_srgb(c) for c in m["emissiveFactor"]))
            mtl.append("")
        with open(path[:-4] + ".mtl", "w", encoding="utf-8") as f:
            f.write("\n".join(mtl))
