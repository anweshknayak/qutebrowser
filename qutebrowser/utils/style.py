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

"""Custom Qt styles.

Unfortunately PyQt doesn't support QProxyStyle, so we need to do this the
hard way...
"""

import functools

from PyQt5.QtWidgets import QCommonStyle, QStyle


class AntiUbuntuStyle(QCommonStyle):

    """Qt style to remove Ubuntu focus rectangle uglyness.

    Based on:

    http://stackoverflow.com/a/17294081
    https://code.google.com/p/makehuman/source/browse/trunk/makehuman/lib/qtgui.py

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
        for method in ['drawComplexControl', 'drawControl', 'drawItemPixmap',
                       'drawItemText', 'generatedIconPixmap',
                       'hitTestComplexControl', 'itemPixmapRect',
                       'itemTextRect', 'pixelMetric', 'polish', 'styleHint',
                       'subControlRect', 'subElementRect', 'unpolish',
                       'sizeFromContents']:
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



class ScrollbarHidingStyle(QCommonStyle):

    """Style which hides the QWebView scrollbar.

    Based on:

    http://qt-project.org/faq/answer/how_can_i_change_the_width_of_the_scrollbar_of_qwebview

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
        for method in ['drawComplexControl', 'drawControl', 'drawItemPixmap',
                       'drawItemText', 'generatedIconPixmap',
                       'hitTestComplexControl', 'itemPixmapRect',
                       'itemTextRect', 'polish', 'styleHint',
                       'subControlRect', 'subElementRect', 'unpolish',
                       'sizeFromContents', 'drawPrimitive']:
            target = getattr(self._style, method)
            setattr(self, method, functools.partial(target))
        super().__init__()

    def pixelMetric(self, metric, option, widget):
        if metric == QStyle.PM_ScrollBarExtent and widget is None:
            return 0
        else:
            return super().pixelMetric(metric, option, widget)
