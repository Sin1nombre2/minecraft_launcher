import os, subprocess, shutil, uuid, threading, zipfile, json, platform
import minecraft_launcher_lib as mcl
import tkinter as tk
from tkinter import ttk

# ====================== CONFIGURACIÓN ======================

def obtener_directorio_minecraft():
    sistema = platform.system()
    base = os.path.expanduser("~")

    if sistema == "Windows":
        return os.path.join(base, "AppData", "Roaming", ".launchermc")
    elif sistema == "Linux":
        return os.path.join(base, ".launchermc")
    elif sistema == "Darwin":
        return os.path.join(base, "Library", "Application Support", ".launchermc")
    else:
        raise Exception("Sistema no soportado")

minecraft_directori = obtener_directorio_minecraft()
instancias_directori = os.path.join(minecraft_directori, "instancias")

os.makedirs(minecraft_directori, exist_ok=True)
os.makedirs(instancias_directori, exist_ok=True)

# Función para obtener versiones instaladas
def obtener_versiones_instaladas():
    """Devuelve lista de versiones instaladas en el directorio principal"""
    versiones = [v['id'] for v in mcl.utils.get_installed_versions(minecraft_directori)]
    if not versiones:
        versiones = ["Sin versiones instaladas"]
    return versiones

# ====================== BARRA DE CARGA ======================
def mostrar_barra_carga(titulo: str, func, *args):
    """Muestra ventana con barra de progreso de forma más estable"""
    root = tk.Tk()
    root.title(titulo)
    root.geometry("360x140")
    root.resizable(False, False)
    root.attributes("-topmost", True)  

    tk.Label(root, text="Procesando, por favor espera...", font=("Arial", 10)).pack(pady=15)

    progress = ttk.Progressbar(root, orient="horizontal", length=320, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(20)

    status_label = tk.Label(root, text="Iniciando...", font=("Arial", 9), fg="gray")
    status_label.pack(pady=5)

    def tarea():
        try:
            func(*args)
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            try:
                # Detener animación y destruir de forma segura
                if root.winfo_exists():
                    progress.stop()
                    root.destroy()
            except:
                pass

    thread = threading.Thread(target=tarea, daemon=True)
    thread.start()

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
                return "".join(c if c.isalnum() or c in " _-()" else "_" for c in name).strip()
    except:
        base = os.path.basename(mrpack_path)
        return os.path.splitext(base)[0]

# ====================== INSTALACIONES ======================
def instalar_minecraft(version: str):
    if not version:
        print("❌ Debes ingresar una versión.")
        return

    def tarea():
        try:
            mcl.install.install_minecraft_version(version, minecraft_directori)
            print(f"✅ Versión {version} instalada correctamente.")
        except Exception as e:
            print(f"❌ Error instalando versión: {e}")

    print(f"Instalando Minecraft {version}...")
    mostrar_barra_carga(f"Instalando {version}", tarea)

def instalar_forge(version: str):
    if not version:
        print("❌ Debes ingresar una versión.")
        return

    def tarea():
        try:
            forge_ver = mcl.forge.find_forge_version(version)
            if not forge_ver:
                print(f"❌ No se encontró Forge para la versión {version}")
                return
            mcl.forge.install_forge_version(forge_ver, minecraft_directori)
            print(f"✅ Forge para {version} instalado correctamente.")
        except Exception as e:
            print(f"❌ Error instalando Forge: {e}")

    print(f"Instalando Forge para {version}...")
    mostrar_barra_carga(f"Instalando Forge - {version}", tarea)

def instalar_neoforge(version: str):
    """Instala NeoForge"""
    if not version:
        print("❌ Debes ingresar una versión.")
        return

    def tarea():
        try:
            neoforge = mcl.mod_loader.get_mod_loader("neoforge")
            
            if not neoforge.is_minecraft_version_supported(version):
                print(f"❌ NeoForge no soporta la versión {version}")
                return

            print(f"Instalando NeoForge para Minecraft {version}...")
            installed_version = neoforge.install(
                version, 
                minecraft_directori,
                callback={"setStatus": print}
            )
            print(f"✅ NeoForge instalado correctamente como: {installed_version}")
        except Exception as e:
            print(f"❌ Error instalando NeoForge: {e}")

    mostrar_barra_carga(f"Instalando NeoForge - {version}", tarea)

def instalar_fabric(version: str):
    if not version:
        print("❌ Debes ingresar una versión.")
        return

    def tarea():
        try:
            loader_version = mcl.fabric.get_latest_loader_version()
            mcl.fabric.install_fabric(version, minecraft_directori, loader_version)
            print(f"✅ Fabric para {version} instalado correctamente.")
        except Exception as e:
            print(f"❌ Error instalando Fabric: {e}")

    print(f"Instalando Fabric para {version}...")
    mostrar_barra_carga(f"Instalando Fabric - {version}", tarea)

def instalar_modpack():
    mrpack_path = input("\nRuta completa del archivo .mrpack: ").strip()

    if not os.path.isfile(mrpack_path):
        print("❌ Archivo no encontrado o ruta inválida.")
        return

    if not ask_yes_no("¿Instalar este modpack?"):
        return

    modpack_name = get_modpack_name(mrpack_path)
    modpack_folder = os.path.join(instancias_directori, modpack_name)

    if os.path.exists(modpack_folder):
        if not ask_yes_no(f"Ya existe la carpeta '{modpack_name}'. ¿Sobrescribir?"):
            print("Instalación cancelada.")
            return

    def tarea():
        try:
            os.makedirs(modpack_folder, exist_ok=True)
            print(f"Instalando modpack en: {modpack_folder}")

            mcl.mrpack.install_mrpack(
                mrpack_path,
                minecraft_directori,
                modpack_directory=modpack_folder,
                callback={"setStatus": print}
            )
            
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
            
            print(f"✅ Modpack '{modpack_name}' instalado correctamente.")
            print(f"   Carpeta: {modpack_folder}")
            print(f"   Versión: {launch_version}")
            
        except Exception as e:
            print(f"❌ Error instalando modpack: {e}")

    mostrar_barra_carga(f"Instalando {modpack_name}", tarea)

# ====================== ELIMINAR ======================
def eliminar_version():
    versiones_lista = obtener_versiones_instaladas()
    print(f"\nVersiones instaladas: {', '.join(versiones_lista)}")
    version = input("Versión a eliminar: ").strip()

    if version not in versiones_lista or version == "Sin versiones instaladas":
        print("❌ Esa versión no está instalada.")
        return

    ruta = os.path.join(minecraft_directori, "versions", version)

    if ask_yes_no(f"¿Eliminar la versión {version}?"):
        try:
            shutil.rmtree(ruta, ignore_errors=True)
            print(f"✅ Versión {version} eliminada.")
        except Exception as e:
            print(f"❌ Error al eliminar: {e}")

def eliminar_modpack():
    if not os.path.exists(instancias_directori):
        print("❌ No hay modpacks instalados.")
        return

    modpacks = [d for d in os.listdir(instancias_directori) if os.path.isdir(os.path.join(instancias_directori, d))]
    if not modpacks:
        print("❌ No hay modpacks instalados.")
        return

    print(f"\nModpacks instalados: {', '.join(modpacks)}")
    nombre = input("Nombre del modpack a eliminar: ").strip()

    ruta = os.path.join(instancias_directori, nombre)
    if os.path.exists(ruta) and ask_yes_no(f"¿Eliminar modpack '{nombre}'?"):
        try:
            shutil.rmtree(ruta, ignore_errors=True)
            print(f"✅ Modpack '{nombre}' eliminado.")
        except Exception as e:
            print(f"❌ Error: {e}")

# ====================== EJECUTAR ======================
def ejecutar_minecraft():
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

    ram_mb = str(ram_int * 1024)

    print("\n¿Qué deseas ejecutar?")
    print("1. Versión Vanilla / Forge / Fabric / NeoForge")
    print("2. Modpack instalado")
    tipo = input("Opción (1/2): ").strip()

    version = ""
    directorio_juego = minecraft_directori

    if tipo == "1":
        versiones_lista = obtener_versiones_instaladas()
        print(f"\nVersiones disponibles: {', '.join(versiones_lista)}")
        version = input("Versión a ejecutar: ").strip()
        if version not in versiones_lista or version == "Sin versiones instaladas":
            print("❌ Versión no encontrada.")
            return

    elif tipo == "2":
        modpacks = [d for d in os.listdir(instancias_directori) if os.path.isdir(os.path.join(instancias_directori, d))]
        if not modpacks:
            print("❌ No hay modpacks instalados en la carpeta de instancias.")
            return

        print(f"\nModpacks disponibles: {', '.join(modpacks)}")
        nombre_modpack = input("Nombre del modpack: ").strip()

        ruta_modpack = os.path.join(instancias_directori, nombre_modpack)
        if not os.path.exists(ruta_modpack):
            print("❌ Modpack no encontrado.")
            return

        info_path = os.path.join(ruta_modpack, "modpack_info.json")
        if not os.path.exists(info_path):
            print("❌ El modpack no tiene información de versión.")
            return

        try:
            with open(info_path, "r", encoding='utf-8') as f:
                modpack_info = json.load(f)
            version = modpack_info["launch_version"]
        except Exception as e:
            print(f"❌ Error leyendo información: {e}")
            return

        directorio_juego = ruta_modpack

    else:
        print("❌ Opción inválida.")
        return

    options = {
        'username': usuario,
        'uuid': str(uuid.uuid4()),
        'token': '',
        'jvmArguments': [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M"]
    }

    if tipo == "2":
        options["gameDirectory"] = directorio_juego

    try:
        comando = mcl.command.get_minecraft_command(version, minecraft_directori, options)
        print(f"\n🚀 Iniciando Minecraft {version} con {ram}GB de RAM...")
        subprocess.run(comando)
    except Exception as e:
        print(f"❌ Error al ejecutar: {e}")

# ====================== INFORMACIÓN ======================
def mostrar_info():
    print("\n" + "="*60)
    print("          INFORMACIÓN DEL SISTEMA")
    print("="*60)
    print(f"Directorio de Minecraft: {minecraft_directori}")
    print(f"Directorio de instancias: {instancias_directori}")
    
    versiones = obtener_versiones_instaladas()
    print(f"Versiones instaladas: {len([v for v in versiones if v != 'Sin versiones instaladas'])}")
    
    if os.path.exists(instancias_directori):
        modpacks = [d for d in os.listdir(instancias_directori) if os.path.isdir(os.path.join(instancias_directori, d))]
        print(f"Modpacks instalados: {len(modpacks)}")
        
        for modpack in modpacks:
            info_path = os.path.join(instancias_directori, modpack, "modpack_info.json")
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

# ====================== MENÚ ======================
def main():
    while True:
        print("\n" + "="*60)
        print("       LANZADOR DE MINECRAFT - Hecho por sin1nombre2")
        print("="*60)
        print("1. Instalar Vanilla")
        print("2. Instalar Forge")
        print("3. Instalar Fabric")
        print("4. Instalar NeoForge")         
        print("5. Instalar Modpack (.mrpack)")
        print("6. Ejecutar Minecraft")
        print("7. Eliminar Versión")
        print("8. Eliminar Modpack")
        print("9. Mostrar Información")
        print("10. Salir")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            version = input("Versión de Minecraft a instalar: ").strip()
            instalar_minecraft(version)
        elif opcion == "2":
            version = input("Versión base para Forge: ").strip()
            instalar_forge(version)
        elif opcion == "3":
            version = input("Versión base para Fabric: ").strip()
            instalar_fabric(version)
        elif opcion == "4":                                 # ← Nueva opción
            version = input("Versión base para NeoForge: ").strip()
            instalar_neoforge(version)
        elif opcion == "5":
            instalar_modpack()
        elif opcion == "6":
            ejecutar_minecraft()
        elif opcion == "7":
            eliminar_version()
        elif opcion == "8":
            eliminar_modpack()
        elif opcion == "9":
            mostrar_info()
        elif opcion == "10":
            print("👋 Saliendo del lanzador...")
            break
        else:
            print("❌ Opción inválida.")

        if opcion != "10":
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
    ║          ✅ Gestión completa de versiones                ║
    ║          ✅ Soporte para NeoForge                        ║
    ║          ✅ Soporte para Fabric                          ║ 
    ║          ✅ Soporte para Forge                           ║     
    ╚══════════════════════════════════════════════════════════╝
    """)
    main()