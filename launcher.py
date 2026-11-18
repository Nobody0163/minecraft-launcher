"""
Copyright (C) 2026 Nobody0163

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# THIS WAS WRITTEN PARTIALLY BY CHATGPT, THIS CONTAINS AI SLOP

import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import threading
import re
import zipfile
import importlib
import subprocess
import sys
import ctypes

DEPENDENCIES = {
	"pygame": "pygame-ce",
	"requests": "requests"
}

for module_name, package_name in DEPENDENCIES.items():
	try:
		importlib.import_module(module_name)
	except ImportError:
		subprocess.check_call([
			sys.executable,
			"-m",
			"pip",
			"install",
			package_name
		])

import pygame
import requests


BASE_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent
VERSIONS_DIR: pathlib.Path = BASE_DIR / "versions"
ASSETS_DIR: pathlib.Path = BASE_DIR / "assets"
LIBRARIES_DIR: pathlib.Path = BASE_DIR / "libraries"
NATIVES_DIR: pathlib.Path = BASE_DIR / "natives"
INSTANCES_DIR: pathlib.Path = BASE_DIR / "instances"
INSTANCES_FILE: pathlib.Path = BASE_DIR / "instances.json"
SELECTED_INSTANCE_FILE: pathlib.Path = BASE_DIR / "selected_instance.txt"
CURRENT_VERSION_FILE: pathlib.Path = BASE_DIR / "current_version.txt"
USERNAME_FILE: pathlib.Path = BASE_DIR / "username.txt"
SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
UPDATE_FILE: pathlib.Path = SCRIPT_PATH.with_suffix(SCRIPT_PATH.suffix + ".new")

GITHUB_OWNER: str = "Nobody0163"
GITHUB_REPOSITORY: str = "minecraft-launcher"
LAUNCHER_VERSION: str = "1.3.1"
GITHUB_RELEASE_API_URL: str = (
	f"https://api.github.com/repos/{GITHUB_OWNER}/"
	f"{GITHUB_REPOSITORY}/releases/latest"
)

VERSION_MANIFEST_URL: str = (
	"https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
)

SESSION: requests.Session = requests.Session()
SESSION.headers.update({"User-Agent": "CustomMinecraftLauncher/1.0"})

WIDTH: int = 900
HEIGHT: int = 650
FPS: int = 60

BACKGROUND: tuple[int, int, int] = (18, 21, 28)
PANEL: tuple[int, int, int] = (29, 34, 44)
BUTTON: tuple[int, int, int] = (43, 51, 65)
BUTTON_HOVER: tuple[int, int, int] = (56, 67, 84)
TEXT: tuple[int, int, int] = (239, 242, 248)
MUTED: tuple[int, int, int] = (145, 155, 172)
ACCENT: tuple[int, int, int] = (76, 190, 124)
ERROR: tuple[int, int, int] = (232, 91, 100)

pygame.init()

SCREEN: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minecraft Launcher")

CLOCK: pygame.time.Clock = pygame.time.Clock()
FONT: pygame.font.Font = pygame.font.Font("C:/Windows/Fonts/segoeui.ttf", 16)
SMALL_FONT: pygame.font.Font = pygame.font.Font("C:/Windows/Fonts/segoeui.ttf", 13)
MEDIUM_FONT: pygame.font.Font = pygame.font.Font("C:/Windows/Fonts/seguisb.ttf", 18)
TITLE_FONT: pygame.font.Font = pygame.font.Font("C:/Windows/Fonts/seguisb.ttf", 30)
BUTTON_FONT: pygame.font.Font = pygame.font.Font("C:/Windows/Fonts/seguisb.ttf", 16)

MANIFEST: dict = {}
VERSIONS: list[dict] = []
VISIBLE_VERSIONS: list[dict] = []
SELECTED_VERSION: str = ""
USERNAME: str = "NO USERNAME SET"
USERNAME_ACTIVE: bool = False
USERNAME_SELECT_ALL: bool = False
USERNAME_RECT: pygame.Rect = pygame.Rect(70, 250, 420, 42)
CURRENT_TAB: str = "launch"
VERSION_FILTER: str = "release"
INSTALL_LOADER: str = "vanilla"
INSTANCES: list[dict] = []
SELECTED_INSTANCE_ID: str = ""
INSTANCE_NAME_INPUT: str = "New instance"
INSTANCE_NAME_ACTIVE: bool = False
INSTANCE_NAME_SELECT_ALL: bool = False
INSTANCE_NAME_RECT: pygame.Rect = pygame.Rect(55, 225, 500, 42)
INSTANCE_SCROLL_OFFSET: int = 0

ACTIVE_FIELD: str = ""
FIELD_SELECT_ALL: bool = False
MEMORY_MAX_RECT: pygame.Rect = pygame.Rect(55, 250, 180, 42)
MEMORY_MIN_RECT: pygame.Rect = pygame.Rect(255, 250, 180, 42)
JVM_ARGS_RECT: pygame.Rect = pygame.Rect(55, 340, 550, 42)
RES_W_RECT: pygame.Rect = pygame.Rect(55, 430, 120, 42)
RES_H_RECT: pygame.Rect = pygame.Rect(200, 430, 120, 42)

STATUS: str = "Loading Minecraft versions..."
STATUS_COLOR: tuple[int, int, int] = TEXT
PROGRESS: float = 0.0
BUSY: bool = False
SHOULD_QUIT: bool = False

DEFAULT_LAUNCH_OPTIONS: dict = {
	"memory_max": "2G",
	"memory_min": "512M",
	"jvm_args": "",
	"resolution_width": "1280",
	"resolution_height": "720",
}


def EnsureInstanceOptions(instance: dict) -> None:
	"""Ensure an instance dict has all launch option keys with defaults."""
	for key, default in DEFAULT_LAUNCH_OPTIONS.items():
		if key not in instance or not isinstance(instance[key], str):
			instance[key] = default


def SaveInstances() -> None:
	INSTANCES_FILE.write_text(
		json.dumps(INSTANCES, indent=2),
		encoding="utf-8",
	)
	SELECTED_INSTANCE_FILE.write_text(SELECTED_INSTANCE_ID, encoding="utf-8")


def GetSelectedInstance() -> dict | None:
	instance = next(
		(instance for instance in INSTANCES if instance["id"] == SELECTED_INSTANCE_ID),
		None,
	)
	if instance is not None:
		EnsureInstanceOptions(instance)
	return instance


def LoadInstances() -> None:
	global INSTANCES, SELECTED_INSTANCE_ID

	INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
	if INSTANCES_FILE.is_file():
		loaded_instances: list[dict] = json.loads(
			INSTANCES_FILE.read_text(encoding="utf-8")
		)
		INSTANCES = [
			instance
			for instance in loaded_instances
			if isinstance(instance, dict)
			and isinstance(instance.get("id"), str)
			and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", instance["id"]) is not None
			and isinstance(instance.get("name"), str)
			and isinstance(instance.get("version_id", ""), str)
		]
		for instance in INSTANCES:
			EnsureInstanceOptions(instance)
	else:
		legacy_version: str = ""
		if CURRENT_VERSION_FILE.is_file():
			legacy_version = CURRENT_VERSION_FILE.read_text(encoding="utf-8").strip()
		INSTANCES = [{
			"id": "default",
			"name": "Default",
			"version_id": legacy_version,
			**DEFAULT_LAUNCH_OPTIONS,
		}]
		legacy_instance_dir: pathlib.Path = INSTANCES_DIR / "default"
		legacy_instance_dir.mkdir(parents=True, exist_ok=True)
		for directory_name in (
			"saves", "mods", "config", "resourcepacks", "shaderpacks",
			"screenshots", "logs", "crash-reports", "server-resource-packs",
		):
			source_dir: pathlib.Path = BASE_DIR / directory_name
			if source_dir.is_dir():
				shutil.move(str(source_dir), str(legacy_instance_dir / directory_name))
		for file_name in ("options.txt", "servers.dat", "servers.dat_old", "usercache.json", "usernamecache.json"):
			source_file: pathlib.Path = BASE_DIR / file_name
			if source_file.is_file():
				shutil.move(str(source_file), str(legacy_instance_dir / file_name))
		SaveInstances()

	if not INSTANCES:
		INSTANCES = [{"id": "default", "name": "Default", "version_id": "", **DEFAULT_LAUNCH_OPTIONS}]
		SaveInstances()

	for instance in INSTANCES:
		instance_dir: pathlib.Path = INSTANCES_DIR / instance["id"]
		instance_dir.mkdir(parents=True, exist_ok=True)
		EnsureInstanceOptions(instance)

	if SELECTED_INSTANCE_FILE.is_file():
		SELECTED_INSTANCE_ID = SELECTED_INSTANCE_FILE.read_text(encoding="utf-8").strip()
	if not any(instance["id"] == SELECTED_INSTANCE_ID for instance in INSTANCES):
		SELECTED_INSTANCE_ID = INSTANCES[0]["id"]
	SaveInstances()


def CreateInstance(name: str, version_id: str = "") -> None:
	global SELECTED_INSTANCE_ID

	clean_name: str = name.strip()[:32] or f"Instance {len(INSTANCES) + 1}"
	instance_id: str = f"instance-{__import__('uuid').uuid4().hex[:10]}"
	installed_version_id: str = ""
	if version_id:
		version_dir: pathlib.Path = VERSIONS_DIR / version_id
		version_json_path: pathlib.Path = version_dir / f"{version_id}.json"
		if version_json_path.is_file():
			version_metadata: dict = json.loads(version_json_path.read_text(encoding="utf-8"))
			base_version_id: str = version_metadata.get("inheritsFrom", version_id)
			base_version_dir: pathlib.Path = VERSIONS_DIR / base_version_id
			if (base_version_dir / f"{base_version_id}.json").is_file() and (base_version_dir / f"{base_version_id}.jar").is_file():
				installed_version_id = version_id
	instance: dict = {
		"id": instance_id,
		"name": clean_name,
		"version_id": installed_version_id,
		**DEFAULT_LAUNCH_OPTIONS,
	}
	INSTANCES.append(instance)
	SELECTED_INSTANCE_ID = instance_id
	(INSTANCES_DIR / instance_id).mkdir(parents=True, exist_ok=True)
	SaveInstances()


def DeleteSelectedInstance() -> None:
	global SELECTED_INSTANCE_ID

	if len(INSTANCES) <= 1:
		SetStatus("You must keep at least one instance.", ERROR)
		return

	instance: dict | None = GetSelectedInstance()
	if instance is None:
		return

	confirmation: int = ctypes.windll.user32.MessageBoxW(
		0,
		f"Delete the instance '{instance['name']}' and all of its worlds, mods, and settings?\n\nThis cannot be undone.",
		"Delete Minecraft Instance",
		0x04 | 0x30 | 0x100,
	)
	if confirmation != 6:
		return

	instance_id: str = instance["id"]
	INSTANCES.remove(instance)
	instance_dir: pathlib.Path = INSTANCES_DIR / instance_id
	if instance_dir.exists():
		shutil.rmtree(instance_dir)
	SELECTED_INSTANCE_ID = INSTANCES[0]["id"]
	SaveInstances()
	SetStatus(f"Deleted instance {instance['name']}.", ACCENT)


def SetInstanceVersion(version_id: str, instance_id: str | None = None) -> None:
	target_id: str = instance_id or SELECTED_INSTANCE_ID
	instance: dict | None = next(
		(item for item in INSTANCES if item["id"] == target_id),
		None,
	)
	if instance is None:
		raise RuntimeError("The target instance no longer exists.")
	instance["version_id"] = version_id
	SaveInstances()


def CheckForUpdates() -> bool:
	try:
		response: requests.Response = SESSION.get(
			GITHUB_RELEASE_API_URL,
			timeout=(3, 5),
			headers={"Accept": "application/vnd.github+json"},
		)
		if response.status_code == 404:
			return False
		response.raise_for_status()
		release: dict = response.json()

		release_version: str = str(release.get("tag_name", "")).lstrip("v")
		current_parts: tuple[int, ...] = tuple(
			int(part) for part in re.findall(r"\d+", LAUNCHER_VERSION)
		)

		release_parts: tuple[int, ...] = tuple(
			int(part) for part in re.findall(r"\d+", release_version)
		)

		if not release_parts or release_parts <= current_parts:
			return False

		assets: list[dict] = release.get("assets", [])
		asset: dict | None = next(
			(item for item in assets if item.get("name") == SCRIPT_PATH.name),
			None,
		)
		if asset is None:
			print(
				f"Update {release_version} is available, but the release "
				f"does not contain an asset named {SCRIPT_PATH.name}."
			)
			return False

		result: int = ctypes.windll.user32.MessageBoxW(
			0,
			f"A new launcher update is available!\n\n"
			f"Current version: {LAUNCHER_VERSION}\n"
			f"New version: {release_version}\n\n"
			f"Would you like to install it now?",
			"Minecraft Launcher Update",
			0x04 | 0x20,
		)

		if result != 6:
			return False

		SetStatus(f"Downloading launcher update {release_version}...")
		update_response: requests.Response = SESSION.get(
			asset["browser_download_url"],
			timeout=(5, 30),
		)
		update_response.raise_for_status()
		content: bytes = update_response.content
		if not content:
			raise RuntimeError("The downloaded launcher update is empty.")

		compile(content.decode("utf-8-sig"), str(SCRIPT_PATH), "exec")

		digest_info: str | None = asset.get("digest")
		if digest_info and digest_info.startswith("sha256:"):
			expected_digest: str = digest_info.removeprefix("sha256:")
			actual_digest: str = hashlib.sha256(content).hexdigest()
			if actual_digest.lower() != expected_digest.lower():
				raise RuntimeError("Launcher update SHA-256 verification failed.")

		UPDATE_FILE.write_bytes(content)
		updater_code: str = "\n".join([
			"import os",
			"import pathlib",
			"import subprocess",
			"import sys",
			"import time",
			"pid = int(sys.argv[1])",
			"source = pathlib.Path(sys.argv[2])",
			"target = pathlib.Path(sys.argv[3])",
			"python = sys.argv[4]",
			"while True:",
			"    try:",
			"        os.kill(pid, 0)",
			"    except OSError:",
			"        break",
			"    time.sleep(0.25)",
			"os.replace(source, target)",
			"subprocess.Popen([python, str(target)], cwd=str(target.parent), close_fds=True)",
		])

		creation_flags: int = 0
		if os.name == "nt":
			creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

		subprocess.Popen(
			[
				sys.executable,
				"-c",
				updater_code,
				str(os.getpid()),
				str(UPDATE_FILE),
				str(SCRIPT_PATH),
				sys.executable,
			],
			cwd=str(BASE_DIR),
			close_fds=True,
			creationflags=creation_flags,
		)
		SetStatus(f"Updating to launcher {release_version}...")
		return True

	except Exception as exception:
		print(f"Launcher update check failed: {exception}")
		return False


def LoadUsername() -> None:
	global USERNAME

	if USERNAME_FILE.is_file():
		username: str = USERNAME_FILE.read_text(encoding="utf-8").strip()
		if username:
			USERNAME = username[:16]


def SaveUsername() -> None:
	USERNAME_FILE.write_text(USERNAME, encoding="utf-8")


def DrawText(
	text: str,
	x: int,
	y: int,
	font: pygame.font.Font = FONT,
	color: tuple[int, int, int] = TEXT,
	align: str = "topleft",
) -> None:
	surface: pygame.Surface = font.render(text, True, color)
	rect: pygame.Rect = surface.get_rect()
	setattr(rect, align, (x, y))
	SCREEN.blit(surface, rect)


def DrawButton(
	rect: pygame.Rect,
	text: str,
	enabled: bool = True,
) -> None:
	mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
	hovered: bool = enabled and rect.collidepoint(mouse_pos)

	color: tuple[int, int, int] = BUTTON_HOVER if hovered else BUTTON
	if not enabled:
		color = (35, 40, 50)

	shadow_rect: pygame.Rect = rect.move(0, 3)
	pygame.draw.rect(SCREEN, (12, 15, 20), shadow_rect, border_radius=8)
	pygame.draw.rect(SCREEN, color, rect, border_radius=8)
	pygame.draw.rect(
		SCREEN,
		(91, 105, 126) if hovered else (59, 69, 85),
		rect,
		width=1,
		border_radius=8,
	)

	surface: pygame.Surface = BUTTON_FONT.render(
		text,
		True,
		TEXT if enabled else MUTED,
	)

	SCREEN.blit(
		surface,
		surface.get_rect(center=rect.center),
	)


def DrawInputField(
	rect: pygame.Rect,
	value: str,
	active: bool,
	placeholder: str = "",
) -> None:
	pygame.draw.rect(SCREEN, (21, 25, 33), rect, border_radius=7)
	pygame.draw.rect(
		SCREEN,
		ACCENT if active else (59, 69, 85),
		rect,
		width=1,
		border_radius=7,
	)
	display = value if value else placeholder
	color = TEXT if value else MUTED
	surface = FONT.render(display[:40], True, color)
	clip = SCREEN.get_clip()
	SCREEN.set_clip(rect.inflate(-10, -4))
	SCREEN.blit(surface, surface.get_rect(midleft=(rect.x + 10, rect.centery)))
	SCREEN.set_clip(clip)


def SetStatus(
	message: str,
	color: tuple[int, int, int] = TEXT,
	progress: float | None = None,
) -> None:
	global STATUS, STATUS_COLOR, PROGRESS

	STATUS = message
	STATUS_COLOR = color

	if progress is not None:
		PROGRESS = max(0.0, min(1.0, progress))

	pygame.event.pump()
	DrawInterface()
	pygame.display.flip()


def DownloadFile(
	url: str,
	path: pathlib.Path,
	sha1: str | None = None,
) -> None:
	if path.is_file():
		if sha1 is None:
			return

		digest: str = hashlib.sha1(path.read_bytes()).hexdigest()
		if digest == sha1:
			return

	path.parent.mkdir(parents=True, exist_ok=True)

	response: requests.Response = SESSION.get(
		url,
		stream=True,
		timeout=(15, 60),
	)
	response.raise_for_status()

	temp_path: pathlib.Path = path.with_suffix(path.suffix + ".part")

	try:
		with temp_path.open("wb") as file:
			for chunk in response.iter_content(chunk_size=1024 * 1024):
				if chunk:
					file.write(chunk)

		if sha1 is not None:
			digest = hashlib.sha1(temp_path.read_bytes()).hexdigest()
			if digest != sha1:
				raise RuntimeError(f"SHA-1 verification failed: {path.name}")

		temp_path.replace(path)
	finally:
		response.close()
		if temp_path.exists():
			temp_path.unlink()


def GetJson(url: str) -> dict | list:
	response: requests.Response = SESSION.get(url, timeout=30)
	response.raise_for_status()
	return response.json()


def LoadVersions() -> None:
	global MANIFEST, VERSIONS

	MANIFEST = GetJson(VERSION_MANIFEST_URL)
	VERSIONS = MANIFEST["versions"]

	ApplyVersionFilter()


def ApplyVersionFilter() -> None:
	global VISIBLE_VERSIONS

	if VERSION_FILTER == "all":
		VISIBLE_VERSIONS = VERSIONS.copy()
	else:
		VISIBLE_VERSIONS = [
			version
			for version in VERSIONS
			if version["type"] == VERSION_FILTER
		]


def IsRuleAllowed(rules: list[dict] | None) -> bool:
	if not rules:
		return True

	allowed: bool = False
	os_name: str = "windows"
	os_arch: str = platform.machine().lower()

	if os_arch == "amd64":
		os_arch = "x86_64"
	elif os_arch == "x86":
		os_arch = "x86"
	elif os_arch == "aarch64":
		os_arch = "arm64"

	for rule in rules:
		os_rule: dict = rule.get("os", {})

		if "name" in os_rule and os_rule["name"] != os_name:
			continue

		if "arch" in os_rule:
			if os_rule["arch"] != os_arch:
				continue

		allowed = rule["action"] == "allow"

	return allowed


def GetNativeClassifier(library: dict) -> str | None:
	natives: dict = library.get("natives", {})
	native_name: str | None = natives.get("windows")

	if native_name is None:
		return None

	arch: str = platform.architecture()[0]
	arch_value: str = "64" if arch == "64bit" else "32"

	return native_name.replace("${arch}", arch_value)


def GetLibraryPath(library: dict) -> pathlib.Path | None:
	artifact: dict | None = library.get("downloads", {}).get("artifact")
	if artifact is not None:
		return pathlib.Path(artifact["path"])

	name: str | None = library.get("name")
	if name is None:
		return None

	coordinate, separator, extension = name.partition("@")
	parts: list[str] = coordinate.split(":")
	if len(parts) not in (3, 4):
		raise ValueError(f"Invalid Maven coordinate: {name}")

	group: str
	artifact_name: str
	version: str
	group, artifact_name, version = parts[:3]
	classifier: str = parts[3] if len(parts) == 4 else ""
	file_name: str = f"{artifact_name}-{version}"
	if classifier:
		file_name += f"-{classifier}"
	file_name += f".{extension if separator else 'jar'}"

	return pathlib.Path(group.replace(".", "/")) / artifact_name / version / file_name


def DownloadLibrary(library: dict) -> pathlib.Path | None:
	if not IsRuleAllowed(library.get("rules")):
		return None

	artifact: dict | None = library.get("downloads", {}).get("artifact")
	relative_path: pathlib.Path | None = GetLibraryPath(library)
	if relative_path is None:
		return None

	library_path: pathlib.Path = LIBRARIES_DIR / relative_path

	if artifact is not None:
		DownloadFile(
			artifact["url"],
			library_path,
			artifact.get("sha1"),
		)
	else:
		name: str = library["name"]
		repository: str = library.get("url", "https://maven.fabricmc.net/")
		DownloadFile(
			repository.rstrip("/") + "/" + relative_path.as_posix(),
			library_path,
		)

	return library_path


def InstallFabric(version: dict, instance_id: str | None = None) -> None:
	global BUSY

	# Install the vanilla files first. Fabric's version profile inherits them.
	InstallVersion(version, instance_id)

	version_id: str = version["id"]
	version_dir: pathlib.Path = VERSIONS_DIR / version_id
	version_json_path: pathlib.Path = version_dir / f"{version_id}.json"
	client_path: pathlib.Path = version_dir / f"{version_id}.jar"
	if not version_json_path.is_file() or not client_path.is_file():
		raise RuntimeError("The vanilla Minecraft installation could not be completed.")

	BUSY = True
	try:
		SetStatus("Fetching Fabric Loader versions...", progress=0.0)

		loader_versions: list[dict] = GetJson(
			f"https://meta.fabricmc.net/v2/versions/loader/{version_id}"
		)
		if not loader_versions:
			raise RuntimeError(f"No Fabric Loader versions are available for Minecraft {version_id}.")

		stable_versions: list[dict] = [
			item for item in loader_versions
			if item.get("loader", {}).get("stable", False)
		]
		loader_version: str = (
			stable_versions[0] if stable_versions else loader_versions[0]
		)["loader"]["version"]

		SetStatus(f"Fetching Fabric {loader_version} profile...", progress=0.05)
		profile: dict = GetJson(
			f"https://meta.fabricmc.net/v2/versions/loader/"
			f"{version_id}/{loader_version}/profile/json"
		)

		profile_id: str = profile["id"]
		profile_dir: pathlib.Path = VERSIONS_DIR / profile_id
		profile_dir.mkdir(parents=True, exist_ok=True)

		libraries: list[dict] = profile.get("libraries", [])
		total_libraries: int = max(1, len(libraries))

		for index, library in enumerate(libraries):
			SetStatus(
				f"Downloading Fabric library {index + 1}/{total_libraries}",
				progress=0.1 + 0.8 * (index + 1) / total_libraries,
			)
			DownloadLibrary(library)

		profile_path: pathlib.Path = profile_dir / f"{profile_id}.json"
		profile_path.write_text(
			json.dumps(profile, indent=2),
			encoding="utf-8",
		)

		SetInstanceVersion(profile_id, instance_id)
		SetStatus(
			f"Installed Fabric {loader_version} for Minecraft {version_id}.",
			ACCENT,
			1.0,
		)
	finally:
		BUSY = False


def InstallVersion(version: dict, instance_id: str | None = None) -> None:
	global BUSY

	BUSY = True

	try:
		version_id: str = version["id"]
		version_dir: pathlib.Path = VERSIONS_DIR / version_id
		version_dir.mkdir(parents=True, exist_ok=True)

		SetStatus(f"Fetching metadata for {version_id}...", progress=0.0)

		version_json: dict = GetJson(version["url"])

		version_json_path: pathlib.Path = version_dir / f"{version_id}.json"
		version_json_path.write_text(
			json.dumps(version_json, indent=2),
			encoding="utf-8",
		)

		# Download the client JAR.
		client_info: dict = version_json["downloads"]["client"]

		SetStatus("Downloading Minecraft client...", progress=0.02)

		DownloadFile(
			client_info["url"],
			version_dir / f"{version_id}.jar",
			client_info.get("sha1"),
		)

		# Download libraries and extract Windows native libraries.
		libraries: list[dict] = version_json.get("libraries", [])
		total_libraries: int = max(1, len(libraries))

		for index, library in enumerate(libraries):
			if not IsRuleAllowed(library.get("rules")):
				continue

			downloads: dict = library.get("downloads", {})
			artifact: dict | None = downloads.get("artifact")

			if artifact is not None:
				relative_path: pathlib.Path = pathlib.Path(artifact["path"])

				SetStatus(
					f"Downloading library {index + 1}/{total_libraries}",
					progress=0.05 + 0.25 * (index + 1) / total_libraries,
				)

				DownloadFile(
					artifact["url"],
					LIBRARIES_DIR / relative_path,
					artifact.get("sha1"),
				)

			classifier_name: str | None = GetNativeClassifier(library)
			if classifier_name is None:
				continue

			classifiers: dict = downloads.get("classifiers", {})
			native_artifact: dict | None = classifiers.get(classifier_name)

			if native_artifact is None:
				continue

			native_path: pathlib.Path = (
				LIBRARIES_DIR / pathlib.Path(native_artifact["path"])
			)

			SetStatus(
				f"Downloading native library {index + 1}/{total_libraries}",
				progress=0.05 + 0.25 * (index + 1) / total_libraries,
			)

			DownloadFile(
				native_artifact["url"],
				native_path,
				native_artifact.get("sha1"),
			)

			native_dir: pathlib.Path = NATIVES_DIR / version_id
			native_dir.mkdir(parents=True, exist_ok=True)

			with zipfile.ZipFile(native_path) as archive:
				for member in archive.infolist():
					if member.is_dir() or member.filename.startswith("META-INF/"):
						continue

					target: pathlib.Path = (
						native_dir / pathlib.PurePosixPath(member.filename)
					)

					target.parent.mkdir(parents=True, exist_ok=True)

					with archive.open(member) as source, target.open("wb") as dest:
						shutil.copyfileobj(source, dest)

		# Download the asset index and its referenced objects.
		asset_index_info: dict = version_json["assetIndex"]
		asset_index_id: str = asset_index_info["id"]

		SetStatus("Downloading asset index...", progress=0.32)

		asset_index_path: pathlib.Path = (
			ASSETS_DIR / "indexes" / f"{asset_index_id}.json"
		)

		DownloadFile(
			asset_index_info["url"],
			asset_index_path,
			asset_index_info.get("sha1"),
		)

		asset_index: dict = json.loads(
			asset_index_path.read_text(encoding="utf-8")
		)

		objects: dict = asset_index.get("objects", {})
		total_assets: int = max(1, len(objects))

		for index, (name, metadata) in enumerate(objects.items()):
			file_hash: str = metadata["hash"]

			object_path: pathlib.Path = (
				ASSETS_DIR / "objects" / file_hash[:2] / file_hash
			)

			DownloadFile(
				f"https://resources.download.minecraft.net/"
				f"{file_hash[:2]}/{file_hash}",
				object_path,
				file_hash,
			)

			if index % 20 == 0 or index + 1 == total_assets:
				SetStatus(
					f"Downloading assets: {index + 1}/{len(objects)}",
					progress=0.32 + 0.63 * (index + 1) / total_assets,
				)

		SetInstanceVersion(version_id, instance_id)

		SetStatus(
			f"Installed Minecraft {version_id} successfully.",
			ACCENT,
			1.0,
		)

	except Exception as exception:
		SetStatus(f"Installation failed: {exception}", ERROR)

	finally:
		BUSY = False



def GetArgumentValues(
	arguments: list,
	variables: dict[str, str],
) -> list[str]:
	result: list[str] = []

	os_name: str = "windows"
	os_arch: str = platform.machine().lower()

	if os_arch == "amd64":
		os_arch = "x86_64"
	elif os_arch == "aarch64":
		os_arch = "arm64"

	os_version: str = platform.version()

	features: dict[str, bool] = {
		"is_demo_user": False,
		"has_custom_resolution": True,
		"has_quick_plays_support": False,
		"is_quick_play_singleplayer": False,
		"is_quick_play_multiplayer": False,
		"is_quick_play_realms": False,
	}

	for argument in arguments:
		if isinstance(argument, str):
			value: list[str] = [argument]
		elif isinstance(argument, dict):
			value = argument.get("value", [])
			if isinstance(value, str):
				value = [value]

			allowed: bool = True

			for rule in argument.get("rules", []):
				os_rule: dict = rule.get("os", {})

				if "name" in os_rule and os_rule["name"] != os_name:
					matches: bool = False
				else:
					matches = True

				if "arch" in os_rule and os_rule["arch"] != os_arch:
					matches = False

				if "version" in os_rule:
					try:
						matches = matches and bool(
							__import__("re").search(
								os_rule["version"],
								os_version,
							)
						)
					except Exception:
						matches = False

				if "features" in rule:
					for feature, expected in rule["features"].items():
						if features.get(feature, False) != expected:
							matches = False
							break

				allowed = matches if rule["action"] == "allow" else not matches

			if not allowed:
				continue
		else:
			continue

		for item in value:
			for key, replacement in variables.items():
				item = item.replace("${" + key + "}", replacement)

			result.append(item)

	return result




def LaunchCurrentInstall() -> None:
	global BUSY

	try:
		instance: dict | None = GetSelectedInstance()
		if instance is None:
			raise FileNotFoundError("Create or select a Minecraft instance first.")
		if not instance.get("version_id"):
			raise FileNotFoundError("Install a Minecraft version for this instance first.")

		instance_id: str = instance["id"]
		instance_dir: pathlib.Path = INSTANCES_DIR / instance_id
		version_id: str = instance["version_id"]

		version_dir: pathlib.Path = VERSIONS_DIR / version_id
		version_json_path: pathlib.Path = version_dir / f"{version_id}.json"

		if not version_json_path.is_file():
			raise FileNotFoundError(
				f"Installation {version_id} is incomplete. Reinstall it first."
			)

		installation_json: dict = json.loads(
			version_json_path.read_text(encoding="utf-8")
		)

		base_version_id: str = installation_json.get("inheritsFrom", version_id)
		base_version_dir: pathlib.Path = VERSIONS_DIR / base_version_id
		base_version_json_path: pathlib.Path = (
			base_version_dir / f"{base_version_id}.json"
		)
		client_path: pathlib.Path = (
			base_version_dir / f"{base_version_id}.jar"
		)

		if not base_version_json_path.is_file() or not client_path.is_file():
			raise FileNotFoundError(
				f"Minecraft {base_version_id} is incomplete. Reinstall it first."
			)

		version_json: dict = json.loads(
			base_version_json_path.read_text(encoding="utf-8")
		)

		client_size: int = client_path.stat().st_size
		if client_size == 0:
			raise RuntimeError("The Minecraft client JAR is empty. Reinstall it.")

		native_dir: pathlib.Path = NATIVES_DIR / base_version_id
		asset_index_id: str = version_json["assetIndex"]["id"]

		classpath: list[str] = [str(client_path)]
		all_libraries: list[dict] = [
			*version_json.get("libraries", []),
			*installation_json.get("libraries", []),
		]

		for library in all_libraries:
			library_path: pathlib.Path | None = GetLibraryPath(library)
			if library_path is None or not IsRuleAllowed(library.get("rules")):
				continue

			full_library_path: pathlib.Path = LIBRARIES_DIR / library_path
			if not full_library_path.is_file():
				raise FileNotFoundError(
					f"Missing library: {full_library_path}. Reinstall the installation."
				)

			if str(full_library_path) not in classpath:
				classpath.append(str(full_library_path))

		classpath_argument: str = os.pathsep.join(classpath)

		memory_max = (instance.get("memory_max") or "2G").strip() or "2G"
		memory_min = (instance.get("memory_min") or "512M").strip() or "512M"
		extra_jvm = (instance.get("jvm_args") or "").strip()
		res_w = (instance.get("resolution_width") or "1280").strip() or "1280"
		res_h = (instance.get("resolution_height") or "720").strip() or "720"

		variables: dict[str, str] = {
			"auth_player_name": USERNAME,
			"version_name": version_id,
			"game_directory": str(instance_dir),
			"assets_root": str(ASSETS_DIR),
			"assets_index_name": asset_index_id,
			"auth_uuid": "00000000000000000000000000000000",
			"auth_access_token": "0",
			"user_type": "legacy",
			"version_type": version_json.get("type", "release"),
			"natives_directory": str(native_dir),
			"launcher_name": "CustomLauncher",
			"launcher_version": "1.0",
			"classpath": classpath_argument,
			"classpath_separator": os.pathsep,
			"library_directory": str(LIBRARIES_DIR),
			"clientid": "",
			"auth_xuid": "",
			"resolution_width": res_w,
			"resolution_height": res_h,
		}

		base_arguments: dict = version_json.get("arguments", {})
		installation_arguments: dict = installation_json.get("arguments", {})

		if installation_json.get("inheritsFrom"):
			jvm_arguments: list = [
				*base_arguments.get("jvm", []),
				*installation_arguments.get("jvm", []),
			]
			game_arguments: list = [
				*base_arguments.get("game", []),
				*installation_arguments.get("game", []),
			]
		else:
			jvm_arguments = base_arguments.get("jvm", [])
			game_arguments = base_arguments.get("game", [])

		if base_arguments or installation_arguments:
			jvm_args: list[str] = GetArgumentValues(jvm_arguments, variables)
			game_args: list[str] = GetArgumentValues(game_arguments, variables)

			jvm_args = [
				argument.replace("${classpath}", classpath_argument)
				for argument in jvm_args
			]

			if not any(
				argument in ("-cp", "-classpath", "--class-path")
				for argument in jvm_args
			):
				jvm_args.extend(["-cp", classpath_argument])
		else:
			jvm_args = [
				"-Djava.library.path=" + str(native_dir),
				"-cp",
				classpath_argument,
			]

			legacy_arguments: list[str] = version_json.get(
				"minecraftArguments",
				"",
			).split()

			game_args = []
			for argument in legacy_arguments:
				for key, value in variables.items():
					argument = argument.replace("${" + key + "}", value)
				game_args.append(argument)

		memory_args = [f"-Xms{memory_min}", f"-Xmx{memory_max}"]
		extra_jvm_list = extra_jvm.split() if extra_jvm else []
		jvm_args = memory_args + extra_jvm_list + jvm_args

		main_class: str = installation_json.get(
			"mainClass",
			version_json["mainClass"],
		)

		command: list[str] = [
			"java",
			"-Djava.library.path=" + str(native_dir),
			*jvm_args,
			main_class,
			*game_args,
		]

		instance_dir.mkdir(parents=True, exist_ok=True)
		SetStatus(f"Launching {instance['name']} ({version_id})...", ACCENT)

		print("Client JAR:", client_path)
		print("Client size:", client_size)
		print("Main class:", main_class)
		print("Classpath:", classpath_argument)
		print("Command:", command)

		BUSY = True

		subprocess.Popen(
			command,
			cwd=instance_dir,
		)

		SetStatus(f"Launched {instance['name']} ({version_id}).", ACCENT)

	except Exception as exception:
		SetStatus(f"Launch failed: {exception}", ERROR)

	finally:
		BUSY = False


def StartBackgroundTask(target, *args) -> None:
	global BUSY

	if BUSY:
		return

	BUSY = True

	def Run() -> None:
		try:
			target(*args)
		except Exception as exception:
			SetStatus(f"Error: {exception}", ERROR)
		finally:
			BUSY = False

	threading.Thread(target=Run, daemon=True).start()


def DrawInterface() -> None:
	SCREEN.fill(BACKGROUND)

	pygame.draw.rect(SCREEN, (23, 28, 37), pygame.Rect(0, 0, WIDTH, 88))
	pygame.draw.line(SCREEN, (45, 54, 68), (0, 87), (WIDTH, 87), 1)
	pygame.draw.rect(SCREEN, ACCENT, pygame.Rect(26, 22, 4, 43), border_radius=2)
	DrawText("Minecraft Launcher", 43, 17, TITLE_FONT)
	DrawText("JAVA EDITION", 45, 57, SMALL_FONT, MUTED)
	DrawText(f"v{LAUNCHER_VERSION}", 850, 43, SMALL_FONT, MUTED, "midright")

	tab_rects: dict[str, pygame.Rect] = {
		"launch": pygame.Rect(25, 103, 130, 42),
		"install": pygame.Rect(160, 103, 130, 42),
		"instances": pygame.Rect(295, 103, 130, 42),
		"options": pygame.Rect(430, 103, 130, 42),
	}
	for tab_name, rect in tab_rects.items():
		selected: bool = CURRENT_TAB == tab_name
		pygame.draw.rect(SCREEN, PANEL if selected else BACKGROUND, rect, border_radius=8)
		if selected:
			pygame.draw.rect(SCREEN, ACCENT, pygame.Rect(rect.x, rect.bottom - 3, rect.width, 3), border_radius=2)
		DrawText(tab_name.title(), *rect.center, MEDIUM_FONT, TEXT if selected else MUTED, "center")

	content_rect: pygame.Rect = pygame.Rect(25, 153, 850, 390)
	pygame.draw.rect(SCREEN, PANEL, content_rect, border_radius=10)
	pygame.draw.rect(SCREEN, (48, 57, 72), content_rect, width=1, border_radius=10)

	if CURRENT_TAB == "launch":
		instance: dict | None = GetSelectedInstance()
		DrawText("Launch Minecraft", 55, 180, TITLE_FONT)
		DrawText("Launch the selected Minecraft instance.", 57, 218, FONT, MUTED)
		DrawText("Username", 70, 250, SMALL_FONT, MUTED)
		DrawInputField(USERNAME_RECT, USERNAME, ACTIVE_FIELD == "username")
		DrawText("Your username is saved automatically.", 70, 302, SMALL_FONT, MUTED)

		pygame.draw.rect(SCREEN, (23, 28, 37), pygame.Rect(555, 235, 270, 125), border_radius=8)
		DrawText("SELECTED INSTANCE", 575, 250, SMALL_FONT, MUTED)
		DrawText(instance["name"][:24] if instance else "None", 575, 275, MEDIUM_FONT)
		version_label = (instance.get("version_id") or "No version installed")[:30] if instance else ""
		DrawText(version_label, 575, 307, SMALL_FONT, MUTED)
		if instance:
			mem_max = instance.get("memory_max", "2G")
			mem_min = instance.get("memory_min", "512M")
			DrawText(f"RAM: {mem_min} – {mem_max}", 575, 328, SMALL_FONT, MUTED)

		launch_rect: pygame.Rect = pygame.Rect(70, 375, 755, 54)
		DrawButton(launch_rect, "Launch Minecraft", not BUSY and bool(instance and instance.get("version_id")))

	elif CURRENT_TAB == "options":
		instance: dict | None = GetSelectedInstance()
		DrawText("Launch options", 50, 169, TITLE_FONT)
		instance_name = instance["name"] if instance else "No instance selected"
		DrawText(f"Editing options for: {instance_name}", 52, 205, FONT, MUTED)

		mem_max = instance.get("memory_max", "2G") if instance else "2G"
		mem_min = instance.get("memory_min", "512M") if instance else "512M"
		jvm = instance.get("jvm_args", "") if instance else ""
		res_w = instance.get("resolution_width", "1280") if instance else "1280"
		res_h = instance.get("resolution_height", "720") if instance else "720"

		DrawText("Max memory", 55, 230, SMALL_FONT, MUTED)
		DrawText("Min memory", 255, 230, SMALL_FONT, MUTED)
		DrawInputField(MEMORY_MAX_RECT, mem_max, ACTIVE_FIELD == "memory_max", "2G")
		DrawInputField(MEMORY_MIN_RECT, mem_min, ACTIVE_FIELD == "memory_min", "512M")
		DrawText("Examples: 2G, 4G, 8G   /   512M, 1G", 450, 260, SMALL_FONT, MUTED)

		DrawText("Extra JVM arguments", 55, 320, SMALL_FONT, MUTED)
		DrawInputField(JVM_ARGS_RECT, jvm, ACTIVE_FIELD == "jvm_args", "-XX:+UseG1GC")
		DrawText("Optional. Space-separated flags passed to Java.", 55, 390, SMALL_FONT, MUTED)

		DrawText("Resolution (width × height)", 55, 410, SMALL_FONT, MUTED)
		DrawInputField(RES_W_RECT, res_w, ACTIVE_FIELD == "res_w", "1280")
		DrawText("×", 182, 440, FONT, MUTED)
		DrawInputField(RES_H_RECT, res_h, ACTIVE_FIELD == "res_h", "720")

		DrawText("Options are saved automatically for the selected instance.", 55, 495, SMALL_FONT, MUTED)

	elif CURRENT_TAB == "install":
		DrawText("Install Minecraft", 50, 169, TITLE_FONT)
		selected_instance: dict | None = GetSelectedInstance()
		DrawText(
			f"Installing will update: {selected_instance['name'] if selected_instance else 'No instance selected'}",
			52, 205, FONT, MUTED,
		)

		filter_rects: dict[str, pygame.Rect] = {
			"release": pygame.Rect(50, 242, 112, 32),
			"snapshot": pygame.Rect(170, 242, 112, 32),
			"old_beta": pygame.Rect(290, 242, 100, 32),
			"all": pygame.Rect(398, 242, 65, 32),
		}
		for name, rect in filter_rects.items():
			label: str = {"release": "Releases", "snapshot": "Snapshots", "old_beta": "Old beta", "all": "All"}[name]
			selected_filter: bool = VERSION_FILTER == name
			pygame.draw.rect(SCREEN, (43, 111, 78) if selected_filter else BUTTON, rect, border_radius=6)
			if selected_filter:
				pygame.draw.rect(SCREEN, ACCENT, rect, width=1, border_radius=6)
			DrawText(label, *rect.center, SMALL_FONT, TEXT if selected_filter else MUTED, "center")

		list_rect: pygame.Rect = pygame.Rect(50, 284, 415, 225)
		pygame.draw.rect(SCREEN, (21, 25, 33), list_rect, border_radius=7)
		clip_rect = SCREEN.get_clip()
		SCREEN.set_clip(list_rect)
		for index, version in enumerate(VISIBLE_VERSIONS):
			y: int = 288 + index * 29 - SCROLL_OFFSET
			if y + 26 < list_rect.top or y > list_rect.bottom:
				continue
			row: pygame.Rect = pygame.Rect(54, y, 407, 26)
			is_selected: bool = version["id"] == SELECTED_VERSION
			if is_selected:
				pygame.draw.rect(SCREEN, (43, 91, 70), row, border_radius=5)
			elif row.collidepoint(pygame.mouse.get_pos()):
				pygame.draw.rect(SCREEN, BUTTON, row, border_radius=5)
			DrawText(version["id"], 64, row.centery, FONT, align="midleft")
			DrawText(version["type"].replace("_", " ").title(), 450, row.centery, SMALL_FONT, MUTED, "midright")
		SCREEN.set_clip(clip_rect)

		max_scroll: int = max(0, len(VISIBLE_VERSIONS) * 29 - list_rect.height)
		if max_scroll > 0:
			track: pygame.Rect = pygame.Rect(469, 288, 3, 221)
			thumb_height: int = max(24, int(track.height * track.height / (track.height + max_scroll)))
			thumb_y: int = track.y + int((track.height - thumb_height) * SCROLL_OFFSET / max_scroll)
			pygame.draw.rect(SCREEN, (48, 57, 72), track, border_radius=2)
			pygame.draw.rect(SCREEN, (120, 135, 155), pygame.Rect(track.x, thumb_y, 3, thumb_height), border_radius=2)

		pygame.draw.line(SCREEN, (48, 57, 72), (495, 235), (495, 510), 1)
		DrawText("Selected version", 525, 245, SMALL_FONT, MUTED)
		DrawText(SELECTED_VERSION or "None selected", 525, 269, MEDIUM_FONT)
		DrawText("Installation type", 525, 315, SMALL_FONT, MUTED)
		vanilla_rect: pygame.Rect = pygame.Rect(525, 340, 135, 38)
		fabric_rect: pygame.Rect = pygame.Rect(670, 340, 135, 38)
		for loader_name, rect in (("vanilla", vanilla_rect), ("fabric", fabric_rect)):
			selected_loader: bool = INSTALL_LOADER == loader_name
			pygame.draw.rect(SCREEN, (43, 111, 78) if selected_loader else BUTTON, rect, border_radius=6)
			pygame.draw.rect(SCREEN, ACCENT if selected_loader else (59, 69, 85), rect, width=1, border_radius=6)
			DrawText("Normal" if loader_name == "vanilla" else "Fabric", *rect.center, FONT, TEXT if selected_loader else MUTED, "center")
		DrawText("Files are shared between instances.", 525, 397, SMALL_FONT, MUTED)
		DrawButton(pygame.Rect(525, 445, 280, 48), "Install selected version", bool(SELECTED_VERSION) and not BUSY)

	else:
		DrawText("Manage instances", 50, 169, TITLE_FONT)
		DrawText("Each instance has separate worlds, mods and settings.", 52, 205, FONT, MUTED)
		pygame.draw.rect(SCREEN, (21, 25, 33), INSTANCE_NAME_RECT, border_radius=7)
		pygame.draw.rect(SCREEN, ACCENT if INSTANCE_NAME_ACTIVE else (59, 69, 85), INSTANCE_NAME_RECT, width=1, border_radius=7)
		name_surface: pygame.Surface = FONT.render(INSTANCE_NAME_INPUT, True, TEXT)
		SCREEN.blit(name_surface, name_surface.get_rect(midleft=(INSTANCE_NAME_RECT.x + 12, INSTANCE_NAME_RECT.centery)))
		DrawButton(pygame.Rect(575, 225, 250, 42), "Create instance", not BUSY)

		instance_list_rect: pygame.Rect = pygame.Rect(50, 282, 775, 205)
		pygame.draw.rect(SCREEN, (21, 25, 33), instance_list_rect, border_radius=7)
		clip_rect = SCREEN.get_clip()
		SCREEN.set_clip(instance_list_rect)
		for index, instance in enumerate(INSTANCES):
			y: int = 287 + index * 48 - INSTANCE_SCROLL_OFFSET
			if y + 43 < instance_list_rect.top or y > instance_list_rect.bottom:
				continue
			row: pygame.Rect = pygame.Rect(55, y, 765, 42)
			selected_instance: bool = instance["id"] == SELECTED_INSTANCE_ID
			if selected_instance:
				pygame.draw.rect(SCREEN, (43, 91, 70), row, border_radius=6)
			elif row.collidepoint(pygame.mouse.get_pos()):
				pygame.draw.rect(SCREEN, BUTTON, row, border_radius=6)
			DrawText(instance["name"][:36], 68, row.centery - 8, FONT, TEXT if selected_instance else MUTED, "midleft")
			DrawText(instance.get("version_id") or "No version installed", 68, row.centery + 11, SMALL_FONT, MUTED, "midleft")
			DrawText("Selected" if selected_instance else "Select", 800, row.centery, SMALL_FONT, ACCENT if selected_instance else MUTED, "midright")
		SCREEN.set_clip(clip_rect)
		DrawButton(pygame.Rect(650, 493, 175, 36), "Delete selected", len(INSTANCES) > 1 and not BUSY)

	progress_rect: pygame.Rect = pygame.Rect(25, 558, 850, 7)
	pygame.draw.rect(SCREEN, (47, 56, 70), progress_rect, border_radius=4)
	if PROGRESS > 0:
		fill_rect: pygame.Rect = progress_rect.copy()
		fill_rect.width = max(4, int(fill_rect.width * PROGRESS))
		pygame.draw.rect(SCREEN, ACCENT, fill_rect, border_radius=4)

	pygame.draw.rect(SCREEN, (23, 28, 37), pygame.Rect(25, 578, 850, 48), border_radius=8)
	status_dot_color: tuple[int, int, int] = ERROR if STATUS_COLOR == ERROR else ACCENT
	pygame.draw.circle(SCREEN, status_dot_color, (44, 602), 4)
	DrawText(STATUS[:115], 58, 602, FONT, STATUS_COLOR, "midleft")


SCROLL_OFFSET: int = 0


def Main() -> None:
	global SHOULD_QUIT
	global SELECTED_VERSION
	global VERSION_FILTER
	global SCROLL_OFFSET
	global USERNAME
	global ACTIVE_FIELD
	global FIELD_SELECT_ALL
	global INSTALL_LOADER
	global CURRENT_TAB
	global SELECTED_INSTANCE_ID
	global INSTANCE_NAME_ACTIVE, INSTANCE_NAME_INPUT, INSTANCE_NAME_SELECT_ALL, INSTANCE_SCROLL_OFFSET

	LoadUsername()
	SaveUsername()
	LoadInstances()

	if CheckForUpdates():
		pygame.quit()
		return

	try:
		LoadVersions()

		if MANIFEST.get("latest", {}).get("release"):
			SELECTED_VERSION = MANIFEST["latest"]["release"]

		SetStatus(f"Loaded {len(VERSIONS)} Minecraft versions.", ACCENT)

	except Exception as exception:
		SetStatus(f"Could not load versions: {exception}", ERROR)

	while not SHOULD_QUIT:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				SHOULD_QUIT = True
				if USERNAME:
					SaveUsername()
				SaveInstances()

			elif event.type == pygame.TEXTINPUT:
				if ACTIVE_FIELD == "username":
					new_characters: str = "".join(
						character for character in event.text
						if character.isascii() and (character.isalnum() or character == "_")
					)
					USERNAME = new_characters[:16] if FIELD_SELECT_ALL else (USERNAME + new_characters)[:16]
					FIELD_SELECT_ALL = False
					SaveUsername()
				elif ACTIVE_FIELD in ("memory_max", "memory_min", "jvm_args", "res_w", "res_h"):
					instance = GetSelectedInstance()
					if instance is None:
						continue
					key_map = {
						"memory_max": "memory_max",
						"memory_min": "memory_min",
						"jvm_args": "jvm_args",
						"res_w": "resolution_width",
						"res_h": "resolution_height",
					}
					key = key_map[ACTIVE_FIELD]
					current = instance.get(key, "")
					allowed = event.text
					if ACTIVE_FIELD in ("memory_max", "memory_min"):
						allowed = "".join(c for c in event.text if c.isalnum() or c in "MmGgKk")
					elif ACTIVE_FIELD in ("res_w", "res_h"):
						allowed = "".join(c for c in event.text if c.isdigit())
					else:
						allowed = "".join(c for c in event.text if c.isprintable())
					if FIELD_SELECT_ALL:
						instance[key] = allowed[:64]
					else:
						instance[key] = (current + allowed)[:64]
					FIELD_SELECT_ALL = False
					SaveInstances()
				elif INSTANCE_NAME_ACTIVE:
					new_characters = "".join(character for character in event.text if character.isprintable())
					INSTANCE_NAME_INPUT = new_characters[:32] if INSTANCE_NAME_SELECT_ALL else (INSTANCE_NAME_INPUT + new_characters)[:32]
					INSTANCE_NAME_SELECT_ALL = False

			elif event.type == pygame.KEYDOWN:
				if ACTIVE_FIELD:
					if event.key == pygame.K_BACKSPACE:
						if ACTIVE_FIELD == "username":
							USERNAME = "" if FIELD_SELECT_ALL else USERNAME[:-1]
							FIELD_SELECT_ALL = False
							SaveUsername()
						elif ACTIVE_FIELD in ("memory_max", "memory_min", "jvm_args", "res_w", "res_h"):
							instance = GetSelectedInstance()
							if instance is not None:
								key_map = {
									"memory_max": "memory_max",
									"memory_min": "memory_min",
									"jvm_args": "jvm_args",
									"res_w": "resolution_width",
									"res_h": "resolution_height",
								}
								key = key_map[ACTIVE_FIELD]
								if FIELD_SELECT_ALL:
									instance[key] = ""
								else:
									instance[key] = instance.get(key, "")[:-1]
								FIELD_SELECT_ALL = False
								SaveInstances()
					elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_TAB):
						ACTIVE_FIELD = ""
						FIELD_SELECT_ALL = False
						pygame.key.stop_text_input()
				elif INSTANCE_NAME_ACTIVE:
					if event.key == pygame.K_BACKSPACE:
						INSTANCE_NAME_INPUT = "" if INSTANCE_NAME_SELECT_ALL else INSTANCE_NAME_INPUT[:-1]
						INSTANCE_NAME_SELECT_ALL = False
					elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
						INSTANCE_NAME_ACTIVE = False
						pygame.key.stop_text_input()

			elif event.type == pygame.MOUSEWHEEL:
				mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
				if CURRENT_TAB == "install" and pygame.Rect(50, 284, 415, 225).collidepoint(mouse_pos):
					max_scroll: int = max(0, len(VISIBLE_VERSIONS) * 29 - 225)
					SCROLL_OFFSET = max(0, min(max_scroll, SCROLL_OFFSET - event.y * 29))
				elif CURRENT_TAB == "instances" and pygame.Rect(50, 282, 775, 205).collidepoint(mouse_pos):
					max_instance_scroll: int = max(0, len(INSTANCES) * 48 - 205)
					INSTANCE_SCROLL_OFFSET = max(0, min(max_instance_scroll, INSTANCE_SCROLL_OFFSET - event.y * 48))

			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button != 1:
					continue

				mouse_pos = event.pos
				tab_rects: dict[str, pygame.Rect] = {
					"launch": pygame.Rect(25, 103, 130, 42),
					"install": pygame.Rect(160, 103, 130, 42),
					"instances": pygame.Rect(295, 103, 130, 42),
					"options": pygame.Rect(430, 103, 130, 42),
				}
				clicked_tab: str | None = next(
					(name for name, rect in tab_rects.items() if rect.collidepoint(mouse_pos)),
					None,
				)
				if clicked_tab is not None:
					CURRENT_TAB = clicked_tab
					ACTIVE_FIELD = ""
					INSTANCE_NAME_ACTIVE = False
					pygame.key.stop_text_input()
					continue

				if CURRENT_TAB == "launch":
					if USERNAME_RECT.collidepoint(mouse_pos):
						ACTIVE_FIELD = "username"
						FIELD_SELECT_ALL = True
						INSTANCE_NAME_ACTIVE = False
						pygame.key.start_text_input()
						continue

					ACTIVE_FIELD = ""
					INSTANCE_NAME_ACTIVE = False
					pygame.key.stop_text_input()
					if pygame.Rect(70, 375, 755, 54).collidepoint(mouse_pos) and not BUSY:
						StartBackgroundTask(LaunchCurrentInstall)

				elif CURRENT_TAB == "options":
					field_clicked = None
					if MEMORY_MAX_RECT.collidepoint(mouse_pos):
						field_clicked = "memory_max"
					elif MEMORY_MIN_RECT.collidepoint(mouse_pos):
						field_clicked = "memory_min"
					elif JVM_ARGS_RECT.collidepoint(mouse_pos):
						field_clicked = "jvm_args"
					elif RES_W_RECT.collidepoint(mouse_pos):
						field_clicked = "res_w"
					elif RES_H_RECT.collidepoint(mouse_pos):
						field_clicked = "res_h"

					if field_clicked:
						ACTIVE_FIELD = field_clicked
						FIELD_SELECT_ALL = True
						INSTANCE_NAME_ACTIVE = False
						pygame.key.start_text_input()
						continue

					ACTIVE_FIELD = ""
					INSTANCE_NAME_ACTIVE = False
					pygame.key.stop_text_input()

				elif CURRENT_TAB == "install":
					ACTIVE_FIELD = ""
					INSTANCE_NAME_ACTIVE = False
					pygame.key.stop_text_input()
					if pygame.Rect(525, 340, 135, 38).collidepoint(mouse_pos):
						INSTALL_LOADER = "vanilla"
						continue
					elif pygame.Rect(670, 340, 135, 38).collidepoint(mouse_pos):
						INSTALL_LOADER = "fabric"
						continue

					filter_rects: dict[str, pygame.Rect] = {
						"release": pygame.Rect(50, 242, 112, 32),
						"snapshot": pygame.Rect(170, 242, 112, 32),
						"old_beta": pygame.Rect(290, 242, 100, 32),
						"all": pygame.Rect(398, 242, 65, 32),
					}
					for name, rect in filter_rects.items():
						if rect.collidepoint(mouse_pos):
							VERSION_FILTER = name
							ApplyVersionFilter()
							SCROLL_OFFSET = 0
							break
					else:
						if pygame.Rect(50, 284, 415, 225).collidepoint(mouse_pos):
							index: int = (mouse_pos[1] - 288 + SCROLL_OFFSET) // 29
							if 0 <= index < len(VISIBLE_VERSIONS):
								SELECTED_VERSION = VISIBLE_VERSIONS[index]["id"]
						elif pygame.Rect(525, 445, 280, 48).collidepoint(mouse_pos) and SELECTED_VERSION and not BUSY:
							selected: dict | None = next(
								(version for version in VERSIONS if version["id"] == SELECTED_VERSION),
								None,
							)
							if selected is not None:
								install_function = InstallFabric if INSTALL_LOADER == "fabric" else InstallVersion
								StartBackgroundTask(install_function, selected, SELECTED_INSTANCE_ID)

				elif CURRENT_TAB == "instances":
					ACTIVE_FIELD = ""
					if INSTANCE_NAME_RECT.collidepoint(mouse_pos):
						INSTANCE_NAME_ACTIVE = True
						INSTANCE_NAME_SELECT_ALL = True
						pygame.key.start_text_input()
						continue
					INSTANCE_NAME_ACTIVE = False
					pygame.key.stop_text_input()
					if pygame.Rect(575, 225, 250, 42).collidepoint(mouse_pos) and not BUSY:
						CreateInstance(INSTANCE_NAME_INPUT, SELECTED_VERSION)
						INSTANCE_NAME_INPUT = "New instance"
						INSTANCE_SCROLL_OFFSET = max(0, len(INSTANCES) * 48 - 205)
						SetStatus(f"Created instance {INSTANCES[-1]['name']}.", ACCENT)
					elif pygame.Rect(650, 493, 175, 36).collidepoint(mouse_pos) and not BUSY:
						DeleteSelectedInstance()
					elif pygame.Rect(50, 282, 775, 205).collidepoint(mouse_pos):
						index = (mouse_pos[1] - 287 + INSTANCE_SCROLL_OFFSET) // 48
						if 0 <= index < len(INSTANCES):
							SELECTED_INSTANCE_ID = INSTANCES[index]["id"]
							SaveInstances()


		DrawInterface()
		pygame.display.flip()
		CLOCK.tick(FPS)

	pygame.quit()


if __name__ == "__main__":
	Main()
