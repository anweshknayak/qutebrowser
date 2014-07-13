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

"""Qt style to remove Ubuntu focus rectangle uglyness.

We might also use this to do more in the future.
"""

from PyQt5.QtWidgets import QCommonStyle
import functools
import inspect


def make_proxy_style(basestyle, proxycls):

    """Build a new style object based on an existing style and a proxy style.

    Based on http://alexgaudio.com/2011/10/07/dynamic-inheritance-python.html

    Args:
        basecls: The base style object to use.
        proxycls: The proxy style mixin.
    """

    class NewStyle(QCommonStyle, proxycls):
        pass

    obj = NewStyle()

    for attr, _meth in inspect.getmembers(basestyle, inspect.isbuiltin):
        if hasattr(proxycls, attr):
            target = getattr(proxycls, attr)
        else:
            target = getattr(basestyle, attr)
        setattr(NewStyle, attr, functools.partial(target, obj))

    #NewStyle.__name__ = '{}_{}'.format(
    #    basestyle.__class__.__name__, proxycls.__name__)
    return obj
