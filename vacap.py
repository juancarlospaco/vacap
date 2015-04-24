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
    r"C:\Python34",
    r"",
]
SAVE_BACKUP_TO = r""
MAKE_BACKUP_ON_STARTUP = True
MAKE_BACKUP_WHEN_RUNNING_ON_BATTERY = True
MAKE_BACKUP_AT_THIS_HOURS = (12, )


##############################################################################


# imports
import ctypes
from ctypes import wintypes
import logging as log
import os
import shutil
import signal
import sys
import time
from datetime import datetime
from getpass import getuser
from hashlib import sha1
from stat import S_IREAD
from tempfile import gettempdir

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMenu, QProgressDialog, QStyle,
                             QSystemTrayIcon)


##############################################################################


class SYSTEM_POWER_STATUS(ctypes.Structure):

    """CTypes Structure to find out if Windows system is running on battery."""

    _fields_ = [
        ('ACLineStatus', wintypes.BYTE), ('BatteryFlag', wintypes.BYTE),
        ('BatteryLifePercent', wintypes.BYTE), ('Reserved1', wintypes.BYTE),
        ('BatteryLifeTime', wintypes.DWORD),
        ('BatteryFullLifeTime', wintypes.DWORD)]


def windows_is_running_on_battery():
    """Try to find out if MS Windows is running on battery."""
    SYSTEM_POWER_STATUS_P = ctypes.POINTER(SYSTEM_POWER_STATUS)
    GetSystemPowerStatus = ctypes.windll.kernel32.GetSystemPowerStatus
    GetSystemPowerStatus.argtypes = [SYSTEM_POWER_STATUS_P]
    GetSystemPowerStatus.restype = wintypes.BOOL
    status = SYSTEM_POWER_STATUS()
    if not GetSystemPowerStatus(ctypes.pointer(status)):
        log.critical(ctypes.WinError())
        return False
    return not bool(status.ACLineStatus)  # ACLineStatus = 1 is AC


def get_free_space_on_disk_on_gb(folder):
    """Return folder/drive free space (in GigaBytes)."""
    if not os.path.isdir(folder):
        return 0
    else:
        return int(shutil.disk_usage(folder).free / 1024 / 1024 / 1024)


def add_to_startup():
    """Try to add itself to windows startup. Ugly but dont touch Registry."""
    log.debug("Try to add the App to MS Windows startup if needed...")
    path_to_vacap = r"C:\Archivos de Programa\vacap\vacap.py"  # Espanol Window
    if not os.path.isfile(path_to_vacap):
        path_to_vacap = r"C:\Program Files\vacap\vacap.py"  # English Windows
    path_to_python = r"C:\Python34\pythonw.exe"  # Default path
    if not os.path.isfile(path_to_python):
        path_to_python = shutil.which("pythonw.exe")  # Fallback path, check it
        log.warning("Cant find Python, FallBack: {}.".format(path_to_python))
    # the command to run vacap with full path to python and vacap
    bat_content = r'start "Vacap" /LOW "{}" "{}"'.format(path_to_python,
                                                         path_to_vacap)
    log.debug("Command for vacap is: {}.".format(bat_content))
    # find out which start folder exists, depends on windows versions
    win_xp = r"C:\Documents and Settings\All Users\Start Menu\Programs\Startup"
    w = r"C:\Users\{}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    win_78 = w.format(getuser())
    if os.path.isdir(win_78):
        startup_folder = win_78  # is windows 7/8
    else:
        startup_folder = win_xp  # is windows ~XP
    # write a BAT file with command to startup vacap if it not exist
    bat_filename = os.path.join(startup_folder, "vacap.bat")
    log.debug("BAT path is: {}.".format(bat_filename))
    if not os.path.isfile(bat_filename) and os.path.isdir(startup_folder):
        with open(bat_filename, "w", encoding="utf-8") as bat_file:
            bat_file.write(bat_content)
    else:
        log.debug("BAT file already exists.")


class Backuper(QProgressDialog):

    """Backuper Dialog with complete informations and progress bar."""

    def __init__(self, destination, origins, parent=None):
        """Init class."""
        super(Backuper, self).__init__(parent)
        self.setWindowTitle(__doc__)
        self.setWindowIcon(
            QIcon(QApplication.style().standardPixmap(QStyle.SP_DriveFDIcon)))
        self.setWindowFlags(Qt.FramelessWindowHint)
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
        self.setValue(0)
        self.setLabelText(self.template)
        self.make_backup()

    def center(self):
        """Center the Window on Current Screen,with MultiMonitor support."""
        window_geometry = self.frameGeometry()
        mousepointer_position = QApplication.desktop().cursor().pos()
        screen = QApplication.desktop().screenNumber(mousepointer_position)
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        window_geometry.moveCenter(centerPoint)
        self.move(window_geometry.topLeft())

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

    def move_zip(self, filename):
        """Try to move ZIP file to final destination."""
        log.info("Checking if {} has Free Space.".format(self.destination))
        free_space_on_disk = get_free_space_on_disk_on_gb(self.destination)
        size_of_the_zip_file = int(os.stat(filename).st_size
                                   / 1024 / 1024 / 1024)
        log.info("Free Space: ~{} GigaBytes.".format(free_space_on_disk))
        log.info("Size of ZIP: ~{} GigaBytes.".format(size_of_the_zip_file))
        if free_space_on_disk > size_of_the_zip_file:
            log.info("Copying to destination: {}".format(self.destination))
            stored_zip_file = shutil.move(filename, self.destination)
            log.info("ZIP file archived as {}.".format(stored_zip_file))
            try:
                log.info("Generating SHA1 Checksum *.BAT hidden file.")
                self.generate_checksum(stored_zip_file)
            except Exception as reason:
                log.warning(reason)
        else:
            log.critical("No Free Space on Backup Destination folder.")

    def generate_checksum(self, filename):
        """Generate a checksum using SHA1."""
        log.info("Making {} Read-Only.".format(filename))
        os.chmod(filename, S_IREAD)
        with open(filename, "rb") as zip_file:
            checksum = sha1(zip_file.read()).hexdigest()
            log.info("SHA1 Checksum: {}".format(checksum))
        checksum_file = filename + ".bat"
        with open(checksum_file, "w") as checksum_filename:
            checksum_filename.write("""@echo off
                echo Valid SHA1 Checksum: {}
                certutil -hashfile "{}" SHA1""".format(checksum, filename))
        log.info("Making SHA1 Checksum *.BAT {} Hidden".format(checksum_file))
        ctypes.windll.kernel32.SetFileAttributesW(checksum_file,
                                                  0x02)  # make hidden file
        log.info("Making {} Read-Only.".format(checksum_file))
        os.chmod(checksum_file, S_IREAD)

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
                QApplication.processEvents()  # Forces the UI to Update
                log.info("Folder to backup: {}.".format(folder_to_backup))
                shutil.make_archive(folder_to_backup, "zip",
                                    folder_to_backup, logger=log)
                self.move_zip(folder_to_backup + ".zip")
        except Exception as reason:
            log.warning(reason)
        else:
            log.info("Copia de Seguridad Backup Termino bien.")
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
        self.traymenu = QMenu("Backup")
        self.traymenu.setIcon(icon)
        self.traymenu.addAction(icon, "Hacer Backup", lambda: self.backup())
        self.traymenu.setFont(QFont("Verdana", 10, QFont.Bold))
        self.setContextMenu(self.traymenu)
        self.activated.connect(self.click_trap)
        add_to_startup()
        log.info("Inicio el programa Vacap.")
        self.show()
        self.showMessage("Vacap", "Copia de Seguridad Backup funcionando.")
        if MAKE_BACKUP_ON_STARTUP:
            log.info("Running Backup on Start-Up.")
            self.backup()
        if len(MAKE_BACKUP_AT_THIS_HOURS):
            log.info("Running Automatic Backup by Scheduled Hours.")
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.run_backup_by_hour)
            self.timer.start(3600000)  # 1 Hour on Milliseconds

    def click_trap(self, value):
        """Trap the mouse tight click."""
        if value == self.Trigger:  # left click
            self.traymenu.exec_(QCursor.pos())

    def run_backup_by_hour(self):
        """Run Automatic Backup if the actual Hour equals Scheduled Hour."""
        if datetime.now().hour in MAKE_BACKUP_AT_THIS_HOURS:
            log.info("Running Automatic Backup by Scheduled Hour.")
            self.backup()

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
        if not MAKE_BACKUP_WHEN_RUNNING_ON_BATTERY:
            if windows_is_running_on_battery():
                return
        self.contextMenu().setDisabled(True)
        self.check_destination_folder()
        if self.check_origins_folders():
            log.info("Starting to BackUp folders...")
            Backuper(destination=self.destination, origins=self.origins)
            self.contextMenu().setDisabled(False)
            self.showMessage("Vacap", "Copia de Seguridad Backup Termino bien")
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
    log.debug("Free Space on Disk: ~{} GigaBytes.".format(
        get_free_space_on_disk_on_gb(os.path.expanduser("~"))))
    log.debug("Running on Battery: {}".format(windows_is_running_on_battery()))
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
