#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hanwol Launcher (HeliosLauncher 기반) distribution.json 생성 스크립트.
mods/ 폴더의 jar 파일을 스캔해서 MD5/size를 계산하고 distribution.json을 (재)생성합니다.
모드를 추가/삭제/업데이트할 때마다 이 스크립트를 다시 실행하세요.
사용법: python3 generate_distribution.py
"""
import hashlib
import json
import os

BASE_URL = "https://raw.githubusercontent.com/anaf-4/laterre-team-laterre-distro/main"  # GitHub raw 링크 (기본 브랜치가 main이 아니라면 이 부분을 실제 브랜치명으로 교체)
MC_VERSION = "1.21.4"
FABRIC_LOADER_VERSION = "0.19.3"
FABRIC_VERSION_ID = f"fabric-loader-{FABRIC_LOADER_VERSION}-{MC_VERSION}"
FABRIC_MAVEN = "https://maven.fabricmc.net"

# Helios(HeliosLauncher)는 classpath를 구성할 때 Fabric의 profile/json에 있는
# "libraries" 배열을 직접 읽지 않고, distribution.json의 Fabric 모듈 아래
# subModules 중 type: "Library" 인 항목들만 읽어서 classpath에 추가합니다.
# (app/assets/js/processbuilder.js의 _resolveServerLibraries / _resolveModuleLibraries 참고)
# 그래서 ASM/Mixin/Intermediary를 여기 명시적으로 선언해야 "NoClassDefFoundError: org/objectweb/asm/..."
# 같은 에러가 나지 않습니다. 아래 값은 meta.fabricmc.net의 profile/json 응답에서 그대로 가져온
# 실제 MD5/size 입니다 (asm 계열은 고정 버전이라 재실행해도 값이 바뀌지 않습니다).
MOD_LOADER_LIBRARIES = [
    {"group": "org.ow2.asm", "artifact": "asm", "version": "9.10.1", "md5": "9cb72080438acf27f2607002e1444a7b", "size": 126151},
    {"group": "org.ow2.asm", "artifact": "asm-analysis", "version": "9.10.1", "md5": "6dd9011ec87f65e4b2e14e938c4118e4", "size": 35140},
    {"group": "org.ow2.asm", "artifact": "asm-commons", "version": "9.10.1", "md5": "8eee0b1bdd046baf472eb83dd5e6bb44", "size": 74840},
    {"group": "org.ow2.asm", "artifact": "asm-tree", "version": "9.10.1", "md5": "62541e1dc62331408ef31317555bf4fa", "size": 51958},
    {"group": "org.ow2.asm", "artifact": "asm-util", "version": "9.10.1", "md5": "d0892ecb209867805e7d2418e5dc6c42", "size": 95628},
    {"group": "net.fabricmc", "artifact": "sponge-mixin", "version": "0.17.3+mixin.0.8.7", "md5": "87002a5fc9faa1543bf4204f8d5876fb", "size": 1540060},
]
# intermediary는 profile/json 응답에 해시가 없어서(이름+url만 제공) complete-distribution.js가
# 실제 파일을 받아서 계산한 값을 loader-info.json에서 읽어옵니다.
INTERMEDIARY = {"group": "net.fabricmc", "artifact": "intermediary", "version": MC_VERSION}


def maven_path(group: str, artifact: str, version: str) -> str:
    return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"

SERVER_ID = "laterre-main"
SERVER_NAME = "LaTerre"
SERVER_DESCRIPTION = "LaTerre 전용 서버"
SERVER_ADDRESS = "laterre.kro.kr"  # 실제 마인크래프트 서버 접속 주소 (기본 포트 25565 사용)
SERVER_ICON_URL = f"{BASE_URL}/icon.png"  # TODO: 서버 아이콘 이미지를 업로드하고 경로를 맞추세요 (없으면 launcher 기본 아이콘 사용됨)
DISTRO_VERSION = "1.0.0"

MOD_DIR = os.path.join(os.path.dirname(__file__), "mods")
SHADERPACK_DIR = os.path.join(os.path.dirname(__file__), "shaderpacks")
LOADER_INFO_PATH = os.path.join(os.path.dirname(__file__), "loader", "loader-info.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "distribution.json")

# 표시용 이름 매핑 (모를 경우 파일명을 그대로 사용)
DISPLAY_NAMES = {
    "architectury": "Architectury API",
    "balm-fabric": "Balm",
    "BendableCuboids": "Bendable Cuboids",
    "bobby": "Bobby",
    "caxton": "Caxton",
    "cdnperspective": "CDN Perspective",
    "DebugKeybind-fabric": "Debug Keybind",
    "defaultoptions-fabric": "Default Options",
    "emotecraft-fabric-for-MC": "Emotecraft",
    "fabric-api": "Fabric API",
    "fabric-language-kotlin": "Fabric Language: Kotlin",
    "iris-fabric": "Iris Shaders",
    "mcef-fabric": "MCEF",
    "player-animation-lib-fabric": "Player Animation Library",
    "sodium-fabric": "Sodium",
    "waveycapes-fabric": "Wavey Capes",
    "WI-Zoom": "WI Zoom",
    "worldversionbackport": "World Version Backport",
    "xaerominimap-fabric": "Xaero's Minimap",
    "xaeroworldmap-fabric": "Xaero's World Map",
}


def display_name(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    for prefix, label in DISPLAY_NAMES.items():
        if stem.startswith(prefix):
            return label
    return stem


def md5_and_size(path: str):
    h = hashlib.md5()
    size = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def build_mod_modules():
    modules = []
    for filename in sorted(os.listdir(MOD_DIR)):
        if not filename.endswith(".jar"):
            continue
        path = os.path.join(MOD_DIR, filename)
        md5, size = md5_and_size(path)
        stem = filename.rsplit(".", 1)[0]
        module = {
            "id": f"laterre.mods:{stem}:1",
            "name": display_name(filename),
            "type": "FabricMod",
            "required": {"value": True, "def": True},
            "artifact": {
                "size": size,
                "MD5": md5,
                "url": f"{BASE_URL}/mods/{filename}",
                "path": filename,
            },
        }
        modules.append(module)
    return modules


def build_library_submodules(loader_info: dict):
    subs = []
    for lib in MOD_LOADER_LIBRARIES:
        rel_path = maven_path(lib["group"], lib["artifact"], lib["version"])
        subs.append({
            "id": f"{lib['group']}:{lib['artifact']}:{lib['version']}",
            "name": lib["artifact"],
            "type": "Library",
            "artifact": {
                "size": lib["size"],
                "MD5": lib["md5"],
                "url": f"{FABRIC_MAVEN}/{rel_path}",
            },
        })

    inter_path = maven_path(INTERMEDIARY["group"], INTERMEDIARY["artifact"], INTERMEDIARY["version"])
    subs.append({
        "id": f"{INTERMEDIARY['group']}:{INTERMEDIARY['artifact']}:{INTERMEDIARY['version']}",
        "name": "Intermediary Mappings",
        "type": "Library",
        "artifact": {
            "size": loader_info.get("intermediarySize", 0),
            "MD5": loader_info.get("intermediaryMD5", "FILL_ME_RUN_complete-distribution.js"),
            "url": f"{FABRIC_MAVEN}/{inter_path}",
        },
    })
    return subs


def build_shaderpack_modules():
    # Helios는 shaderpack을 distribution.json으로 직접 관리하지 않고, 그냥
    # instances/<serverId>/shaderpacks/ 폴더에 있는 .zip 파일을 스캔해서 보여줍니다
    # (dropinmodutil.js의 scanForShaderpacks). 그래서 type: "File"로 등록해서
    # 그 경로에 파일을 떨궈주기만 하면, Settings > Mods > Shaderpacks 목록에
    # 자동으로 뜨고 유저가 선택만 하면 됩니다 (이미 설치된 Iris가 실제로 적용).
    modules = []
    if not os.path.isdir(SHADERPACK_DIR):
        return modules
    for filename in sorted(os.listdir(SHADERPACK_DIR)):
        if not filename.endswith(".zip"):
            continue
        path = os.path.join(SHADERPACK_DIR, filename)
        md5, size = md5_and_size(path)
        stem = filename.rsplit(".", 1)[0]
        modules.append({
            "id": f"laterre.shaderpacks:{stem}:1",
            "name": stem,
            "type": "File",
            "required": {"value": True, "def": True},
            "artifact": {
                "size": size,
                "MD5": md5,
                "url": f"{BASE_URL}/shaderpacks/{filename}",
                "path": f"shaderpacks/{filename}",
            },
        })
    return modules


def build_fabric_module():
    loader_info = {}
    if os.path.exists(LOADER_INFO_PATH):
        with open(LOADER_INFO_PATH, "r", encoding="utf-8") as f:
            loader_info = json.load(f)

    fabric_module = {
        "id": f"net.fabricmc:fabric-loader:{FABRIC_LOADER_VERSION}",
        "name": f"Fabric Loader {FABRIC_LOADER_VERSION}",
        "type": "Fabric",
        "artifact": {
            "size": loader_info.get("loaderSize", 0),
            "MD5": loader_info.get("loaderMD5", "FILL_ME_RUN_complete-distribution.js"),
            "url": f"{BASE_URL}/loader/fabric-loader-{FABRIC_LOADER_VERSION}.jar",
        },
        "subModules": [
            {
                "id": FABRIC_VERSION_ID,
                "name": f"Fabric {MC_VERSION} Version Manifest",
                "type": "VersionManifest",
                "artifact": {
                    "size": loader_info.get("manifestSize", 0),
                    "MD5": loader_info.get("manifestMD5", "FILL_ME_RUN_complete-distribution.js"),
                    "url": f"{BASE_URL}/loader/{FABRIC_VERSION_ID}.json",
                },
            },
            *build_library_submodules(loader_info),
        ],
    }
    return fabric_module


def main():
    distribution = {
        "version": DISTRO_VERSION,
        "servers": [
            {
                "id": SERVER_ID,
                "name": SERVER_NAME,
                "description": SERVER_DESCRIPTION,
                "icon": SERVER_ICON_URL,
                "version": DISTRO_VERSION,
                "address": SERVER_ADDRESS,
                "minecraftVersion": MC_VERSION,
                "mainServer": True,
                "autoconnect": True,
                "modules": [build_fabric_module()] + build_mod_modules() + build_shaderpack_modules(),
            }
        ],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(distribution, f, ensure_ascii=False, indent=2)

    print(f"[OK] {OUT_PATH} 생성 완료 ({len(distribution['servers'][0]['modules'])}개 모듈)")


if __name__ == "__main__":
    main()
