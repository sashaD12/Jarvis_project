import json
import os
import re
import subprocess
import time
from typing import Any

from config_loader import BASE_DIR

CACHE_FILE = os.path.join(BASE_DIR, "programs_cache.json")
CACHE_TTL_SEC = 60 * 60 * 6
MIN_ACCEPT_SCORE = 78.0
MIN_TOKEN_LEN = 3
MAX_EXE_WALK_DEPTH = 4

UK_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ye",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi", "й": "y", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ю": "yu",
    "я": "ya", "ь": "", "ъ": "", "ы": "y", "э": "e",
}

SPOKEN_ALIASES = {
    "епік": "epic",
    "епікгеймс": "epic games",
    "епік геймс": "epic games",
    "епик": "epic",
    "геймс": "games",
    "столзон": "stalcraft",
    "сталзон": "stalcraft",
    "стол зон": "stalcraft",
    "стал зон": "stalcraft",
    "сталкрафт": "stalcraft",
    "stalcraft": "stalcraft",
    "хром": "chrome",
    "едж": "edge",
    "діскорд": "discord",
    "стім": "steam",
    "телеграм": "telegram",
    "ватсап": "whatsapp",
    "ворд": "word",
    "ексель": "excel",
    "спотіфай": "spotify",
    "танки": "танки",
    "танкі": "танки",
    "wot": "world of tanks",
    "вот": "world of tanks",
    "world of tanks": "world of tanks",
}

JUNK_TOKENS = {
    "й", "і", "та", "a", "the", "app", "apps", "запусти", "відкрий", "програму", "программу",
}

SKIP_DIR_NAMES = {
    "windows", "winsxs", "system32", "syswow64", "$recycle.bin", "node_modules",
    "microsoft", "windowsapps", "temp", "tmp", "cache", "caches",
}

BLOCKED_QUERY_TOKENS = {
    "удалить",
    "удали",
    "удалення",
    "удаления",
    "видалити",
    "видали",
    "видалення",
    "delete",
    "uninstall",
    "uninstaller",
    "remove",
    "очистить",
    "очисти",
    "очистити",
    "деінстал",
    "деинстал",
}

BLOCKED_APP_NAME_RE = re.compile(
    r"(^|\b)(uninstall|uninstaller|remove\s+program|delete|удалить|видалити|очистить)(\b|$)",
    flags=re.IGNORECASE,
)

BLOCKED_PATH_RE = re.compile(
    r"(uninstall|unins\d*|uninst|remove\s*device)",
    flags=re.IGNORECASE,
)


def is_blocked_query(query: str) -> bool:
    text = _normalize(query)
    if not text:
        return True
    tokens = set(text.split())
    if tokens & BLOCKED_QUERY_TOKENS:
        return True
    compact = _compact(text)
    return any(token in compact for token in ("uninstall", "удалить", "видалити", "delete"))


def is_blocked_app(app: dict[str, str] | None = None, name: str = "", path: str = "") -> bool:
    app_name = name or (str(app.get("name") or "") if app else "")
    app_path = path or (str(app.get("path") or "") if app else "")
    if app_name and BLOCKED_APP_NAME_RE.search(app_name):
        return True
    lower_name = app_name.lower().strip()
    if lower_name in {"uninstall", "uninstaller", "remove", "delete"}:
        return True
    if app_path and BLOCKED_PATH_RE.search(app_path):
        base = os.path.basename(app_path).lower()
        if base.endswith(".exe") and (
            base.startswith("unins")
            or "uninstall" in base
            or base in {"uninstall.exe", "uninst.exe"}
        ):
            return True
        if "uninstall" in app_path.lower() and app_path.lower().endswith((".lnk", ".url")):
            return True
    return False


def filter_launchable_apps(apps: list[dict[str, str]]) -> list[dict[str, str]]:
    return [app for app in apps if not is_blocked_app(app)]


def _to_latin(text: str) -> str:
    return "".join(UK_TO_LAT.get(ch, ch) for ch in text.lower())


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ё", "е")
    text = re.sub(r"[^\w\sа-яіїєґ]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", _normalize(text))


def clean_program_query(query: str) -> str:
    text = _normalize(query)
    tokens = []
    for token in text.split():
        if token in JUNK_TOKENS:
            continue
        if len(token) < 2:
            continue
        tokens.append(token)
    cleaned = " ".join(tokens).strip()
    if cleaned in SPOKEN_ALIASES:
        return SPOKEN_ALIASES[cleaned]
    mapped = [SPOKEN_ALIASES.get(t, t) for t in cleaned.split()]
    return " ".join(mapped).strip()


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _start_menu_dirs() -> list[str]:
    dirs: list[str] = []
    appdata = os.environ.get("APPDATA", "")
    programdata = os.environ.get("PROGRAMDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")
    public = os.environ.get("PUBLIC", "")
    for base in (
        os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(programdata, "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(userprofile, "Desktop"),
        os.path.join(public, "Desktop") if public else "",
    ):
        if base and os.path.isdir(base):
            dirs.append(base)
    return dirs


def _disk_search_roots() -> list[str]:
    roots: list[str] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = os.environ.get(key, "")
        if key == "LOCALAPPDATA" and value:
            value = os.path.join(value, "Programs")
        if value and os.path.isdir(value):
            roots.append(value)

    userprofile = os.environ.get("USERPROFILE", "")
    extras = [
        r"C:\Program Files\Epic Games",
        r"C:\Program Files (x86)\Epic Games",
        r"C:\Program Files\Steam",
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files (x86)\Steam\steamapps\common",
        r"C:\Program Files\Steam\steamapps\common",
        r"D:\SteamLibrary",
        r"D:\SteamLibrary\steamapps\common",
        r"D:\Games",
        r"E:\Games",
        os.path.join(userprofile, "Games") if userprofile else "",
    ]
    for path in extras:
        if path and os.path.isdir(path) and path not in roots:
            roots.append(path)
    return roots


def _scan_shortcuts() -> list[dict[str, str]]:
    apps: list[dict[str, str]] = []
    seen: set[str] = set()
    for root_dir in _start_menu_dirs():
        for root, _dirs, files in os.walk(root_dir):
            for name in files:
                lower = name.lower()
                if not (lower.endswith(".lnk") or lower.endswith(".url")):
                    continue
                title = os.path.splitext(name)[0]
                path = os.path.join(root, name)
                if is_blocked_app(name=title, path=path):
                    continue
                key = path.lower()
                if key in seen:
                    continue
                seen.add(key)
                apps.append({"name": title, "path": path, "source": "shortcut"})
    return apps


def _scan_start_apps() -> list[dict[str, str]]:
    apps: list[dict[str, str]] = []
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return apps
        data = json.loads(completed.stdout)
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return apps
        for item in data:
            name = str(item.get("Name") or "").strip()
            app_id = str(item.get("AppID") or "").strip()
            if name and app_id:
                if is_blocked_app(name=name, path=app_id):
                    continue
                apps.append({"name": name, "path": app_id, "source": "startapps"})
    except Exception:
        return apps
    return apps


def _scan_registry_uninstall() -> list[dict[str, str]]:
    apps: list[dict[str, str]] = []
    try:
        import winreg
    except ImportError:
        return apps

    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in roots:
        try:
            with winreg.OpenKey(hive, path) as root:
                for i in range(0, winreg.QueryInfoKey(root)[0]):
                    try:
                        sub_name = winreg.EnumKey(root, i)
                        with winreg.OpenKey(root, sub_name) as sub:
                            def _get(name: str) -> str:
                                try:
                                    value, _ = winreg.QueryValueEx(sub, name)
                                    return str(value).strip()
                                except OSError:
                                    return ""

                            display = _get("DisplayName")
                            location = _get("InstallLocation")
                            display_icon = _get("DisplayIcon")
                            if not display:
                                continue
                            target = ""
                            if location and os.path.isdir(location):
                                target = location
                            elif display_icon:
                                icon_path = display_icon.split(",")[0].strip().strip('"')
                                if icon_path.lower().endswith(".exe") and os.path.isfile(icon_path):
                                    target = icon_path
                            if target:
                                apps.append({"name": display, "path": target, "source": "registry"})
                    except OSError:
                        continue
        except OSError:
            continue
    return apps


def _scan_epic_games() -> list[dict[str, str]]:
    apps: list[dict[str, str]] = []
    manifest_dirs = [
        os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Epic", "EpicGamesLauncher", "Data", "Manifests"),
    ]
    launcher_candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Epic Games", "Launcher", "Portal", "Binaries", "Win32", "EpicGamesLauncher.exe"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Epic Games", "Launcher", "Portal", "Binaries", "Win64", "EpicGamesLauncher.exe"),
    ]
    for launcher in launcher_candidates:
        if os.path.isfile(launcher):
            apps.append({"name": "Epic Games Launcher", "path": launcher, "source": "epic"})
            apps.append({"name": "Epic Games", "path": launcher, "source": "epic"})
            break

    for manifest_dir in manifest_dirs:
        if not os.path.isdir(manifest_dir):
            continue
        for name in os.listdir(manifest_dir):
            if not name.lower().endswith(".item"):
                continue
            path = os.path.join(manifest_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            if data.get("bIsIncompleteInstall"):
                continue
            display = str(data.get("DisplayName") or "").strip()
            install_location = str(data.get("InstallLocation") or "").strip()
            launch_exe = str(data.get("LaunchExecutable") or "").strip().replace("/", "\\")
            app_name = str(data.get("AppName") or "").strip()
            if not display or not install_location or not launch_exe:
                continue
            full_path = os.path.normpath(os.path.join(install_location, launch_exe))
            if not os.path.isfile(full_path):
                continue

            aliases = {display}
            folder = os.path.basename(install_location.rstrip("\\/"))
            if folder:
                aliases.add(folder)
            if app_name:
                aliases.add(app_name)
            lower_display = display.lower()
            if "civilization" in lower_display:
                aliases.update({"Civilization", "Civilization VI", "цива", "циву", "цивілізація"})
            if "epic" in lower_display and "launcher" in lower_display:
                aliases.update({"Epic Games", "Epic Games Launcher", "епік", "епік геймс"})

            for alias in aliases:
                alias = str(alias).strip()
                if alias:
                    apps.append({"name": alias, "path": full_path, "source": "epic"})

    epic_root = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Epic Games")
    if os.path.isdir(epic_root):
        for entry in os.listdir(epic_root):
            if entry.lower() in {"launcher", "directxredist"}:
                continue
            game_dir = os.path.join(epic_root, entry)
            if not os.path.isdir(game_dir):
                continue
            already = any(
                a["source"] == "epic" and a["path"].lower().startswith(game_dir.lower())
                for a in apps
            )
            if already:
                continue
            picked = _pick_best_exe_in_dir(game_dir, entry)
            if picked:
                apps.append({"name": entry, "path": picked["path"], "source": "epic"})
                apps.append({"name": picked["name"], "path": picked["path"], "source": "epic"})
    return apps


def build_app_index() -> list[dict[str, str]]:
    apps: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for scanner in (_scan_shortcuts, _scan_start_apps, _scan_registry_uninstall, _scan_epic_games):
        for app in scanner():
            if is_blocked_app(app):
                continue
            key = f"{app['name'].lower()}::{app['path']}".lower()
            if key in seen_paths:
                continue
            seen_paths.add(key)
            apps.append(app)
    return apps


def _save_cache(apps: list[dict[str, str]]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"created_at": time.time(), "apps": apps}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_app_index(force_refresh: bool = False) -> list[dict[str, str]]:
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if (
                isinstance(cached, dict)
                and isinstance(cached.get("apps"), list)
                and time.time() - float(cached.get("created_at", 0)) < CACHE_TTL_SEC
            ):
                return filter_launchable_apps(cached["apps"])
        except Exception:
            pass

    apps = build_app_index()
    _save_cache(apps)
    return apps


def _meaningful_tokens(query: str) -> list[str]:
    tokens: list[str] = []
    for token in _normalize(query).split():
        if token in JUNK_TOKENS:
            continue
        mapped = SPOKEN_ALIASES.get(token, token)
        latin = _compact(_to_latin(mapped))
        if len(latin) < MIN_TOKEN_LEN:
            continue
        tokens.append(latin)
    return tokens


def _query_variants(query: str) -> list[str]:
    q = clean_program_query(query)
    variants = {q, _to_latin(q), _compact(q), _compact(_to_latin(q))}
    if q in SPOKEN_ALIASES:
        alias = SPOKEN_ALIASES[q]
        variants.update({alias, _compact(alias)})
    tokens = q.split()
    if tokens:
        mapped_tokens = [SPOKEN_ALIASES.get(t, _to_latin(t)) for t in tokens]
        variants.add(" ".join(mapped_tokens))
        variants.add("".join(mapped_tokens))
        variants.add(_compact("".join(mapped_tokens)))
    return [v for v in variants if v]


def score_app(query: str, app_name: str) -> tuple[float, float]:
    cleaned = clean_program_query(query)
    if not cleaned:
        return 0.0, 0.0

    from slang_parser import acronym_score

    best = acronym_score(cleaned, app_name)
    coverage = 1.0 if best >= 88.0 else 0.0

    variants = _query_variants(cleaned)
    name = _normalize(app_name)
    name_compact = _compact(name)
    name_lat_compact = _compact(_to_latin(name))
    name_chunks = re.findall(r"[a-z0-9]{3,}", name_lat_compact)

    for variant in variants:
        v_compact = _compact(variant)
        if len(v_compact) < MIN_TOKEN_LEN:
            continue
        if v_compact == name_compact or v_compact == name_lat_compact:
            best = max(best, 100.0)
            continue
        if v_compact in name_lat_compact or v_compact in name_compact:
            ratio = len(v_compact) / max(len(name_lat_compact), 1)
            best = max(best, 85.0 + 12.0 * ratio)
            continue

        dist = _levenshtein(v_compact, name_lat_compact)
        if dist <= 2 and len(v_compact) >= 5:
            best = max(best, 82.0 - 8.0 * dist)

    tokens = _meaningful_tokens(cleaned)
    token_hits = 0.0
    if tokens:
        for token in tokens:
            hit = False
            if token in name_lat_compact:
                hit = True
            else:
                for chunk in name_chunks:
                    if _levenshtein(token, chunk) <= 1:
                        hit = True
                        break
            if hit:
                token_hits += 1.0
        token_coverage = token_hits / len(tokens)
        coverage = max(coverage, token_coverage)
        if token_coverage >= 0.67:
            best = max(best, 70.0 + 28.0 * token_coverage)
        if token_coverage >= 1.0:
            best = max(best, 98.0)

    return best, coverage


def _pick_best_exe_in_dir(folder: str, query: str) -> dict[str, str] | None:
    best: tuple[float, float, str, str] | None = None
    folder_name = os.path.basename(folder.rstrip("\\/"))
    for root, dirs, files in os.walk(folder):
        depth = root[len(folder):].count(os.sep)
        if depth > MAX_EXE_WALK_DEPTH:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIR_NAMES]
        for name in files:
            lower = name.lower()
            if not lower.endswith(".exe"):
                continue
            if lower.startswith("unins") or lower in {
                "unitycrashhandler64.exe",
                "vcredist.exe",
                "installchainer.exe",
                "epiconlineServices.exe",
                "eosbootstrapper.exe",
                "crashreportclient.exe",
                "ue4prereqsetup_x64.exe",
            }:
                continue
            if "redist" in lower or "prereq" in lower or "crash" in lower:
                continue
            path = os.path.join(root, name)
            title = os.path.splitext(name)[0]
            score_name, cov_name = score_app(query, title)
            score_folder, cov_folder = score_app(query, folder_name)
            score = max(score_name, score_folder * 0.95)
            coverage = max(cov_name, cov_folder)
            if score < 70.0:
                continue
            if "launcher" in title.lower():
                score += 5.0
            if title.lower().endswith("_launcher") or title.lower().endswith("launcher"):
                score += 3.0
            if best is None or score > best[0] or (score == best[0] and coverage > best[1]):
                best = (score, coverage, title, path)
    if best is None:
        return None
    return {
        "name": best[2],
        "path": best[3],
        "source": "disk",
        "score": best[0],
        "coverage": best[1],
    }


def live_search_on_disk(query: str) -> list[dict[str, Any]]:
    cleaned = clean_program_query(query)
    if not cleaned:
        return []

    variants = [_compact(v) for v in _query_variants(cleaned) if len(_compact(v)) >= 4]
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for root in _disk_search_roots():
        try:
            entries = list(os.scandir(root))
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir():
                continue
            if entry.name.lower() in SKIP_DIR_NAMES:
                continue
            folder_compact = _compact(entry.name)
            folder_score, folder_cov = score_app(cleaned, entry.name)
            interesting = folder_score >= 70.0 or any(v in folder_compact for v in variants)
            if not interesting:
                continue
            picked = _pick_best_exe_in_dir(entry.path, cleaned)
            if picked is None:
                continue
            key = picked["path"].lower()
            if key in seen:
                continue
            seen.add(key)
            if folder_score > float(picked.get("score", 0)):
                picked["score"] = folder_score
                picked["coverage"] = folder_cov
                picked["name"] = entry.name
            found.append(picked)

    found.sort(key=lambda item: (-float(item["score"]), -float(item.get("coverage", 0)), len(item["name"])))
    return found[:8]


def find_best_apps(
    query: str,
    limit: int = 5,
    apps: list[dict[str, str]] | None = None,
) -> list[tuple[float, float, dict[str, str]]]:
    if is_blocked_query(query):
        return []
    index = apps if apps is not None else load_app_index()
    scored: list[tuple[float, float, dict[str, str]]] = []
    for app in index:
        if is_blocked_app(app):
            continue
        score, coverage = score_app(query, app["name"])
        if score >= MIN_ACCEPT_SCORE:
            scored.append((score, coverage, app))
    scored.sort(key=lambda item: (-item[0], -item[1], len(item[2]["name"])))
    return scored[:limit]


def launch_target(target: str, source: str = "path") -> None:
    if os.path.isdir(target):
        picked = None
        for name in os.listdir(target):
            if name.lower().endswith(".exe") and not name.lower().startswith("unins"):
                picked = os.path.join(target, name)
                break
        if picked:
            target = picked
        else:
            os.startfile(target)
            return

    if source == "startapps" and not os.path.exists(target):
        subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{target}"], shell=False)
        return
    try:
        os.startfile(target)
    except OSError:
        subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)


def resolve_program(program_name: str, whitelist: dict[str, str] | None = None) -> dict[str, Any] | None:
    name = clean_program_query(program_name)
    if not name:
        return None
    if is_blocked_query(name) or is_blocked_query(program_name):
        print(f"Blocked system/destructive program query: {program_name}")
        return None

    if whitelist:
        if name in whitelist:
            return {"name": name, "path": whitelist[name], "source": "whitelist", "score": 100.0}
        for key, value in whitelist.items():
            if key in name or name in key:
                return {"name": key, "path": value, "source": "whitelist", "score": 95.0}

    index = load_app_index()
    matches = find_best_apps(name, limit=5, apps=index)

    try:
        from slang_parser import best_acronym_matches

        for score, app in best_acronym_matches(name, index, min_score=88.0)[:5]:
            matches.append((score, 1.0, app))
    except Exception as e:
        print(f"Acronym parse failed: {e}")

    if not matches:
        index = load_app_index(force_refresh=True)
        matches = find_best_apps(name, limit=5, apps=index)
        try:
            from slang_parser import best_acronym_matches

            for score, app in best_acronym_matches(name, index, min_score=88.0)[:5]:
                matches.append((score, 1.0, app))
        except Exception:
            pass

    disk_hits = live_search_on_disk(name)
    for hit in disk_hits:
        score = float(hit["score"])
        coverage = float(hit.get("coverage", 0.0))
        if score >= MIN_ACCEPT_SCORE:
            matches.append(
                (
                    score,
                    coverage,
                    {"name": str(hit["name"]), "path": str(hit["path"]), "source": "disk"},
                )
            )

    try:
        from neural_parser import neural_rank_programs

        for ranked in neural_rank_programs(name, apps=index, limit=5):
            path = str(ranked.get("path") or "")
            app_name = str(ranked.get("name") or "")
            if not path or not app_name:
                continue
            if is_blocked_app(name=app_name, path=path):
                continue
            neural_score = float(ranked.get("score") or 0.0)
            matches.append(
                (
                    max(neural_score, 80.0),
                    float(ranked.get("similarity") or 0.0),
                    {
                        "name": app_name,
                        "path": path,
                        "source": str(ranked.get("source") or "neural"),
                    },
                )
            )
    except Exception as e:
        print(f"Neural program rank failed: {e}")

    if not matches:
        try:
            from name_resolver import resolve_informal_names

            print(f"Resolving informal name online: {name}")
            for candidate in resolve_informal_names(name, limit=6):
                web_matches = find_best_apps(candidate, limit=5, apps=index)
                for score, coverage, app in web_matches:
                    matches.append((max(score, 90.0), coverage, app))
                try:
                    from slang_parser import best_acronym_matches

                    for score, app in best_acronym_matches(candidate, index, min_score=88.0)[:3]:
                        matches.append((max(score, 93.0), 1.0, app))
                except Exception:
                    pass
                for hit in live_search_on_disk(candidate):
                    score = float(hit["score"])
                    coverage = float(hit.get("coverage", 0.0))
                    if score >= 70.0:
                        matches.append(
                            (
                                max(score, 92.0),
                                coverage,
                                {
                                    "name": str(hit["name"]),
                                    "path": str(hit["path"]),
                                    "source": "disk+web",
                                },
                            )
                        )
                exact = [
                    app
                    for app in index
                    if candidate.lower() in app["name"].lower()
                    or app["name"].lower() in candidate.lower()
                ]
                for app in exact:
                    matches.append((96.0, 1.0, app))
        except Exception as e:
            print(f"Online name resolve failed: {e}")

    if not matches:
        return None

    matches = [item for item in matches if not is_blocked_app(item[2])]
    if not matches:
        return None

    matches.sort(
        key=lambda item: (
            -item[0],
            -item[1],
            0 if item[2].get("source") == "epic" else 1,
            len(item[2]["name"]),
        )
    )
    score, coverage, app = matches[0]
    if len(matches) > 1:
        second_score = matches[1][0]
        if score - second_score < 4.0 and coverage < matches[1][1]:
            score, coverage, app = matches[1]

    if score < MIN_ACCEPT_SCORE and app.get("source") not in {"disk+web"}:
        return None

    return {
        "name": app["name"],
        "path": app["path"],
        "source": app["source"],
        "score": score,
        "coverage": coverage,
        "query": name,
        "candidates": [{"name": a["name"], "score": s, "coverage": c} for s, c, a in matches[:5]],
    }
