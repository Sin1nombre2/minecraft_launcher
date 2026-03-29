# Lanzador de Minecraft - Consola y Gráfico

Un lanzador ligero para Minecraft desarrollado en Python que permite instalar versiones **Vanilla**, **Forge** y **modpacks .mrpack** de Modrinth.

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

Instala las dependencias:

python -m pip install -U minecraft-launcher-lib
Para la versión con interfaz gráfica también instala:
python -m pip install customtkinter

📂 Archivos del proyecto

.launcher_sin_interfaz.py → Versión Consola
.launcher_con_interfaz.py → Versión con Interfaz Gráfica (recomendada✅)


Cómo usar (powershell)
Versión Consola
abre powershell en donde tienes el archivo y ejecuta: python .launcher_sin_interfaz.py
Versión con Interfaz Gráfica
python .launcher_con_interfaz.py

cómo usar (Visual Studio Code es necesario la extension de python) 
Versión Consola
Solo Ejecuta el script por medio de python
Versión Grafica
Solo Ejecuta el script por medio de python 

📖 Guía de uso
Instalación de Modpacks (.mrpack)

En la versión consola: selecciona la opción 3
En la versión gráfica: haz clic en "Instalar Modpack (.mrpack)"
Pega la ruta completa del archivo .mrpack
Elige si deseas instalar los archivos opcionales (se recomienda responder No a la mayoría, especialmente a: Essential, FancyMenu, Xaero's Minimap, Litematica, JEI, Jade, etc.)


⚠️ Problemas comunes y soluciones

Error SSL durante la instalación → Ejecuta el script como Administrador
Mods incompatibles → Desactiva los archivos opcionales al instalar el modpack
El juego crashea → Revisa la carpeta crash-reports y elimina los mods incompatibles de la carpeta mods


👤 Autor

GitHub: @sin1nombre2
Discord: sin1nombre2


📌 Próximas mejoras

Soporte completo para Fabric y Quilt
Actualización automática de la lista de versiones
Guardado de configuraciones en JSON
Mejora en el manejo de errores SSL
Opción para instalar mods individuales


🤝 Contribuciones
Las contribuciones son bienvenidas. Si encuentras algún bug o tienes ideas para mejorar el lanzador, no dudes en abrir un Issue o hacer un Pull Request.

📄 Licencia
Este proyecto está bajo la licencia MIT.

¡Gracias por usar el Lanzador de Minecraft!
Cualquier duda o sugerencia, contáctame por Discord.
