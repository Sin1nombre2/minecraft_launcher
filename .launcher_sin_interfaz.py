
import minecraft_launcher_lib
import os
import subprocess
import sys

# ====================== CONFIGURACIÓN ======================
user_window = os.environ.get("USERNAME", "Usuario")
minecraft_directori = f"C:/Users/{user_window}/AppData/Roaming/.launchermc"

# Crear carpeta si no existe
os.makedirs(minecraft_directori, exist_ok=True)

# Obtener versiones instaladas
versiones_instaladas = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directori)
versiones_instaladas_lista = [v['id'] for v in versiones_instaladas]

if not versiones_instaladas_lista:
    print("No hay versiones instaladas todavía.")
    versiones_instaladas_lista.append("sin versiones instaladas")


# ====================== FUNCIONES ======================

def ask_yes_no(pregunta: str) -> bool:
    """Función para preguntar Sí/No"""
    while True:
        respuesta = input(f"{pregunta} [S/N]: ").strip().upper()
        if respuesta == "S":
            return True
        elif respuesta == "N":
            return False
        else:
            print("Respuesta inválida. Usa S o N.")


def instalar_minecraft(version: str):
    if not version:
        print("Error: No ingresaste ninguna versión.")
        return
    try:
        print(f"Instalando versión vanilla {version}...")
        minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directori)
        print(f"✅ Versión {version} instalada correctamente.")
    except Exception as e:
        print(f"❌ Error al instalar la versión: {e}")


def instalar_forge(version: str):
    if not version:
        print("Error: No ingresaste ninguna versión.")
        return
    try:
        forge_version = minecraft_launcher_lib.forge.find_forge_version(version)
        if not forge_version:
            print(f"❌ No se encontró Forge para la versión {version}.")
            return
        
        print(f"Instalando Forge para {version}...")
        minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directori)
        print(f"✅ Forge para {version} instalado correctamente.")
    except Exception as e:
        print(f"❌ Error al instalar Forge: {e}")


def instalar_modpack():
    """Instala un modpack en formato .mrpack (Modrinth)"""
    mrpack_path = input("\nIngresa la ruta completa del archivo .mrpack: ").strip()

    if not mrpack_path or not os.path.isfile(mrpack_path):
        print("❌ Error: No se encontró el archivo .mrpack o la ruta es incorrecta.")
        return

    try:
        info = minecraft_launcher_lib.mrpack.get_mrpack_information(mrpack_path)
    except Exception:
        print("❌ Error: El archivo no es un .mrpack válido.")
        return

    # Mostrar información
    print("\n" + "="*50)
    print("INFORMACIÓN DEL MODPACK")
    print("="*50)
    print(f"Nombre:     {info.get('name', 'Desconocido')}")
    print(f"Resumen:    {info.get('summary', 'Sin descripción')}")
    print(f"Versión MC: {info.get('minecraftVersion', 'Desconocida')}")
    print("="*50)

    if not ask_yes_no("¿Deseas instalar este modpack?"):
        return

    # Directorio donde instalar el modpack
    modpack_dir = input("\nRuta donde instalar el modpack (Enter = usar directorio principal): ").strip()
    if not modpack_dir:
        modpack_dir = minecraft_directori

    # Archivos opcionales
    optional_files = []
    for archivo in info.get("optionalFiles", []):
        if ask_yes_no(f"¿Instalar archivo opcional: {archivo}?"):
            optional_files.append(archivo)

    mrpack_options = {"optionalFiles": optional_files}

    # Instalar
    print("\nIniciando instalación del modpack... (puede tardar varios minutos)")
    try:
        minecraft_launcher_lib.mrpack.install_mrpack(
            mrpack_path,
            minecraft_directori,
            modpack_directory=modpack_dir,
            mrpack_install_options=mrpack_options,
            callback={"setStatus": print}   # Muestra progreso
        )
        print("✅ ¡Modpack instalado correctamente!")
    except Exception as e:
        print(f"❌ Error durante la instalación del modpack: {e}")


def ejecutar_minecraft(mine_user: str, version: str, ram: str):
    if not mine_user or not version or not ram:
        print("❌ Error: Faltan datos (usuario, versión o RAM).")
        return

    try:
        options = {
            'username': mine_user,
            'uuid': '',
            'token': '',
            'jvmArguments': [f"-Xmx{ram}G", f"-Xms{ram}G"],
            'launcherVersion': "1.0"
        }

        print(f"\nIniciando Minecraft con la versión: {version}")
        print(f"Usuario: {mine_user} | RAM: {ram}GB")
        print("Cerrando launcher y abriendo el juego...")

        comando = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directori, options)
        subprocess.run(comando)

    except Exception as e:
        print(f"❌ Error al iniciar Minecraft: {e}")


# ====================== MENÚ PRINCIPAL ======================
def main():
    while True:
        print("\n" + "="*60)
        print("       LANZADOR DE MINECRAFT - VERSIÓN CONSOLA")
        print("="*60)
        print("1. Instalar versión de Minecraft (Vanilla)")
        print("2. Instalar Forge")
        print("3. Instalar Modpack (.mrpack)")
        print("4. Ejecutar Minecraft")
        print("5. Salir")
        print("="*60)

        choice = input("\nSelecciona una opción (1-5): ").strip()

        if choice == '1':
            print(f"\nVersiones instaladas: {', '.join(versiones_instaladas_lista)}")
            version = input("Ingresa la versión de Minecraft a instalar (ej: 1.21.3): ").strip()
            instalar_minecraft(version)

        elif choice == '2':
            print(f"\nVersiones instaladas: {', '.join(versiones_instaladas_lista)}")
            version = input("Ingresa la versión de Minecraft para instalar Forge (ej: 1.21.3): ").strip()
            instalar_forge(version)

        elif choice == '3':
            instalar_modpack()

        elif choice == '4':
            mine_user = input("\nIngresa tu nombre de usuario: ").strip()
            print(f"\nVersiones instaladas: {', '.join(versiones_instaladas_lista)}")
            version = input("Selecciona la versión a ejecutar: ").strip()
            ram = input("Ingresa la cantidad de RAM en GB (ej: 6): ").strip()
            ejecutar_minecraft(mine_user, version, ram)

        elif choice == '5':
            print("\n¡Gracias por usar el lanzador! Hasta luego.")
            break

        else:
            print("❌ Opción no válida. Por favor, elige entre 1 y 5.")


if __name__ == "__main__":
    main()
