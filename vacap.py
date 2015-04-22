#!C:/Python34/pythonw.exe
# -*- coding: utf-8 -*-


"""Vacap."""


##############################################################################
# Instalar:
# https://www.python.org/ftp/python/3.4.2/python-3.4.2.msi
# http://download.qt.io/official_releases/qt/5.4/5.4.1/qt-opensource-windows-x86-mingw491_opengl-5.4.1.exe
# http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.1/PyQt5-5.4.1-gpl-Py3.4-Qt5.4.1-x32.exe


# Configurar:
MAKE_BACKUP_FROM = [
    r"C:\Users\Administrator\Desktop",
    "",
]
SAVE_BACKUP_TO = ""


##############################################################################


# metadata
__version__ = '0.0.1'
__license__ = ' BSD '
__author__ = ' Juan Carlos '
__email__ = ' juancarlospaco@gmail.com '
__url__ = 'https://github.com/juancarlospaco/vacap'
__source__ = ('https://raw.githubusercontent.com/juancarlospaco/'
              'vacap/master/vacap.py')


# imports
import ctypes
import logging as log
import os
import platform
import signal
import sys
import time
from datetime import datetime
from hashlib import sha1
from shutil import copy2, make_archive
from stat import S_IREAD
from tempfile import gettempdir

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMenu, QMessageBox, QProgressDialog,
                             QStyle, QSystemTrayIcon)


##############################################################################


def get_free_space_on_disk_on_gb(folder):
    """Return folder/drive free space (in GigaBytes)."""
    if not os.path.isdir(folder):
        return 0
    if sys.platform.startswith("win"):
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(folder), None,
            None, ctypes.pointer(free_bytes))
        free_space_on_disk_on_gb = free_bytes.value / 1024 / 1024 / 1024
    else:
        stat_folder = os.statvfs(folder)
        fsize_to_gb = stat_folder.f_frsize / 1024 / 1024/ 1024
        free_space_on_disk_on_gb = stat_folder.f_bavail * fsize_to_gb
    return int(free_space_on_disk_on_gb)


class Backuper(QProgressDialog):

    """Backuper Dialog with complete informations and progress bar."""

    def __init__(self, destination, origins, parent=None):
        """Init class."""
        super(Backuper, self).__init__(parent)
        self.setWindowTitle(__doc__)
        self.setWindowIcon(
            QIcon(QApplication.style().standardPixmap(QStyle.SP_DriveFDIcon)))
        # self.setWindowFlags(Qt.Window |  Qt.CustomizeWindowHint |
        #                    Qt.WindowTitleHint | Qt::WindowMinMaxButtonsHint)
        # Qt.FramelessWindow
        self.setCancelButton(None)
        self._time, self._date = time.time(), datetime.now().isoformat()[:-7]
        self.destination, self.origins = destination, origins
        self.template = """<h3>Copia de Seguridad BackUp</h3><hr><table>
        <tr><td><b>Desde:</b></td>      <td>{}</td>
        <tr><td><b>Hacia:  </b></td>      <td>{}</td> <tr>
        <tr><td><b>Tiempo de Inicio:</b></td>   <td>{}</td>
        <tr><td><b>Tiempo Actual:</b></td>    <td>{}</td> <tr>
        <tr><td><b>Tiempo Transcurrido:</b></td>   <td>{}</td>
        <tr><td><b>Faltante:</b></td> <td>{}</td> <tr>
        <tr><td><b>Porcentaje:</b></td>     <td>{}%</td></table><hr>
        <i>Por favor no toque nada hasta que termine, proceso trabajando</i>"""
        self.show()
        self.center()
        self.make_backup()

    def center(self):
        """Center the Window on Current Screen,with MultiMonitor support."""
        window_geometry = self.frameGeometry()
        mousepointer_position = QApplication.desktop().cursor().pos()
        screen = QApplication.desktop().screenNumber(mousepointer_position)
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        window_geometry.moveCenter(centerPoint)
        return bool(not self.move(window_geometry.topLeft()))

    def closeEvent(self, event):
        """Force NO Quit."""
        return event.ignore()

    def seconds_time_to_human_str(self, time_on_seconds=0):
        """Calculate time, with precision from seconds to days."""
        minutes, seconds = divmod(int(time_on_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        human_time_string = ""
        if days:
            human_time_string += "%02d Dias " % days
        if hours:
            human_time_string += "%02d Horas " % hours
        if minutes:
            human_time_string += "%02d Minutos " % minutes
        human_time_string += "%02d Segundos" % seconds
        return human_time_string

    def make_backup(self):
        """Try to make backups."""
        self.make_zip()

    def copy_zip(self, filename):
        """Try to copy ZIP file to final destination."""
        log.info("Checking if {} has Free Space.".format(self.destination))
        free_space_on_disk = get_free_space_on_disk_on_gb(self.destination)
        size_of_the_zip_file = os.stat(filename).st_size / 1024 / 1024 / 1024
        if free_space_on_disk > size_of_the_zip_file:
            log.info("Copying to destination: {}".format(self.destination))
            stored_zip_file = copy2(filename, self.destination)
            log.info("ZIP file archived as {}.".format(stored_zip_file))
            try:
                log.info("Generating SHA1 Checksum hidden file.")
                self.generate_checksum(stored_zip_file)
            except Exception as reason:
                log.warning(reason)
        else:
            log.critical("No more Free Space on Backup Destination folder.")

    def generate_checksum(self, filename):
        """Generate a checksum using SHA1."""
        log.info("Making {} Read-Only.".format(filename))
        os.chmod(filename, S_IREAD)
        with open(filename, "rb") as zip_file:
            checksum = sha1(zip_file.read()).hexdigest()
            log.info("Calculating SHA1 Checksum: {}".format(checksum))
        checksum_file = filename + ".bat"
        with open(checksum_file, "w") as checksum_filename:
            checksum_filename.write(("echo Valid SHA1 Checksum: {}"
                "certutil -hashfile '{}' sha1").format(checksum, filename))
        log.info("Making SHA1 Checksum *.BAT {} Hidden".format(checksum_file))
        ctypes.windll.kernel32.SetFileAttributesW(checksum_file,
                                                  0x02)  # make hidden file

    def make_zip(self):
        """Try to make a ZIP file."""
        try:
            # iterate over lists of folders to backup
            for folder_to_backup in self.origins:
                percentage = int(self.origins.index(folder_to_backup) /
                                 len(self.origins) * 100)
                self.setLabelText(self.template.format(
                    folder_to_backup[:99], self.destination.lower()[:99],
                    self._date, datetime.now().isoformat()[:-7],
                    self.seconds_time_to_human_str(time.time() - self._time),
                    len(self.origins) - self.origins.index(folder_to_backup),
                    percentage))
                self.setValue(percentage)
                log.info("Folder to backup: {}.".format(folder_to_backup))
                make_archive(folder_to_backup, "zip", folder_to_backup,
                             logger=log)
                self.copy_zip(folder_to_backup + ".zip")
        except Exception as reason:
            log.warning(reason)
        else:
            QMessageBox.information(self, __doc__.title(),
                                    "Copia de Seguridad Backup Termino bien.")
        finally:
            log.info("Finished BackUp from {} to {}.".format(
                self.origins, self.destination))


##############################################################################


class MainWindow(QSystemTrayIcon):

    """Main widget for Vacap, not really a window since not needed."""

    def __init__(self, icon, parent=None):
        """Tray icon main widget."""
        super(MainWindow, self).__init__(icon, parent)
        log.info("Iniciando el programa Vacap...")
        self.destination, self.origins = SAVE_BACKUP_TO, MAKE_BACKUP_FROM
        self.setToolTip(__doc__ + "\nClick Derecho y 'Hacer Backup'!")
        traymenu = QMenu("Backup")
        traymenu.setIcon(icon)
        traymenu.addAction(icon, "Hacer Backup", lambda: self.backup())
        traymenu.setFont(QFont("Verdana", 10, QFont.Bold))
        self.setContextMenu(traymenu)
        log.info("Inicio el programa Vacap.")
        self.show()

    def check_destination_folder(self):
        """Check destination folder."""
        log.info("Checking destination folder {}.".format(self.destination))
        # What if destination folder been removed.
        if not os.path.isdir(self.destination):
            log.critical("Folder {} does not exist, saving to {}!.".format(
                self.destination, gettempdir()))
            self.destination = gettempdir()
        # What if destination folder is not Writable by the user.
        if not os.access(self.destination, os.W_OK):
            log.critical("Folder {} permission denied (Not Writable).".format(
                self.destination))
            self.destination = gettempdir()
        # get date and time for folder name
        t = datetime.now().isoformat().lower().split(".")[0].replace(":", "_")
        # prepare a new folder with date-time inside destination folder
        log.info("Folder {} is OK for BackUp.".format(self.destination))
        self.destination = os.path.join(self.destination, t)
        if not os.path.isdir(self.destination):
            os.mkdir(self.destination)
            log.info("Created New Folder {}.".format(self.destination))

    def check_origins_folders(self):
        """Check origin folders."""
        log.info("Checking origins folders {}.".format(self.origins))
        # remove repeated items if any
        self.origins = list(set(self.origins))
        for folder_to_check in self.origins:
            # if folder is not a folder
            if not os.path.isdir(folder_to_check):
                log.critical("Folder {} dont exist.".format(folder_to_check))
                self.origins.remove(folder_to_check)
            # if folder is not readable
            elif not os.access(folder_to_check, os.R_OK):
                log.critical("Folder {} not Readable.".format(folder_to_check))
                self.origins.remove(folder_to_check)
            else:  # folder is ok
                log.info("Folder {} is OK to BackUp.".format(folder_to_check))
        return bool(len(self.origins))

    def backup(self):
        """Backup desde MAKE_BACKUP_FROM hacia SAVE_BACKUP_TO."""
        self.contextMenu().setDisabled(True)
        self.check_destination_folder()

        if self.check_origins_folders():
            log.info("Starting to BackUp folders...")
            Backuper(destination=self.destination, origins=self.origins)
            self.contextMenu().setDisabled(False)
        else:
            log.critical("Vacap is not properly configured, Exiting...")
            sys.exit(1)


##############################################################################


def main():
    """Main Loop."""
    log_file_path = os.path.join(gettempdir(), "vacap.log")
    log.basicConfig(level=-1, filemode="w", filename=log_file_path,
                    format="%(levelname)s:%(asctime)s %(message)s %(lineno)s")
    log.getLogger().addHandler(log.StreamHandler(sys.stderr))
    log.info(__doc__)
    log.debug("LOG File: '{}'.".format(log_file_path))
    log.debug("CONFIG: Make Backup from: {}.".format(MAKE_BACKUP_FROM))
    log.debug("CONFIG: Save Backup to: {}.".format(SAVE_BACKUP_TO))
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # CTRL+C work to quit app
    app = QApplication(sys.argv)
    app.setApplicationName("vacap")
    app.setOrganizationName("vacap")
    app.setOrganizationDomain("vacap")
    icon = QIcon(app.style().standardPixmap(QStyle.SP_DriveFDIcon))
    app.setWindowIcon(icon)
    win = MainWindow(icon)
    win.show()
    sys.exit(app.exec_())


if __name__ in '__main__':
    main()
