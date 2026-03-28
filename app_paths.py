import os
import shutil
import sys
import tempfile
from pathlib import Path


APP_DATA_DIRNAME = "DBX-V3 Desktop"


def _resource_roots():
    seen = set()
    meipass = getattr(sys, "_MEIPASS", None)
    candidates = [Path(meipass)] if meipass else []
    candidates.append(Path(__file__).resolve().parent)

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        yield resolved


def find_resource_path(*relative_parts):
    for root in _resource_roots():
        candidate = root.joinpath(*relative_parts)
        if candidate.exists():
            return candidate
    return None


def get_resource_path(*relative_parts):
    existing_path = find_resource_path(*relative_parts)
    if existing_path is not None:
        return str(existing_path)
    return str(next(_resource_roots()).joinpath(*relative_parts))


def get_app_data_dir():
    candidates = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    roaming_app_data = os.environ.get("APPDATA")
    user_profile = os.environ.get("USERPROFILE")

    if local_app_data:
        candidates.append(Path(local_app_data) / APP_DATA_DIRNAME)
    if roaming_app_data:
        candidates.append(Path(roaming_app_data) / APP_DATA_DIRNAME)
    if user_profile:
        candidates.append(Path(user_profile) / "AppData" / "Local" / APP_DATA_DIRNAME)
        candidates.append(Path(user_profile) / "AppData" / "Roaming" / APP_DATA_DIRNAME)

    candidates.append(Path.home() / ".dbx-v3-desktop")
    candidates.append(Path(tempfile.gettempdir()) / "dbx-v3-desktop")

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            continue

    raise OSError("Nao foi possivel preparar um diretorio de dados gravavel para a aplicacao.")


def get_log_file_path(filename="debug_nesting.log"):
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return str(logs_dir / filename)


def ensure_user_file(filename, source_relative_path=None, default_text=None):
    target_path = get_app_data_dir() / filename
    if target_path.exists():
        return str(target_path)

    target_path.parent.mkdir(parents=True, exist_ok=True)

    source_parts = source_relative_path or (filename,)
    if isinstance(source_parts, str):
        source_parts = (source_parts,)

    source_path = find_resource_path(*source_parts)
    if source_path is not None:
        shutil.copy2(source_path, target_path)
        return str(target_path)

    if default_text is not None:
        target_path.write_text(default_text, encoding="utf-8")

    return str(target_path)
