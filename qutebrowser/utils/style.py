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

"""Qt style to remove Ubuntu focus rectangle uglyness.

We might also use this to do more in the future.
"""

import logging
import functools

import sip
from PyQt5.QtWidgets import QCommonStyle, QStyle, QStyleOptionTab, QTabBar


class TabStyle(QCommonStyle):

    """Qt style to remove Ubuntu focus rectangle uglyness.

    Unfortunately PyQt doesn't support QProxyStyle, so we need to do this the
    hard way...

    Based on:

    http://stackoverflow.com/a/17294081
    https://code.google.com/p/makehuman/source/browse/trunk/makehuman/lib/qtgui.py

    Tabs based on:
    http://www.qtcentre.org/wiki/index.php?title=Customizing_QTabWidget%27s_QTabBar

    Attributes:
        _style: The base/"parent" style.
    """

    def __init__(self, style):
        """Initialize all functions we're not overriding.

        This simply calls the corresponding function in self._style.

        Args:
            style: The base/"parent" style.
        """
        self._style = style
        for method in ['drawComplexControl', 'drawItemPixmap',
                       'drawItemText', 'generatedIconPixmap',
                       'hitTestComplexControl', 'itemPixmapRect',
                       'itemTextRect', 'pixelMetric', 'polish', 'styleHint',
                       'subControlRect', 'subElementRect', 'unpolish']:
            target = getattr(self._style, method)
            setattr(self, method, functools.partial(target))
        super().__init__()

    def drawPrimitive(self, element, option, painter, widget=None):
        """Override QCommonStyle.drawPrimitive.

        Call the genuine drawPrimitive of self._style, except when a focus
        rectangle should be drawn.

        Args:
            element: PrimitiveElement pe
            option: const QStyleOption * opt
            painter: QPainter * p
            widget: const QWidget * widget
        """
        if element == QStyle.PE_FrameFocusRect:
            return
        return self._style.drawPrimitive(element, option, painter, widget)

    def sizeFromContents(self, typ, option, size, widget):
        logging.warn("sizeFromContents {}".format(typ))
        s = self._style.sizeFromContents(typ, option, size, widget)
        if typ != QStyle.CT_TabBarTab:
            return s
        logging.warn("sizeFromContents")
        #tab = sip.cast(opt, QWebPage.ErrorPageExtensionOption)
        tab = option
        if tab.shape in [QTabBar.RoundedWest, QTabBar.RoundedEast,
                         QTabBar.TriangularWest, QTabBar.TriangularEast]:
            s.transpose()
        return s

    def drawControl(self, element, option, painter, widget):
        logging.warn("drawControl 1")
        shape_mapping = {
            QTabBar.RoundedWest: QTabBar.RoundedNorth,
            QTabBar.TriangularWest: QTabBar.TriangularNorth,
            QTabBar.RoundedEast: QTabBar.RoundedSouth,
            QTabBar.TriangularEast: QTabBar.TriangularSouth,
        }
        if element != QStyle.CE_TabBarTabLabel:
            return self._style.drawControl(element, option, painter, widget)
        logging.warn("drawControl")
        tab = option
        opt = QStyleOptionTab(tab)
        opt.shape = shape_mapping[tab.shape]
        return self._style.drawControl(element, option, painter, widget)
