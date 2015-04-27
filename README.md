# vacap

Es un sencillo y no por eso, menos potente gestor de backups, pensado para usuarios poco experimentados a la hora de instarlas aplicaciones. "VACAP" funciona en todas las versiones de Windows!!!


Links para bajar paquetes necesarios: 

Hay que tener en cuenta, que OS se está utilizando su arquitectura y versión. Importante!!


**Python 3.x.x**

Por ejemplo para un Win 7 x86 se deberían bajar "Windows x86 MSI installer" del siquiente limk:

 https://www.python.org/ftp/python/3.4.2/python-3.4.2.msi



**Qt 5.x.x**

http://download.qt.io/official_releases/qt/5.4/5.4.1/qt-opensource-windows-x86-mingw491_opengl-5.4.1.exe

**PyQt 5**

http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.1/PyQt5-5.4.1-gpl-Py3.4-Qt5.4.1-x32.exe

**Editar el archivo vacap.py** 

- Especificar los path absolutos entre comillas dobles de las carpetas de la que se hará la copia de seguridad.
- Especificar el path absoluto entre comillas dobles de la carpeta donde se van a guardar las copias *(ZIP)*.



**Correr por primera vez en la consola**

las siguientes lineas:
  
  - `"C:\Python34\python.exe" "C:\.... '<path donde hayas guardado el arch vacap.py'"`
  
  - Aparecerá al lado del reloj un icono con un disco, haciendo click, comienza a ejecutarse el backup.
