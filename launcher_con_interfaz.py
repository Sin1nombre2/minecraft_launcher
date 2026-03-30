import os
import subprocess
import shutil
import uuid
import threading
import zipfile
import json
import minecraft_launcher_lib as mcl
import customtkinter as ctk
from tkinter import messagebox, filedialog
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
version_info = {}
# ====================== VENTANA DE CARGA ======================
def ventana_carga(titulo="Instalando..."):
    win = ctk.CTkToplevel(ventana)
    win.geometry("400x180")
    win.title(titulo)
    win.grab_set()
    win.resizable(False, False)
    label_status = ctk.CTkLabel(win, text="Preparando...", font=("Arial", 13), wraplength=350)
    label_status.pack(pady=20)
    barra = ctk.CTkProgressBar(win, width=340)
    barra.pack(pady=10)
    barra.start()
    return win, label_status, barra
# ====================== REFRESH ======================
def refresh_versions():
    global version_info
    version_info = {}
    
    try:
        versiones = mcl.utils.get_installed_versions(minecraft_directori)
        lista_ids = [v['id'] for v in versiones]
        
        modpack_versions = []
        if os.path.exists(instancias_dir):
            for modpack_name in os.listdir(instancias_dir):
                modpack_path = os.path.join(instancias_dir, modpack_name)
                if os.path.isdir(modpack_path):
                    version_file = os.path.join(modpack_path, "version.json")
                    if os.path.exists(version_file):
                        try:
                            with open(version_file, 'r') as f:
                                vdata = json.load(f)
                                v_id = vdata.get('id', f"{modpack_name}")
                                modpack_versions.append(f"[Modpack] {modpack_name}")
                                version_info[f"[Modpack] {modpack_name}"] = {
                                    'type': 'modpack',
                                    'version_id': v_id,
                                    'path': modpack_path
                                }
                        except:
                            pass
        
        all_versions = modpack_versions + lista_ids
        
        if not all_versions:
            all_versions = ['No hay versiones instaladas']
            vers.set('No hay versiones instaladas')
        else:
            vers.set(all_versions[0])
            
        for v_id in lista_ids:
            version_info[v_id] = {
                'type': 'normal',
                'path': minecraft_directori
            }
        
        versiones_menu.configure(values=all_versions)
        
    except Exception as e:
        vers.set('Error al cargar versiones')
        versiones_menu.configure(values=['Error al cargar'])
        print(f"Error refresh_versions: {e}")
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

# ==================== NUEVO BOTÓN ====================
bt_iniciar_modpack = ctk.CTkButton(ventana, text='Iniciar Modpack', fg_color="#8b5cf6", width=220, height=35)

mantener_abierta = ctk.BooleanVar(value=True)
check_mantener = ctk.CTkCheckBox(ventana, text="Mantener launcher abierto después de iniciar", variable=mantener_abierta)
# ====================== INSTALACIÓN EN HILO ======================
def run_installation(install_func, success_msg, error_title="Error"):
    win, label_status, barra = ventana_carga("Instalando...")
    def set_status(text):
        try:
            display_text = text[:60] + "..." if len(text) > 60 else text
            label_status.configure(text=display_text)
        except:
            pass
    def thread_target():
        try:
            install_func(set_status)
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
    try:
        with zipfile.ZipFile(mrpack_path) as z:
            for name in z.namelist():
                if name.endswith('.json') and ('index' in name.lower() or 'manifest' in name.lower()):
                    try:
                        with z.open(name) as f:
                            data = json.load(f)
                            pack_name = data.get("name", data.get("packName", ""))
                            if pack_name:
                                return pack_name.strip().replace(" ", "_").replace("/", "_")
                    except:
                        continue
    except Exception as e:
        print(f"Error leyendo mrpack: {e}")
    
    base = os.path.basename(mrpack_path)
    return os.path.splitext(base)[0].replace(" ", "_")
# ====================== INSTALAR MODPACK ======================
def instalar_modpack():
    mrpack_path = filedialog.askopenfilename(
        title="Seleccionar archivo .mrpack",
        filetypes=[("Modpack Modrinth", "*.mrpack"), ("Todos los archivos", "*.*")]
    )
    if not mrpack_path or not os.path.isfile(mrpack_path):
        return
    modpack_name = get_modpack_name(mrpack_path)
    modpack_folder = os.path.join(instancias_dir, modpack_name)
    if os.path.exists(modpack_folder):
        if not messagebox.askyesno("Carpeta existente",
            f"Ya existe una carpeta llamada '{modpack_name}'.\n¿Quieres sobrescribirla?"):
            return
        shutil.rmtree(modpack_folder, ignore_errors=True)

    def install(set_status):
        os.makedirs(modpack_folder, exist_ok=True)
        
        callback = {
            "setStatus": set_status,
            "setProgress": lambda p: None,
            "setMax": lambda m: None
        }
        
        mcl.mrpack.install_mrpack(
            mrpack_path,
            minecraft_directori,
            modpack_directory=modpack_folder,
            callback=callback
        )
        
        try:
            launch_version = mcl.mrpack.get_mrpack_launch_version(mrpack_path)
            modpack_info = {
                "launch_version": launch_version,
                "mrpack_path": mrpack_path,
                "modpack_name": modpack_name,
                "install_date": str(os.path.getmtime(mrpack_path))
            }
            info_path = os.path.join(modpack_folder, "modpack_info.json")
            with open(info_path, "w", encoding='utf-8') as f:
                json.dump(modpack_info, f, indent=4, ensure_ascii=False)
        except:
            pass

        try:
            os.startfile(modpack_folder)
        except:
            pass

    run_installation(
        install,
        f"Modpack '{modpack_name}' instalado correctamente en:\n{modpack_folder}\n\nSe abrió la carpeta.",
        "Error al instalar Modpack"
    )
# ====================== INSTALAR VANILLA ======================
def instalar_minecraft(version):
    def install(set_status):
        mcl.install.install_minecraft_version(version, minecraft_directori)
    run_installation(install, f"Versión {version} instalada correctamente", "Error al instalar Vanilla")
# ====================== INSTALAR FORGE ======================
def instalar_forge(version):
    def install(set_status):
        forge_versions = mcl.forge.find_forge_version(version)
        if not forge_versions:
            raise Exception(f"No hay Forge disponible para la versión {version}")
        
        forge_version = forge_versions[0] if isinstance(forge_versions, list) else forge_versions
        mcl.forge.install_forge_version(forge_version, minecraft_directori)
    run_installation(install, f"Forge para {version} instalado correctamente", "Error al instalar Forge")
# ====================== ELIMINAR ======================
def eliminar_version():
    version = vers.get()
    if version in ['No hay versiones instaladas', 'Cargando...', 'Error al cargar']:
        messagebox.showerror("Error", "No hay versiones para eliminar")
        return
    
    if version.startswith("[Modpack]"):
        messagebox.showinfo("Info", "Para eliminar un modpack usa el botón 'Eliminar Modpack'")
        return
    ruta = os.path.join(minecraft_directori, "versions", version)
    if messagebox.askyesno("Confirmar", f"¿Eliminar la versión {version}?"):
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
    modpacks = [d for d in os.listdir(instancias_dir)
                if os.path.isdir(os.path.join(instancias_dir, d))]
    
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
        if messagebox.askyesno("Confirmar", f"¿Eliminar el modpack '{selected}'?\nEsta acción no se puede deshacer."):
            try:
                ruta = os.path.join(instancias_dir, selected)
                shutil.rmtree(ruta, ignore_errors=True)
                messagebox.showinfo("Éxito", "Modpack eliminado correctamente")
                refresh_versions()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        win_select.destroy()
    ctk.CTkButton(win_select, text="Eliminar", fg_color="red", command=confirmar).pack(pady=10)
    ctk.CTkButton(win_select, text="Cancelar", command=win_select.destroy).pack()
# ====================== VENTANA VERSIÓN ======================
def abrir_ventana_version(titulo, comando):
    win = ctk.CTkToplevel(ventana)
    win.geometry('380x200')
    win.title(titulo)
    win.grab_set()
    win.resizable(False, False)
    ctk.CTkLabel(win, text="Versión de Minecraft:", font=("Arial", 12)).pack(pady=15)
    entry = ctk.CTkEntry(win, width=220, placeholder_text="Ej: 1.21.3")
    entry.pack(pady=10)
    entry.focus_set()
    def instalar_y_cerrar():
        version = entry.get().strip()
        if version:
            comando(version)
        win.destroy()
    ctk.CTkButton(win, text="Instalar", width=140, command=instalar_y_cerrar).pack(pady=20)
# ====================== NUEVA VENTANA PARA INICIAR MODPACK ======================
def abrir_ventana_iniciar_modpack():
    if not os.path.exists(instancias_dir):
        messagebox.showerror("Error", "No hay modpacks instalados")
        return
    
    modpacks = [d for d in os.listdir(instancias_dir) if os.path.isdir(os.path.join(instancias_dir, d))]
    if not modpacks:
        messagebox.showerror("Error", "No hay modpacks instalados")
        return

    win = ctk.CTkToplevel(ventana)
    win.title("Iniciar Modpack")
    win.geometry("420x280")
    win.grab_set()
    win.resizable(False, False)

    ctk.CTkLabel(win, text="Selecciona el modpack a ejecutar:", font=("Arial", 14)).pack(pady=20)

    var = ctk.StringVar(value=modpacks[0])
    combo = ctk.CTkOptionMenu(win, variable=var, values=modpacks, width=300)
    combo.pack(pady=10)

    def lanzar():
        modpack_name = var.get()
        ruta_modpack = os.path.join(instancias_dir, modpack_name)

        if not os.path.exists(ruta_modpack):
            messagebox.showerror("Error", "Modpack no encontrado")
            win.destroy()
            return

        info_path = os.path.join(ruta_modpack, "modpack_info.json")
        if not os.path.exists(info_path):
            messagebox.showerror("Error", "El modpack no tiene información de versión.\nReinstálalo.")
            win.destroy()
            return

        try:
            with open(info_path, "r", encoding='utf-8') as f:
                modpack_info = json.load(f)
            version_id = modpack_info["launch_version"]
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer modpack_info.json:\n{str(e)}")
            win.destroy()
            return

        # ====================== LANZAMIENTO DEL MODPACK ======================
        nombre = entry_nombre.get().strip()
        ram_str = entry_ram.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Introduce un nombre de jugador")
            win.destroy()
            return
        try:
            ram = int(ram_str)
            if ram < 1 or ram > 32:
                raise ValueError
        except:
            ram = 4

        options = {
            'username': nombre,
            'uuid': str(uuid.uuid4()),
            'token': '',
            'jvmArguments': [f"-Xmx{ram}G", f"-Xms{max(1, ram//2)}G"],
            'gameDirectory': ruta_modpack,
        }

        try:
            comando = mcl.command.get_minecraft_command(version_id, minecraft_directori, options)
            
            def run_mc():
                try:
                    subprocess.run(comando, check=True)
                    if not mantener_abierta.get():
                        ventana.after(0, ventana.destroy)
                except Exception as e:
                    ventana.after(0, lambda: messagebox.showerror("Error", f"Error al ejecutar:\n{str(e)}"))
            
            threading.Thread(target=run_mc, daemon=True).start()
            win.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar comando:\n{str(e)}")
            win.destroy()

    ctk.CTkButton(win, text="Iniciar Modpack", fg_color="#8b5cf6", width=200, command=lanzar).pack(pady=20)
    ctk.CTkButton(win, text="Cancelar", command=win.destroy).pack()

# ====================== EJECUTAR (VERSIÓN NORMAL) ======================
def ejecutar_minecraft():
    nombre = entry_nombre.get().strip()
    ram_str = entry_ram.get().strip()
    version_seleccionada = vers.get()

    if not nombre:
        messagebox.showerror("Error", "Introduce un nombre de jugador")
        return
    
    if version_seleccionada in ['No hay versiones instaladas', 'Cargando...', 'Error al cargar']:
        messagebox.showerror("Error", "No hay ninguna versión instalada")
        return

    try:
        ram = int(ram_str)
        if ram < 1 or ram > 32:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "RAM debe ser un número entre 1 y 32 GB")
        return

    info = version_info.get(version_seleccionada)
    if not info:
        messagebox.showerror("Error", "Información de versión no encontrada")
        return

    if info['type'] == 'modpack':
        version_id = info['version_id']
        game_directory = info['path']
    else:
        version_id = version_seleccionada
        game_directory = minecraft_directori

    options = {
        'username': nombre,
        'uuid': str(uuid.uuid4()),
        'token': '',
        'jvmArguments': [f"-Xmx{ram}G", f"-Xms{max(1, ram//2)}G"],
        'gameDirectory': game_directory,
    }

    try:
        comando = mcl.command.get_minecraft_command(version_id, minecraft_directori, options)
        
        def run_mc():
            try:
                subprocess.run(comando, check=True)
                if not mantener_abierta.get():
                    ventana.after(0, ventana.destroy)
            except Exception as e:
                ventana.after(0, lambda: messagebox.showerror("Error", f"Error al ejecutar:\n{str(e)}"))
        
        threading.Thread(target=run_mc, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror("Error", f"Error al generar comando de inicio:\n{str(e)}")
# ====================== ASIGNAR COMANDOS ======================
bt_instalar_version.configure(command=lambda: abrir_ventana_version("Instalar Vanilla", instalar_minecraft))
bt_instalar_forge.configure(command=lambda: abrir_ventana_version("Instalar Forge", instalar_forge))
bt_instalar_mrpack.configure(command=instalar_modpack)
bt_ejecutar.configure(command=ejecutar_minecraft)
bt_eliminar_version.configure(command=eliminar_version)
bt_eliminar_modpack.configure(command=eliminar_modpack)

# Asignar nuevo botón
bt_iniciar_modpack.configure(command=abrir_ventana_iniciar_modpack)
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
bt_iniciar_modpack.place(x=380, y=280)          
check_mantener.place(x=30, y=480)
bt_ejecutar.place(x=240, y=520)
# ====================== INICIO ======================
refresh_versions()
ventana.mainloop()
