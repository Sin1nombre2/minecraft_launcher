
import minecraft_launcher_lib
import os
import subprocess
import sys
import customtkinter as ctk
from tkinter import messagebox

# ====================== CONFIGURACIÓN DE ESTILOS ======================
ctk.set_appearance_mode("dark")      # Modo oscuro
ctk.set_default_color_theme("blue")  # Tema de color

# ====================== VENTANA PRINCIPAL ======================
ventana = ctk.CTk()
ventana.geometry('700x550')
ventana.title('Lanzador de Minecraft - Modpacks y Versiones')
ventana.resizable(False, False)

# Directorio de Minecraft (carpeta personalizada)
user_window = os.environ.get("USERNAME", "Usuario")
minecraft_directori = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"

# Crear carpeta si no existe
os.makedirs(minecraft_directori, exist_ok=True)

# ====================== WIDGETS ======================
# Botones principales
bt_ejecutar = ctk.CTkButton(ventana, text='Iniciar Minecraft', text_color="white", fg_color="#3b82f6", width=200)
bt_instalar_version = ctk.CTkButton(ventana, text='Instalar Versión Vanilla', text_color="white", fg_color="#10b981", width=200)
bt_instalar_forge = ctk.CTkButton(ventana, text='Instalar Forge', text_color="white", fg_color="#ef4444", width=200)
bt_instalar_mrpack = ctk.CTkButton(ventana, text='Instalar Modpack (.mrpack)', text_color="white", fg_color="#8b5cf6", width=200)

# Campos de texto
label_nombre = ctk.CTkLabel(ventana, text='Nombre de jugador:', text_color="white", font=("Arial", 12))
label_ram = ctk.CTkLabel(ventana, text='RAM a usar (GB):', text_color="white", font=("Arial", 12))

entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Introduce tu nombre", width=200)
entry_ram = ctk.CTkEntry(ventana, placeholder_text="Ej: 4 o 8", width=200)

# Menú de versiones instaladas
versiones_instaladas = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directori)
versiones_instaladas_lista = [v['id'] for v in versiones_instaladas]

if versiones_instaladas_lista:
    vers = ctk.StringVar(value=versiones_instaladas_lista[0])
else:
    vers = ctk.StringVar(value='No hay versiones instaladas')
    versiones_instaladas_lista = ['No hay versiones instaladas']

versiones_menu = ctk.CTkOptionMenu(ventana, variable=vers, values=versiones_instaladas_lista, width=300)

# ====================== FUNCIONES ======================

def ask_yes_no(title: str, text: str) -> bool:
    """Ventana de confirmación Sí/No"""
    respuesta = messagebox.askyesno(title, text)
    return respuesta


def instalar_modpack():
    """Instala un archivo .mrpack de Modrinth"""
    mrpack_path = ctk.CTkInputDialog(text="Pega la ruta completa del archivo .mrpack:", title="Instalar Modpack").get_input()

    if not mrpack_path or not os.path.isfile(mrpack_path):
        messagebox.showerror("Error", "No se encontró el archivo .mrpack o la ruta es inválida.")
        return

    try:
        info = minecraft_launcher_lib.mrpack.get_mrpack_information(mrpack_path)
    except Exception:
        messagebox.showerror("Error", "El archivo no es un .mrpack válido.")
        return

    # Mostrar información del modpack
    mensaje_info = f"Nombre: {info.get('name', 'Desconocido')}\n"
    mensaje_info += f"Resumen: {info.get('summary', 'Sin descripción')}\n"
    mensaje_info += f"Versión de Minecraft: {info.get('minecraftVersion', 'Desconocida')}"

    if not ask_yes_no("¿Instalar este modpack?", mensaje_info):
        return

    # Directorio del modpack
    modpack_dir = ctk.CTkInputDialog(
        text="Ruta donde instalar el modpack (dejar vacío para usar el directorio principal):",
        title="Directorio del Modpack"
    ).get_input()

    if not modpack_dir:
        modpack_dir = minecraft_directori

    # Archivos opcionales
    optional_files = []
    for archivo in info.get("optionalFiles", []):
        if ask_yes_no("Archivo opcional", f"¿Quieres instalar el archivo opcional?\n{archivo}"):
            optional_files.append(archivo)

    mrpack_options = {"optionalFiles": optional_files}

    # Instalar
    try:
        messagebox.showinfo("Instalando", "Iniciando instalación del modpack...\nEsto puede tardar varios minutos.")
        minecraft_launcher_lib.mrpack.install_mrpack(
            mrpack_path,
            minecraft_directori,
            modpack_directory=modpack_dir,
            mrpack_install_options=mrpack_options,
            callback={"setStatus": print}   # Muestra progreso en consola
        )
        messagebox.showinfo("¡Éxito!", "El modpack se instaló correctamente.\nCierra y abre para poderlo abrir desde el menu de versiones.")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error durante la instalación:\n{str(e)}")


def instalar_minecraft():
    version = entry_version.get() if 'entry_version' in globals() else None
    if not version:
        messagebox.showerror("Error", "Debes introducir una versión.")
        return

    try:
        minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directori)
        messagebox.showinfo("Éxito", f"Versión {version} instalada correctamente.\nCierra y abre el launcher para actualizar la lista.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo instalar la versión:\n{str(e)}")


def instalar_forge():
    version = entry_version.get() if 'entry_version' in globals() else None
    if not version:
        messagebox.showerror("Error", "Debes introducir una versión de Minecraft.")
        return

    forge_version = minecraft_launcher_lib.forge.find_forge_version(version)
    if forge_version:
        try:
            minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directori)
            messagebox.showinfo("Éxito", f"Forge para {version} instalado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", f"No se encontró Forge para la versión {version}.")


def abrir_ventana_version(titulo, comando):
    global entry_version
    win = ctk.CTkToplevel(ventana)
    win.geometry('350x180')
    win.title(titulo)
    win.grab_set()

    ctk.CTkLabel(win, text="Introduce la versión de Minecraft:", font=("Arial", 12)).pack(pady=10)
    entry_version = ctk.CTkEntry(win, placeholder_text="Ej: 1.21.3", width=200)
    entry_version.pack(pady=10)

    ctk.CTkButton(win, text="Instalar", command=comando).pack(pady=10)


def ejecutar_minecraft():
    nombre = entry_nombre.get().strip()
    ram = entry_ram.get().strip()
    version = vers.get()

    if not nombre:
        messagebox.showerror("Error", "Por favor, introduce tu nombre de jugador.")
        return
    if not ram:
        messagebox.showerror("Error", "Por favor, introduce la cantidad de RAM (ej: 4).")
        return
    if version.startswith("No hay"):
        messagebox.showerror("Error", "No tienes versiones instaladas.")
        return

    try:
        options = {
            'username': nombre,
            'uuid': '',
            'token': '',
            'jvmArguments': [f"-Xmx{ram}G", f"-Xms{ram}G"],
            'launcherVersion': "1.0"
        }

        ventana.destroy()  # Cerrar la ventana antes de lanzar Minecraft
        comando = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directori, options)
        subprocess.run(comando)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar Minecraft:\n{str(e)}")


# ====================== ASIGNAR COMANDOS ======================
bt_instalar_version.configure(command=lambda: abrir_ventana_version("Instalar Versión Vanilla", instalar_minecraft))
bt_instalar_forge.configure(command=lambda: abrir_ventana_version("Instalar Forge", instalar_forge))
bt_instalar_mrpack.configure(command=instalar_modpack)
bt_ejecutar.configure(command=ejecutar_minecraft)

# ====================== POSICIONAMIENTO  ======================
# Columna izquierda
label_nombre.place(x=30, y=30)
entry_nombre.place(x=30, y=60)

label_ram.place(x=30, y=110)
entry_ram.place(x=30, y=140)

versiones_menu.place(x=30, y=220)

# Botones columna derecha
bt_instalar_version.place(x=380, y=30)
bt_instalar_forge.place(x=380, y=80)
bt_instalar_mrpack.place(x=380, y=130)
bt_ejecutar.place(x=250, y=480)

ventana.mainloop()
