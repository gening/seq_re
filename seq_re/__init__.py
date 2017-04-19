# coding:utf-8

"""
N-dimensional Sequence Regular Expression (SEQ RE)
==================================================

This module provides regular expression matching operations on a sequence data structure
like the following::

    seq_m_n = [[str_11, str_12, ... str_1n],
               [str_21, str_22, ... str_2n],
                ...,
               [str_m1, str_m2, ... str_mn]]

The sequence is a homogeneous multidimensional array (齐次多维数组).

A element in each dimension can be considered as either a string, a word, a phrase,
a char, a flag, a token or a tag, and maybe a set of tags or values (multi-values) later.

To match a pattern in an n-dimension sequence,
the SEQ RE patterns is written like one of the examples::

    (/::PERSON/+) /was|has been/ /an/? .{0,3} (/^painter|drawing artist|画家/)

    (?P<name@0,1,2>/::PERSON/) /:VERB be:/ /born/ /on/ (?P<birthday@0:3>(/::NUMBER|MONTH/|/-/){2,3})


1. The syntax of SEQ RE pattern
-------------------------------

A SEQ RE pattern most looks like the ordinary regular express (RE) used in Python,
in which the delimiters ``/.../`` is to indicate a tuple of n dimensions.

1.1 Inside ``/.../``
++++++++++++++++++++

- ``/``

  is the beginning and end delimiter of the tuple, e.g. ``/.../``.

- ``:``

  separates the each dimension in the tuple,
  and the continuous ``:`` at the tail can be omitted,
  e.g. ``/A|B:X:/``, ``/A|B:X/``.

- ``|``

  indicates the different values of one dimension, e.g. ``A|B``.
  These values form a set, and any string in the set will be matched,
  e.g. ``A|B`` will match ``A`` or ``B``.

- ``^``

  be the first character in one dimension,
  all the string that are not in the value set of this dimension will be matched.
  And ``^`` has no special meaning if it’s not the first character of the dimension.
  If ``^`` comes the first character in a dimension but it is a part of a literal string,
  ``\^`` should be used to escape it.

- The priority of above-mentioned operations:

  ``/`` > ``:`` > ``^`` (not literal) > ``|`` > ``^`` (literal) .

- ``\``

  is an escaping symbol before aforementioned special characters.
  Characters other than ``/``, ``:`` or ``\`` lose their special meaning inside ``／...／``.
  To express ``/``, ``:`` or ``|`` in literal, ``\`` should be added before ``/``, ``:`` or ``|``.
  Meanwhile, to represent a literal backslash ``\`` before ``/``, ``:`` or ``|``,
  ``\\`` should be used in the plain text
  that is to say ``'\\\\\\\\'`` must be used in the python code.

1.2 Outside ``/.../``
+++++++++++++++++++++

- The special meanings of special characters in the ordinary RE are only available here,
  but with the limitations discussed below.

  1. ***Not*** support the following escaped special characters:
     ``\\number``, ``\\A``, ``\\b``, ``\\B``, ``\\d``, ``\\D``, ``\\s``, ``\\S``,
     ``\\w``, ``\\W``, ``\\Z``, ``\\a``, ``\\b``, ``\\f``, ``\\n``, ``\\r``, ``\\t``, ``\\v``,
     ``\\x``.

  2. ***Not*** support ``[`` and ``]`` as special characters to indicate a set of characters.

  3. ***Not*** support ranges of characters,
     such as ``[0-9A-Za-z]``, ``[\\u4E00-\\u9FBB\\u3007]`` (Unihan and Chinese character ``〇``)
     used in ordinary RE.

  4. The whitespace and non-special characters are ignored.

- ``.`` is an abbreviation of ``/:::/``.

- The named groups in the pattern are very useful.
  As an extension, a format indices string starts with ``@`` can be followed after the group name,
  to describe which dimensions of the tuples in this group will be output as the result.
  For example: ``(?P<name@d1,d2:d3>...)``,
  in which ``d1``, ``d2``, ``d3`` is the index number of a dimension.

  1. ``@`` means the matched result in all of dimensions will be output.

  2. ``@0,2:4`` means the matched result only in the 0th
     and from 2nd to 3rd of dimensions will be output.

  3. ``@@`` means the pattern of the group itself will be output other than the matched result.

1.3 Boolean logic in the ``/.../``
++++++++++++++++++++++++++++++++++

Given a 3-D sequence ``[[s1, s2, s3], ... ]``,

- AND

  ``/X::Y/`` will match ``s1`` == ``X`` && ``s2`` == ``Y``.
  Its behavior looks like the ordinary RE pattern ``(?:X.Y)``.

- OR

  ``/X::/|/::Y/`` will match ``s1`` == ``X`` || ``s2`` == ``Y``.
  Its behavior looks like the ordinary RE pattern ``(?:X..)|(?:..Y)``

- NOT

  If ``/:^P:/`` will match ``s2`` != ``P``.
  Its behavior looks like the ordinary RE pattern ``(?:.[^P].)``.

  We can also use a negative lookahead assertion of ordinary RE,
  to give a negative covered the following.
  e.g. ``(?!/:P://Q/)/:://::/`` <==> ``/:^P://^Q::/``,
  which behavior looks like the ordinary RE pattern ``(?!(?:.P.))...``.

2. Notes
--------

***Not*** support comparing the number of figures.

Multi-values in one dimension is not supported now, but this feature may be improved later.

3. Examples
-----------

The usage of seq_re module::

    from __future__ import print_function
    import seq_re

    n = 3
    pattern = '(?P<name@0>/::PERSON/+) /is|was|has been/ /a|an/? (?P<attrib@0,1>.{0,3}) (/artist/)'
    seq = [['Vincent van Gogh', 'NNP', 'PERSON'],
           ['was', 'VBD', 'O'],
           ['a', 'DT', 'O'],
           ['Dutch', 'JJ', 'O'],
           ['Post-Impressionist', 'NN', 'O'],
           ['painter', 'NN', 'OCCUPATION'],
           ['who', 'WP', 'O'],
           ['is', 'VBZ', 'O'],
           ['among', 'IN', 'O'],
           ['the', 'DT', 'O'],
           ['most', 'RBS', 'O'],
           ['famous', 'JJ', 'O'],
           ['and', 'CC', 'O'],
           ['influential', 'JJ', 'O'],
           ['figures', 'NNS', 'O'],
           ['in', 'IN', 'O'],
           ['the', 'DT', 'O'],
           ['history', 'NN', 'O'],
           ['of', 'IN', 'O'],
           ['Western art', 'NNP', 'DOMAIN'],
           ['.', '.', 'O']]
    placeholder_dict = {'artist': ['painter', 'drawing artist']}

    sr = seq_re.SeqRegex(n).compile(pattern, **placeholder_dict)
    match = sr.search(seq)
    if match:
        for g in match.group_list:
            print(' '.join(['`'.join(tup) for tup in g[1]]))
        for name in sorted(match.named_group_dict,
                           key=lambda gn: match.named_group_dict[gn][0]):
            print(name, match.format_group_to_str(name, True))

Module contents
===============
Wrapper namespace of global objects.

"""
__author__ = "GE Ning <https://github.com/gening/seq_re>"
__copyright__ = "Copyright (C) 2017 GE Ning"
__license__ = "LGPL-3.0"
__version__ = "0.2"

# global classes and functions
from seq_re_main import SeqRegex
from seq_re_bootstrap import bootstrap

SeqRegex = SeqRegex
"""Wrapper namespace of SeqRegex in `seq_re_main <seq_re_main.html>`_ module."""

bootstrap = bootstrap
"""Wrapper namespace of bootstrap() in `seq_re_bootstrap <seq_re_bootstrap.html>`_ module"""
