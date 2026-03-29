import os, sys, subprocess, threading, shutil, uuid
import minecraft_launcher_lib
import tkinter as tk
from tkinter import ttk, messagebox

# ====================== CONFIGURACIÓN ======================
user_window = os.environ.get("USERNAME", "Usuario")
minecraft_directori = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"

os.makedirs(minecraft_directori, exist_ok=True)

versiones_instaladas = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directori)
versiones_instaladas_lista = [v['id'] for v in versiones_instaladas]

if not versiones_instaladas_lista:
    versiones_instaladas_lista.append("sin versiones instaladas")


# ====================== VENTANA DE CARGA ======================
def mostrar_barra_carga(func, *args):
    root = tk.Tk()
    root.title("Instalando...")
    root.geometry("300x100")
    root.resizable(False, False)

    label = tk.Label(root, text="Descargando / Instalando...")
    label.pack(pady=10)

    progress = ttk.Progressbar(root, orient="horizontal", length=250, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(10)

    def tarea():
        try:
            func(*args)
        finally:
            root.destroy()

    threading.Thread(target=tarea).start()
    root.mainloop()


# ====================== FUNCIONES ======================

def ask_yes_no(pregunta: str) -> bool:
    while True:
        respuesta = input(f"{pregunta} [S/N]: ").strip().upper()
        if respuesta == "S":
            return True
        elif respuesta == "N":
            return False
        else:
            print("Respuesta inválida. Usa S o N.")


def instalar_minecraft(version: str):
    def tarea():
        try:
            minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directori)
            print(f"✅ Versión {version} instalada correctamente.")
        except Exception as e:
            print(f"❌ Error: {e}")

    if version:
        print(f"Instalando versión {version}...")
        mostrar_barra_carga(tarea)
    else:
        print("❌ No ingresaste versión.")


def instalar_forge(version: str):
    def tarea():
        try:
            forge_version = minecraft_launcher_lib.forge.find_forge_version(version)
            if not forge_version:
                print("❌ No se encontró Forge.")
                return

            minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directori)
            print(f"✅ Forge instalado.")
        except Exception as e:
            print(f"❌ Error: {e}")

    if version:
        mostrar_barra_carga(tarea)
    else:
        print("❌ No ingresaste versión.")


def instalar_modpack():
    mrpack_path = input("\nRuta del .mrpack: ").strip()

    if not os.path.isfile(mrpack_path):
        print("❌ Archivo no válido.")
        return

    try:
        info = minecraft_launcher_lib.mrpack.get_mrpack_information(mrpack_path)
    except:
        print("❌ No es un .mrpack válido.")
        return

    modpack_name = info.get('name', 'Modpack').strip()
    modpack_name = "".join(c if c.isalnum() or c in " _-()" else "_" for c in modpack_name)

    if not ask_yes_no("¿Instalar modpack?"):
        return

    instances_dir = os.path.join(minecraft_directori, "instances")
    os.makedirs(instances_dir, exist_ok=True)

    modpack_dir = os.path.join(instances_dir, modpack_name)

    def tarea():
        try:
            minecraft_launcher_lib.mrpack.install_mrpack(
                mrpack_path,
                minecraft_directori,
                modpack_directory=modpack_dir,
                callback={"setStatus": print}
            )
            print("✅ Modpack instalado.")
        except Exception as e:
            print(f"❌ Error: {e}")

    mostrar_barra_carga(tarea)


def eliminar_version():
    print(f"\nVersiones: {', '.join(versiones_instaladas_lista)}")
    version = input("¿Qué versión deseas eliminar?: ").strip()

    ruta = os.path.join(minecraft_directori, "versions", version)

    if os.path.exists(ruta):
        shutil.rmtree(ruta)
        print("✅ Versión eliminada.")
    else:
        print("❌ No existe esa versión.")


def eliminar_modpack():
    instances_dir = os.path.join(minecraft_directori, "instances")

    if not os.path.exists(instances_dir):
        print("❌ No hay modpacks.")
        return

    modpacks = os.listdir(instances_dir)
    print(f"\nModpacks: {', '.join(modpacks)}")

    nombre = input("¿Qué modpack eliminar?: ").strip()
    ruta = os.path.join(instances_dir, nombre)

    if os.path.exists(ruta):
        shutil.rmtree(ruta)
        print("✅ Modpack eliminado.")
    else:
        print("❌ No existe.")


def ejecutar_minecraft(mine_user: str, version: str, ram: str):
    try:
        options = {
            'username': mine_user,
            'uuid': str(uuid.uuid4()),
            'token': '',
            'jvmArguments': [f"-Xmx{ram}G", f"-Xms{ram}G"]
        }

        comando = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directori, options)
        subprocess.run(comando)

    except Exception as e:
        print(f"❌ Error: {e}")


# ====================== MENÚ ======================
def main():
    while True:
        print("\n" + "="*60)
        print("LANZADOR MINECRAFT     Autor:Sin1Nombre2")
        print("="*60)
        print("1. Instalar Vanilla")
        print("2. Instalar Forge")
        print("3. Instalar Modpack")
        print("4. Ejecutar")
        print("5. Eliminar versión")
        print("6. Eliminar modpack")
        print("7. Salir")

        choice = input("Opción: ").strip()

        if choice == '1':
            print("Versiones instaladas:")
            for v in versiones_instaladas_lista:
                print(f"- {v}")
            version = input("Versión a instalar: ")
            instalar_minecraft(version)

        elif choice == '2':
            print("Versiones instaladas:")
            for v in versiones_instaladas_lista:
                print(f"- {v}")
            version = input("Versión a instalar: ")
            instalar_forge(version)

        elif choice == '3':
            instalar_modpack()

        elif choice == '4':
            user = input("Usuario: ")
            print("Versiónes instaladas:")
            for v in versiones_instaladas_lista:
                print(f"- {v}")
            version = input("Versión: ")
            ram = input("RAM (GB): ")
            ejecutar_minecraft(user, version, ram)

        elif choice == '5':
            eliminar_version()

        elif choice == '6':
            eliminar_modpack()

        elif choice == '7':
            break

        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    main()