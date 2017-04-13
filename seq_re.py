# coding:utf-8

"""
N-dimensional Sequence Regular Expression

This module provides regular expression matching operations on a sequence data structure
like the following:

seq_m_n = [[str_11, str_12, ... str_1n],  
           [str_21, str_22, ... str_2n],  
            ...,  
           [str_m1, str_m2, ... str_mn]]

The sequence is a homogeneous multidimensional array (齐次多维数组).

A element in each dimension can be considered as either a string, a word, a phrase, 
a char, a flag, a token or a tag, and maybe a set of tags later.



Examples：
(/::PERSON/+) /was|is/ /a|an|the/? .{0,5} (/painter|drawing artist|画家/)
(?P<person_name@0,1:3>/::PERSON/) /:VERB be:/ /born/ /on/ 
(?P<birthday@0:2>(/:^NUMBER:DATE/|/-/){2,3})

其中
元组

序列元组使用/:::/表示，其中用:作为维度的分割，每个维度可以用|表示多值集合
它们是逻辑或的关系。
^ has no special meaning if it’s not the first character in the set.
运算优先级 / > : > ^ > |
缩写. <==> /:::/

在／／中
Special characters lose their special meaning inside ／...／

元组之外可以用使用正则表达的符号

使用带命名的组有一个好处是：可以指定输出维度：
(?P<name@d1,d2>...)
name group name
@ 全部维度，可以省略
@1,2,3 或 1:3 指定维度
@@ 返回规则本身


不支持正则表达式的转义字符\d \n ....
不支持[] as special characters.
不支持字符范围[A-Za-z0-9][uxxxx-uxxxx]
空格被忽略

Boolean Logic:
Given a 3-D sequence: [D1, D2, D3]
and
if `/X::Y/`, then match `D1 == X && D2 == Y`, pseudo re pattern = `(?:X.Y)`
or
if `/X::/|/::Y/`, then match `D1 == X || D2 == Y`, pseudo re pattern = `(?:X..)|(?:..Y)`
not
if `/:^Z:/`, then match `D2 != Z`, pseudo re pattern = `(?:.[^Z].)`

we can also use a negative lookahead assertion of re, to give a negative covered the following.
such as `(?!/:Z:/)/::/` <==> `/:^Z:/`, pseudo re pattern = `(?!(?:.Z.))...`
尽管可以使用`(?!/:P://Q/)/::/`, `(?!/:P://Q/)...`, 推荐使用固定的否定长度，
并且否定的数量与后面跟随的数量一致，避免因表达式不清晰而产生副作用。

todo 逻辑有问题
re.findall('a|b*', 'aaaaaaa')
['a', 'a', 'a', 'a', 'a', 'a', 'a', '']
re.findall('(a|b)*', 'aaaaaaa')
['a', '']
re.findall('[a|b]*', 'aaaaaaa')
['aaaaaaa', '']
re.findall('(a|b){0,5}', 'aaaaaaa')
['a', 'a', '']



此外
to represent a literal backslash `\`, '\\\\' must be used in the python code 
before the special characters to express the `\\` as the pattern string.
不支持比较数字大小


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
    将词汇编码后用正则表达式匹配后，对结果进行解码
    """

    # ######################################## #
    #                                          #
    #  Class Members                           #
    #                                          #
    # ######################################## #

    def __init__(self, ndim):
        if isinstance(ndim, int) and ndim > 0:
            self._ndim = ndim  # 维度
        else:
            raise ValueError('invalid number of dimensions')
        self._seq_pattern = None
        self._placeholder_dict = None
        self._map_encode = dict()  # 编码词典：多字token->unicode单字
        self._map_decode = dict()  # 解码词典：unicode单字->多字token
        self._map_counter = 0  # 计数器：不同token的数量
        self._parser = sp.SeqRegexParser()
        self._regex = None

    @property
    def ndim(self):
        return self._ndim

    @property
    def seq_pattern(self):
        return self._seq_pattern

    def _clear(self):
        self._seq_pattern = None
        self._placeholder_dict = None
        self._map_encode.clear()
        self._map_decode.clear()
        self._map_counter = 0
        self._parser.__init__()
        self._regex = None

    # ######################################## #
    #                                          #
    #  Encoding Functions                      #
    #                                          #
    # ######################################## #

    def _encode_str(self, decoded_str, default=None):
        if decoded_str in self._map_encode:
            return self._map_encode[decoded_str]
        elif default is None:
            # 映射到从'中'字开始连续的unicode
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
            self._map_decode[encoded_str] = decoded_str
            self._map_counter += 1
            return encoded_str
        else:
            return default

    def _encode_pattern(self):
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
        # debug
        # print self._parser.dump()
        # print u''.join(pattern_str_list)
        return u''.join(pattern_str_list)

    def _encode_sequence(self, nd_sequence):
        """对tokens列表编码为连续文本字符串"""
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

        __slots__ = ('group_list', 'named_group_dict', 'sq_re')

        def __init__(self, outer_class):
            self.group_list = []
            self.named_group_dict = dict()  # add index to consider as collections.OrderedDict
            self.sq_re = outer_class

        def format_group_to_str(self, group_name, trimmed=True):
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
        self._clear()
        self._seq_pattern = seq_pattern
        self._placeholder_dict = placeholder_dict
        regex_pattern = self._encode_pattern()
        self._regex = re.compile(regex_pattern)
        return self.SeqRegexObject(self)

    def finditer(self, seq_pattern, nd_sequence):
        """
        在tokens中，用规则rule进行正则表达式匹配
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
        在tokens中，用规则rule进行正则表达式匹配
        如果没有命中则返回None
        若命中 (group_list, named_group_dict)
        """
        return next(self.finditer(seq_pattern, nd_sequence), None)

    def findall(self, seq_pattern, nd_sequence):
        """not overlapping"""
        return [self.finditer(seq_pattern, nd_sequence)]

    def is_useless_for(self, nd_sequence):
        # for preliminary screening the seq in advanced,
        # to check whether regular expression has no chance of success.
        # for literals in the negative set,
        # not sure whether they should or should not be in the seq.
        # for literals in the positive set,
        # any one could be in the seq,
        # and their order cannot be determined in advanced.
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
