# coding:utf-8

"""
N-dimensional Sequence Regular Expression (SEQ_RE)
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
the SEQ_RE patterns is written like one of the examples::

    (/::PERSON/+) /was|has been/ /an/? .{0,3} (/^painter|drawing artist|画家/)
    
    (?P<name@0,1,2>/::PERSON/) /:VERB be:/ /born/ /on/ (?P<birthday@0:3>(/::NUMBER|MONTH/|/-/){2,3})


1. The syntax of SEQ_RE pattern
-------------------------------

A SEQ_RE pattern most looks like the ordinary regular express (RE) used in Python,
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

    import seq_re
    
    sr = seq_re.SeqRegex(n).compile(pattern, **placeholder_dict)
    match = sr.search(seq)
    if match:
        for g in match.group_list:
            print ' '.join(['`'.join(g[1])])
        for name in match.named_group_dict.iterkeys():
            print name, match.format_group_to_str(name)


The APIs of SEQ_RE module
=========================

"""
# todo: doc
# todo: deal with multi-value elements in the sequence
# todo: assign an default name uniquely for group

__author__ = "GE Ning <https://github.com/gening/seq_re>"
__copyright__ = "Copyright (C) 2017 GE Ning"
__license__ = "Apache License 2.0"
__version__ = "0.1.4"

import re

import seq_re_parse as sp


class SeqRegex(object):
    """
    Encode each dimension of the pattern and sequence into a single char.
    
    And then form the pattern and sequence into a linear string, 
    which are suitable for using the ordinary regular expression (RE) to match.
    
    Finally, the match result will be located in the original sequence.
    """

    # ######################################## #
    #                                          #
    #  Class Members                           #
    #                                          #
    # ######################################## #

    def __init__(self, ndim):
        if isinstance(ndim, int) and ndim > 0:
            self._ndim = ndim  # the number of dimensions
        else:
            raise ValueError('invalid number of dimensions')
        self._seq_pattern = None  # the original string of pattern
        self._placeholder_dict = None  # the substitutions of placeholders in the pattern
        self._map_encode = dict()  # encoding dict：a phrase (words) => a single char of unicode
        # self._map_decode = dict()  # decoding dict：a single char of unicode => original words
        self._map_counter = 0  # counter：the number of different phrases
        self._parser = sp.SeqRegexParser()  # the SeqRegexPasrse object
        self._regex = None  # the ordinary regular expression object: RegexObject

    @property
    def ndim(self):
        """The number of dimensions"""
        return self._ndim

    @property
    def seq_pattern(self):
        """The original string of pattern"""
        return self._seq_pattern

    def _clear(self):
        self._seq_pattern = None
        self._placeholder_dict = None
        self._map_encode.clear()
        # self._map_decode.clear()
        self._map_counter = 0
        self._parser.__init__()
        self._regex = None

    # ######################################## #
    #                                          #
    #  Encoding Functions                      #
    #                                          #
    # ######################################## #

    def _encode_str(self, decoded_str, default=None):
        """Encode a string.
        
        :param decoded_str: a string to be encoded
        :param default: the default string to replace the string which has not been encoded
        :return: an encoded string if default is not None else default
        """
        if decoded_str in self._map_encode:
            return self._map_encode[decoded_str]
        elif default is None:
            # 映射到从'中'字开始连续的unicode字符
            # continuously map to the unicode chars from the chinese u'中'
            # ord(u'中') = 20013
            # sys.maxunicode = 65535 or 1114111
            # so, at least nearly 35k unicode characters can be used to encode
            # words, phrases, tokens, tags in a pattern.
            # and the words from text to look up, which are not occurred in the pattern,
            # are ignored during the encoding.
            try:
                encoded_str = unichr(ord(u'中') + self._map_counter)
            except ValueError:
                raise ValueError(u'too many different string')
            self._map_encode[decoded_str] = encoded_str
            # self._map_decode[encoded_str] = decoded_str
            self._map_counter += 1
            return encoded_str
        else:
            return default

    def _encode_pattern(self):
        """Encode the original string SEQ_RE pattern into a equivalent of ordinary RE pattern.
        
        :return: a ordinary RE string
        """
        parsed = self._parser.parse(self._ndim, self._seq_pattern, **self._placeholder_dict)
        # transform _pattern_stack into pseudo regular expression string for check or test
        pattern_str_list = []
        if parsed:
            for ix in xrange(len(parsed)):
                flag, string, pos = parsed[ix]
                if flag == sp.Flags.LITERAL:
                    pattern_str_list.append(self._encode_str(string))
                elif string is not None:
                    pattern_str_list.append(string)
        # for debug
        # print self._parser.dump()
        # print u''.join(pattern_str_list)
        return u''.join(pattern_str_list)

    def _encode_sequence(self, nd_sequence):
        """Encode the n-dimension sequence into a linear of string for matching the pattern"""
        self._nd_sequence = nd_sequence
        stack_encoded = []
        default_encoded_str = None if self._parser.exists_negative_set() else u'.'
        for nd_tuple in nd_sequence:
            for element in nd_tuple:
                stack_encoded.append(self._encode_str(element, default_encoded_str))
        return u''.join(stack_encoded)

    # ######################################## #
    #                                          #
    #  Result Objects                          #
    #                                          #
    # ######################################## #

    class SeqRegexObject(object):
        """The class wraps the SeqRegex itself for the simplified use."""

        __slots__ = ('_outer',)

        def __init__(self, outer_class):
            assert isinstance(outer_class, SeqRegex)
            self._outer = outer_class

        def finditer(self, nd_sequence):
            return self._outer.finditer(self._outer._seq_pattern, nd_sequence)

        def search(self, nd_sequence):
            return self._outer.search(self._outer._seq_pattern, nd_sequence)

        def findall(self, nd_sequence):
            return self._outer.findall(self._outer._seq_pattern, nd_sequence)

        def is_useless_for(self, nd_sequence):
            return self._outer.is_useless_for(nd_sequence)

    class SeqMatchObject(object):
        """The class manages the match results that the SeqRegex returned, 
        and the matched group can be acquired by the group_list or named_group_dict.
        """

        __slots__ = ('group_list', 'named_group_dict', 'sq_re')

        def __init__(self, outer_class):
            # public member
            self.group_list = []
            """All indexed groups matched in a result, including named and unnamed groups"""
            self.named_group_dict = dict()  # add index to consider as collections.OrderedDict
            """All named groups matched in a result"""
            self.sq_re = outer_class  # The outer class is the SeqRegex itself
            """The SeqRegex Instance which returned this SeqMatchObject Instance"""

        def format_group_to_str(self, group_name, trimmed=True):
            """Output a named group matched in the result, according the format string 
            indicated after the group name in the original pattern string.
            
            :param group_name: The group name
            :param trimmed: Remove the group name and parentheses if trimmed == True else keep them
            :return: A string of the matched result
            """
            formatted_str_list = []

            def formatter(nd_elements):
                formatted_str = u':'.join([u'|'.join(fs) if hasattr(fs, '__iter__') else
                                           unicode(fs) for fs in
                                           nd_elements])  # support multi-value element
                formatted_str = formatted_str.rstrip(u':')
                if len(formatted_str) > 0:
                    return u'/%s/' % formatted_str
                else:
                    return u'.'

            if group_name in self.named_group_dict:
                group_index, match_sequence, _, _ = self.named_group_dict[group_name]
                # noinspection PyProtectedMember
                if group_name in self.sq_re._parser.named_group_format_indices:
                    # noinspection PyProtectedMember
                    format_indices = self.sq_re._parser.named_group_format_indices[group_name]
                    if format_indices is not None:
                        for match_tuple in match_sequence:
                            formatted_tuple = [u''] * self.sq_re.ndim
                            for low, high in format_indices:
                                formatted_tuple[low: high] = match_tuple[low: high]
                            formatted_str_list.append(formatter(formatted_tuple))
                    else:
                        # noinspection PyProtectedMember
                        # `@@` => get pattern itself
                        pattern_sub = self.sq_re._parser.get_pattern_by_name(group_name)
                        # `(?:P<name@@>pattern_sub)`
                        if trimmed:
                            # `pattern_sub`
                            pattern_sub = pattern_sub[pattern_sub.find('>') + 1: -1]
                        formatted_str_list.append(pattern_sub)
                else:
                    # default formatter
                    for match_tuple in match_sequence:
                        formatted_str_list.append(formatter(match_tuple))
            return ' '.join(formatted_str_list)

    # ######################################## #
    #                                          #
    #  Regex Matching                          #
    #                                          #
    # ######################################## #

    def compile(self, seq_pattern, **placeholder_dict):
        """Compile a SEQ_RE pattern into a ordinary RE object.
        
        :param seq_pattern: A string of SEQ_RE pattern
        :param placeholder_dict: {placeholder_name1: p1, placeholder_name2: p2}  
                                 in which p1, p2 could be a str or a list of str.
        :return: A SeqRegexObject Instance
        """
        self._clear()
        self._seq_pattern = seq_pattern
        self._placeholder_dict = placeholder_dict
        regex_pattern = self._encode_pattern()
        self._regex = re.compile(regex_pattern)
        return self.SeqRegexObject(self)

    def finditer(self, seq_pattern, nd_sequence):
        """
        Return an iterator yielding SeqMatchObject instances 
        over all non-overlapping matches for the SEQ_RE pattern in n-dimension sequence.
        
        The matched group can be acquired by the group_list or named_group_dict 
        of SeqMatchObject returned.
        
        :param seq_pattern: A string of SEQ_RE pattern
        :param nd_sequence: An N-dimensional Sequence
        :return: An iterator which generates a SeqMatchObject Instance
        """
        if seq_pattern != self._seq_pattern:
            self.compile(seq_pattern)

        text_line = self._encode_sequence(nd_sequence)
        for match in self._regex.finditer(text_line):
            match_object = SeqRegex.SeqMatchObject(self)
            # The entire match (group_index = 0) and Parenthesized subgroups
            for group_index in range(len(match.groups()) + 1):
                start = match.start(group_index) / self._ndim
                end = match.end(group_index) / self._ndim
                match_object.group_list.append((group_index,
                                                nd_sequence[start:end], start, end))
            # Named subgroups
            for group_name, group_index in self._regex.groupindex.items():
                start = match.start(group_index) / self._ndim
                end = match.end(group_index) / self._ndim
                # group_index is needed to sort the named groups in order
                match_object.named_group_dict[group_name] = (group_index,
                                                             nd_sequence[start:end], start, end)
            yield match_object

    def search(self, seq_pattern, nd_sequence):
        """
        Scan through n-dimension sequence looking for 
        the first location where the SEQ_RE pattern produces a match, 
        and return a corresponding SeqMatchObject instance.
        
        :param seq_pattern: A string of SEQ_RE pattern
        :param nd_sequence: An N-dimensional Sequence
        :return: A SeqMatchObject Instance if match else None
        """
        return next(self.finditer(seq_pattern, nd_sequence), None)

    def findall(self, seq_pattern, nd_sequence):
        """Similar to the finditer() function.
        
        :param seq_pattern: A string of SEQ_RE pattern
        :param nd_sequence: An N-dimensional Sequence
        :return: A list of SeqMatchObject Instance
        """
        return [self.finditer(seq_pattern, nd_sequence)]

    def is_useless_for(self, nd_sequence):
        """For preliminary screening the seq in advanced, 
        to check whether regular expression has no chance of success.
        
        :param nd_sequence: An N-dimensional Sequence
        :return: True if SEQ_RE no chance of success else False
        """
        # for literals in the negative set,
        # not sure whether they should or should not be in the seq.
        # for literals in the positive set,
        # any one could be in the seq,
        # and their order cannot be determined in advanced.
        # fixme: if seq_pattern is None
        positive_sets = self._parser.get_positive_literal_sets()
        useless = True
        for each_set in positive_sets:
            useless = True
            for literal in each_set:
                # seq.find(literal) > -1 but seq is not a string
                for nd_tuple in nd_sequence:
                    for e in nd_tuple:
                        # list, set
                        if hasattr(e, '__iter__'):
                            if literal in e:
                                useless = False
                                break
                        # string
                        else:
                            if literal == e:
                                useless = False
                                break
        return useless
