# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Launcher for an external editor."""

import os
import tempfile

from PyQt5.QtCore import pyqtSignal, QProcess, QObject

from qutebrowser.config import config
from qutebrowser.utils import message, log


class ExternalEditor(QObject):

    """Class to simplify editing a text in an external editor.

    Attributes:
        _text: The current text before the editor is opened.
        _oshandle: The OS level handle to the tmpfile.
        _filehandle: The file handle to the tmpfile.
        _proc: The QProcess of the editor.
        _win_id: The window ID the ExternalEditor is associated with.
    """

    editing_finished = pyqtSignal(str)

    def __init__(self, win_id, parent=None):
        super().__init__(parent)
        self._text = None
        self._oshandle = None
        self._filename = None
        self._proc = None
        self._win_id = win_id

    def _cleanup(self):
        """Clean up temporary files after the editor closed."""
        os.close(self._oshandle)
        try:
            os.remove(self._filename)
        except PermissionError as e:
            # NOTE: Do not replace this with "raise CommandError" as it's
            # executed async.
            message.error(self._win_id,
                          "Failed to delete tempfile... ({})".format(e))

    def on_proc_closed(self, exitcode, exitstatus):
        """Write the editor text into the form field and clean up tempfile.

        Callback for QProcess when the editor was closed.
        """
        log.procs.debug("Editor closed")
        if exitstatus != QProcess.NormalExit:
            # No error/cleanup here, since we already handle this in
            # on_proc_error
            return
        try:
            if exitcode != 0:
                # NOTE: Do not replace this with "raise CommandError" as it's
                # executed async.
                message.error(
                    self._win_id, "Editor did quit abnormally (status "
                                  "{})!".format(exitcode))
                return
            encoding = config.get('general', 'editor-encoding')
            with open(self._filename, 'r', encoding=encoding) as f:
                text = ''.join(f.readlines())
            log.procs.debug("Read back: {}".format(text))
            self.editing_finished.emit(text)
        finally:
            self._cleanup()

    def on_proc_error(self, error):
        """Display an error message and clean up when editor crashed."""
        messages = {
            QProcess.FailedToStart: "The process failed to start.",
            QProcess.Crashed: "The process crashed.",
            QProcess.Timedout: "The last waitFor...() function timed out.",
            QProcess.WriteError: ("An error occurred when attempting to write "
                                  "to the process."),
            QProcess.ReadError: ("An error occurred when attempting to read "
                                 "from the process."),
            QProcess.UnknownError: "An unknown error occurred.",
        }
        # NOTE: Do not replace this with "raise CommandError" as it's
        # executed async.
        message.error(self._win_id,
                      "Error while calling editor: {}".format(messages[error]))
        self._cleanup()

    def edit(self, text):
        """Edit a given text.

        Args:
            text: The initial text to edit.
        """
        if self._text is not None:
            raise ValueError("Already editing a file!")
        self._text = text
        self._oshandle, self._filename = tempfile.mkstemp(text=True)
        if text:
            encoding = config.get('general', 'editor-encoding')
            with open(self._filename, 'w', encoding=encoding) as f:
                f.write(text)
        self._proc = QProcess(self)
        self._proc.finished.connect(self.on_proc_closed)
        self._proc.error.connect(self.on_proc_error)
        editor = config.get('general', 'editor')
        executable = editor[0]
        args = [self._filename if arg == '{}' else arg for arg in editor[1:]]
        log.procs.debug("Calling \"{}\" with args {}".format(executable, args))
        self._proc.start(executable, args)
