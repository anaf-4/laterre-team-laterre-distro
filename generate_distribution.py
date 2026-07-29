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

SERVER_ID = "laterre-main"
SERVER_NAME = "LaTerre"
SERVER_DESCRIPTION = "LaTerre 전용 서버"
SERVER_ADDRESS = "laterre.kro.kr"  # 실제 마인크래프트 서버 접속 주소 (기본 포트 25565 사용)
SERVER_ICON_URL = f"{BASE_URL}/icon.png"  # TODO: 서버 아이콘 이미지를 업로드하고 경로를 맞추세요 (없으면 launcher 기본 아이콘 사용됨)
DISTRO_VERSION = "1.0.0"

MOD_DIR = os.path.join(os.path.dirname(__file__), "mods")
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
            }
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
                "modules": [build_fabric_module()] + build_mod_modules(),
            }
        ],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(distribution, f, ensure_ascii=False, indent=2)

    print(f"[OK] {OUT_PATH} 생성 완료 ({len(distribution['servers'][0]['modules'])}개 모듈)")


if __name__ == "__main__":
    main()
