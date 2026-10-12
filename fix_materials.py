#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Link downloaded Sketchfab textures/colors into the exported glTF.

osgconv writes empty materials (textures are downloaded to textures/ but never
referenced). The real material setup lives in the public viewer options
(https://sketchfab.com/i/models/<uid>/options): per material name, channels
like AlbedoPBR / DiffusePBR / NormalMap / EmitColor with texture uids.

glTF material index -> Sketchfab material name comes from file.osgjs
(osg.Material in traversal order, same order osgconv emits). When file.osgjs
is gone (cleaned downloads), fall back to matching material names inside the
mesh/node names (FBX-style "<object>_<material>_<n>").

Usage (existing downloads):
  python3 fix_materials.py downloads/<Model-uid8>/ [more folders...]
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import quote

WRAP = {"REPEAT": 10497, "CLAMP_TO_EDGE": 33071, "MIRRORED_REPEAT": 33648}
MAG = {"NEAREST": 9728, "LINEAR": 9729}
MIN = {
    "NEAREST": 9728,
    "LINEAR": 9729,
    "NEAREST_MIPMAP_NEAREST": 9984,
    "LINEAR_MIPMAP_NEAREST": 9985,
    "NEAREST_MIPMAP_LINEAR": 9986,
    "LINEAR_MIPMAP_LINEAR": 9987,
}


def fetch_options(uid: str, http_get_json: Callable[[str], dict]) -> dict:
    return http_get_json(f"https://sketchfab.com/i/models/{uid}/options")


def _sketchfab_materials(options: dict) -> list[dict]:
    mats = (options or {}).get("materials") or {}
    return [m for m in mats.values() if isinstance(m, dict) and "channels" in m]


# ---------------------------------------------------------------------------
# glTF material index -> Sketchfab material name
# ---------------------------------------------------------------------------

def _osgjs_material_names(osgjs: Path) -> list[str]:
    """osg.Material names in first-use order across geometries."""
    data = json.loads(osgjs.read_text(encoding="utf-8"))
    names_by_id: dict[int, str] = {}
    order: list[int] = []

    # StateSets/Materials repeat as {"UniqueID": n} references; resolve them
    registry: dict = {}

    def collect(n: Any) -> None:
        if isinstance(n, dict):
            for k, v in n.items():
                if k in ("osg.StateSet", "osg.Material") and isinstance(v, dict) and len(v) > 1 and "UniqueID" in v:
                    registry.setdefault((k, str(v["UniqueID"])), v)
                collect(v)
        elif isinstance(n, list):
            for v in n:
                collect(v)

    def resolve(kind: str, obj: Any) -> Any:
        if isinstance(obj, dict) and set(obj) == {"UniqueID"}:
            return registry.get((kind, str(obj["UniqueID"])), obj)
        return obj

    collect(data)

    def visit_stateset(ss: Any) -> None:
        if not isinstance(ss, dict):
            return
        ss = resolve("osg.StateSet", ss.get("osg.StateSet", ss))
        for entry in ss.get("AttributeList") or []:
            if isinstance(entry, dict) and "osg.Material" in entry:
                mat = resolve("osg.Material", entry["osg.Material"])
                mid = mat.get("UniqueID")
                if mat.get("Name"):
                    names_by_id.setdefault(mid, str(mat["Name"]))
                if mid not in order:
                    order.append(mid)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "StateSet":
                    visit_stateset(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return [names_by_id.get(mid, "") for mid in order]


def _names_by_material(gltf: dict) -> dict[int, list[str]]:
    """glTF material index -> mesh/node names that use it."""
    out: dict[int, list[str]] = {}
    mesh_nodes: dict[int, list[str]] = {}
    for n in gltf.get("nodes") or []:
        if "mesh" in n and n.get("name"):
            mesh_nodes.setdefault(n["mesh"], []).append(n["name"])
    for mi, mesh in enumerate(gltf.get("meshes") or []):
        names = ([mesh["name"]] if mesh.get("name") else []) + mesh_nodes.get(mi, [])
        for p in mesh.get("primitives") or []:
            if "material" in p:
                out.setdefault(p["material"], []).extend(names)
    return out


def _match_by_object_names(gltf: dict, sf_names: list[str]) -> list[Optional[str]]:
    used = _names_by_material(gltf)
    result: list[Optional[str]] = []
    for i in range(len(gltf.get("materials") or [])):
        best: Optional[str] = None
        for obj in used.get(i, []):
            stem = re.sub(r"_\d+$", "", obj)
            for name in sf_names:
                if not name:
                    continue
                if stem == name or stem.endswith("_" + name):
                    if best is None or len(name) > len(best):
                        best = name
        result.append(best)
    return result


def _resolve_names(gltf: dict, sf_names: list[str], osgjs: Optional[Path]) -> tuple[list[Optional[str]], str]:
    n = len(gltf.get("materials") or [])
    # glTF written by osgjs_convert tags each material with its Sketchfab name
    tagged = [((m.get("extras") or {}).get("sf_material")) for m in gltf.get("materials") or []]
    if n and all(tagged):
        return list(tagged), "extras"
    if osgjs and osgjs.is_file():
        names = _osgjs_material_names(osgjs)
        if len(names) == n:
            return list(names), "osgjs"
    names = _match_by_object_names(gltf, sf_names)
    return names, "nombres"


# ---------------------------------------------------------------------------
# Sketchfab channels -> glTF PBR
# ---------------------------------------------------------------------------

def _on(ch: dict, key: str) -> Optional[dict]:
    c = ch.get(key)
    return c if isinstance(c, dict) and c.get("enable") else None


def _scaled_color(c: dict) -> list[float]:
    col = c.get("color") or [1, 1, 1]
    f = float(c.get("factor", 1))
    return [max(0.0, min(1.0, float(x) * f)) for x in col[:3]]


class _Builder:
    def __init__(self, gltf: dict, tex_dir: Path, rel_prefix: str):
        self.gltf = gltf
        self.tex_dir = tex_dir
        self.rel_prefix = rel_prefix
        self.images: list[dict] = []
        self.textures: list[dict] = []
        self.samplers: list[dict] = []
        self._img_idx: dict[str, int] = {}
        self._tex_idx: dict[tuple, int] = {}
        self._smp_idx: dict[tuple, int] = {}
        self.uses_transform = False
        self.uses_emissive_strength = False
        self.missing: set[str] = set()

    def _file_for(self, tuid: str) -> Optional[Path]:
        hits = sorted(self.tex_dir.glob(f"{tuid}_*")) if self.tex_dir.is_dir() else []
        hits = [p for p in hits if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        return hits[0] if hits else None

    def texture_ref(self, channel: dict) -> Optional[dict]:
        tex = channel.get("texture")
        if not isinstance(tex, dict) or not tex.get("uid"):
            return None
        path = self._file_for(str(tex["uid"]))
        if path is None:
            self.missing.add(str(tex["uid"]))
            return None
        if path.name not in self._img_idx:
            self._img_idx[path.name] = len(self.images)
            self.images.append({"name": re.sub(r"^[0-9a-f]{32}_", "", path.stem), "uri": self.rel_prefix + quote(path.name)})
        smp_key = (
            WRAP.get(tex.get("wrapS"), 10497),
            WRAP.get(tex.get("wrapT"), 10497),
            MAG.get(tex.get("magFilter"), 9729),
            MIN.get(tex.get("minFilter"), 9987),
        )
        if smp_key not in self._smp_idx:
            self._smp_idx[smp_key] = len(self.samplers)
            self.samplers.append(
                {"wrapS": smp_key[0], "wrapT": smp_key[1], "magFilter": smp_key[2], "minFilter": smp_key[3]}
            )
        tkey = (self._img_idx[path.name], self._smp_idx[smp_key])
        if tkey not in self._tex_idx:
            self._tex_idx[tkey] = len(self.textures)
            self.textures.append({"source": tkey[0], "sampler": tkey[1]})
        ref: dict = {"index": self._tex_idx[tkey]}
        uvt = channel.get("UVTransforms") or {}
        scale = uvt.get("scale") or [1, 1]
        offset = uvt.get("offset") or [0, 0]
        if list(scale) != [1, 1] or list(offset) != [0, 0]:
            ref["extensions"] = {"KHR_texture_transform": {"scale": list(scale), "offset": list(offset)}}
            self.uses_transform = True
        return ref

    def material(self, base: dict, sf: dict) -> dict:
        ch = sf.get("channels") or {}
        mat: dict = {k: v for k, v in base.items() if k in ("doubleSided", "extensions", "extras")}
        mat["name"] = sf.get("name") or mat.get("name") or ""
        pbr: dict = {}

        # Base color: metal/rough (AlbedoPBR) > spec/gloss (DiffusePBR) > classic (DiffuseColor)
        albedo = _on(ch, "AlbedoPBR") or _on(ch, "DiffusePBR") or _on(ch, "DiffuseColor")
        color = [1.0, 1.0, 1.0]
        if albedo:
            ref = self.texture_ref(albedo)
            if ref:
                pbr["baseColorTexture"] = ref
                f = float(albedo.get("factor", 1))
                color = [f, f, f]
            else:
                color = _scaled_color(albedo)
        alpha = 1.0
        opacity = _on(ch, "Opacity")
        if opacity:
            alpha = float(opacity.get("factor", 1))
            if alpha < 1.0 or opacity.get("texture"):
                mat["alphaMode"] = "BLEND"
        if _on(ch, "AlphaMask"):
            mat["alphaMode"] = "MASK"
        pbr["baseColorFactor"] = color + [alpha]

        if _on(ch, "AlbedoPBR"):
            metal = _on(ch, "MetalnessPBR")
            pbr["metallicFactor"] = float(metal.get("factor", 0)) if metal else 0.0
        else:
            pbr["metallicFactor"] = 0.0
        rough = _on(ch, "RoughnessPBR")
        gloss = _on(ch, "GlossinessPBR")
        if rough:
            pbr["roughnessFactor"] = float(rough.get("factor", 1))
        elif gloss:
            pbr["roughnessFactor"] = 1.0 - float(gloss.get("factor", 0))
        else:
            pbr["roughnessFactor"] = 0.6
        mat["pbrMetallicRoughness"] = pbr

        normal = _on(ch, "NormalMap")
        if normal:
            ref = self.texture_ref(normal)
            if ref:
                ref["scale"] = float(normal.get("factor", 1))
                mat["normalTexture"] = ref

        ao = _on(ch, "AOPBR")
        if ao:
            ref = self.texture_ref(ao)
            if ref:
                ref["strength"] = float(ao.get("factor", 1))
                mat["occlusionTexture"] = ref

        emit = _on(ch, "EmitColor")
        if emit:
            ref = self.texture_ref(emit)
            f = float(emit.get("factor", 1))
            if ref:
                mat["emissiveTexture"] = ref
                mat["emissiveFactor"] = [min(f, 1.0)] * 3
                strength = f
            else:
                col = emit.get("color") or [1, 1, 1]
                peak = max(max(float(x) for x in col[:3]) * f, 0.0)
                strength = max(peak, 1.0)
                ec = [max(0.0, min(1.0, float(x) * f / strength)) for x in col[:3]]
                if any(ec):
                    mat["emissiveFactor"] = ec
                else:
                    strength = 1.0
            if strength > 1.0:
                # glTF caps emissiveFactor at 1; the overshoot goes in the extension
                mat.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {"emissiveStrength": strength}
                self.uses_emissive_strength = True
            else:
                # osgconv leaves a 0.0 strength that would black out the emission
                (mat.get("extensions") or {}).pop("KHR_materials_emissive_strength", None)
        return mat


_TEXTURE_SLOTS = ("normalTexture", "occlusionTexture", "emissiveTexture")


def _strip_textures(mat: dict) -> dict:
    """Copy of a glTF material without texture bindings (indices may no longer exist)."""
    out = {k: v for k, v in mat.items() if k not in _TEXTURE_SLOTS and k != "pbrMetallicRoughness"}
    pbr = {k: v for k, v in (mat.get("pbrMetallicRoughness") or {}).items()
           if k not in ("baseColorTexture", "metallicRoughnessTexture")}
    if pbr:
        out["pbrMetallicRoughness"] = pbr
    return out


def _has_texture(mat: dict) -> bool:
    pbr = mat.get("pbrMetallicRoughness") or {}
    return any(k in mat for k in _TEXTURE_SLOTS) or "baseColorTexture" in pbr or "metallicRoughnessTexture" in pbr


def _fix_missing_texcoords(gltf: dict) -> None:
    """Primitives without TEXCOORD_0 can't use textured materials (invalid glTF): give them an untextured copy."""
    mats = gltf.get("materials") or []
    clones: dict[int, int] = {}
    for mesh in gltf.get("meshes") or []:
        for prim in mesh.get("primitives") or []:
            mi = prim.get("material")
            if mi is None or "TEXCOORD_0" in (prim.get("attributes") or {}) or mi >= len(mats):
                continue
            if not _has_texture(mats[mi]):
                continue
            if mi not in clones:
                mats.append(_strip_textures(mats[mi]))
                clones[mi] = len(mats) - 1
            prim["material"] = clones[mi]


def _write_gltf(path: Path, gltf: dict) -> None:
    tmp = path.with_suffix(".gltf.tmp")
    tmp.write_text(json.dumps(gltf), encoding="utf-8")
    os.replace(tmp, path)


def apply_sketchfab_materials(
    gltf_path: Path,
    options: dict,
    *,
    osgjs: Optional[Path] = None,
    log: Callable[[str], None] = print,
) -> int:
    """Rewrite materials of gltf_path in place. Returns number of materials linked."""
    gltf_path = Path(gltf_path)
    gltf = json.loads(gltf_path.read_text(encoding="utf-8"))
    sf_mats = _sketchfab_materials(options)
    if not sf_mats or not gltf.get("materials"):
        log("  sin materiales que enlazar")
        if gltf.get("materials"):
            _fix_missing_texcoords(gltf)
            _write_gltf(gltf_path, gltf)
        return 0

    by_name: dict[str, dict] = {}
    for m in sf_mats:
        by_name.setdefault(str(m.get("name") or ""), m)
    names, source = _resolve_names(gltf, list(by_name), osgjs)

    builder = _Builder(gltf, gltf_path.parent / "textures", "textures/")
    linked = 0
    new_mats: list[dict] = []
    for i, base in enumerate(gltf["materials"]):
        sf = by_name.get(names[i] or "") if i < len(names) else None
        if sf is None:
            new_mats.append(_strip_textures(base))
            continue
        new_mats.append(builder.material(base, sf))
        linked += 1

    if linked == 0:
        log("  ningun material enlazado: el glTF se deja como esta")
        _fix_missing_texcoords(gltf)
        _write_gltf(gltf_path, gltf)
        return 0

    gltf["materials"] = new_mats
    for key, items in (("images", builder.images), ("textures", builder.textures), ("samplers", builder.samplers)):
        if items:
            gltf[key] = items
        else:
            gltf.pop(key, None)
    if builder.uses_transform:
        used = gltf.setdefault("extensionsUsed", [])
        if "KHR_texture_transform" not in used:
            used.append("KHR_texture_transform")

    if builder.uses_emissive_strength:
        used = gltf.setdefault("extensionsUsed", [])
        if "KHR_materials_emissive_strength" not in used:
            used.append("KHR_materials_emissive_strength")

    _fix_missing_texcoords(gltf)
    _write_gltf(gltf_path, gltf)

    log(
        f"  materiales: {linked}/{len(new_mats)} enlazados (por {source}), "
        f"texturas: {len(builder.images)}"
    )
    if builder.missing:
        log(f"  texturas no encontradas en textures/: {len(builder.missing)}")
    if linked < len(new_mats):
        log("  aviso: algunos materiales no se pudieron identificar; volver a descargar el modelo (el paso corre con file.osgjs presente)")
    return linked


def _fix_folder(folder: Path) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from main import http_get_json  # noqa: E402

    folder = Path(folder)
    info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    gltf_path = Path(info.get("output") or "")
    if not gltf_path.is_file():
        gltfs = sorted(folder.glob("*.gltf"), key=lambda p: p.stat().st_size)
        if not gltfs:
            raise FileNotFoundError(f"sin .gltf en {folder}")
        gltf_path = gltfs[-1]
    print(f"{folder.name}:")
    options = fetch_options(info["uid"], http_get_json)
    apply_sketchfab_materials(gltf_path, options, osgjs=folder / "file.osgjs")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for arg in sys.argv[1:]:
        _fix_folder(Path(arg))
