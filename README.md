# Lanzador de Minecraft - Consola y Gráfico

Un lanzador ligero para Minecraft desarrollado en Python que permite instalar versiones Vanilla, Forge y **modpacks .mrpack** de Modrinth.

Este repositorio contiene **dos versiones** del lanzador:
- **Versión Consola** (ligera y sin dependencias gráficas)
- **Versión con Interfaz Gráfica** (usando CustomTkinter)

---

## ✨ Características

- Instalar versiones oficiales de Minecraft (Vanilla)
- Instalar Forge
- Instalar modpacks completos en formato **.mrpack** (Modrinth)
- Soporte para archivos opcionales durante la instalación
- Ejecutar Minecraft con RAM personalizada y nombre de usuario
- Dos versiones disponibles: Consola y con Interfaz Gráfica

---

## 📋 Requisitos

- **Python 3.10** o superior
- **Java 17 o 21** instalado y configurado en el PATH (recomendado Java 21)
- Conexión a internet

---

## 🚀 Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/sin1nombre2/minecraft-launcher.git
cd minecraft-launcher

Instala las dependencias necesarias:

pip install -U minecraft-launcher-lib
Para la versión con interfaz gráfica también instala:pip install customtkinter

📂 Archivos del proyecto

launcher.py → Versión Consola (recomendada para la mayoría)
launcher_gui.py → Versión con Interfaz Gráfica


Cómo usar
Versión Consola (launcher.py)
Bashpython launcher.py
Versión con Interfaz Gráfica (launcher_gui.py)
Bashpython launcher_gui.py

📖 Guía de uso
Instalación de Modpacks (.mrpack)

En la versión consola selecciona la opción 3
En la versión gráfica haz clic en "Instalar Modpack (.mrpack)"
Pega la ruta del archivo .mrpack
Elige si deseas instalar los archivos opcionales (se recomienda desactivar los que generan incompatibilidades como Essential, FancyMenu, Xaero, Litematica, etc.)

Problemas comunes

Error SSL durante la instalación: Ejecuta el script como Administrador
Mods incompatibles: Desactiva los archivos opcionales al instalar el modpack
El juego crashea: Revisa la carpeta crash-reports y elimina mods incompatibles de la carpeta mods


👤 Autor

GitHub: @sin1nombre2
Discord: [@sin__nombre__](discord.com/users/886004158149296138)


📌 Próximas mejoras

Soporte completo para Fabric y Quilt
Actualización automática de la lista de versiones
Guardado de configuraciones
Mejora en el manejo de errores SSL
Opción para instalar mods individuales


🤝 Contribuciones
Las contribuciones son bienvenidas. Si encuentras algún bug o tienes ideas para mejorar el lanzador, no dudes en abrir un Issue o hacer un Pull Request.

📄 Licencia
Este proyecto está bajo la licencia MIT.

¡Gracias por usar el Lanzador de Minecraft!
Cualquier duda o sugerencia, contáctame por Discord.
