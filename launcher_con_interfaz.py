import os
import subprocess
import shutil
import uuid
import threading
import zipfile
import json
import minecraft_launcher_lib as mcl
import customtkinter as ctk
from tkinter import messagebox

# ====================== CONFIGURACIÓN ======================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ventana = ctk.CTk()
ventana.geometry('700x580')
ventana.title('Lanzador de Minecraft - Hecho por: Sin1Nombre2')
ventana.resizable(False, False)

try:
    ventana.iconbitmap("icono.ico")
except:
    pass

user_window = os.environ.get("USERNAME", "Usuario")
minecraft_directori = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"
instancias_dir = os.path.join(minecraft_directori, "instancias")

os.makedirs(minecraft_directori, exist_ok=True)
os.makedirs(instancias_dir, exist_ok=True)

vers = ctk.StringVar(value="Cargando...")

# ====================== VENTANA DE CARGA ======================
def ventana_carga(titulo="Instalando..."):
    win = ctk.CTkToplevel(ventana)
    win.geometry("400x180")
    win.title(titulo)
    win.grab_set()
    win.resizable(False, False)

    label_status = ctk.CTkLabel(win, text="Preparando...", font=("Arial", 13))
    label_status.pack(pady=20)

    barra = ctk.CTkProgressBar(win, width=340)
    barra.pack(pady=10)
    barra.start()

    return win, label_status, barra

# ====================== REFRESH ======================
def refresh_versions():
    try:
        versiones = mcl.utils.get_installed_versions(minecraft_directori)
        lista = [v['id'] for v in versiones] or ['No hay versiones instaladas']
        vers.set(lista[0] if lista else 'No hay versiones instaladas')
        versiones_menu.configure(values=lista)
    except:
        vers.set('Error al cargar versiones')
        versiones_menu.configure(values=['Error al cargar'])

# ====================== WIDGETS ======================
label_nombre = ctk.CTkLabel(ventana, text='Nombre de jugador:')
label_ram = ctk.CTkLabel(ventana, text='RAM a usar (GB):')

entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Introduce tu nombre", width=220)
entry_ram = ctk.CTkEntry(ventana, placeholder_text="Ej: 4, 8, 16", width=220)

versiones_menu = ctk.CTkOptionMenu(ventana, variable=vers, values=["Cargando..."], width=300)

bt_ejecutar = ctk.CTkButton(ventana, text='Iniciar Minecraft', fg_color="#3b82f6", width=220, height=35)
bt_instalar_version = ctk.CTkButton(ventana, text='Instalar Versión Vanilla', fg_color="#10b981", width=220)
bt_instalar_forge = ctk.CTkButton(ventana, text='Instalar Forge', fg_color="#ef4444", width=220)
bt_instalar_mrpack = ctk.CTkButton(ventana, text='Instalar Modpack (.mrpack)', fg_color="#8b5cf6", width=220)
bt_eliminar_version = ctk.CTkButton(ventana, text='Eliminar Versión', fg_color="#f59e0b", width=220)
bt_eliminar_modpack = ctk.CTkButton(ventana, text='Eliminar Modpack', fg_color="#dc2626", width=220)

mantener_abierta = ctk.BooleanVar(value=True)
check_mantener = ctk.CTkCheckBox(ventana, text="Mantener launcher abierto después de iniciar", variable=mantener_abierta)

# ====================== INSTALACIÓN EN HILO ======================
def run_installation(install_func, success_msg, error_title="Error"):
    win, label_status, _ = ventana_carga("Instalando...")

    def set_status(text):
        try:
            label_status.configure(text=text)
            win.update_idletasks()
        except:
            pass

    def thread_target():
        try:
            install_func({"setStatus": set_status})
            ventana.after(0, lambda: messagebox.showinfo("Éxito", success_msg))
            ventana.after(0, refresh_versions)
        except Exception as e:
            error_msg = str(e)
            ventana.after(0, lambda: messagebox.showerror(error_title, error_msg))
        finally:
            try:
                ventana.after(0, win.destroy)
            except:
                pass

    threading.Thread(target=thread_target, daemon=True).start()

# ====================== OBTENER NOMBRE DEL MODPACK ======================
def get_modpack_name(mrpack_path):
    """Extrae el nombre del modpack desde el manifest.json del .mrpack"""
    try:
        with zipfile.ZipFile(mrpack_path) as z:
            with z.open("modrinth.index.json") as f:
                data = json.load(f)
                return data.get("name", "Modpack_Desconocido").strip().replace(" ", "_")
    except:
        # Fallback si no se puede leer el manifest
        base = os.path.basename(mrpack_path)
        return os.path.splitext(base)[0]

# ====================== INSTALAR MODPACK (MEJORADO) ======================
def instalar_modpack():
    mrpack_path = ctk.CTkInputDialog(
        text="Ruta completa del archivo .mrpack:",
        title="Instalar Modpack"
    ).get_input()

    if not mrpack_path or not os.path.isfile(mrpack_path):
        messagebox.showerror("Error", "Ruta inválida o archivo no encontrado")
        return

    modpack_name = get_modpack_name(mrpack_path)
    modpack_folder = os.path.join(instancias_dir, modpack_name)

    # Evitar sobrescribir si ya existe 
    if os.path.exists(modpack_folder):
        if not messagebox.askyesno("Carpeta existente", 
            f"Ya existe una carpeta llamada '{modpack_name}'.\n¿Quieres sobrescribirla?"):
            return

    def install(callback):
        # Creamos la carpeta del modpack
        os.makedirs(modpack_folder, exist_ok=True)

        # Instalamos el modpack directamente en su carpeta
        mcl.mrpack.install_mrpack(
            mrpack_path,
            minecraft_directori,           
            modpack_directory=modpack_folder,  
            callback=callback
        )

    run_installation(
        install, 
        f"Modpack '{modpack_name}' instalado correctamente en:\n{modpack_folder}",
        "Error al instalar Modpack"
    )

# ====================== INSTALAR VANILLA ======================
def instalar_minecraft():
    version = entry_version.get().strip()
    if not version:
        messagebox.showerror("Error", "Introduce una versión")
        return

    def install(callback):
        mcl.install.install_minecraft_version(version, minecraft_directori, callback=callback)

    run_installation(install, f"Versión {version} instalada correctamente", "Error al instalar Vanilla")

# ====================== INSTALAR FORGE ======================
def instalar_forge():
    version = entry_version.get().strip()
    if not version:
        messagebox.showerror("Error", "Introduce una versión")
        return

    def install(callback):
        forge_version = mcl.forge.find_forge_version(version)
        if forge_version is None:
            raise Exception(f"No hay Forge disponible para la versión {version}")
        mcl.forge.install_forge_version(forge_version, minecraft_directori, callback=callback)

    run_installation(install, f"Forge para {version} instalado correctamente", "Error al instalar Forge")

# ====================== ELIMINAR ======================
def eliminar_version():
    version = vers.get()
    if version in ['No hay versiones instaladas', 'Cargando...', 'Error al cargar']:
        messagebox.showerror("Error", "No hay versiones para eliminar")
        return

    ruta = os.path.join(minecraft_directori, "versions", version)
    if ask_yes_no("Confirmar", f"¿Eliminar {version}?"):
        try:
            shutil.rmtree(ruta, ignore_errors=True)
            messagebox.showinfo("Éxito", f"Versión {version} eliminada")
            refresh_versions()
        except Exception as e:
            messagebox.showerror("Error", str(e))

def eliminar_modpack():
    if not os.path.exists(instancias_dir):
        messagebox.showerror("Error", "No hay modpacks instalados")
        return

    modpacks = [d for d in os.listdir(instancias_dir) if os.path.isdir(os.path.join(instancias_dir, d))]
    if not modpacks:
        messagebox.showerror("Error", "No hay modpacks instalados")
        return

    win_select = ctk.CTkToplevel(ventana)
    win_select.title("Eliminar Modpack")
    win_select.geometry("400x280")
    win_select.grab_set()

    ctk.CTkLabel(win_select, text="Selecciona el modpack:", font=("Arial", 13)).pack(pady=15)

    var = ctk.StringVar(value=modpacks[0])
    combo = ctk.CTkOptionMenu(win_select, variable=var, values=modpacks, width=280)
    combo.pack(pady=10)

    def confirmar():
        selected = var.get()
        if not selected:
            return
        if ask_yes_no("Confirmar", f"¿Eliminar '{selected}'?"):
            try:
                shutil.rmtree(os.path.join(instancias_dir, selected), ignore_errors=True)
                messagebox.showinfo("Éxito", "Modpack eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        win_select.destroy()

    ctk.CTkButton(win_select, text="Eliminar", fg_color="red", command=confirmar).pack(pady=10)
    ctk.CTkButton(win_select, text="Cancelar", command=win_select.destroy).pack()

def ask_yes_no(title, text):
    return messagebox.askyesno(title, text)

# ====================== VENTANA VERSIÓN ======================
entry_version = None

def abrir_ventana_version(titulo, comando):
    global entry_version
    win = ctk.CTkToplevel(ventana)
    win.geometry('380x200')
    win.title(titulo)
    win.grab_set()
    win.resizable(False, False)

    ctk.CTkLabel(win, text="Versión de Minecraft:", font=("Arial", 12)).pack(pady=15)
    entry_version = ctk.CTkEntry(win, width=220, placeholder_text="Ej: 1.21.3")
    entry_version.pack(pady=10)

    ctk.CTkButton(win, text="Instalar", width=140, command=comando).pack(pady=20)

# ====================== EJECUTAR ======================
def ejecutar_minecraft():
    nombre = entry_nombre.get().strip()
    ram_str = entry_ram.get().strip()
    version = vers.get()

    if not nombre:
        messagebox.showerror("Error", "Introduce un nombre de jugador")
        return
    if version in ['No hay versiones instaladas', 'Cargando...', 'Error al cargar']:
        messagebox.showerror("Error", "No hay ninguna versión instalada")
        return

    try:
        ram = int(ram_str)
        if ram < 1 or ram > 32:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "RAM debe ser un número entre 1 y 32")
        return

    options = {
        'username': nombre,
        'uuid': str(uuid.uuid4()),
        'token': '',
        'jvmArguments': [f"-Xmx{ram}G"],
    }

    try:
        comando = mcl.command.get_minecraft_command(version, minecraft_directori, options)
        subprocess.run(comando, check=True)

        if not mantener_abierta.get():
            ventana.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Error al iniciar Minecraft:\n{str(e)}")

# ====================== ASIGNAR COMANDOS ======================
bt_instalar_version.configure(command=lambda: abrir_ventana_version("Instalar Vanilla", instalar_minecraft))
bt_instalar_forge.configure(command=lambda: abrir_ventana_version("Instalar Forge", instalar_forge))
bt_instalar_mrpack.configure(command=instalar_modpack)
bt_ejecutar.configure(command=ejecutar_minecraft)
bt_eliminar_version.configure(command=eliminar_version)
bt_eliminar_modpack.configure(command=eliminar_modpack)

# ====================== POSICIONES ======================
label_nombre.place(x=30, y=30)
entry_nombre.place(x=30, y=60)
label_ram.place(x=30, y=110)
entry_ram.place(x=30, y=140)
versiones_menu.place(x=30, y=210)

bt_instalar_version.place(x=380, y=30)
bt_instalar_forge.place(x=380, y=80)
bt_instalar_mrpack.place(x=380, y=130)
bt_eliminar_version.place(x=380, y=180)
bt_eliminar_modpack.place(x=380, y=230)

check_mantener.place(x=30, y=480)
bt_ejecutar.place(x=240, y=520)

# ====================== INICIO ======================
refresh_versions()
ventana.mainloop()