#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# metadata
"""Vacap."""
__package__ = "vacap"
__version__ = '0.0.1'
__license__ = ' GPLv3+ LGPLv3+ '
__author__ = ' Juan Carlos '
__email__ = ' juancarlospaco@gmail.com '
__url__ = 'https://github.com/juancarlospaco/vacap'
__source__ = ('https://raw.githubusercontent.com/juancarlospaco/'
              'vacap/master/vacap.py')


# imports
import logging as log
import os
import sys
import time
from datetime import datetime
from os import path
from tempfile import gettempdir
import signal
from shutil import make_archive
import winsound

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMenu, QMessageBox, QProgressDialog,
                             QSystemTrayIcon)


##############################################################################

MAKE_BACKUP_FROM = [
    "",
    "",
    "",
]
SAVE_BACKUP_TO = ""


##############################################################################


QSS_STYLE = """
QWidget { background-color: #302F2F; border-radius: 9px }
QWidget:item:selected { background-color: skyblue }
QMenu { border: 1px solid gray; color: silver; font-weight: light }
QMenu::item { font-size: 20px; padding:0; margin:0; margin: 0; border: 0 }
QMenu::item:selected { color: black }
"""


###############################################################################


class Backuper(QProgressDialog):

    """Backuper Dialog with complete informations and progress bar."""

    def __init__(self, destination, origins, parent=None):
        """Init class."""
        super(Backuper, self).__init__(parent)
        self.setWindowTitle(__doc__)
        self._time, self._date = time.time(), datetime.now().isoformat()[:-7]
        self.destination, self.origins = destination, origins
        log.debug("Copying from {} to {}.".format(self._url, self._dst))
        self.template = """<h3>Copiando</h3><hr><table>
        <tr><td><b>Desde:</b></td>      <td>{}</td>
        <tr><td><b>Hacia:  </b></td>      <td>{}</td> <tr>
        <tr><td><b>Tiempo de Inicio:</b></td>   <td>{}</td>
        <tr><td><b>Tiempo Actual:</b></td>    <td>{}</td> <tr>
        <tr><td><b>Tiempo Transcurrido:</b></td>   <td>{}</td>
        <tr><td><b>Faltante:</b></td> <td>{}</td> <tr>
        <tr><td><b>Porcentaje:</b></td>     <td>{}%</td></table><hr>"""
        self.make_backup()
        self.show()
        self.exec_()

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

    def make_backup(self, destination=self.destination, origins=self.origins):
        # try to make backups
        total = len(self.origins)
        try:
            # iterate over lists of folders to backup
            for folder_to_backup in self.origins:
                log.info("BackUp folder {}.".format(folder_to_backup))
                percentage = int(self.origins.index(folder_to_backup) /
                                 len(self.origins) * 100)
                self.setLabelText(self.template.format(
                    folder_to_backup[:99], self.destination.lower()[:99],
                    self._date, datetime.now().isoformat()[:-7],
                    self.seconds_time_to_human_str(time.time() - self._time),
                    len(self.origins) - self.origins.index(folder_to_backup),
                    percentage))
                self.setValue(percentage)
                make_archive(folder_to_backup, "zip", self.destination,
                             logger=log)
        except Exception as reason:
            log.warning(reason)
        finally:
            log.info("Finished BackUp from {} to {}.".format(
                MAKE_BACKUP_FROM , backup_destination))
            self.setValue(100)
            QMessageBox.information(self, __doc__.title(),
                                    "<b>Backup Terminado Correctamente !.")
            winsound.Beep(2500, 1000)

    def update_download_progress(self, bytesReceived, bytesTotal):
        """Calculate statistics and update the UI with them."""
        # Calculate download speed values, with precision from Kb/s to Gb/s
        elapsed = time.clock()
        percentage = int(100.0 * bytesReceived // bytesTotal)
        self.setLabelText(self.template.format(
            self._url.lower()[:99], self._dst.lower()[:99],
            self._date, datetime.now().isoformat()[:-7],
            self.seconds_time_to_human_string(time.time() - self._time),
            self.seconds_time_to_human_string(missing),
            downloaded_MB, total_data_MB, download_speed, percentage))
        self.setValue(percentage)


###############################################################################


class MainWindow(QSystemTrayIcon):

    """Main widget for Vacap, not really a window since not needed."""

    def __init__(self):
        """Tray icon main widget."""
        super(MainWindow, self).__init__()
        log.info("Iniciando el programa Vacap...")
        self.destination, self.origins = SAVE_BACKUP_TO, MAKE_BACKUP_FROM
        self.setIcon(QIcon.fromTheme("edit-paste"))
        self.setToolTip(__doc__ + "\nClick Derecho y 'Hacer Backup'!")
        traymenu = QMenu("Backup")
        self.setIcon(QIcon("edit-new-file"))
        traymenu.setStyleSheet(QSS_STYLE.strip())
        traymenu.addAction(" Hacer Backup ", lambda: self.backup())
        traymenu.setFont(QFont('Oxygen', 20))
        self.setContextMenu(traymenu)
        log.info("Finalizado el inicio del programa Vacap.")
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
        log.info("Folder {} is OK for BackUp.".format(self.destination)
        self.destination = os.path.join(SAVE_BACKUP_TO, t)
        if not os.path.isdir(self.destination):
            os.mkdir(self.destination)
            log.info("Destination Folder now is {}.".format(self.destination)

    def check_origins_folders(self):
        """Check origin folders."""
        log.info("Checking origins folders {}.".format(self.origins))
        self.origins = list(set(self.origins))  # remove repeated items if any
        for folder_to_check in self.origins:
            # if folder is not a folder or is not readable
            if not os.path.isdir(folder_to_check):
                log.critical("Folder {} dont exist.".format(folder_to_check))
                self.origins.remove(folder_to_check)
            elif not os.access(folder_to_check, os.R_OK):
                log.critical("Folder {} not Readable.".format(folder_to_check))
                self.origins.remove(folder_to_check)
            else:
                log.info("Folder {} is OK to BackUp.".format(folder_to_check))

    def backup(self):
        """Backup desde MAKE_BACKUP_FROM hacia SAVE_BACKUP_TO."""
        self.check_destination_folder()
        self.check_origins_folders()
        log.info("Starting to BackUp folders...")
        Backuper(destination=self.destination, origins=self.origins)


###############################################################################


def main():
    """Main Loop."""
    log.basicConfig(level=-1, format="%(levelname)s:%(asctime)s %(message)s")
    log.getLogger().addHandler(log.StreamHandler(sys.stderr))
    log.info(__doc__)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # CTRL+C work to quit app
    app = QApplication(sys.argv)
    app.setApplicationName("vacap")
    app.setOrganizationName("vacap")
    app.setOrganizationDomain("vacap")
    app.setWindowIcon(QIcon.fromTheme("edit-new-file"))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ in '__main__':
    main()
