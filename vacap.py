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
import signal
import sys
import time
from datetime import datetime
from os import path
from shutil import make_archive
from tempfile import gettempdir

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QMenu, QMessageBox, QProgressDialog,
                             QStyle, QSystemTrayIcon)


##############################################################################

MAKE_BACKUP_FROM = [
    "C:/Users/Administrator",
    "",
    "",
]
SAVE_BACKUP_TO = ""


##############################################################################


class Backuper(QProgressDialog):

    """Backuper Dialog with complete informations and progress bar."""

    def __init__(self, destination, origins, parent=None):
        """Init class."""
        super(Backuper, self).__init__(parent)
        self.setWindowTitle(__doc__)
        self._time, self._date = time.time(), datetime.now().isoformat()[:-7]
        self.destination, self.origins = destination, origins
        self.template = """<h3>Copiando</h3><hr><table>
        <tr><td><b>Desde:</b></td>      <td>{}</td>
        <tr><td><b>Hacia:  </b></td>      <td>{}</td> <tr>
        <tr><td><b>Tiempo de Inicio:</b></td>   <td>{}</td>
        <tr><td><b>Tiempo Actual:</b></td>    <td>{}</td> <tr>
        <tr><td><b>Tiempo Transcurrido:</b></td>   <td>{}</td>
        <tr><td><b>Faltante:</b></td> <td>{}</td> <tr>
        <tr><td><b>Porcentaje:</b></td>     <td>{}%</td></table><hr>"""
        self.show()
        self.make_backup()
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

    def make_backup(self):
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
                self.origins, self.destination))


###############################################################################


class MainWindow(QSystemTrayIcon):

    """Main widget for Vacap, not really a window since not needed."""

    def __init__(self):
        """Tray icon main widget."""
        super(MainWindow, self).__init__()
        log.info("Iniciando el programa Vacap...")
        self.destination, self.origins = SAVE_BACKUP_TO, MAKE_BACKUP_FROM
        self.setIcon(QApplication().style().standardPixmap(QStyle.SP_FileIcon))
        self.setToolTip(__doc__ + "\nClick Derecho y 'Hacer Backup'!")
        traymenu = QMenu("Backup")
        self.setIcon(QIcon("edit-new-file"))
        traymenu.addAction(" Hacer Backup ", lambda: self.backup())
        traymenu.setFont(QFont('Oxygen', 20))
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
        return bool(len(self.origins))

    def backup(self):
        """Backup desde MAKE_BACKUP_FROM hacia SAVE_BACKUP_TO."""
        self.check_destination_folder()
        if self.check_origins_folders():
            log.info("Starting to BackUp folders...")
            Backuper(destination=self.destination, origins=self.origins)
        else:
            log.critical("Vacap is not properly configured, Exiting...")
            sys.exit(1)


###############################################################################


def main():
    """Main Loop."""
    log.basicConfig(
        level=-1, format="%(levelname)s:%(asctime)s %(message)s",
        filemode="w", filename=os.path.join(gettempdir(), "vacap.log"))
    log.getLogger().addHandler(log.StreamHandler(sys.stderr))
    log.info(__doc__)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # CTRL+C work to quit app
    app = QApplication(sys.argv)
    app.setApplicationName("vacap")
    app.setOrganizationName("vacap")
    app.setOrganizationDomain("vacap")
    app.setWindowIcon(app.style().standardPixmap(QStyle.SP_FileIcon))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ in '__main__':
    main()
