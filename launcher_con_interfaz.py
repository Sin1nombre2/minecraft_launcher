import minecraft_launcher_lib
import os
import subprocess
import sys
import customtkinter as ctk
from tkinter import messagebox
import shutil

# ====================== CONFIGURACIÓN DE ESTILOS ======================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ====================== VENTANA PRINCIPAL ======================
ventana = ctk.CTk()
ventana.geometry('700x550')
ventana.title('Lanzador de Minecraft - Hecho por: Sin1Nombre2')
ventana.resizable(False, False)

user_window = os.environ.get("USERNAME", "Usuario")
minecraft_directori = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"
os.makedirs(minecraft_directori, exist_ok=True)

# ====================== VENTANA DE CARGA ======================
def ventana_carga(titulo="Instalando..."):
    win = ctk.CTkToplevel(ventana)
    win.geometry("300x120")
    win.title(titulo)
    win.grab_set()

    label = ctk.CTkLabel(win, text="Por favor espera...")
    label.pack(pady=10)

    barra = ctk.CTkProgressBar(win, width=250)
    barra.pack(pady=10)
    barra.start()  # animación infinita

    return win

# ====================== WIDGETS ======================
bt_ejecutar = ctk.CTkButton(ventana, text='Iniciar Minecraft', fg_color="#3b82f6", width=200)
bt_instalar_version = ctk.CTkButton(ventana, text='Instalar Versión Vanilla', fg_color="#10b981", width=200)
bt_instalar_forge = ctk.CTkButton(ventana, text='Instalar Forge', fg_color="#ef4444", width=200)
bt_instalar_mrpack = ctk.CTkButton(ventana, text='Instalar Modpack (.mrpack)', fg_color="#8b5cf6", width=200)
bt_eliminar_version = ctk.CTkButton(ventana, text='Eliminar Versión', fg_color="#f59e0b", width=200)
bt_eliminar_modpack = ctk.CTkButton(ventana, text='Eliminar Modpack', fg_color="#000000", width=200)

label_nombre = ctk.CTkLabel(ventana, text='Nombre de jugador:')
label_ram = ctk.CTkLabel(ventana, text='RAM a usar (GB):')

entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Introduce tu nombre", width=200)
entry_ram = ctk.CTkEntry(ventana, placeholder_text="Ej: 4 o 8", width=200)

versiones_instaladas = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directori)
versiones_instaladas_lista = [v['id'] for v in versiones_instaladas]

if versiones_instaladas_lista:
    vers = ctk.StringVar(value=versiones_instaladas_lista[0])
else:
    vers = ctk.StringVar(value='No hay versiones instaladas')
    versiones_instaladas_lista = ['No hay versiones instaladas']

versiones_menu = ctk.CTkOptionMenu(ventana, variable=vers, values=versiones_instaladas_lista, width=300)

# ====================== FUNCIONES ======================

def ask_yes_no(title, text):
    return messagebox.askyesno(title, text)

# ====================== ELIMINAR ======================
def eliminar_version():
    version = vers.get()
    ruta = os.path.join(minecraft_directori, "versions", version)

    if not os.path.exists(ruta):
        messagebox.showerror("Error", "La versión no existe")
        return

    if ask_yes_no("Confirmar", f"¿Eliminar {version}?"):
        shutil.rmtree(ruta)
        messagebox.showinfo("Éxito", "Versión eliminada (reinicia launcher)")

def eliminar_modpack():
    instances_dir = os.path.join(minecraft_directori, "instances")

    if not os.path.exists(instances_dir):
        messagebox.showerror("Error", "No hay modpacks instalados")
        return

    modpacks = os.listdir(instances_dir)

    if not modpacks:
        messagebox.showerror("Error", "No hay modpacks")
        return

    modpack = modpacks[0]  # simple (puedes mejorar luego)

    ruta = os.path.join(instances_dir, modpack)

    if ask_yes_no("Confirmar", f"¿Eliminar modpack {modpack}?"):
        shutil.rmtree(ruta)
        messagebox.showinfo("Éxito", "Modpack eliminado")

# ====================== INSTALAR MODPACK ======================
def instalar_modpack():
    mrpack_path = ctk.CTkInputDialog(
        text="Ruta del archivo .mrpack:",
        title="Instalar Modpack"
    ).get_input()

    if not mrpack_path or not os.path.isfile(mrpack_path):
        messagebox.showerror("Error", "Ruta inválida")
        return

    ventana_load = ventana_carga("Instalando Modpack")

    try:
        minecraft_launcher_lib.mrpack.install_mrpack(
            mrpack_path,
            minecraft_directori,
            callback={"setStatus": print}
        )
        messagebox.showinfo("Éxito", "Modpack instalado")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    ventana_load.destroy()

# ====================== INSTALAR VERSION ======================
def instalar_minecraft():
    version = entry_version.get()

    if not version:
        messagebox.showerror("Error", "Introduce una versión")
        return

    ventana_load = ventana_carga("Instalando versión")

    try:
        minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directori)
        messagebox.showinfo("Éxito", f"{version} instalada")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    ventana_load.destroy()

# ====================== FORGE ======================
def instalar_forge():
    version = entry_version.get()

    ventana_load = ventana_carga("Instalando Forge")

    try:
        forge_version = minecraft_launcher_lib.forge.find_forge_version(version)
        minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directori)
        messagebox.showinfo("Éxito", "Forge instalado")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    ventana_load.destroy()

# ====================== VENTANA VERSION ======================
def abrir_ventana_version(titulo, comando):
    global entry_version
    win = ctk.CTkToplevel(ventana)
    win.geometry('350x180')
    win.title(titulo)
    win.grab_set()

    ctk.CTkLabel(win, text="Versión:").pack(pady=10)
    entry_version = ctk.CTkEntry(win)
    entry_version.pack(pady=10)

    ctk.CTkButton(win, text="Instalar", command=comando).pack(pady=10)

# ====================== EJECUTAR ======================
def ejecutar_minecraft():
    nombre = entry_nombre.get()
    ram = entry_ram.get()
    version = vers.get()

    options = {
        'username': nombre,
        'uuid': '',
        'token': '',
        'jvmArguments': [f"-Xmx{ram}G"],
    }

    ventana.destroy()
    comando = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directori, options)
    subprocess.run(comando)

# ====================== COMANDOS ======================
bt_instalar_version.configure(command=lambda: abrir_ventana_version("Vanilla", instalar_minecraft))
bt_instalar_forge.configure(command=lambda: abrir_ventana_version("Forge", instalar_forge))
bt_instalar_mrpack.configure(command=instalar_modpack)
bt_ejecutar.configure(command=ejecutar_minecraft)
bt_eliminar_version.configure(command=eliminar_version)
bt_eliminar_modpack.configure(command=eliminar_modpack)

# ====================== POSICIONES ======================
label_nombre.place(x=30, y=30)
entry_nombre.place(x=30, y=60)

label_ram.place(x=30, y=110)
entry_ram.place(x=30, y=140)

versiones_menu.place(x=30, y=220)

bt_instalar_version.place(x=380, y=30)
bt_instalar_forge.place(x=380, y=80)
bt_instalar_mrpack.place(x=380, y=130)

bt_eliminar_version.place(x=380, y=180)
bt_eliminar_modpack.place(x=380, y=230)

bt_ejecutar.place(x=250, y=480)

ventana.mainloop()