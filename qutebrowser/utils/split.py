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

"""Our own fork of shlex.split with some added and removed features."""

import re

from qutebrowser.utils import log

## Semantics:
## w/o   quotes: \ escapes everything
## w/i d-quotes: \ escapes only q-quotes and back-slash
## w/i s-quotes: no escaping is done at all

re_dquote  = re.compile(r'"(([^"\\]|\\.)*)"?')
re_squote  = re.compile(r"'(.*?)('|$)")
re_escaped = re.compile(r'\\(.)|(\\)$')
re_esc_quote = re.compile(r'\\([\\"])')
re_outside = re.compile(r"""([^\s\\'"]+)""") # " emacs happy


class EOFError(ValueError):
    def __init__(self, line):
        self.line = line
class UnmatchedQuoteError(EOFError): pass
class UnmatchedSingleQuoteError(UnmatchedQuoteError):
    def __str__(self):
        return "Unmatched single quote: %s" % self.line
class UnmatchedDoubleQuoteError(UnmatchedQuoteError):
    def __str__(self):
        return "Unmatched double quote: %s" % self.line


class Arg:
    """
    Simple helper class for a string-like type which
    distinguishs between 'empty' and 'undefined'.
    """
    def __init__(self):
        self.arg = None

    def __ne__(self, other): return self.arg != other
    #def __eq__(self, other): return self.arg == other	# unused
    #def __repr__(self):      return repr(self.arg)	# unused
    def __str__(self):       return str(self.arg)

    def append(self, text):
        if self.arg is None: self.arg = text
        else:                self.arg += text


def shellwords(line):
    arg_list = []
    i = 0; start = 0; arg = Arg()
    while i < len(line):
        c = line[i]
        if c == '"': # handle double quote:
            match = re_dquote.match(line, i)
            if not match:
                raise UnmatchedDoubleQuoteError(line)
            i = match.end()
            snippet = match.group(1)
            arg.append( re_esc_quote.sub(r'\1', snippet))

        elif c == "'": # handle single quote:
            match = re_squote.match(line, i)
            if not match:
                raise UnmatchedSingleQuoteError(line)
            i = match.end()
            arg.append(match.group(1))
            # there is _no_ escape-charakter within single quotes!

        elif c == "\\": # handle backslash = escape-charakter
            match = re_escaped.match(line, i)
            if not match:
                raise EOFError(line)
            i = match.end()
            escaped = match.group(1)
            if escaped is not None:
                arg.append(escaped)
            else:
                arg.append(match.group(2))

        elif c.isspace(): # handle whitespace
            if arg != None:
                arg_list.append(str(arg))
            arg = Arg()
            while i < len(line) and line[i].isspace():
                i += 1
        else:
            match = re_outside.match(line, i)
            assert match
            i = match.end()
            arg.append(match.group())

    if arg != None: arg_list.append(str(arg))

    return arg_list


def split(s, keep=False):
    """Split a string via ShellLexer.

    Args:
        keep: Whether to keep are special chars in the split output.
    """
    return shellwords(s)
