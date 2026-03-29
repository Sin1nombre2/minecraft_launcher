import os, subprocess, shutil, uuid, threading
import minecraft_launcher_lib as mcl
import tkinter as tk
from tkinter import ttk

# ====================== CONFIGURACIÓN ======================
user_window = os.environ.get("USERNAME", "Usuario")
minecraft_dir = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"
os.makedirs(minecraft_dir, exist_ok=True)

# Cargar versiones
versiones_lista = [v['id'] for v in mcl.utils.get_installed_versions(minecraft_dir)]
if not versiones_lista:
    versiones_lista = ["Sin versiones instaladas"]

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
            root.destroy()

    threading.Thread(target=tarea, daemon=True).start()
    root.mainloop()


# ====================== FUNCIONES AUXILIARES ======================
def ask_yes_no(pregunta: str) -> bool:
    while True:
        resp = input(f"{pregunta} [S/N]: ").strip().upper()
        if resp in ["S", "SI", "Y"]:
            return True
        if resp in ["N", "NO"]:
            return False
        print("Respuesta inválida. Usa S o N.")


# ====================== INSTALACIONES ======================
def instalar_minecraft(version: str):
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
    mrpack_path = input("\nRuta completa del archivo .mrpack: ").strip()

    if not os.path.isfile(mrpack_path):
        print("❌ Archivo no encontrado o ruta inválida.")
        return

    if not ask_yes_no("¿Instalar este modpack?"):
        return

    def tarea():
        try:
            mcl.mrpack.install_mrpack(
                mrpack_path,
                minecraft_dir,
                callback={"setStatus": print}
            )
            print("✅ Modpack instalado correctamente.")
        except Exception as e:
            print(f"❌ Error instalando modpack: {e}")

    mostrar_barra_carga("Instalando Modpack", tarea)


# ====================== ELIMINAR ======================
def eliminar_version():
    print(f"\nVersiones instaladas: {', '.join(versiones_lista)}")
    version = input("Versión a eliminar: ").strip()

    if version not in versiones_lista or version == "Sin versiones instaladas":
        print("❌ Esa versión no está instalada.")
        return

    ruta = os.path.join(minecraft_dir, "versions", version)

    if ask_yes_no(f"¿Eliminar la versión {version}?"):
        try:
            shutil.rmtree(ruta)
            print(f"✅ Versión {version} eliminada.")
        except Exception as e:
            print(f"❌ Error al eliminar: {e}")


def eliminar_modpack():
    instances_dir = os.path.join(minecraft_dir, "instances")
    if not os.path.exists(instances_dir):
        print("❌ No hay modpacks instalados.")
        return

    modpacks = [d for d in os.listdir(instances_dir) if os.path.isdir(os.path.join(instances_dir, d))]
    if not modpacks:
        print("❌ No hay modpacks instalados.")
        return

    print(f"\nModpacks instalados: {', '.join(modpacks)}")
    nombre = input("Nombre del modpack a eliminar: ").strip()

    ruta = os.path.join(instances_dir, nombre)
    if os.path.exists(ruta) and ask_yes_no(f"¿Eliminar modpack '{nombre}'?"):
        try:
            shutil.rmtree(ruta)
            print(f"✅ Modpack '{nombre}' eliminado.")
        except Exception as e:
            print(f"❌ Error: {e}")


# ====================== EJECUTAR ======================
def ejecutar_minecraft():
    usuario = input("Nombre de usuario: ").strip()
    if not usuario:
        print("❌ Debes ingresar un nombre de usuario.")
        return

    print(f"\nVersiones disponibles: {', '.join(versiones_lista)}")
    version = input("Versión a ejecutar: ").strip()
    ram = input("RAM en GB (ej: 6): ").strip()

    try:
        ram_int = int(ram)
        if ram_int < 1 or ram_int > 32:
            raise ValueError
    except ValueError:
        print("❌ RAM inválida. Usa un número entre 1 y 32.")
        return

    options = {
        'username': usuario,
        'uuid': str(uuid.uuid4()),
        'token': '',
        'jvmArguments': [f"-Xmx{ram}G", f"-Xms{ram}G"]
    }

    try:
        comando = mcl.command.get_minecraft_command(version, minecraft_dir, options)
        print(f"\nIniciando Minecraft {version} con {ram}GB de RAM...")
        subprocess.run(comando)
    except Exception as e:
        print(f"❌ Error al ejecutar Minecraft: {e}")


# ====================== MENÚ PRINCIPAL ======================
def main():
    while True:
        print("\n" + "="*60)
        print("          LANZADOR DE MINECRAFT - Hecho por sin1nombre2   ")
        print("="*60)
        print("1. Instalar Vanilla")
        print("2. Instalar Forge")
        print("3. Instalar Modpack (.mrpack)")
        print("4. Ejecutar Minecraft")
        print("5. Eliminar Versión")
        print("6. Eliminar Modpack")
        print("7. Salir")

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
            print("👋 Saliendo del lanzador...")
            break
        else:
            print("❌ Opción inválida.")

        if opcion != "7":
            input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    main()