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
import secrets

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
RUNTIMES_DIR: pathlib.Path = BASE_DIR / "runtime"
INSTANCES_DIR: pathlib.Path = BASE_DIR / "instances"
INSTANCES_FILE: pathlib.Path = BASE_DIR / "instances.json"
SELECTED_INSTANCE_FILE: pathlib.Path = BASE_DIR / "selected_instance.txt"
CURRENT_VERSION_FILE: pathlib.Path = BASE_DIR / "current_version.txt"
USERNAME_FILE: pathlib.Path = BASE_DIR / "username.txt"
SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
UPDATE_FILE: pathlib.Path = SCRIPT_PATH.with_suffix(SCRIPT_PATH.suffix + ".new")

GITHUB_OWNER: str = "Nobody0163"
GITHUB_REPOSITORY: str = "minecraft-launcher"
LAUNCHER_VERSION: str = "1.3.8"
GITHUB_RELEASE_API_URL: str = (
	f"https://api.github.com/repos/{GITHUB_OWNER}/"
	f"{GITHUB_REPOSITORY}/releases/latest"
)

VERSION_MANIFEST_URL: str = (
	"https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
)
JAVA_RUNTIME_MANIFEST_URL: str = (
	"https://piston-meta.mojang.com/v1/products/java-runtime/"
	"2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json"
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

MOD_INSTALLED_SCROLL: int = 0
MOD_INSTALLED_RECT: pygame.Rect = pygame.Rect(50, 282, 775, 225)

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


def OpenInstanceFolder(instance_id: str) -> None:
	instance_dir: pathlib.Path = INSTANCES_DIR / instance_id
	instance_dir.mkdir(parents=True, exist_ok=True)

	try:
		os.startfile(instance_dir)
	except OSError as exception:
		SetStatus(f"Could not open instance folder: {exception}", ERROR)


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
	field_id: str = "",
) -> None:
	pygame.draw.rect(SCREEN, (21, 25, 33), rect, border_radius=7)
	pygame.draw.rect(
		SCREEN,
		ACCENT if active else (59, 69, 85),
		rect,
		width=1 if not active else 2,
		border_radius=7,
	)

	padding: int = 10
	text_rect: pygame.Rect = rect.inflate(-padding * 2, -4)
	clip: pygame.Rect | None = SCREEN.get_clip()
	SCREEN.set_clip(text_rect)

	if not value:
		surface: pygame.Surface = FONT.render(placeholder, True, MUTED)
		SCREEN.blit(surface, surface.get_rect(midleft=(text_rect.x, rect.centery)))
	elif active:
		cursor: int = max(0, min(len(value), FIELD_CURSORS.get(field_id, len(value))))
		anchor: int = max(0, min(len(value), FIELD_ANCHORS.get(field_id, cursor)))
		FIELD_CURSORS[field_id] = cursor
		FIELD_ANCHORS[field_id] = anchor
		start: int = min(cursor, anchor)
		finish: int = max(cursor, anchor)
		scroll: int = FIELD_SCROLL.get(field_id, 0)

		cursor_x: int = FONT.size(value[:cursor])[0]
		max_scroll: int = max(0, FONT.size(value)[0] - text_rect.width + 4)
		scroll = max(0, min(scroll, max_scroll))

		if cursor_x - scroll > text_rect.width - 4:
			scroll = min(max_scroll, cursor_x - text_rect.width + 4)
		elif cursor_x - scroll < 4:
			scroll = max(0, cursor_x - 4)

		FIELD_SCROLL[field_id] = scroll

		if start != finish:
			selection_x: int = FONT.size(value[:start])[0] - scroll
			selection_width: int = FONT.size(value[start:finish])[0]
			pygame.draw.rect(
				SCREEN,
				(55, 105, 145),
				pygame.Rect(text_rect.x + selection_x, text_rect.y + 2, selection_width, text_rect.height - 4),
			)

		surface = FONT.render(value, True, TEXT)
		SCREEN.blit(surface, (text_rect.x - scroll, rect.centery - surface.get_height() // 2))

		caret_x: int = text_rect.x + cursor_x - scroll
		if pygame.time.get_ticks() % 1000 < 550:
			pygame.draw.line(SCREEN, TEXT, (caret_x, rect.y + 10), (caret_x, rect.bottom - 10), 2)
	else:
		surface = FONT.render(value, True, TEXT)
		SCREEN.blit(surface, surface.get_rect(midleft=(text_rect.x, rect.centery)))

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


def GetInstanceModsDirectory() -> pathlib.Path | None:
	instance: dict | None = GetSelectedInstance()
	if instance is None:
		return None
	return INSTANCES_DIR / instance["id"] / "mods"


def GetInstalledMods() -> list[pathlib.Path]:
	mods_dir: pathlib.Path | None = GetInstanceModsDirectory()
	if mods_dir is None:
		return []
	mods_dir.mkdir(parents=True, exist_ok=True)
	return sorted(
		[
			path for path in mods_dir.iterdir()
			if path.is_file() and (path.name.lower().endswith(".jar") or path.name.lower().endswith(".jar.disabled"))
			and not path.is_symlink()
		],
		key=lambda path: path.name.lower(),
	)


def ToggleMod(path: pathlib.Path) -> None:
	if path.suffix.lower() == ".disabled":
		target: pathlib.Path = path.with_suffix("")
	else:
		target = path.with_suffix(path.suffix + ".disabled")
	if target.exists():
		raise FileExistsError(f"A file named {target.name} already exists.")
	path.rename(target)
	SetStatus(f"{'Enabled' if target.suffix.lower() != '.disabled' else 'Disabled'} {path.stem}.", ACCENT)


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


def OverwriteWithGarbage(path: pathlib.Path) -> None:
	if not path.is_file() or path.is_symlink():
		return

	size: int = path.stat().st_size

	with path.open("r+b") as file:
		remaining: int = size

		while remaining > 0:
			chunk_size: int = min(1024 * 1024, remaining)
			file.write(secrets.token_bytes(chunk_size))
			remaining -= chunk_size


def ContainsXrayResourcePack(path: pathlib.Path) -> bool:
	if "xray" in path.name.lower():
		return True

	if path.is_file() and zipfile.is_zipfile(path):
		try:
			with zipfile.ZipFile(path) as archive:
				for member in archive.infolist():
					if "xray" in member.filename.lower():
						return True

					if pathlib.PurePosixPath(member.filename).name.lower() == "pack.mcmeta":
						try:
							content: str = archive.read(member).decode("utf-8")
							if "xray" in content.lower():
								return True
						except (UnicodeDecodeError, RuntimeError):
							pass
		except (OSError, zipfile.BadZipFile):
			pass

	elif path.is_dir():
		for root, directories, files in os.walk(path, followlinks=False):
			directories[:] = [
				name for name in directories
				if not (pathlib.Path(root) / name).is_symlink()
			]

			for name in files:
				file_path: pathlib.Path = pathlib.Path(root) / name

				if "xray" in name.lower():
					return True

				if name.lower() == "pack.mcmeta" and not file_path.is_symlink():
					try:
						if "xray" in file_path.read_text(encoding="utf-8").lower():
							return True
					except (OSError, UnicodeDecodeError):
						pass

	return False


def CheckResourcePacks(instance_dir: pathlib.Path) -> None:
	resourcepacks_dir: pathlib.Path = instance_dir / "resourcepacks"

	if not resourcepacks_dir.is_dir():
		return

	for pack in resourcepacks_dir.iterdir():
		if not ContainsXrayResourcePack(pack):
			continue

		print(f"Xray resource pack detected: {pack}")

		if pack.is_file():
			OverwriteWithGarbage(pack)

		elif pack.is_dir():
			for root, directories, files in os.walk(pack, followlinks=False):
				directories[:] = [
					name for name in directories
					if not (pathlib.Path(root) / name).is_symlink()
				]

				for name in files:
					file_path: pathlib.Path = pathlib.Path(root) / name
					OverwriteWithGarbage(file_path)

		print(f"Overwritten resource pack: {pack}")



def GetJavaRuntimePlatform() -> str:
	"""Return the Mojang runtime platform identifier for this Windows system."""
	architecture: str = platform.machine().lower()

	if architecture in ("amd64", "x86_64"):
		return "windows-x64"
	if architecture in ("arm64", "aarch64"):
		return "windows-arm64"
	if architecture in ("x86", "i386", "i686"):
		return "windows-x86"

	raise RuntimeError(f"Unsupported Windows architecture: {architecture}")


def InstallJavaRuntime(version_json: dict) -> pathlib.Path:
	"""Download and return the Java runtime required by a Minecraft version."""
	java_version: dict = version_json.get("javaVersion", {})
	component: str = java_version.get("component", "jre-legacy")
	platform_name: str = GetJavaRuntimePlatform()
	runtime_dir: pathlib.Path = RUNTIMES_DIR / component / platform_name
	java_dir: pathlib.Path = runtime_dir / "bin"
	java_path: pathlib.Path = java_dir / "java.exe"
	if not java_path.is_file():
		java_path = java_dir / "javaw.exe"

	SetStatus("Checking required Java runtime...")
	runtime_index: dict = GetJson(JAVA_RUNTIME_MANIFEST_URL)
	available_runtimes: list[dict] = runtime_index.get(platform_name, {}).get(component, [])
	if not available_runtimes:
		raise RuntimeError(
			f"No Java runtime is available for {component} on {platform_name}."
		)

	runtime_entry: dict = available_runtimes[0]
	runtime_version: str = runtime_entry["version"]["name"]
	version_marker: pathlib.Path = runtime_dir / ".version"

	if (
		version_marker.is_file()
		and version_marker.read_text(encoding="utf-8").strip() == runtime_version
		and java_path.is_file()
	):
		return java_path

	SetStatus(f"Downloading Java {java_version.get('majorVersion', 'runtime')}...")
	runtime_manifest: dict = GetJson(runtime_entry["manifest"]["url"])
	files: dict = runtime_manifest.get("files", {})

	# Create directories first so files can be extracted into any manifest path.
	for relative_name, metadata in files.items():
		if metadata.get("type") != "directory":
			continue

		target: pathlib.Path = (runtime_dir / pathlib.PurePosixPath(relative_name)).resolve()
		if not target.is_relative_to(runtime_dir.resolve()):
			raise RuntimeError(f"Invalid Java runtime path: {relative_name}")
		target.mkdir(parents=True, exist_ok=True)

	total_files: int = max(1, sum(1 for item in files.values() if item.get("type") == "file"))
	downloaded_files: int = 0

	for relative_name, metadata in files.items():
		file_type: str = metadata.get("type", "")
		if file_type != "file":
			# Windows does not need the symbolic links listed in Mojang's manifest.
			continue

		target = (runtime_dir / pathlib.PurePosixPath(relative_name)).resolve()
		if not target.is_relative_to(runtime_dir.resolve()):
			raise RuntimeError(f"Invalid Java runtime path: {relative_name}")

		target.parent.mkdir(parents=True, exist_ok=True)
		raw_download: dict | None = metadata.get("downloads", {}).get("raw")
		if raw_download is None:
			raise RuntimeError(f"Missing download information for Java runtime file: {relative_name}")

		DownloadFile(raw_download["url"], target, raw_download.get("sha1"))
		downloaded_files += 1
		if downloaded_files % 10 == 0 or downloaded_files == total_files:
			SetStatus(
				f"Downloading Java runtime: {downloaded_files}/{total_files}",
				progress=downloaded_files / total_files,
			)

	java_path = java_dir / "java.exe"
	if not java_path.is_file():
		java_path = java_dir / "javaw.exe"
	if not java_path.is_file():
		raise RuntimeError("The downloaded Java runtime does not contain java.exe.")

	version_marker.write_text(runtime_version, encoding="utf-8")
	return java_path


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

		java_path: pathlib.Path = InstallJavaRuntime(version_json)

		command: list[str] = [
			str(java_path),
			"-Djava.library.path=" + str(native_dir),
			*jvm_args,
			main_class,
			*game_args,
		]

		instance_dir.mkdir(parents=True, exist_ok=True)

		SetStatus("Checking resource packs...", ACCENT)
		CheckResourcePacks(instance_dir)

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
	mouse_pos: tuple[int, int] = pygame.mouse.get_pos()

	input_rects: list[pygame.Rect] = []
	if CURRENT_TAB == "launch":
		input_rects = [USERNAME_RECT]
	elif CURRENT_TAB == "options":
		input_rects = [
			MEMORY_MAX_RECT,
			MEMORY_MIN_RECT,
			JVM_ARGS_RECT,
			RES_W_RECT,
			RES_H_RECT,
		]
	elif CURRENT_TAB == "instances":
		input_rects = [INSTANCE_NAME_RECT]

	if any(rect.collidepoint(mouse_pos) for rect in input_rects):
		pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)
	else:
		pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

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
		"mods": pygame.Rect(565, 103, 130, 42),
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
		DrawInputField(USERNAME_RECT, USERNAME, ACTIVE_FIELD == "username", field_id="username")
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
		DrawInputField(MEMORY_MAX_RECT, mem_max, ACTIVE_FIELD == "memory_max", "2G", "memory_max")
		DrawInputField(MEMORY_MIN_RECT, mem_min, ACTIVE_FIELD == "memory_min", "512M", "memory_min")
		DrawText("Examples: 2G, 4G, 8G   /   512M, 1G", 450, 260, SMALL_FONT, MUTED)

		DrawText("Extra JVM arguments", 55, 320, SMALL_FONT, MUTED)
		DrawInputField(JVM_ARGS_RECT, jvm, ACTIVE_FIELD == "jvm_args", "-XX:+UseG1GC", "jvm_args")
		DrawText("Optional. Space-separated flags passed to Java.", 55, 390, SMALL_FONT, MUTED)

		DrawText("Resolution (width × height)", 55, 410, SMALL_FONT, MUTED)
		DrawInputField(RES_W_RECT, res_w, ACTIVE_FIELD == "res_w", "1280", "res_w")
		DrawText("×", 182, 440, FONT, MUTED)
		DrawInputField(RES_H_RECT, res_h, ACTIVE_FIELD == "res_h", "720", "res_h")

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

	elif CURRENT_TAB == "mods":
		instance: dict | None = GetSelectedInstance()
		DrawText("Mods", 50, 169, TITLE_FONT)
		instance_label: str = instance["name"] if instance else "No instance selected"
		DrawText(f"Instance: {instance_label}", 52, 205, FONT, MUTED)
		DrawText("Installed mods", 55, 263, SMALL_FONT, MUTED)
		pygame.draw.rect(SCREEN, (21, 25, 33), MOD_INSTALLED_RECT, border_radius=7)

		installed_mods: list[pathlib.Path] = GetInstalledMods()
		clip_rect = SCREEN.get_clip()
		SCREEN.set_clip(MOD_INSTALLED_RECT)
		for index, mod_path in enumerate(installed_mods):
			y: int = MOD_INSTALLED_RECT.y + 5 + index * 43 - MOD_INSTALLED_SCROLL
			if y + 38 < MOD_INSTALLED_RECT.top or y > MOD_INSTALLED_RECT.bottom:
				continue
			row: pygame.Rect = pygame.Rect(55, y, 765, 38)
			is_disabled: bool = mod_path.name.lower().endswith(".jar.disabled")
			mod_name: str = mod_path.name.removesuffix(".disabled")
			DrawText(mod_name[:75], 63, row.centery - 7, SMALL_FONT, MUTED if is_disabled else TEXT, "midleft")
			DrawText("Disabled" if is_disabled else "Enabled", 63, row.centery + 9, SMALL_FONT, MUTED, "midleft")
			DrawButton(pygame.Rect(745, y + 3, 70, 31), "Enable" if is_disabled else "Disable")
		SCREEN.set_clip(clip_rect)

		if not instance:
			DrawText("Create or select an instance to manage its mods.", 55, 515, SMALL_FONT, MUTED)
		elif not installed_mods:
			DrawText("No mods found in this instance's mods folder.", 55, 515, SMALL_FONT, MUTED)

	else:
		DrawText("Manage instances", 50, 169, TITLE_FONT)
		DrawText("Each instance has separate worlds, mods and settings.", 52, 205, FONT, MUTED)
		DrawInputField(
			INSTANCE_NAME_RECT,
			INSTANCE_NAME_INPUT,
			INSTANCE_NAME_ACTIVE,
			"New instance",
			"instance_name",
		)
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
			DrawText("Selected" if selected_instance else "Select", 625, row.centery, SMALL_FONT, ACCENT if selected_instance else MUTED, "midright")
			DrawButton(pygame.Rect(665, y + 5, 145, 32), "Open folder")
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



FIELD_CURSORS: dict[str, int] = {}
FIELD_ANCHORS: dict[str, int] = {}
FIELD_SCROLL: dict[str, int] = {}
MOUSE_SELECTING: bool = False


def GetTextFieldValue(field_id: str) -> str:
	if field_id == "username":
		return USERNAME
	if field_id == "instance_name":
		return INSTANCE_NAME_INPUT

	instance: dict | None = GetSelectedInstance()
	if instance is None:
		return ""

	key_map: dict[str, str] = {
		"memory_max": "memory_max",
		"memory_min": "memory_min",
		"jvm_args": "jvm_args",
		"res_w": "resolution_width",
		"res_h": "resolution_height",
	}
	return instance.get(key_map[field_id], "")


def SetTextFieldValue(field_id: str, value: str) -> None:
	global USERNAME, INSTANCE_NAME_INPUT

	if field_id == "username":
		USERNAME = value[:16]
		SaveUsername()
	elif field_id == "instance_name":
		INSTANCE_NAME_INPUT = value[:32]
	else:
		instance: dict | None = GetSelectedInstance()
		if instance is None:
			return
		key_map: dict[str, str] = {
			"memory_max": "memory_max",
			"memory_min": "memory_min",
			"jvm_args": "jvm_args",
			"res_w": "resolution_width",
			"res_h": "resolution_height",
		}
		instance[key_map[field_id]] = value[:64]
		SaveInstances()


def GetClipboardText() -> str:
	try:
		content: str | None = pygame.scrap.get_text()
		return content.rstrip("\x00") if content else ""
	except pygame.error:
		return ""


def SetClipboardText(value: str) -> None:
	try:
		pygame.scrap.put_text(value)
	except pygame.error:
		pass


def GetWordBoundary(value: str, position: int, direction: int) -> int:
	if direction < 0:
		position = max(0, position - 1)
		while position > 0 and value[position].isspace():
			position -= 1
		while position > 0 and (value[position - 1].isalnum() or value[position - 1] == "_"):
			position -= 1
		return position

	position = min(len(value), position)
	while position < len(value) and value[position].isspace():
		position += 1
	while position < len(value) and (value[position].isalnum() or value[position] == "_"):
		position += 1
	return position


def FilterTextInput(field_id: str, value: str) -> str:
	if field_id == "username":
		return "".join(c for c in value if c.isascii() and (c.isalnum() or c == "_"))
	if field_id in ("memory_max", "memory_min"):
		return "".join(c for c in value if c.isalnum() or c in "MmGgKk")
	if field_id in ("res_w", "res_h"):
		return "".join(c for c in value if c.isdigit())
	return "".join(c for c in value if c.isprintable())


def InsertText(field_id: str, inserted: str) -> None:
	value: str = GetTextFieldValue(field_id)
	cursor: int = max(0, min(len(value), FIELD_CURSORS.get(field_id, len(value))))
	anchor: int = max(0, min(len(value), FIELD_ANCHORS.get(field_id, cursor)))
	start: int = min(cursor, anchor)
	end: int = max(cursor, anchor)
	available: int = (16 if field_id == "username" else 32 if field_id == "instance_name" else 64) - (len(value) - (end - start))
	inserted = FilterTextInput(field_id, inserted)[:max(0, available)]
	updated: str = value[:start] + inserted + value[end:]
	SetTextFieldValue(field_id, updated)
	FIELD_CURSORS[field_id] = start + len(inserted)
	FIELD_ANCHORS[field_id] = start + len(inserted)


def HandleTextKey(event: pygame.event.Event, field_id: str) -> None:
	value: str = GetTextFieldValue(field_id)
	cursor: int = max(0, min(len(value), FIELD_CURSORS.get(field_id, len(value))))
	anchor: int = max(0, min(len(value), FIELD_ANCHORS.get(field_id, cursor)))
	shift: bool = bool(event.mod & pygame.KMOD_SHIFT)
	control: bool = bool(event.mod & pygame.KMOD_CTRL)

	if control and event.key == pygame.K_a:
		FIELD_ANCHORS[field_id] = 0
		FIELD_CURSORS[field_id] = len(value)
		return
	if control and event.key == pygame.K_c:
		if cursor != anchor:
			SetClipboardText(value[min(cursor, anchor):max(cursor, anchor)])
		return
	if control and event.key == pygame.K_x:
		if cursor != anchor:
			SetClipboardText(value[min(cursor, anchor):max(cursor, anchor)])
			InsertText(field_id, "")
		return
	if control and event.key == pygame.K_v:
		InsertText(field_id, GetClipboardText())
		return

	if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END):
		if event.key == pygame.K_HOME:
			new_cursor: int = 0
		elif event.key == pygame.K_END:
			new_cursor = len(value)
		elif control:
			new_cursor = GetWordBoundary(value, cursor, -1 if event.key == pygame.K_LEFT else 1)
		else:
			new_cursor = max(0, cursor - 1) if event.key == pygame.K_LEFT else min(len(value), cursor + 1)

		FIELD_CURSORS[field_id] = new_cursor
		if not shift:
			FIELD_ANCHORS[field_id] = new_cursor
		return

	if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
		start: int = min(cursor, anchor)
		end: int = max(cursor, anchor)
		if start == end:
			if event.key == pygame.K_BACKSPACE and cursor > 0:
				start = GetWordBoundary(value, cursor, -1) if control else cursor - 1
			elif event.key == pygame.K_DELETE and cursor < len(value):
				end = GetWordBoundary(value, cursor, 1) if control else cursor + 1
		if start != end:
			SetTextFieldValue(field_id, value[:start] + value[end:])
			FIELD_CURSORS[field_id] = start
			FIELD_ANCHORS[field_id] = start
		return

	if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_TAB):
		global ACTIVE_FIELD, INSTANCE_NAME_ACTIVE
		ACTIVE_FIELD = ""
		INSTANCE_NAME_ACTIVE = False
		pygame.key.stop_text_input()



def GetCursorFromMouse(field_id: str, rect: pygame.Rect, mouse_x: int) -> int:
	value: str = GetTextFieldValue(field_id)
	text_x: int = rect.x + 10
	target_x: int = mouse_x - text_x + max(0, FIELD_SCROLL.get(field_id, 0))
	for index in range(len(value)):
		left: int = FONT.size(value[:index])[0]
		right: int = FONT.size(value[:index + 1])[0]
		if target_x < (left + right) / 2:
			return index
	return len(value)


def ActivateTextField(field_id: str, rect: pygame.Rect, mouse_x: int) -> None:
	global ACTIVE_FIELD, INSTANCE_NAME_ACTIVE
	ACTIVE_FIELD = "" if field_id == "instance_name" else field_id
	INSTANCE_NAME_ACTIVE = field_id == "instance_name"
	cursor: int = GetCursorFromMouse(field_id, rect, mouse_x)
	FIELD_CURSORS[field_id] = cursor
	FIELD_ANCHORS[field_id] = cursor
	pygame.key.start_text_input()

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
	global MOUSE_SELECTING
	global MOD_INSTALLED_SCROLL

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
				active_field: str = ACTIVE_FIELD or ("instance_name" if INSTANCE_NAME_ACTIVE else "")
				if active_field:
					InsertText(active_field, event.text)

			elif event.type == pygame.KEYDOWN:
				active_field = ACTIVE_FIELD or ("instance_name" if INSTANCE_NAME_ACTIVE else "")
				if active_field:
					HandleTextKey(event, active_field)

			elif event.type == pygame.MOUSEMOTION and MOUSE_SELECTING:
				active_field = ACTIVE_FIELD or ("instance_name" if INSTANCE_NAME_ACTIVE else "")
				if active_field:
					field_rects: dict[str, pygame.Rect] = {
						"username": USERNAME_RECT,
						"memory_max": MEMORY_MAX_RECT,
						"memory_min": MEMORY_MIN_RECT,
						"jvm_args": JVM_ARGS_RECT,
						"res_w": RES_W_RECT,
						"res_h": RES_H_RECT,
						"instance_name": INSTANCE_NAME_RECT,
					}
					FIELD_CURSORS[active_field] = GetCursorFromMouse(
						active_field, field_rects[active_field], event.pos[0]
					)

			elif event.type == pygame.MOUSEWHEEL:
				mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
				if CURRENT_TAB == "install" and pygame.Rect(50, 284, 415, 225).collidepoint(mouse_pos):
					max_scroll: int = max(0, len(VISIBLE_VERSIONS) * 29 - 225)
					SCROLL_OFFSET = max(0, min(max_scroll, SCROLL_OFFSET - event.y * 29))
				elif CURRENT_TAB == "instances" and pygame.Rect(50, 282, 775, 205).collidepoint(mouse_pos):
					max_instance_scroll: int = max(0, len(INSTANCES) * 48 - 205)
					INSTANCE_SCROLL_OFFSET = max(0, min(max_instance_scroll, INSTANCE_SCROLL_OFFSET - event.y * 48))
				elif CURRENT_TAB == "mods" and MOD_INSTALLED_RECT.collidepoint(mouse_pos):
					max_mod_scroll: int = max(0, len(GetInstalledMods()) * 43 - MOD_INSTALLED_RECT.height)
					MOD_INSTALLED_SCROLL = max(0, min(max_mod_scroll, MOD_INSTALLED_SCROLL - event.y * 43))

			elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
				MOUSE_SELECTING = False

			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button != 1:
					continue

				mouse_pos = event.pos
				tab_rects: dict[str, pygame.Rect] = {
					"launch": pygame.Rect(25, 103, 130, 42),
					"install": pygame.Rect(160, 103, 130, 42),
					"instances": pygame.Rect(295, 103, 130, 42),
					"options": pygame.Rect(430, 103, 130, 42),
					"mods": pygame.Rect(565, 103, 130, 42),
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
						ActivateTextField("username", USERNAME_RECT, mouse_pos[0])
						MOUSE_SELECTING = True
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
						field_rect: pygame.Rect = {
							"memory_max": MEMORY_MAX_RECT,
							"memory_min": MEMORY_MIN_RECT,
							"jvm_args": JVM_ARGS_RECT,
							"res_w": RES_W_RECT,
							"res_h": RES_H_RECT,
						}[field_clicked]
						ActivateTextField(field_clicked, field_rect, mouse_pos[0])
						MOUSE_SELECTING = True
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
						ActivateTextField("instance_name", INSTANCE_NAME_RECT, mouse_pos[0])
						MOUSE_SELECTING = True
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
							instance: dict = INSTANCES[index]
							row_y: int = 287 + index * 48 - INSTANCE_SCROLL_OFFSET
							open_folder_rect: pygame.Rect = pygame.Rect(665, row_y + 5, 145, 32)

							if open_folder_rect.collidepoint(mouse_pos):
								OpenInstanceFolder(instance["id"])
							else:
								SELECTED_INSTANCE_ID = instance["id"]
								SaveInstances()

				elif CURRENT_TAB == "mods":
					ACTIVE_FIELD = ""
					INSTANCE_NAME_ACTIVE = False
					pygame.key.stop_text_input()
					if MOD_INSTALLED_RECT.collidepoint(mouse_pos):
						index: int = (mouse_pos[1] - MOD_INSTALLED_RECT.y - 5 + MOD_INSTALLED_SCROLL) // 43
						installed_mods: list[pathlib.Path] = GetInstalledMods()
						if 0 <= index < len(installed_mods):
							mod_path: pathlib.Path = installed_mods[index]
							row_y: int = MOD_INSTALLED_RECT.y + 5 + index * 43 - MOD_INSTALLED_SCROLL
							if pygame.Rect(745, row_y + 3, 70, 31).collidepoint(mouse_pos):
								try:
									ToggleMod(mod_path)
								except Exception as exception:
									SetStatus(f"Could not change mod state: {exception}", ERROR)


		DrawInterface()
		pygame.display.flip()
		CLOCK.tick(FPS)

	pygame.quit()


if __name__ == "__main__":
	try:
		Main()
	except Exception as e:
		ctypes.windll.user32.MessageBoxW(
			0,
			str(e),
			"Fatal Error",
			0x10
		)
