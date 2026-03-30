import os
import subprocess
import shutil
import uuid
import threading
import zipfile
import json
import minecraft_launcher_lib as mcl
import tkinter as tk
from tkinter import ttk

# ====================== CONFIGURACIÓN ======================
user_window = os.environ.get("USERNAME", "Usuario")
minecraft_dir = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"
instancias_dir = os.path.join(minecraft_dir, "instancias")

os.makedirs(minecraft_dir, exist_ok=True)
os.makedirs(instancias_dir, exist_ok=True)

# Función para obtener versiones instaladas (se actualiza dinámicamente)
def obtener_versiones_instaladas():
    """Devuelve lista de versiones instaladas en el directorio principal"""
    versiones = [v['id'] for v in mcl.utils.get_installed_versions(minecraft_dir)]
    if not versiones:
        versiones = ["Sin versiones instaladas"]
    return versiones

# ====================== BARRA DE CARGA ======================
def mostrar_barra_carga(titulo: str, func, *args):
    """Muestra ventana con barra de progreso mientras se ejecuta una función"""
    root = tk.Tk()
    root.title(titulo)
    root.geometry("340x120")
    root.resizable(False, False)
    root.attributes("-topmost", True)  

    tk.Label(root, text="Procesando, por favor espera...", font=("Arial", 10)).pack(pady=12)

    progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(15)

    def tarea():
        try:
            func(*args)
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            try:
                root.destroy()
            except:
                pass

    threading.Thread(target=tarea, daemon=True).start()
    root.mainloop()

# ====================== FUNCIONES AUXILIARES ======================
def ask_yes_no(pregunta: str) -> bool:
    """Pregunta sí/no al usuario y devuelve True/False"""
    while True:
        resp = input(f"{pregunta} [S/N]: ").strip().upper()
        if resp in ["S", "SI", "Y"]:
            return True
        if resp in ["N", "NO"]:
            return False
        print("Respuesta inválida. Usa S o N.")

def get_modpack_name(mrpack_path: str) -> str:
    """Extrae el nombre del modpack desde el manifest del .mrpack"""
    try:
        with zipfile.ZipFile(mrpack_path) as z:
            with z.open("modrinth.index.json") as f:
                data = json.load(f)
                name = data.get("name", "Modpack_Desconocido")
                # Limpiar nombre para usarlo como carpeta
                return "".join(c if c.isalnum() or c in " _-()" else "_" for c in name).strip()
    except:
        # Fallback si no se puede leer el manifest
        base = os.path.basename(mrpack_path)
        return os.path.splitext(base)[0]

# ====================== INSTALACIONES ======================
def instalar_minecraft(version: str):
    """Instala una versión vanilla de Minecraft"""
    if not version:
        print("❌ Debes ingresar una versión.")
        return

    def tarea():
        try:
            mcl.install.install_minecraft_version(version, minecraft_dir)
            print(f"✅ Versión {version} instalada correctamente.")
        except Exception as e:
            print(f"❌ Error instalando versión: {e}")

    print(f"Instalando Minecraft {version}...")
    mostrar_barra_carga(f"Instalando {version}", tarea)

def instalar_forge(version: str):
    """Instala Forge para una versión específica"""
    if not version:
        print("❌ Debes ingresar una versión.")
        return

    def tarea():
        try:
            forge_ver = mcl.forge.find_forge_version(version)
            if not forge_ver:
                print(f"❌ No se encontró Forge para la versión {version}")
                return
            mcl.forge.install_forge_version(forge_ver, minecraft_dir)
            print(f"✅ Forge para {version} instalado correctamente.")
        except Exception as e:
            print(f"❌ Error instalando Forge: {e}")

    print(f"Instalando Forge para {version}...")
    mostrar_barra_carga(f"Instalando Forge - {version}", tarea)

def instalar_modpack():
    """Instala un modpack desde archivo .mrpack"""
    mrpack_path = input("\nRuta completa del archivo .mrpack: ").strip()

    if not os.path.isfile(mrpack_path):
        print("❌ Archivo no encontrado o ruta inválida.")
        return

    if not ask_yes_no("¿Instalar este modpack?"):
        return

    modpack_name = get_modpack_name(mrpack_path)
    modpack_folder = os.path.join(instancias_dir, modpack_name)

    # Verificar si ya existe
    if os.path.exists(modpack_folder):
        if not ask_yes_no(f"Ya existe la carpeta '{modpack_name}'. ¿Sobrescribir?"):
            print("Instalación cancelada.")
            return

    def tarea():
        try:
            os.makedirs(modpack_folder, exist_ok=True)
            print(f"Instalando modpack en: {modpack_folder}")

            # Instalar el modpack
            mcl.mrpack.install_mrpack(
                mrpack_path,
                minecraft_dir,
                modpack_directory=modpack_folder,
                callback={"setStatus": print}
            )
            
            # OBTENER Y GUARDAR LA VERSIÓN DE LANZAMIENTO
            launch_version = mcl.mrpack.get_mrpack_launch_version(mrpack_path)
            
            # Guardar metadatos del modpack
            modpack_info = {
                "launch_version": launch_version,
                "mrpack_path": mrpack_path,
                "modpack_name": modpack_name,
                "install_date": str(os.path.getmtime(mrpack_path))
            }
            info_path = os.path.join(modpack_folder, "modpack_info.json")
            with open(info_path, "w", encoding='utf-8') as f:
                json.dump(modpack_info, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Modpack '{modpack_name}' instalado correctamente.")
            print(f"   Carpeta: {modpack_folder}")
            print(f"   Versión: {launch_version}")
            
        except Exception as e:
            print(f"❌ Error instalando modpack: {e}")

    mostrar_barra_carga(f"Instalando {modpack_name}", tarea)

# ====================== ELIMINAR ======================
def eliminar_version():
    """Elimina una versión instalada de Minecraft"""
    versiones_lista = obtener_versiones_instaladas()
    print(f"\nVersiones instaladas: {', '.join(versiones_lista)}")
    version = input("Versión a eliminar: ").strip()

    if version not in versiones_lista or version == "Sin versiones instaladas":
        print("❌ Esa versión no está instalada.")
        return

    ruta = os.path.join(minecraft_dir, "versions", version)

    if ask_yes_no(f"¿Eliminar la versión {version}?"):
        try:
            shutil.rmtree(ruta, ignore_errors=True)
            print(f"✅ Versión {version} eliminada.")
        except Exception as e:
            print(f"❌ Error al eliminar: {e}")

def eliminar_modpack():
    """Elimina un modpack instalado"""
    if not os.path.exists(instancias_dir):
        print("❌ No hay modpacks instalados.")
        return

    modpacks = [d for d in os.listdir(instancias_dir) if os.path.isdir(os.path.join(instancias_dir, d))]
    if not modpacks:
        print("❌ No hay modpacks instalados.")
        return

    print(f"\nModpacks instalados: {', '.join(modpacks)}")
    nombre = input("Nombre del modpack a eliminar: ").strip()

    ruta = os.path.join(instancias_dir, nombre)
    if os.path.exists(ruta) and ask_yes_no(f"¿Eliminar modpack '{nombre}'?"):
        try:
            shutil.rmtree(ruta, ignore_errors=True)
            print(f"✅ Modpack '{nombre}' eliminado.")
        except Exception as e:
            print(f"❌ Error: {e}")

# ====================== EJECUTAR ======================
def ejecutar_minecraft():
    """Ejecuta Minecraft (versión normal o modpack)"""
    usuario = input("Nombre de usuario: ").strip()
    if not usuario:
        print("❌ Debes ingresar un nombre de usuario.")
        return

    ram = input("RAM en GB (ej: 6): ").strip()
    try:
        ram_int = int(ram)
        if ram_int < 1 or ram_int > 32:
            raise ValueError
    except ValueError:
        print("❌ RAM inválida. Usa un número entre 1 y 32.")
        return

    ram_mb = str(ram_int * 1024)  # Convertir GB a MB

    print("\n¿Qué deseas ejecutar?")
    print("1. Versión Vanilla / Forge")
    print("2. Modpack instalado")
    tipo = input("Opción (1/2): ").strip()

    version = ""
    directorio_juego = minecraft_dir  # Por defecto

    if tipo == "1":
        # Ejecutar versión normal
        versiones_lista = obtener_versiones_instaladas()
        print(f"\nVersiones disponibles: {', '.join(versiones_lista)}")
        version = input("Versión a ejecutar: ").strip()
        if version not in versiones_lista or version == "Sin versiones instaladas":
            print("❌ Versión no encontrada.")
            return

    elif tipo == "2":
        # Ejecutar modpack
        modpacks = [d for d in os.listdir(instancias_dir) if os.path.isdir(os.path.join(instancias_dir, d))]
        if not modpacks:
            print("❌ No hay modpacks instalados en la carpeta de instancias.")
            return

        print(f"\nModpacks disponibles: {', '.join(modpacks)}")
        nombre_modpack = input("Nombre del modpack: ").strip()

        ruta_modpack = os.path.join(instancias_dir, nombre_modpack)
        if not os.path.exists(ruta_modpack):
            print("❌ Modpack no encontrado.")
            return

        # LEER INFORMACIÓN DEL MODPACK
        info_path = os.path.join(ruta_modpack, "modpack_info.json")
        if not os.path.exists(info_path):
            print("❌ El modpack no tiene información de versión.")
            print("   Debe reinstalarlo con el código actualizado.")
            return

        try:
            with open(info_path, "r", encoding='utf-8') as f:
                modpack_info = json.load(f)
            version = modpack_info["launch_version"]
        except Exception as e:
            print(f"❌ Error leyendo información: {e}")
            return

        # Verificar que la versión exista en el directorio principal
        versiones_lista = obtener_versiones_instaladas()
        if version not in versiones_lista:
            print(f"❌ La versión {version} no está instalada.")
            print("   reinstale el modpack.")
            return

        directorio_juego = ruta_modpack

    else:
        print("❌ Opción inválida.")
        return

    # Configurar opciones de lanzamiento
    options = {
        'username': usuario,
        'uuid': str(uuid.uuid4()),
        'token': '',
        'jvmArguments': [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M"]
    }

    # IMPORTANTE: Para modpacks, usar gameDirectory
    if tipo == "2":
        options["gameDirectory"] = directorio_juego

    try:
        comando = mcl.command.get_minecraft_command(
            version, 
            minecraft_dir,  # Directorio donde están las versiones
            options
        )
        print(f"\n🚀 Iniciando Minecraft {version} con {ram}GB de RAM...")
        if tipo == "2":
            print(f"   (Carpeta de juego: {directorio_juego})")
        subprocess.run(comando)
    except Exception as e:
        print(f"❌ Error al ejecutar: {e}")

# ====================== INFORMACIÓN DEL SISTEMA ======================
def mostrar_info():
    """Muestra información del sistema y versiones instaladas"""
    print("\n" + "="*60)
    print("          INFORMACIÓN DEL SISTEMA")
    print("="*60)
    print(f"Directorio de Minecraft: {minecraft_dir}")
    print(f"Directorio de instancias: {instancias_dir}")
    
    versiones = obtener_versiones_instaladas()
    print(f"Versiones instaladas: {len([v for v in versiones if v != 'Sin versiones instaladas'])}")
    
    if os.path.exists(instancias_dir):
        modpacks = [d for d in os.listdir(instancias_dir) if os.path.isdir(os.path.join(instancias_dir, d))]
        print(f"Modpacks instalados: {len(modpacks)}")
        
        # Mostrar modpacks con sus versiones
        for modpack in modpacks:
            info_path = os.path.join(instancias_dir, modpack, "modpack_info.json")
            if os.path.exists(info_path):
                try:
                    with open(info_path, "r") as f:
                        info = json.load(f)
                    version = info.get("launch_version", "Desconocida")
                    print(f"  • {modpack} → {version}")
                except:
                    print(f"  • {modpack} → (Error al leer versión)")
            else:
                print(f"  • {modpack} → (Sin información - reinstalar)")
    
    print("="*60)

# ====================== MENÚ PRINCIPAL ======================
def main():
    """Menú principal del launcher"""
    while True:
        print("\n" + "="*60)
        print("       LANZADOR DE MINECRAFT - Hecho por sin1nombre2")
        print("="*60)
        print("1. Instalar Vanilla")
        print("2. Instalar Forge")
        print("3. Instalar Modpack (.mrpack)")
        print("4. Ejecutar Minecraft")
        print("5. Eliminar Versión")
        print("6. Eliminar Modpack")
        print("7. Mostrar Información")
        print("8. Salir")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            version = input("Versión de Minecraft a instalar: ").strip()
            instalar_minecraft(version)
        elif opcion == "2":
            version = input("Versión base para Forge: ").strip()
            instalar_forge(version)
        elif opcion == "3":
            instalar_modpack()
        elif opcion == "4":
            ejecutar_minecraft()
        elif opcion == "5":
            eliminar_version()
        elif opcion == "6":
            eliminar_modpack()
        elif opcion == "7":
            mostrar_info()
        elif opcion == "8":
            print("👋 Saliendo del lanzador...")
            break
        else:
            print("❌ Opción inválida.")

        if opcion != "8":
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          🎮 LANZADOR DE MINECRAFT 🎮                     ║
    ║                                                          ║
    ║          Desarrollado por sin1nombre2                    ║
    ║                                                          ║
    ║          ✅ Soporte para Modpacks .mrpack                ║
    ║          ✅ Aislamiento de instancias                    ║
    ║          ✅ Barra de progreso visual                     ║
    ║          ✅ Gestión completa de versiones                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    main()