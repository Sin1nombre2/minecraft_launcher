import os
import sys
import json
import uuid
import shutil
import zipfile
import logging
import platform
import subprocess
import threading
import queue
import re
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
import minecraft_launcher_lib as mcl
from tkinter import filedialog, messagebox


# ============================================================
# Minecraft Launcher - offline launcher
# Includes Vanilla / Forge / Fabric / NeoForge / .mrpack
# ============================================================

APP_NAME = "Minecraft Launcher"
APP_VERSION = "3.0.0"

minecraft_running = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ------------------------- PATHS ----------------------------

def get_launcher_directory():
    home = Path.home()
    if platform.system() == "Windows":
        return home / "AppData" / "Roaming" / ".launchermc"
    if platform.system() == "Darwin":
        return home / "Library" / "Application Support" / ".launchermc"
    return home / ".launchermc"


MINECRAFT_DIR = get_launcher_directory()
VERSIONS_DIR = MINECRAFT_DIR / "versions"
INSTANCES_DIR = MINECRAFT_DIR / "instances"
CONFIG_FILE = MINECRAFT_DIR / "launcher_config.json"
PROFILES_FILE = MINECRAFT_DIR / "profiles.json"
LOG_FILE = MINECRAFT_DIR / "launcher.log"

for directory in (MINECRAFT_DIR, VERSIONS_DIR, INSTANCES_DIR):
    directory.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
logging.info("Launcher iniciado - %s %s", APP_NAME, APP_VERSION)


# ------------------------- CONFIG ---------------------------

DEFAULT_CONFIG = {
    "username": "Player",
    "ram": 4,
    "keep_open": True,
    "java_path": "",
    "last_version": "",
    "theme": "dark",
    "width": 1050,
    "height": 700,
}

DEFAULT_PROFILES = {
    "Player": {
        "username": "Player",
        "uuid": str(uuid.uuid4()),
    }
}


def load_json(path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except Exception as e:
        logging.exception("No se pudo leer %s: %s", path, e)
    return default.copy() if isinstance(default, dict) else default


def save_json(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        temp.replace(path)
    except Exception as e:
        logging.exception("No se pudo guardar %s: %s", path, e)
        raise


config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
profiles = load_json(PROFILES_FILE, DEFAULT_PROFILES)


# ------------------------- HELPERS --------------------------

def safe_name(value):
    value = re.sub(r'[<>:"/\\|?*]', "_", str(value))
    value = value.strip().strip(".")
    return value[:80] or "Instance"


def human_size(size):
    size = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def run_on_ui(callback):
    try:
        app.after(0, callback)
    except Exception:
        pass


def show_error(title, error):
    logging.exception("%s: %s", title, error)
    run_on_ui(lambda: messagebox.showerror(title, str(error)))


def is_safe_child(path, parent):
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


# ------------------------- JAVA -----------------------------

def detect_java():
    """Returns a list of Java executables found on the machine."""
    candidates = []

    configured = str(config.get("java_path", "")).strip()
    if configured:
        p = Path(configured)
        if p.exists():
            candidates.append(str(p))

    # minecraft-launcher-lib
    try:
        if hasattr(mcl, "java_utils"):
            fn = getattr(mcl.java_utils, "find_system_java_versions", None)
            if fn:
                result = fn()
                if isinstance(result, dict):
                    for value in result.values():
                        if isinstance(value, str):
                            candidates.append(value)
                        elif isinstance(value, dict):
                            for key in ("path", "executable", "java_path"):
                                if value.get(key):
                                    candidates.append(str(value[key]))
                elif isinstance(result, list):
                    for item in result:
                        if isinstance(item, str):
                            candidates.append(item)
                        elif isinstance(item, dict):
                            for key in ("path", "executable", "java_path"):
                                if item.get(key):
                                    candidates.append(str(item[key]))
    except Exception as e:
        logging.warning("java_utils no disponible: %s", e)

    if platform.system() == "Windows":
        names = ["java.exe"]
    else:
        names = ["java"]

    for name in names:
        found = shutil.which(name)
        if found:
            candidates.append(found)

    # JAVA_HOME
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_bin = Path(java_home) / "bin" / ("java.exe" if platform.system() == "Windows" else "java")
        if java_bin.exists():
            candidates.append(str(java_bin))

    unique = []
    seen = set()
    for item in candidates:
        try:
            key = str(Path(item).resolve())
        except Exception:
            key = str(item)
        if key not in seen:
            seen.add(key)
            unique.append(str(item))

    return unique


def java_version(java_path):
    try:
        result = subprocess.run(
            [java_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        text = (result.stderr or "") + "\n" + (result.stdout or "")
        match = re.search(r'version "([^"]+)"', text)
        if match:
            return match.group(1)
        return "Desconocida"
    except Exception:
        return "No disponible"


# ------------------------- MOD LOADERS ----------------------

def get_loader(name):
    return mcl.mod_loader.get_mod_loader(name)


def get_loader_versions(name, mc_version):
    loader = get_loader(name)
    if hasattr(loader, "get_loader_versions"):
        return loader.get_loader_versions(mc_version)
    return []


def install_mod_loader(name, mc_version, status):
    loader = get_loader(name)
    status(f"Comprobando {name.title()} para Minecraft {mc_version}...")
    if not loader.is_minecraft_version_supported(mc_version):
        raise RuntimeError(f"{name.title()} no soporta Minecraft {mc_version}.")

    status(f"Obteniendo la versión más reciente de {name.title()}...")
    loader_version = loader.get_latest_loader_version(mc_version)
    status(f"Instalando {name.title()} {loader_version}...")

    
    try:
        mcl.install.install_minecraft_version(mc_version, str(MINECRAFT_DIR))
    except Exception as e:
        logging.warning("Vanilla previa no pudo instalarse o no era necesaria: %s", e)

    installed = loader.install(
        mc_version,
        str(MINECRAFT_DIR),
        loader_version,
        callback={
            "setStatus": status,
            "setProgress": lambda p: None,
            "setMax": lambda m: None,
        },
    )
    return installed


# ------------------------- VERSION DATA --------------------

def get_installed_versions():
    result = []
    try:
        for item in mcl.utils.get_installed_versions(str(MINECRAFT_DIR)):
            if item.get("id"):
                result.append(item["id"])
    except Exception as e:
        logging.exception("Error obteniendo versiones: %s", e)
    return result


def get_available_minecraft_versions():
    try:
        versions = mcl.utils.get_version_list()
        if isinstance(versions, list):
            return [v.get("id") for v in versions if v.get("id")]
        return []
    except Exception as e:
        logging.exception("Error obteniendo versiones online: %s", e)
        raise


def get_instances():
    result = []
    if not INSTANCES_DIR.exists():
        return result

    for folder in INSTANCES_DIR.iterdir():
        if not folder.is_dir():
            continue
        info_file = folder / "instance.json"
        info = {}
        if info_file.exists():
            info = load_json(info_file, {})
        result.append({
            "name": folder.name,
            "path": str(folder),
            "version": info.get("launch_version", info.get("version", "?")),
            "loader": info.get("loader", "Modpack"),
            "size": calculate_folder_size(folder),
        })
    return sorted(result, key=lambda x: x["name"].lower())


def calculate_folder_size(path):
    total = 0
    try:
        for root, _, files in os.walk(path):
            for filename in files:
                try:
                    total += (Path(root) / filename).stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


# ------------------------- INSTALLATION --------------------

class TaskRunner:
    def __init__(self, title="Procesando..."):
        self.title = title
        self.window = None
        self.status_label = None
        self.progress = None

    def start(self, function, success_message):
        self.window = ctk.CTkToplevel(app)
        self.window.title(self.title)
        self.window.geometry("480x190")
        self.window.resizable(False, False)
        self.window.transient(app)
        self.window.grab_set()

        ctk.CTkLabel(
            self.window,
            text=self.title,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(20, 8))

        self.status_label = ctk.CTkLabel(
            self.window,
            text="Preparando...",
            wraplength=420,
        )
        self.status_label.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self.window, width=400, mode="indeterminate")
        self.progress.pack(pady=15)
        self.progress.start()

        def status(text):
            run_on_ui(lambda: self.status_label.configure(text=str(text)[:100]))

        def target():
            try:
                function(status)
                run_on_ui(lambda: self.finish(True, success_message))
            except Exception as e:
                logging.exception("Task failed")
                run_on_ui(lambda e=e: self.finish(False, str(e)))

        threading.Thread(target=target, daemon=True).start()

    def finish(self, success, message):
        if self.progress:
            self.progress.stop()
        if self.window and self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()

        if success:
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)

        refresh_all()


def install_vanilla(version):
    def task(status):
        status(f"Instalando Minecraft {version}...")
        mcl.install.install_minecraft_version(
            version,
            str(MINECRAFT_DIR),
            callback={
                "setStatus": status,
                "setProgress": lambda p: None,
                "setMax": lambda m: None,
            },
        )
    TaskRunner("Instalar Vanilla").start(task, f"Minecraft {version} instalado correctamente.")


def install_loader(name, version):
    def task(status):
        installed = install_mod_loader(name, version, status)
        status(f"Instalado como {installed}")
    TaskRunner(f"Instalar {name.title()}").start(
        task,
        f"{name.title()} para {version} instalado correctamente.",
    )


def get_mrpack_name(path):
    try:
        with zipfile.ZipFile(path) as archive:
            for filename in archive.namelist():
                if filename.endswith(".json"):
                    try:
                        with archive.open(filename) as f:
                            data = json.load(f)
                        if isinstance(data, dict):
                            name = data.get("name") or data.get("packName")
                            if name:
                                return safe_name(name)
                    except Exception:
                        continue
    except Exception as e:
        logging.warning("No se pudo leer nombre del mrpack: %s", e)

    return safe_name(Path(path).stem)


def install_mrpack():
    path = filedialog.askopenfilename(
        title="Seleccionar Modpack",
        filetypes=[("Modrinth Modpack", "*.mrpack"), ("Todos los archivos", "*.*")],
    )
    if not path:
        return

    path = Path(path)
    name = get_mrpack_name(path)
    instance_dir = INSTANCES_DIR / name

    if instance_dir.exists():
        if not messagebox.askyesno(
            "Instancia existente",
            f"Ya existe '{name}'. ¿Quieres reemplazarla?",
        ):
            return

    def task(status):
        if instance_dir.exists():
            shutil.rmtree(instance_dir)

        instance_dir.mkdir(parents=True, exist_ok=True)
        status("Instalando contenido del modpack...")

        mcl.mrpack.install_mrpack(
            str(path),
            str(MINECRAFT_DIR),
            modpack_directory=str(instance_dir),
            callback={
                "setStatus": status,
                "setProgress": lambda p: None,
                "setMax": lambda m: None,
            },
        )

        launch_version = mcl.mrpack.get_mrpack_launch_version(str(path))

        info = {
            "name": name,
            "source": str(path),
            "launch_version": launch_version,
            "installed_at": datetime.now().isoformat(timespec="seconds"),
        }

        save_json(instance_dir / "instance.json", info)
        status("Modpack instalado.")

    TaskRunner("Instalar Modpack").start(
        task,
        f"Modpack '{name}' instalado correctamente.",
    )


# ------------------------- PROFILES ------------------------

def ensure_profile(username):
    username = username.strip() or "Player"
    if username not in profiles:
        profiles[username] = {
            "username": username,
            "uuid": str(uuid.uuid4()),
        }
        save_json(PROFILES_FILE, profiles)
    return profiles[username]


def delete_profile(username):
    if len(profiles) <= 1:
        messagebox.showwarning("Perfil", "Debes conservar al menos un perfil.")
        return
    if username not in profiles:
        return

    if messagebox.askyesno("Eliminar perfil", f"¿Eliminar el perfil '{username}'?"):
        del profiles[username]
        save_json(PROFILES_FILE, profiles)
        refresh_profiles()


# ------------------------- LAUNCH --------------------------

def parse_ram():
    value = str(ram_var.get()).strip()
    try:
        ram = int(value)
    except ValueError:
        raise ValueError("La RAM debe ser un número entero.")

    if ram < 1 or ram > 64:
        raise ValueError("La RAM debe estar entre 1 y 64 GB.")

    return ram


def choose_java():
    found = detect_java()
    if not found:
        messagebox.showwarning(
            "Java",
            "No se encontró Java automáticamente. Selecciona el ejecutable de Java.",
        )
        path = filedialog.askopenfilename(
            title="Seleccionar Java",
            filetypes=[("Java", "java.exe" if platform.system() == "Windows" else "java"),
                       ("Todos los archivos", "*.*")],
        )
        if path:
            config["java_path"] = path
            save_json(CONFIG_FILE, config)
            refresh_java()
        return

    # Small selection dialog
    win = ctk.CTkToplevel(app)
    win.title("Seleccionar Java")
    win.geometry("650x350")
    win.transient(app)
    win.grab_set()

    ctk.CTkLabel(
        win,
        text="Java detectado",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(pady=15)

    selected = ctk.StringVar(value=config.get("java_path") or found[0])

    values = [f"{p}  —  Java {java_version(p)}" for p in found]
    mapping = dict(zip(values, found))

    combo = ctk.CTkOptionMenu(
        win,
        values=values,
        variable=ctk.StringVar(value=values[0]),
        width=570,
    )
    combo.pack(pady=15)

    def save_java():
        chosen = mapping.get(combo.get())
        if chosen:
            config["java_path"] = chosen
            save_json(CONFIG_FILE, config)
            refresh_java()
        win.destroy()

    ctk.CTkButton(win, text="Usar este Java", command=save_java).pack(pady=15)
    ctk.CTkButton(win, text="Cancelar", command=win.destroy).pack()


def build_launch_options(profile, ram, game_directory):
    options = {
        "username": profile["username"],
        "uuid": profile["uuid"],
        # Offline launch: empty token. No Microsoft authentication is implemented.
        "token": "",
        "jvmArguments": [
            f"-Xmx{ram}G",
            f"-Xms{max(1, min(ram, max(1, ram // 2)))}G",
        ],
        "gameDirectory": str(game_directory),
        "launcherName": APP_NAME,
        "launcherVersion": APP_VERSION,
    }

    java_path = str(config.get("java_path", "")).strip()
    if java_path and Path(java_path).exists():
        options["executablePath"] = java_path

    return options


def launch_game(version_id, game_directory):
    global minecraft_running

    if minecraft_running:
        messagebox.showinfo(
            "Minecraft en ejecución",
            "Minecraft ya está abierto. Cierra el juego antes de volver a iniciarlo.",
        )
        return

    try:
        ram = parse_ram()
        username = profile_var.get().strip()

        if not username:
            raise ValueError("Selecciona o crea un perfil.")

        profile = ensure_profile(username)
        options = build_launch_options(profile, ram, game_directory)

        logging.info(
            "Lanzando %s | perfil=%s | RAM=%s | dir=%s",
            version_id,
            username,
            ram,
            game_directory,
        )

        command = mcl.command.get_minecraft_command(
            version_id,
            str(MINECRAFT_DIR),
            options,
        )

        config["username"] = username
        config["ram"] = ram
        config["last_version"] = version_id
        config["keep_open"] = bool(keep_open_var.get())
        save_json(CONFIG_FILE, config)

        # Estado: Minecraft está arrancando.
        minecraft_running = True
        run_on_ui(lambda: play_status_label.configure(text="⏳ Abriendo juego..."))
        run_on_ui(lambda: play_button.configure(
            state="disabled",
            text="⏳ Abriendo juego..."
        ))

        append_console(f"[LAUNCH] {version_id} | {username} | {ram} GB")
        append_console(f"[JAVA] {config.get('java_path') or 'automático'}")

        def run():
            global minecraft_running

            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(game_directory),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                
                run_on_ui(lambda: play_status_label.configure(
                    text="🟢 Juego en ejecución"
                ))
                run_on_ui(lambda: play_button.configure(
                    state="disabled",
                    text="🟢 Minecraft en ejecución"
                ))
                append_console("[MINECRAFT] Juego en ejecución.")

                for line in iter(process.stdout.readline, ""):
                    if line:
                        append_console(line.rstrip())

                process.stdout.close()
                code = process.wait()

                minecraft_running = False
                append_console(f"[MINECRAFT] Proceso terminado con código {code}")

                run_on_ui(lambda: play_status_label.configure(
                    text="⚪ Juego cerrado"
                ))
                run_on_ui(lambda: play_button.configure(
                    state="normal",
                    text="▶  JUGAR"
                ))

                if not keep_open_var.get():
                    run_on_ui(app.destroy)

            except Exception as e:
                minecraft_running = False
                logging.exception("Minecraft no pudo iniciarse")
                run_on_ui(lambda: play_status_label.configure(
                    text="🔴 Error al abrir Minecraft"
                ))
                run_on_ui(lambda: play_button.configure(
                    state="normal",
                    text="▶  JUGAR"
                ))
                run_on_ui(
                    lambda e=e: messagebox.showerror(
                        "Error al iniciar Minecraft",
                        str(e),
                    )
                )

        threading.Thread(target=run, daemon=True).start()

    except Exception as e:
        minecraft_running = False
        show_error("No se pudo iniciar Minecraft", e)
        try:
            play_status_label.configure(text="🔴 Error al abrir Minecraft")
            play_button.configure(state="normal", text="▶  JUGAR")
        except Exception:
            pass


def launch_selected():
    selected = version_var.get().strip()

    if not selected or selected.startswith("No hay"):
        messagebox.showwarning("Versión", "Selecciona una versión instalada.")
        return

    if selected.startswith("[Modpack] "):
        name = selected[len("[Modpack] "):]
        instance = INSTANCES_DIR / name
        info = load_json(instance / "instance.json", {})

        version_id = info.get("launch_version")
        if not version_id:
            messagebox.showerror("Modpack", "No se encontró la versión de Minecraft del modpack.")
            return

        launch_game(version_id, instance)
    else:
        launch_game(selected, MINECRAFT_DIR)


# ------------------------- VERSION INSTALL UI --------------

def install_dialog(loader_name):
    win = ctk.CTkToplevel(app)
    win.title(f"Instalar {loader_name}")
    win.geometry("470x300")
    win.transient(app)
    win.grab_set()

    ctk.CTkLabel(
        win,
        text=f"Instalar {loader_name}",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(pady=(25, 15))

    ctk.CTkLabel(win, text="Versión de Minecraft").pack()

    version_entry = ctk.CTkEntry(win, width=300, placeholder_text="Ejemplo: 1.21.8")
    version_entry.pack(pady=10)
    version_entry.focus()

    def install():
        version = version_entry.get().strip()
        if not version:
            messagebox.showwarning("Versión", "Escribe una versión.")
            return

        win.destroy()
        if loader_name == "Vanilla":
            install_vanilla(version)
        else:
            install_loader(loader_name.lower(), version)

    ctk.CTkButton(win, text="Instalar", width=180, command=install).pack(pady=15)
    ctk.CTkButton(win, text="Cancelar", width=180, command=win.destroy).pack()


def online_versions_dialog():
    win = ctk.CTkToplevel(app)
    win.title("Versiones disponibles")
    win.geometry("600x600")
    win.transient(app)
    win.grab_set()

    ctk.CTkLabel(
        win,
        text="Versiones de Minecraft",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(pady=15)

    listbox = ctk.CTkTextbox(win, width=530, height=430)
    listbox.pack(pady=10)
    listbox.insert("end", "Consultando Mojang...\n")
    listbox.configure(state="disabled")

    def load():
        try:
            versions = get_available_minecraft_versions()
            # Keep the UI manageable.
            releases = versions[:200]
            text = "\n".join(releases)
            run_on_ui(lambda: (
                listbox.configure(state="normal"),
                listbox.delete("1.0", "end"),
                listbox.insert("end", text),
                listbox.configure(state="disabled"),
            ))
        except Exception as e:
            run_on_ui(lambda e=e: messagebox.showerror("Versiones", str(e)))

    threading.Thread(target=load, daemon=True).start()
    ctk.CTkButton(win, text="Cerrar", command=win.destroy).pack(pady=10)


# ------------------------- MODPACK UI ----------------------

def delete_selected_modpack():
    selected = instance_var.get().strip()
    if not selected:
        messagebox.showwarning("Modpack", "Selecciona un modpack.")
        return

    folder = INSTANCES_DIR / selected
    if not is_safe_child(folder, INSTANCES_DIR):
        messagebox.showerror("Seguridad", "Ruta de instancia inválida.")
        return

    if messagebox.askyesno("Eliminar modpack", f"¿Eliminar '{selected}' completamente?"):
        try:
            shutil.rmtree(folder)
            refresh_instances()
            refresh_all()
        except Exception as e:
            show_error("No se pudo eliminar", e)


def open_instance_folder():
    selected = instance_var.get().strip()
    if not selected:
        return

    folder = INSTANCES_DIR / selected
    if not folder.exists():
        return

    try:
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception as e:
        show_error("Carpeta", e)


# ------------------------- DELETE VERSION ------------------

def delete_selected_version():
    selected = version_var.get().strip()

    if not selected or selected.startswith("No hay"):
        return

    if selected.startswith("[Modpack] "):
        messagebox.showinfo(
            "Versión",
            "Los modpacks se eliminan desde la pestaña Modpacks.",
        )
        return

    folder = VERSIONS_DIR / selected
    if not is_safe_child(folder, VERSIONS_DIR):
        messagebox.showerror("Seguridad", "Ruta de versión inválida.")
        return

    if not folder.exists():
        messagebox.showerror("Versión", "La versión no existe.")
        return

    if messagebox.askyesno(
        "Eliminar versión",
        f"¿Eliminar '{selected}'?\n\nEsto elimina su carpeta de versión.",
    ):
        try:
            shutil.rmtree(folder)
            refresh_all()
        except Exception as e:
            show_error("No se pudo eliminar la versión", e)


# ------------------------- PROFILE UI ----------------------

def refresh_profiles():
    names = sorted(profiles.keys(), key=str.lower)
    if not names:
        profiles.update(DEFAULT_PROFILES)
        save_json(PROFILES_FILE, profiles)
        names = list(profiles)

    profile_menu.configure(values=names)

    current = config.get("username")
    if current in names:
        profile_var.set(current)
    else:
        profile_var.set(names[0])


def add_profile():
    win = ctk.CTkToplevel(app)
    win.title("Nuevo perfil")
    win.geometry("420x250")
    win.transient(app)
    win.grab_set()

    ctk.CTkLabel(
        win,
        text="Crear perfil offline",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(pady=20)

    entry = ctk.CTkEntry(win, width=280, placeholder_text="Nombre del jugador")
    entry.pack(pady=10)
    entry.focus()

    def create():
        name = entry.get().strip()
        if not name:
            return
        if len(name) > 16:
            messagebox.showerror("Perfil", "El nombre no puede superar 16 caracteres.")
            return
        if not re.fullmatch(r"[A-Za-z0-9_]+", name):
            messagebox.showerror(
                "Perfil",
                "Usa solo letras, números y guion bajo.",
            )
            return

        ensure_profile(name)
        config["username"] = name
        save_json(CONFIG_FILE, config)
        refresh_profiles()
        win.destroy()

    ctk.CTkButton(win, text="Crear", command=create).pack(pady=15)
    ctk.CTkButton(win, text="Cancelar", command=win.destroy).pack()


def remove_current_profile():
    delete_profile(profile_var.get())
    refresh_profiles()


# ------------------------- SETTINGS ------------------------

def refresh_java():
    java = config.get("java_path", "")
    if java:
        java_label.configure(
            text=f"Java seleccionado:\n{java}\nVersión: {java_version(java)}"
        )
    else:
        found = detect_java()
        if found:
            java_label.configure(
                text=f"Java automático:\n{found[0]}\nVersión: {java_version(found[0])}"
            )
        else:
            java_label.configure(text="Java: no encontrado")


def save_settings():
    try:
        ram = parse_ram()
        config["ram"] = ram
    except Exception:
        messagebox.showerror("RAM", "Introduce una cantidad válida de RAM.")
        return

    config["keep_open"] = bool(keep_open_var.get())
    config["username"] = profile_var.get()
    config["theme"] = appearance_var.get()
    save_json(CONFIG_FILE, config)

    ctk.set_appearance_mode(config["theme"])
    refresh_java()
    messagebox.showinfo("Configuración", "Configuración guardada.")


# ------------------------- CONSOLE --------------------------

console_queue = queue.Queue()


def append_console(text):
    try:
        console_queue.put(str(text))
    except Exception:
        pass


def process_console():
    try:
        while True:
            text = console_queue.get_nowait()
            console_text.configure(state="normal")
            console_text.insert("end", text + "\n")
            console_text.see("end")
            console_text.configure(state="disabled")
    except queue.Empty:
        pass

    app.after(100, process_console)


def clear_console():
    console_text.configure(state="normal")
    console_text.delete("1.0", "end")
    console_text.configure(state="disabled")


# ------------------------- REFRESH --------------------------

def refresh_versions():
    installed = get_installed_versions()
    instances = get_instances()

    values = []
    values.extend(installed)
    values.extend(f"[Modpack] {x['name']}" for x in instances)

    if not values:
        values = ["No hay versiones instaladas"]

    version_menu.configure(values=values)

    current = config.get("last_version")
    if current in values:
        version_var.set(current)
    elif version_var.get() not in values:
        version_var.set(values[0])


def refresh_instances():
    instances = get_instances()
    names = [x["name"] for x in instances]

    if names:
        instance_menu.configure(values=names)
        if instance_var.get() not in names:
            instance_var.set(names[0])

        instance_info.configure(
            text="\n".join(
                f"{x['name']}  |  {x['version']}  |  {x['loader']}  |  {human_size(x['size'])}"
                for x in instances
            )
        )
    else:
        instance_menu.configure(values=["No hay modpacks"])
        instance_var.set("No hay modpacks")
        instance_info.configure(text="No hay modpacks instalados.")


def refresh_all():
    refresh_versions()
    refresh_instances()
    refresh_profiles()
    refresh_java()


# ------------------------- MAIN UI --------------------------

app = ctk.CTk()
app.title(f"{APP_NAME} {APP_VERSION}")
app.geometry(f"{config.get('width', 1050)}x{config.get('height', 700)}")
app.minsize(950, 650)

profile_var = ctk.StringVar(value=config.get("username", "Player"))
ram_var = ctk.StringVar(value=str(config.get("ram", 4)))
version_var = ctk.StringVar(value="")
instance_var = ctk.StringVar(value="")
keep_open_var = ctk.BooleanVar(value=config.get("keep_open", True))
appearance_var = ctk.StringVar(value=config.get("theme", "dark"))

# Sidebar
sidebar = ctk.CTkFrame(app, width=210, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar,
    text="MINECRAFT\nLAUNCHER",
    font=ctk.CTkFont(size=24, weight="bold"),
).pack(pady=(35, 30))

content = ctk.CTkFrame(app, fg_color="transparent")
content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

tabs = ctk.CTkTabview(content)
tabs.pack(fill="both", expand=True)

tabs.add("Jugar")
tabs.add("Instalar")
tabs.add("Modpacks")
tabs.add("Perfiles")
tabs.add("Consola")
tabs.add("Configuración")

# Sidebar buttons select tabs
for text, tab in [
    ("▶  Jugar", "Jugar"),
    ("＋  Instalar", "Instalar"),
    ("▣  Modpacks", "Modpacks"),
    ("♙  Perfiles", "Perfiles"),
    ("⌁  Consola", "Consola"),
    ("⚙  Configuración", "Configuración"),
]:
    ctk.CTkButton(
        sidebar,
        text=text,
        anchor="w",
        height=42,
        fg_color="transparent",
        command=lambda t=tab: tabs.set(t),
    ).pack(fill="x", padx=15, pady=4)

ctk.CTkLabel(
    sidebar,
    text=f"v{APP_VERSION}\nSin Microsoft Login",
    text_color="gray",
).pack(side="bottom", pady=25)

# ---------------- JUGAR ----------------

play = tabs.tab("Jugar")

ctk.CTkLabel(
    play,
    text="Jugar Minecraft",
    font=ctk.CTkFont(size=30, weight="bold"),
).pack(anchor="w", padx=30, pady=(30, 5))

ctk.CTkLabel(
    play,
    text="Selecciona una instalación y pulsa JUGAR.",
    text_color="gray",
).pack(anchor="w", padx=30, pady=(0, 25))

play_card = ctk.CTkFrame(play)
play_card.pack(fill="x", padx=30, pady=10)

ctk.CTkLabel(play_card, text="Perfil").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
profile_menu = ctk.CTkOptionMenu(play_card, variable=profile_var, values=list(profiles), width=300)
profile_menu.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

ctk.CTkLabel(play_card, text="RAM (GB)").grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
ram_entry = ctk.CTkEntry(play_card, textvariable=ram_var, width=120)
ram_entry.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="w")

ctk.CTkLabel(play_card, text="Instalación").grid(row=2, column=0, padx=20, pady=(5, 5), sticky="w")
version_menu = ctk.CTkOptionMenu(play_card, variable=version_var, values=["Cargando..."], width=450)
version_menu.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="w")

keep_check = ctk.CTkCheckBox(
    play_card,
    text="Mantener launcher abierto después de iniciar",
    variable=keep_open_var,
)
keep_check.grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="w")

play_button = ctk.CTkButton(
    play,
    text="▶  JUGAR",
    height=55,
    width=300,
    font=ctk.CTkFont(size=18, weight="bold"),
    command=launch_selected,
)
play_button.pack(pady=(30, 8))

play_status_label = ctk.CTkLabel(
    play,
    text="Listo para jugar",
    font=ctk.CTkFont(size=13),
    text_color="gray",
)
play_status_label.pack(pady=(0, 10))

# ---------------- INSTALAR ----------------

install_tab = tabs.tab("Instalar")

ctk.CTkLabel(
    install_tab,
    text="Instalar",
    font=ctk.CTkFont(size=30, weight="bold"),
).pack(anchor="w", padx=30, pady=(30, 20))

install_grid = ctk.CTkFrame(install_tab)
install_grid.pack(fill="x", padx=30, pady=10)

buttons = [
    ("Minecraft Vanilla", "Vanilla", "#10b981"),
    ("Forge", "Forge", "#ef4444"),
    ("NeoForge", "NeoForge", "#f97316"),
    ("Fabric", "Fabric", "#06b6d4"),
]

for index, (label, loader, color) in enumerate(buttons):
    ctk.CTkButton(
        install_grid,
        text=label,
        fg_color=color,
        height=50,
        command=lambda l=loader: install_dialog(l),
    ).grid(row=index // 2, column=index % 2, padx=15, pady=15, sticky="ew")

install_grid.grid_columnconfigure(0, weight=1)
install_grid.grid_columnconfigure(1, weight=1)

ctk.CTkButton(
    install_tab,
    text="📦 Instalar Modpack .mrpack",
    height=50,
    command=install_mrpack,
).pack(fill="x", padx=30, pady=15)

ctk.CTkButton(
    install_tab,
    text="☁ Ver versiones disponibles",
    height=45,
    command=online_versions_dialog,
).pack(fill="x", padx=30, pady=5)

ctk.CTkButton(
    install_tab,
    text="🗑 Eliminar versión seleccionada",
    fg_color="#b45309",
    height=45,
    command=delete_selected_version,
).pack(fill="x", padx=30, pady=20)

# ---------------- MODPACKS ----------------

packs = tabs.tab("Modpacks")

ctk.CTkLabel(
    packs,
    text="Modpacks",
    font=ctk.CTkFont(size=30, weight="bold"),
).pack(anchor="w", padx=30, pady=(30, 20))

instance_menu = ctk.CTkOptionMenu(
    packs,
    variable=instance_var,
    values=["No hay modpacks"],
    width=500,
)
instance_menu.pack(anchor="w", padx=30, pady=10)

instance_info = ctk.CTkLabel(
    packs,
    text="Cargando...",
    justify="left",
    anchor="w",
)
instance_info.pack(fill="x", padx=30, pady=20)

ctk.CTkButton(
    packs,
    text="▶ Iniciar modpack seleccionado",
    height=50,
    command=launch_selected,
).pack(fill="x", padx=30, pady=8)

ctk.CTkButton(
    packs,
    text="📁 Abrir carpeta de instancia",
    height=45,
    command=open_instance_folder,
).pack(fill="x", padx=30, pady=8)

ctk.CTkButton(
    packs,
    text="🗑 Eliminar modpack",
    fg_color="#dc2626",
    height=45,
    command=delete_selected_modpack,
).pack(fill="x", padx=30, pady=8)

# ---------------- PERFILES ----------------

profiles_tab = tabs.tab("Perfiles")

ctk.CTkLabel(
    profiles_tab,
    text="Perfiles offline",
    font=ctk.CTkFont(size=30, weight="bold"),
).pack(anchor="w", padx=30, pady=(30, 10))

ctk.CTkLabel(
    profiles_tab,
    text="Estos perfiles no son cuentas Microsoft. Solo guardan nombre y UUID local.",
    text_color="gray",
).pack(anchor="w", padx=30, pady=(0, 20))

ctk.CTkButton(
    profiles_tab,
    text="＋ Crear perfil",
    command=add_profile,
).pack(anchor="w", padx=30, pady=10)

ctk.CTkButton(
    profiles_tab,
    text="🗑 Eliminar perfil actual",
    fg_color="#dc2626",
    command=remove_current_profile,
).pack(anchor="w", padx=30, pady=10)

# ---------------- CONSOLA ----------------

console_tab = tabs.tab("Consola")

ctk.CTkLabel(
    console_tab,
    text="Consola / Logs",
    font=ctk.CTkFont(size=30, weight="bold"),
).pack(anchor="w", padx=20, pady=(20, 10))

console_text = ctk.CTkTextbox(console_tab, font=("Consolas", 12))
console_text.pack(fill="both", expand=True, padx=20, pady=10)
console_text.configure(state="disabled")

ctk.CTkButton(
    console_tab,
    text="Limpiar consola",
    command=clear_console,
).pack(anchor="e", padx=20, pady=10)

# ---------------- CONFIGURACIÓN ----------------

settings = tabs.tab("Configuración")

ctk.CTkLabel(
    settings,
    text="Configuración",
    font=ctk.CTkFont(size=30, weight="bold"),
).pack(anchor="w", padx=30, pady=(30, 20))

java_label = ctk.CTkLabel(settings, text="Java: buscando...", justify="left", anchor="w")
java_label.pack(fill="x", padx=30, pady=10)

ctk.CTkButton(
    settings,
    text="☕ Seleccionar Java",
    command=choose_java,
).pack(anchor="w", padx=30, pady=10)

ctk.CTkLabel(settings, text="RAM predeterminada (GB)").pack(anchor="w", padx=30, pady=(20, 5))
settings_ram = ctk.CTkEntry(settings, textvariable=ram_var, width=150)
settings_ram.pack(anchor="w", padx=30)

ctk.CTkLabel(settings, text="Tema").pack(anchor="w", padx=30, pady=(20, 5))
appearance_menu = ctk.CTkOptionMenu(
    settings,
    variable=appearance_var,
    values=["dark", "light", "system"],
)
appearance_menu.pack(anchor="w", padx=30)

ctk.CTkButton(
    settings,
    text="💾 Guardar configuración",
    height=45,
    command=save_settings,
).pack(anchor="w", padx=30, pady=25)

ctk.CTkLabel(
    settings,
    text=f"Directorio del launcher:\n{MINECRAFT_DIR}\n\nLog:\n{LOG_FILE}",
    justify="left",
    text_color="gray",
).pack(anchor="w", padx=30, pady=10)

# ---------------- STARTUP ----------------

refresh_all()
refresh_java()
process_console()
append_console(f"[INFO] {APP_NAME} {APP_VERSION}")
append_console(f"[INFO] Directorio: {MINECRAFT_DIR}")
append_console("[INFO] Microsoft Login: desactivado/no incluido.")

def on_close():
    try:
        config["username"] = profile_var.get()
        config["ram"] = int(ram_var.get())
    except Exception:
        pass

    config["keep_open"] = bool(keep_open_var.get())
    config["theme"] = appearance_var.get()
    config["width"] = app.winfo_width()
    config["height"] = app.winfo_height()

    try:
        save_json(CONFIG_FILE, config)
    except Exception:
        pass

    logging.info("Launcher cerrado")
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_close)
app.mainloop()
