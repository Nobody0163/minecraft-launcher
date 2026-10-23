# THIS WAS WRITTEN BY CHATGPT, THIS IS PURE AI SLOP

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

import pygame
import requests


BASE_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent
VERSIONS_DIR: pathlib.Path = BASE_DIR / "versions"
ASSETS_DIR: pathlib.Path = BASE_DIR / "assets"
LIBRARIES_DIR: pathlib.Path = BASE_DIR / "libraries"
NATIVES_DIR: pathlib.Path = BASE_DIR / "natives"
CURRENT_VERSION_FILE: pathlib.Path = BASE_DIR / "current_version.txt"
USERNAME_FILE: pathlib.Path = BASE_DIR / "username.txt"
SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
UPDATE_FILE: pathlib.Path = SCRIPT_PATH.with_suffix(SCRIPT_PATH.suffix + ".new")

GITHUB_OWNER: str = "Nobody0163"
GITHUB_REPOSITORY: str = "minecraft-launcher"
LAUNCHER_VERSION: str = "1.0.0"
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

BACKGROUND: tuple[int, int, int] = (28, 30, 36)
PANEL: tuple[int, int, int] = (40, 43, 51)
BUTTON: tuple[int, int, int] = (65, 72, 88)
BUTTON_HOVER: tuple[int, int, int] = (85, 96, 120)
TEXT: tuple[int, int, int] = (235, 237, 242)
MUTED: tuple[int, int, int] = (160, 165, 178)
ACCENT: tuple[int, int, int] = (85, 170, 105)
ERROR: tuple[int, int, int] = (220, 85, 85)

pygame.init()

SCREEN: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minecraft Launcher")

CLOCK: pygame.time.Clock = pygame.time.Clock()
FONT: pygame.font.Font = pygame.font.Font(None, 25)
SMALL_FONT: pygame.font.Font = pygame.font.Font(None, 20)
TITLE_FONT: pygame.font.Font = pygame.font.Font(None, 42)

MANIFEST: dict = {}
VERSIONS: list[dict] = []
VISIBLE_VERSIONS: list[dict] = []
SELECTED_VERSION: str = ""
USERNAME: str = "Player"
USERNAME_ACTIVE: bool = False
USERNAME_SELECT_ALL: bool = False
USERNAME_RECT: pygame.Rect = pygame.Rect(465, 220, 380, 36)
VERSION_FILTER: str = "release"

STATUS: str = "Loading Minecraft versions..."
STATUS_COLOR: tuple[int, int, int] = TEXT
PROGRESS: float = 0.0
BUSY: bool = False
SHOULD_QUIT: bool = False



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
) -> None:
	surface: pygame.Surface = font.render(text, True, color)
	SCREEN.blit(surface, (x, y))


def DrawButton(
	rect: pygame.Rect,
	text: str,
	enabled: bool = True,
) -> None:
	mouse_pos: tuple[int, int] = pygame.mouse.get_pos()

	color: tuple[int, int, int] = BUTTON
	if enabled and rect.collidepoint(mouse_pos):
		color = BUTTON_HOVER
	if not enabled:
		color = (48, 50, 57)

	pygame.draw.rect(SCREEN, color, rect, border_radius=6)

	surface: pygame.Surface = FONT.render(
		text,
		True,
		TEXT if enabled else MUTED,
	)

	SCREEN.blit(
		surface,
		surface.get_rect(center=rect.center),
	)


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


def GetJson(url: str) -> dict:
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


def InstallVersion(version: dict) -> None:
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

		CURRENT_VERSION_FILE.write_text(version_id, encoding="utf-8")

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
		if not CURRENT_VERSION_FILE.is_file():
			raise FileNotFoundError("Install a Minecraft version first.")

		version_id: str = CURRENT_VERSION_FILE.read_text(
			encoding="utf-8"
		).strip()

		version_dir: pathlib.Path = VERSIONS_DIR / version_id
		version_json_path: pathlib.Path = version_dir / f"{version_id}.json"
		client_path: pathlib.Path = version_dir / f"{version_id}.jar"

		if not version_json_path.is_file() or not client_path.is_file():
			raise FileNotFoundError(
				f"Minecraft {version_id} is incomplete. Reinstall it first."
			)

		version_json: dict = json.loads(
			version_json_path.read_text(encoding="utf-8")
		)

		client_size: int = client_path.stat().st_size
		if client_size == 0:
			raise RuntimeError("The Minecraft client JAR is empty. Reinstall it.")

		native_dir: pathlib.Path = NATIVES_DIR / version_id
		asset_index_id: str = version_json["assetIndex"]["id"]

		classpath: list[str] = [str(client_path)]

		for library in version_json.get("libraries", []):
			if not IsRuleAllowed(library.get("rules")):
				continue

			artifact: dict | None = (
				library.get("downloads", {}).get("artifact")
			)

			if artifact is None:
				continue

			library_path: pathlib.Path = (
				LIBRARIES_DIR / pathlib.Path(artifact["path"])
			)

			if library_path.is_file():
				classpath.append(str(library_path))

		classpath_argument: str = os.pathsep.join(classpath)

		variables: dict[str, str] = {
			"auth_player_name": USERNAME,
			"version_name": version_id,
			"game_directory": str(BASE_DIR),
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
			"resolution_width": "1280",
			"resolution_height": "720",
		}

		arguments: dict = version_json.get("arguments", {})

		if arguments:
			jvm_args: list[str] = GetArgumentValues(
				arguments.get("jvm", []),
				variables,
			)

			game_args: list[str] = GetArgumentValues(
				arguments.get("game", []),
				variables,
			)

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

			game_args = version_json.get(
				"minecraftArguments",
				"",
			).split()

			game_args = [
				argument.replace("${" + key + "}", value)
				for argument in game_args
				for key, value in variables.items()
			] if False else [
				argument
				for argument in game_args
			]

			resolved_game_args: list[str] = []

			for argument in game_args:
				for key, value in variables.items():
					argument = argument.replace("${" + key + "}", value)

				resolved_game_args.append(argument)

			game_args = resolved_game_args

		command: list[str] = [
			"java",
			"-Djava.library.path=" + str(native_dir),
			*jvm_args,
			version_json["mainClass"],
			*game_args,
		]

		SetStatus(f"Launching Minecraft {version_id}...", ACCENT)

		print("Client JAR:", client_path)
		print("Client size:", client_size)
		print("Main class:", version_json["mainClass"])
		print("Classpath:", classpath_argument)
		print("Command:", command)

		BUSY = True

		subprocess.Popen(
			command,
			cwd=BASE_DIR,
		)

		SetStatus(f"Minecraft {version_id} launched.", ACCENT)

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

	DrawText("Minecraft Launcher", 30, 22, TITLE_FONT)
	DrawText("Java Edition", 32, 66, SMALL_FONT, MUTED)

	pygame.draw.rect(
		SCREEN,
		PANEL,
		pygame.Rect(25, 105, 400, 450),
		border_radius=8,
	)

	DrawText("Select a version", 42, 120)

	filter_rects: dict[str, pygame.Rect] = {
		"release": pygame.Rect(40, 155, 105, 32),
		"snapshot": pygame.Rect(152, 155, 105, 32),
		"old_beta": pygame.Rect(264, 155, 75, 32),
		"all": pygame.Rect(346, 155, 65, 32),
	}

	for name, rect in filter_rects.items():
		label: str = {
			"release": "Releases",
			"snapshot": "Snapshots",
			"old_beta": "Old beta",
			"all": "All",
		}[name]

		color: tuple[int, int, int] = (
			ACCENT if VERSION_FILTER == name else BUTTON
		)

		pygame.draw.rect(SCREEN, color, rect, border_radius=5)

		surface: pygame.Surface = SMALL_FONT.render(label, True, TEXT)
		SCREEN.blit(surface, surface.get_rect(center=rect.center))

	list_rect: pygame.Rect = pygame.Rect(40, 200, 370, 335)
	pygame.draw.rect(SCREEN, BACKGROUND, list_rect, border_radius=5)

	clip_rect: pygame.Rect = SCREEN.get_clip()
	SCREEN.set_clip(list_rect)

	for index, version in enumerate(VISIBLE_VERSIONS):
		y: int = 204 + index * 31 - SCROLL_OFFSET

		if y < 170 or y > 540:
			continue

		row: pygame.Rect = pygame.Rect(43, y, 364, 28)

		if version["id"] == SELECTED_VERSION:
			pygame.draw.rect(SCREEN, ACCENT, row, border_radius=4)

		elif row.collidepoint(pygame.mouse.get_pos()):
			pygame.draw.rect(SCREEN, BUTTON, row, border_radius=4)

		DrawText(version["id"], 52, y + 4, SMALL_FONT)

		DrawText(
			version["type"],
			305,
			y + 4,
			SMALL_FONT,
			TEXT if version["id"] == SELECTED_VERSION else MUTED,
		)

	SCREEN.set_clip(clip_rect)

	pygame.draw.rect(
		SCREEN,
		PANEL,
		pygame.Rect(445, 105, 430, 450),
		border_radius=8,
	)

	DrawText("Installation", 465, 120)

	if SELECTED_VERSION:
		DrawText(f"Selected: {SELECTED_VERSION}", 465, 165)
	else:
		DrawText("Select a version from the list.", 465, 165, color=MUTED)

	DrawText("Username", 465, 195, SMALL_FONT, MUTED)

	pygame.draw.rect(
		SCREEN,
		BUTTON_HOVER if USERNAME_ACTIVE else BACKGROUND,
		USERNAME_RECT,
		border_radius=5,
	)
	pygame.draw.rect(
		SCREEN,
		ACCENT if USERNAME_ACTIVE else BUTTON,
		USERNAME_RECT,
		width=2,
		border_radius=5,
	)

	username_surface: pygame.Surface = FONT.render(USERNAME, True, TEXT)
	username_area: pygame.Rect = username_surface.get_rect(
		midleft=(USERNAME_RECT.x + 10, USERNAME_RECT.centery)
	)
	SCREEN.blit(username_surface, username_area)

	current_version: str = "None installed"

	if CURRENT_VERSION_FILE.is_file():
		current_version = CURRENT_VERSION_FILE.read_text(
			encoding="utf-8"
		).strip()

	DrawText("Current installation:", 465, 270, SMALL_FONT, MUTED)
	DrawText(current_version, 465, 295)

	install_rect: pygame.Rect = pygame.Rect(465, 335, 380, 48)
	launch_rect: pygame.Rect = pygame.Rect(465, 395, 380, 48)

	DrawButton(
		install_rect,
		"Install / Reinstall Selected Version",
		bool(SELECTED_VERSION) and not BUSY,
	)

	DrawButton(
		launch_rect,
		"Launch Current Install",
		not BUSY,
	)

	DrawText("Status", 30, 575, SMALL_FONT, MUTED)
	DrawText(STATUS[:110], 30, 600, SMALL_FONT, STATUS_COLOR)

	progress_rect: pygame.Rect = pygame.Rect(465, 465, 380, 12)
	pygame.draw.rect(SCREEN, BUTTON, progress_rect, border_radius=4)

	if PROGRESS > 0:
		fill_rect: pygame.Rect = progress_rect.copy()
		fill_rect.width = int(fill_rect.width * PROGRESS)

		pygame.draw.rect(SCREEN, ACCENT, fill_rect, border_radius=4)


SCROLL_OFFSET: int = 0


def Main() -> None:
	global SHOULD_QUIT
	global SELECTED_VERSION
	global VERSION_FILTER
	global SCROLL_OFFSET
	global USERNAME
	global USERNAME_ACTIVE
	global USERNAME_SELECT_ALL

	LoadUsername()
	SaveUsername()

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

			elif event.type == pygame.TEXTINPUT and USERNAME_ACTIVE:
				new_characters: str = "".join(
					character
					for character in event.text
					if character.isascii()
					and (character.isalnum() or character == "_")
				)
				if USERNAME_SELECT_ALL:
					USERNAME = new_characters[:16]
				else:
					USERNAME = (USERNAME + new_characters)[:16]

				USERNAME_SELECT_ALL = False
				SaveUsername()

			elif event.type == pygame.KEYDOWN and USERNAME_ACTIVE:
				if event.key == pygame.K_BACKSPACE:
					if USERNAME_SELECT_ALL:
						USERNAME = ""
					else:
						USERNAME = USERNAME[:-1]

					USERNAME_SELECT_ALL = False
					SaveUsername()
				elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
					USERNAME_ACTIVE = False
					pygame.key.stop_text_input()

			elif event.type == pygame.MOUSEWHEEL:
				mouse_pos: tuple[int, int] = pygame.mouse.get_pos()

				if pygame.Rect(40, 200, 370, 335).collidepoint(mouse_pos):
					max_scroll: int = max(
						0,
						len(VISIBLE_VERSIONS) * 31 - 330,
					)

					SCROLL_OFFSET = max(
						0,
						min(max_scroll, SCROLL_OFFSET - event.y * 31),
					)

			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button != 1:
					continue

				mouse_pos = event.pos

				if USERNAME_RECT.collidepoint(mouse_pos):
					USERNAME_ACTIVE = True
					USERNAME_SELECT_ALL = True
					pygame.key.start_text_input()
					continue

				USERNAME_ACTIVE = False
				pygame.key.stop_text_input()

				filter_rects: dict[str, pygame.Rect] = {
					"release": pygame.Rect(40, 155, 105, 32),
					"snapshot": pygame.Rect(152, 155, 105, 32),
					"old_beta": pygame.Rect(264, 155, 75, 32),
					"all": pygame.Rect(346, 155, 65, 32),
				}

				for name, rect in filter_rects.items():
					if rect.collidepoint(mouse_pos):
						VERSION_FILTER = name
						ApplyVersionFilter()
						SCROLL_OFFSET = 0
						break
				else:
					if pygame.Rect(40, 200, 370, 335).collidepoint(mouse_pos):
						index: int = (
							mouse_pos[1] - 204 + SCROLL_OFFSET
						) // 31

						if 0 <= index < len(VISIBLE_VERSIONS):
							SELECTED_VERSION = VISIBLE_VERSIONS[index]["id"]

					elif pygame.Rect(465, 335, 380, 48).collidepoint(mouse_pos):
						if SELECTED_VERSION and not BUSY:
							selected: dict | None = next(
								(
									version
									for version in VERSIONS
									if version["id"] == SELECTED_VERSION
								),
								None,
							)

							if selected is not None:
								StartBackgroundTask(InstallVersion, selected)

					elif pygame.Rect(465, 395, 380, 48).collidepoint(mouse_pos):
						if not BUSY:
							StartBackgroundTask(LaunchCurrentInstall)

		DrawInterface()
		pygame.display.flip()
		CLOCK.tick(FPS)

	pygame.quit()


if __name__ == "__main__":
	Main()
