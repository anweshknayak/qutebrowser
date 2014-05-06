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

"""The main tabbed browser widget."""

import logging
from functools import partial

from PyQt5.QtWidgets import QApplication, QSizePolicy
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QClipboard, QIcon

import qutebrowser.utils.url as urlutils
import qutebrowser.utils.message as message
import qutebrowser.config.config as config
import qutebrowser.commands.utils as cmdutils
from qutebrowser.widgets._tabwidget import TabWidget
from qutebrowser.widgets.webview import WebView
from qutebrowser.browser.signalfilter import SignalFilter
from qutebrowser.browser.curcommand import CurCommandDispatcher


class TabbedBrowser(TabWidget):

    """A TabWidget with QWebViews inside.

    Provides methods to manage tabs, convenience methods to interact with the
    current tab (cur_*) and filters signals to re-emit them when they occured
    in the currently visible tab.

    For all tab-specific signals (cur_*) emitted by a tab, this happens:
       - the signal gets added to a signal_cache of the tab, so it can be
         emitted again if the current tab changes.
       - the signal gets filtered with _filter_signals and self.cur_* gets
         emitted if the signal occured in the current tab.

    Attributes:
        _url_stack: Stack of URLs of closed tabs.
        _tabs: A list of open tabs.
        _filter: A SignalFilter instance.
        cur: A CurCommandDispatcher instance to dispatch commands to the
             current tab.

    Signals:
        cur_progress: Progress of the current tab changed (loadProgress).
        cur_load_started: Current tab started loading (loadStarted)
        cur_load_finished: Current tab finished loading (loadFinished)
        cur_statusbar_message: Current tab got a statusbar message
                               (statusBarMessage)
        cur_url_changed: Current URL changed (urlChanged)
        cur_link_hovered: Link hovered in current tab (linkHovered)
        cur_scroll_perc_changed: Scroll percentage of current tab changed.
                                 arg 1: x-position in %.
                                 arg 2: y-position in %.
        hint_strings_updated: Hint strings were updated.
                              arg: A list of hint strings.
        quit: The last tab was closed, quit application.
        resized: Emitted when the browser window has resized, so the completion
                 widget can adjust its size to it.
                 arg: The new size.
    """

    cur_progress = pyqtSignal(int)
    cur_load_started = pyqtSignal()
    cur_load_finished = pyqtSignal(bool)
    cur_statusbar_message = pyqtSignal(str)
    cur_url_changed = pyqtSignal('QUrl')
    cur_link_hovered = pyqtSignal(str, str, str)
    cur_scroll_perc_changed = pyqtSignal(int, int)
    hint_strings_updated = pyqtSignal(list)
    quit = pyqtSignal()
    resized = pyqtSignal('QRect')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentChanged.connect(lambda idx:
                                    self.widget(idx).signal_cache.replay())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tabs = []
        self._url_stack = []
        self._filter = SignalFilter(self)
        self.cur = CurCommandDispatcher(self)
        # FIXME adjust this to font size
        self.setIconSize(QSize(12, 12))

    def _connect_tab_signals(self, tab):
        """Set up the needed signals for tab."""
        # filtered signals
        tab.linkHovered.connect(self._filter.create(self.cur_link_hovered))
        tab.loadProgress.connect(self._filter.create(self.cur_progress))
        tab.loadFinished.connect(self._filter.create(self.cur_load_finished))
        tab.page().mainFrame().loadStarted.connect(partial(
            self.on_load_started, tab))
        tab.loadStarted.connect(self._filter.create(self.cur_load_started))
        tab.statusBarMessage.connect(
            self._filter.create(self.cur_statusbar_message))
        tab.scroll_pos_changed.connect(
            self._filter.create(self.cur_scroll_perc_changed))
        tab.urlChanged.connect(self._filter.create(self.cur_url_changed))
        # hintmanager
        tab.hintmanager.hint_strings_updated.connect(self.hint_strings_updated)
        tab.hintmanager.openurl.connect(self.cur.openurl_slot)
        # misc
        tab.titleChanged.connect(self.on_title_changed)
        tab.open_tab.connect(self.tabopen)
        tab.iconChanged.connect(self.on_icon_changed)

    @pyqtSlot(str, bool)
    def tabopen(self, url, background=False):
        """Open a new tab with a given url.

        Inner logic for tabopen and backtabopen.
        Also connect all the signals we need to _filter_signals.

        Args:
            url: The URL to open.
            background: Whether to oepn the tab in the background.
        """
        logging.debug("Opening {}".format(url))
        url = urlutils.qurl(url)
        tab = WebView(self)
        self._connect_tab_signals(tab)
        self._tabs.append(tab)
        self.addTab(tab, urlutils.urlstring(url))
        tab.show()
        tab.openurl(url)
        if not background:
            self.setCurrentWidget(tab)

    def cntwidget(self, count=None):
        """Return a widget based on a count/idx.

        Args:
            count: The tab index, or None.

        Return:
            The current widget if count is None.
            The widget with the given tab ID if count is given.
            None if no widget was found.
        """
        if count is None:
            return self.currentWidget()
        elif 1 <= count <= self.count():
            return self.widget(count - 1)
        else:
            return None

    @cmdutils.register(instance='mainwindow.tabs')
    def tabclose(self, count=None):
        """Close the current/[count]th tab.

        Command handler for :close.

        Args:
            count: The tab index to close, or None

        Emit:
            quit: If last tab was closed and last-close in config is set to
                  quit.
        """
        idx = self.currentIndex() if count is None else count - 1
        tab = self.cntwidget(count)
        if tab is None:
            return
        last_close = config.get('tabbar', 'last-close')
        if self.count() > 1:
            url = tab.url()
            if not url.isEmpty():
                self._url_stack.append(url)
            self.removeTab(idx)
            self._tabs.remove(tab)
        elif last_close == 'quit':
            self.quit.emit()
        elif last_close == 'blank':
            tab.openurl('about:blank')

    @cmdutils.register(instance='mainwindow.tabs', split=False, name='tabopen')
    def tabopen_cmd(self, url):
        """Open a new tab with a given url."""
        self.tabopen(url, background=False)

    @cmdutils.register(instance='mainwindow.tabs', split=False,
                       name='backtabopen')
    def backtabopen_cmd(self, url):
        """Open a new tab in background."""
        self.tabopen(url, background=True)

    @cmdutils.register(instance='mainwindow.tabs', hide=True)
    def tabopencur(self):
        """Set the statusbar to :tabopen and the current URL."""
        url = urlutils.urlstring(self.currentWidget().url())
        message.set_cmd_text(':tabopen ' + url)

    @cmdutils.register(instance='mainwindow.tabs', hide=True)
    def opencur(self):
        """Set the statusbar to :open and the current URL."""
        url = urlutils.urlstring(self.currentWidget().url())
        message.set_cmd_text(':open ' + url)

    @cmdutils.register(instance='mainwindow.tabs', name='undo')
    def undo_close(self):
        """Switch to the previous tab, or skip [count] tabs.

        Command handler for :undo.
        """
        if self._url_stack:
            self.tabopen(self._url_stack.pop())
        else:
            message.error("Nothing to undo!")

    @cmdutils.register(instance='mainwindow.tabs', name='tabprev')
    def switch_prev(self, count=1):
        """Switch to the ([count]th) previous tab.

        Command handler for :tabprev.

        Args:
            count: How many tabs to switch back.
        """
        newidx = self.currentIndex() - count
        if newidx >= 0:
            self.setCurrentIndex(newidx)
        elif config.get('tabbar', 'wrap'):
            self.setCurrentIndex(newidx % self.count())
        else:
            message.error("First tab")

    @cmdutils.register(instance='mainwindow.tabs', name='tabnext')
    def switch_next(self, count=1):
        """Switch to the next tab, or skip [count] tabs.

        Command handler for :tabnext.

        Args:
            count: How many tabs to switch forward.
        """
        newidx = self.currentIndex() + count
        if newidx < self.count():
            self.setCurrentIndex(newidx)
        elif config.get('tabbar', 'wrap'):
            self.setCurrentIndex(newidx % self.count())
        else:
            message.error("Last tab")

    @cmdutils.register(instance='mainwindow.tabs', nargs=(0, 1))
    def paste(self, sel=False, tab=False):
        """Open a page from the clipboard.

        Command handler for :paste.

        Args:
            sel: True to use primary selection, False to use clipboard
            tab: True to open in a new tab.
        """
        clip = QApplication.clipboard()
        mode = QClipboard.Selection if sel else QClipboard.Clipboard
        url = clip.text(mode)
        if not url:
            message.error("Clipboard is empty.")
            return
        logging.debug("Clipboard contained: '{}'".format(url))
        if tab:
            self.tabopen(url)
        else:
            self.cur.openurl(url)

    @cmdutils.register(instance='mainwindow.tabs')
    def tabpaste(self, sel=False):
        """Open a page from the clipboard in a new tab.

        Command handler for :paste.

        Args:
            sel: True to use primary selection, False to use clipboard
        """
        self.paste(sel, True)

    @cmdutils.register(instance='mainwindow.tabs')
    def focus_tab(self, idx=None, count=None):
        """Select the tab given as argument or in count.

        Args:
            idx: The tab index to focus, starting with 1.
        """
        if ((idx is None and count is None) or
                (idx is not None and count is not None)):
            message.error("Either argument or count must be given!")
            return
        try:
            i = int(idx) if idx is not None else count
        except ValueError:
            message.error("Invalid argument: {}".format(idx))
            return
        if 1 <= i <= self.count():
            self.setCurrentIndex(i - 1)
        else:
            message.error("Index out of bounds!")
            return

    @pyqtSlot(str, str)
    def on_config_changed(self, section, option):
        """Update tab config when config was changed."""
        super().on_config_changed(section, option)
        for tab in self._tabs:
            tab.on_config_changed(section, option)

    @pyqtSlot()
    def on_load_started(self, tab):
        """Clear signal cache and icon when a tab started loading.

        Args:
            tab: The tab where the signal belongs to.
        """
        tab.signal_cache.clear()
        self.setTabIcon(self.indexOf(tab), QIcon())

    @pyqtSlot(str)
    def on_title_changed(self, text):
        """Set the title of a tab.

        Slot for the titleChanged signal of any tab.

        Args:
            text: The text to set.
        """
        logging.debug("title changed to '{}'".format(text))
        if text:
            self.setTabText(self.indexOf(self.sender()), text)
        else:
            logging.debug("ignoring title change")

    @pyqtSlot()
    def on_icon_changed(self):
        """Set the icon of a tab.

        Slot for the iconChanged signal of any tab.
        """
        tab = self.sender()
        self.setTabIcon(self.indexOf(tab), tab.icon())

    @pyqtSlot(str)
    def on_mode_left(self, mode):
        """Give focus to tabs if command mode was left."""
        if mode == "command":
            self.setFocus()

    def resizeEvent(self, e):
        """Extend resizeEvent of QWidget to emit a resized signal afterwards.

        Args:
            e: The QResizeEvent

        Emit:
            resize: Always emitted.
        """
        super().resizeEvent(e)
        self.resized.emit(self.geometry())
