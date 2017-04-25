# coding:utf-8

"""
Parse the syntax of sequence regular express pattern
====================================================

Parse the original string of seq_re pattern into an queue of parsed parts,
and translate the syntax of each part into its equivalent of the ordinary regular expression.

"""

__author__ = "GE Ning <https://github.com/gening/seq_regex>"
__copyright__ = "Copyright (C) 2017 GE Ning"
__license__ = "LGPL-3.0"
__version__ = "1.2"

# todo: deal with multi-value elements in the sequence
# todo: assign an default name uniquely for group
"""
multi-value elements in the tuple
=> unfold multi-values as new element of the tuple

pattern:
element match a =>
(?![^a]{3}).{3}
match
x 123
v a23
v 1a3
v 12a
v aa3
v 1aa
v a2a
v aaa

element match ^a =>
(?![a]{3}).{3}
match
v 123
v a23
v 1a3
v 12a
v aa3
v 1aa
v a2a
x aaa

element match . =>
.{3}

sequence:
the 3rd element is 3 multi-values
tup = [W,P,(A,B,C)] =>
extend
WPABC

tup = [W,P,X] =>
extend
WPXXX
"""


class Flags(object):
    """The functional flags of the parsed pattern part"""
    EX = 'EX'  # general expression
    EXP = 'EXP'  # automatic expansion
    EXT_START = 'EXT_S'  # non-capturing group pattern start
    EXT_END = 'EXT_E'  # non-capturing group pattern end
    EXT_SIGN = 'EXT_SIG'  # non-capturing group notation
    GROUP_START = 'GRP_S'  # capturing group pattern start
    GROUP_END = 'GRP_E'  # capturing group pattern end
    GROUP_NAME = 'GRP_NAM'  # group name define
    TUPLE_START = 'TUP_S'  # tuple pattern start
    TUPLE_END = 'TUP_E'  # tuple pattern end
    SET_START = 'SET_S'  # tuple pattern start
    SET_END = 'SET_E'  # tuple pattern end
    SET_NEG = 'SET_NEG'  # negative sign
    LITERAL = 'LITERAL'  # need to be encoded


class SeqRegexParser(object):
    """The class wraps the parse function, and manages the states of the global variables."""

    def __init__(self):
        self._len_tuple = 0  # the length of the tuple
        self._placeholder_dict = None  # the substitutions of placeholders in the pattern
        self._pattern_str = None  # the string of original pattern
        self._pattern_tokenized = None  # the Tokenizer of pattern to help iterate the chars of it
        self._pattern_stack = None  # the queue of substrings of pattern, which has been parsed
        self.named_group_format_indices = None  # the format indices of name groups

    def _set(self, len_tuple, pattern_str, placeholder_dict):
        """initialize the class"""
        if isinstance(len_tuple, int) and len_tuple > 0:
            self._len_tuple = len_tuple
        else:
            raise ValueError('invalid number of len_tuple')
        if pattern_str is not None:
            self._pattern_str = pattern_str
        else:
            raise ValueError('invalid pattern string')
        self._placeholder_dict = placeholder_dict
        self._pattern_tokenized = Tokenizer(pattern_str)
        self._pattern_stack = []
        self.named_group_format_indices = dict()

    @property
    def len_tuple(self):
        """The length of the tuple"""
        return self._len_tuple

    @property
    def pattern(self):
        """The original string of pattern"""
        return self._pattern_str

    @classmethod
    def _parse_indices(cls, indices_string):
        """Parse the format string.

        :param indices_string: indices_string: `0,2:4`
        :return: return index_range_list = [(group_index_begin, group_index_end), ...]
        """
        index_range_list = indices_string.split(',')
        for ix, indices in enumerate(index_range_list):
            index_list = indices.split(':')
            if len(index_list) == 1:
                index = int(index_list[0].strip())
                index_range_list[ix] = (index, index + 1)
            elif len(index_list) == 2:
                index_range_list[ix] = (int(index_list[0].strip()), int(index_list[1].strip()))
            else:
                raise ValueError
        return index_range_list

    def _parse_group_identifier(self, identifier_string):
        """Parse the group identifier.
        # `name` => name, [(0, len_tuple)]
        # `name@` =>name, [(0, len_tuple)]
        # `name@format_string` => name, [(group_index_begin, group_index_end), ...]
        # `name@@` => name, None

        :param identifier_string: name, name@indices_string, name@@
        :return: ('group_name', [(group_index_begin, group_index_end), ...])
        """
        source = self._pattern_tokenized
        name = ''
        format_indices = []
        items = identifier_string.split('@')
        if len(items) > 0:
            name = items[0]
            if name == '':
                raise source.error('missing group name', len(identifier_string) + 1)
        # A
        if len(items) == 1:
            format_indices.append((0, self._len_tuple))
        # A@ => ['A', '']
        # A@B => ['A', 'B']
        elif len(items) == 2:
            format_string = items[1]
            if format_string == '':
                format_indices.append((0, self._len_tuple))
            elif format_string != '':
                try:
                    format_indices = self._parse_indices(format_string)
                except ValueError:
                    raise source.error('invalid format indices `%s`' % format_string,
                                       len(format_string) + 1)
        # A@@ => ['A', '', '']
        elif len(items) == 3 and items[1] == '' and items[2] == '':
            format_indices = None
        # A@B@C => ['A', 'B', 'C']
        else:
            format_string = '@'.join(items[1:])
            raise source.error('invalid format indices `%s`' % format_string,
                               len(format_string) + 1)
        return name, format_indices

    def _parse_placeholder(self, placeholder_name):
        """Parse placeholder name in the pattern string,
        and substitute it by a set of placeholder values through looking up placeholder_dict

        :param placeholder_name: string
        :return: [substitutions of str type]
        """
        str_list = []
        # placeholder name
        placeholder_set = self._placeholder_dict.get(placeholder_name, placeholder_name)
        if hasattr(placeholder_set, '__iter__'):
            # list, set
            str_list.extend(placeholder_set)
        else:
            # a single string
            str_list.append(placeholder_set)
        return str_list

    def _parse_element(self, negative_flag, element_set):
        """Parse the element as the following:
        #  None  <==>   `|`
        #  `A`   <==>  `A|`  <==>  `|A`
        # `^A`   <==> `^A|`  <==> `^|A`
        #  `A|B` !<=> `^A|B`
        # `\^`    ==>  ok
        #  `^`   <==>  `^|`     ==> error
        # given that A and B are the values of the same one element.

        :param negative_flag: The position of negative sign related
        :param element_set: [([char1, char2, ...], pos), ...]
        :return: parsed = [(Flag, parsed_pattern, begin_pos), ...]
        """
        source = self._pattern_tokenized
        parsed = self._pattern_stack

        if negative_flag >= 0:
            negatived = True
        else:
            negatived = False

        # avoid `placeholder|placeholder` => [["p11""p12"]["p2"]]
        # in which escaped `[` and `]` are misunderstand.
        # replaced by ["p11""p12""p2"]
        elements = []
        for value_chars, source_pos in element_set:
            value_str = ''.join(value_chars)  # value_chars = [a1, a2, ...]
            if value_str in self._placeholder_dict:
                for v in self._parse_placeholder(value_str):
                    elements.append([v, None])
            else:
                elements.append([value_str, source_pos])

        if len(elements) == 0:
            # nothing to be negatived
            if negatived:
                raise source.error('unexpected negative sign `^`', source.pos - negative_flag)
            # `.`
            else:
                parsed.append([Flags.EXP, '.', source.pos - 1])
        elif not negatived and len(elements) == 1:
            # `A`
            value_str, source_pos = elements[0]
            parsed.append([Flags.LITERAL, value_str, source_pos])
        else:
            # `[AB]` `[^A]` `[^AB]`
            parsed.append([Flags.SET_START, '[', None])
            if negatived:
                parsed.append([Flags.SET_NEG, '^', negative_flag])
            for value_str, source_pos in elements:
                parsed.append([Flags.LITERAL, value_str, source_pos])
            parsed.append([Flags.SET_END, ']', None])

        # clear element_set
        element_set[:] = []
        return

    def _parse_tuple(self):
        """Parse the tuple pattern in the square brackets:
        # which is delimited by `[...]` excluding the delimited `[` and `]`:
        # `[X;]` `[X;Y]` `[;Y]`
        # `[]` `[|]` `[;]` `[|;]``[;|]`
        # given that X and Y are elements.
        # in that all `(` and `)` in the elements are parsed as plain text,
        # which have no syntax meaning, the nested recursion of this function is not required.
        #
        # when `]`
        # => parse element
        # => add . if len_index < len_tuple
        # when `;`
        # => parse element
        # => len_index ++
        # when `|`
        # => add an element value to set
        # when `^`
        # => negative all elements if it's the first

        :return: parsed = [(Flag, parsed_pattern, begin_pos), ...]
        """
        source = self._pattern_tokenized
        parsed = self._pattern_stack
        len_index = 0
        element_list = []  # [(value_list, pos), ...] = [([char1, char2, ...], pos), ...]
        negative_flag = -1
        # open the `[`
        start_pos = source.pos - 1
        parsed.append([Flags.TUPLE_START, '(?:', start_pos])
        while True:
            this = source.next
            this_pos = source.pos
            if this is None:
                # unexpected end of tuple pattern
                raise source.error('unbalanced square bracket `[`', source.pos - start_pos)
            if this in ']':  # terminator = ']'
                if negative_flag >= 0 or len(element_list) > 0:
                    self._parse_element(negative_flag, element_list)
                    # negative_flag = -1
                    len_index += 1
                # check the consistency of len_tuple
                # [a;bc;def]
                # ^ ^  ^   ^
                # 0 1  2   3
                len_vacancy = self._len_tuple - len_index
                if len_vacancy > 0:
                    parsed.append([Flags.EXP, '.' * len_vacancy, None])
                break  # end of tuple pattern
            source.get()

            if this == ';':
                # if terminator !=']':
                #     raise source.error('invalid `;` out inside `[...]`', 1)
                # parse the element
                self._parse_element(negative_flag, element_list)
                negative_flag = -1
                # move len_index forwards
                len_index += 1
                if len_index >= self._len_tuple:
                    raise source.error('out of the tuple length range')
            elif this == '|':
                if source.next not in '|;]':
                    # nothing to be alternated previously
                    # if len(element_list) == 0:
                    #    ignore raising source.error('unexpected alternate sign `|`')
                    # new value of the element
                    element_list.append(([], this_pos + 1))
            elif this == '^' and len(element_list) == 0 and negative_flag < 0:
                # `^` has no special meaning if it’s not the first character in the set.
                # negatived = True
                negative_flag = this_pos
            else:
                if len(element_list) == 0:
                    element_list.append(([], this_pos))
                if this[0] == '\\':
                    if this[1] in '];|\\':
                        element_list[-1][0].append(this[1])
                    elif this[1] == '^' and len(element_list[0][0]) == 0:
                        # so only if it's the first character, `^` can be escaped.
                        element_list[-1][0].append(this[1])
                    else:
                        element_list[-1][0].append(this[0:2])
                else:
                    element_list[-1][0].append(this)
        # close the `]`
        parsed.append([Flags.TUPLE_END, ')', source.pos])
        return

    def _parse_group(self):
        """Parse the group pattern inside the parentheses
        which is delimited by `(...)` including the delimited `(` and `)`:
        # => separate the group extension prefix:
        #   `(?:...)`
        #   `(?P<name>...)`
        #   `(?P=name)`
        #   `(?#comment)`
        #   `(?(id/name)...)`
        #   `(?=...)`
        #   `(?!...)`
        #   `(?<=...)`
        #   `(?<!...)`
        # => if there is a sub pattern, then parse sub pattern
        # => separate the format indices of a named group from its name: `<name@0,2:4>`
        # => only `(pattern)` and `(?P<name>pattern)` will be counted as capturing groups,
        #    and assigned the group index.

        :return: parsed = [(Flag, parsed_pattern, begin_pos), ...]
        """
        source = self._pattern_tokenized
        parsed = self._pattern_stack
        group = False  # capturing group flag
        # open group
        start_pos = source.pos - 1
        parsed.append([Flags.EXT_START, '(', start_pos])
        # group content
        if source.match('?'):
            # this is an extension notation
            char = source.get()
            if char is None:
                raise source.error('unexpected end of pattern')
            elif char == ':':
                group = False
                # non-capturing group
                parsed.append([Flags.EXT_SIGN, '?:', source.pos - 2])
            elif char == 'P':
                if source.match('<'):
                    group = True
                    parsed[-1][0] = Flags.GROUP_START
                    parsed.append([Flags.EXT_SIGN, '?P<', source.pos - 3])
                    # named group: skip forward to end of name and format
                    identifier = source.get_until('>')  # terminator will be consumed silently
                    name, format_indices = self._parse_group_identifier(identifier)
                    self.named_group_format_indices[name] = format_indices
                    parsed.append([Flags.GROUP_NAME, name, source.pos - len(identifier) - 1])
                    parsed.append([Flags.EX, '>', source.pos - 1])
                elif source.match('='):
                    parsed.append([Flags.EXT_SIGN, '?P=', source.pos - 3])
                    # named back reference
                    name = source.get_until(')', skip=False)  # terminator will be not consumed
                    parsed.append([Flags.EX, name, source.pos - len(name)])
                    # close the group
                    parsed.append([Flags.EXT_END, ')', source.pos])
                    # not contain any pattern
                    return
            elif char == '#':
                # group = False
                parsed.pop(-1)  # pop the start of group
                # comment group ignores everything including `/.../`
                # source.get_until(')', skip=False)  # terminator will be not consumed
                while True:
                    if source.next is None:
                        raise source.error("missing `)`, unterminated comment",
                                           source.pos - start_pos)
                    if source.match(')', skip=False):
                        break
                    else:
                        source.get()
                # not contain any pattern
                return
            elif char in '=!<':
                group = False
                # lookahead assertions
                if char == '<':
                    char = source.get()
                    if char is None:
                        raise source.error('unexpected end of pattern')
                    if char not in '=!':
                        raise source.error('unknown extension `?<%s`' % char, len(char) + 2)
                    else:
                        char = '<' + char
                char = '?' + char
                parsed.append([Flags.EXT_SIGN, char, source.pos - len(char)])
            elif char == '(':
                group = False
                parsed.append([Flags.EXT_SIGN, '?(', source.pos - 2])
                # conditional back reference group
                cond_name = source.get_until(')')  # terminator will be consumed silently
                parsed.append([Flags.EX, cond_name, source.pos - len(cond_name) - 1])
                parsed.append([Flags.EX, ')', source.pos - 1])
            else:
                raise source.error('unknown extension `?%s`' % char, len(char) + 1)
                # parsed.append([Flags.EX, '?' + char, source.pos - 2])
                # pass
        else:
            # without extension notation as an unnamed group
            group = True
            parsed[-1][0] = Flags.GROUP_START
            pass
        # group contains a sub pattern
        self._parse_sub()
        # close group
        if group:
            start_flag = Flags.GROUP_START
            end_flag = Flags.GROUP_END
        else:
            start_flag = Flags.EXT_START
            end_flag = Flags.EXT_END
        if parsed[-1][0] == start_flag:
            parsed.pop(-1)
        else:
            parsed.append([end_flag, ')', source.pos])
        return

    def _parse_sub(self):
        """Parse the sub pattern `...`
        which maybe contain the group pattern `(...)` or the tuple pattern `/.../`:
        # => check invalid char outside of comments: [ ] \
        # => remove redundant char: whitespace
        # => count continuous dots separately,
        #    not replace regex pattern '.\+' => '(?:' + '.' * len_tuple + ')'
        # => deal with delimiter: `(group pattern)`, `/tuple pattern/`

        :return: parsed = [(Flag, parsed_pattern, begin_pos), ...]
        """
        source = self._pattern_tokenized
        parsed = self._pattern_stack
        while True:
            # hold the position at source to retain the boundary
            this = source.next
            this_pos = source.pos
            if this is None:
                break  # end of pattern
            if this == ')':
                break  # recursive end of group pattern
            # move index of the source forward
            source.get()

            if this == '.':
                parsed.append([Flags.EXP, '(?:' + '.' * self._len_tuple + ')', this_pos])
            elif this == '(':
                # parse the whole group content `...` without consuming `(` and `)`
                self._parse_group()
                if not source.match(')'):
                    # unexpected end of group pattern
                    raise source.error('unbalanced parenthesis `(`', source.pos - this_pos)
            elif this == '[':
                # parse the tuple whole content `...` without consuming `[` and `]`
                self._parse_tuple()
                if not source.match(']'):
                    # unexpected end of group pattern
                    raise source.error('unbalanced square bracket `[`', source.pos - this_pos)
            elif this in ']':
                # not recursive within the tuple
                raise source.error('unbalanced square bracket `]`', 1)
            elif this[0] == '\\':
                raise source.error('invalid escape expression `\\`', len(this))
            elif this in '*+?{,}' or this in '0123456789' or this in '^$' or this in '|':
                # repeat with digital
                # at beginning or end
                # branch
                parsed.append([Flags.EX, this, this_pos])
            # omit whitespace
            elif this.isspace():
                pass
            # omit non-special chars
            else:
                raise source.error('unsupported syntax char `%s`' % this, 1)
                # otherwise:
                # deal with non-special chars as tuple
                # parse the tuple in which `:` is not accepted
                # and `|`, `^` has already been excluded because they are special chars
                # tuple terminator could be any special char (not digital), whitespace or None
                # finally bring no more benefits other than bugs
        return

    def _parse_seq(self):
        """Parse the whole pattern `...`.
        For the pattern `...)...`, parser will be stopped at `)` and an error will be raised.

        :return: parsed = [(Flag, parsed_pattern, begin_pos), ...]
        """
        source = self._pattern_tokenized
        parsed = self._pattern_stack
        # parse the seq pattern
        self._parse_sub()
        # parsing exit before end of pattern
        if source.next is not None:
            # unexpected end of pattern
            assert source.next == ')'
            raise source.error('unbalanced parenthesis `)`')
        return parsed

    def parse(self, len_tuple, pattern_str, **placeholder_dict):
        """The main entry of functions.

        Parse the pattern by translating its syntax into the equivalent in regular expression
        and return a pattern stack for future encode.

        :param len_tuple: the length of the tuple
        :param pattern_str: The string of original pattern
        :param placeholder_dict: The substitutions of placeholders in the pattern
        :return: parsed = [(Flag, parsed_pattern, begin_pos), ...]
        """
        self._set(len_tuple, pattern_str, placeholder_dict)
        parsed = self._parse_seq()
        return parsed

    def dump(self):
        """Transform self._pattern_stack into pseudo regular expression string
        for debugging or testing.

        :return: A string of parsed pattern similar to the ordinary RE
        """
        dump_stack = []
        if self._pattern_stack:
            for flag, string, pos in self._pattern_stack:
                if flag == Flags.LITERAL:
                    dump_stack.append('"%s"' % string)
                elif string is not None:
                    dump_stack.append(string)
        return ''.join(dump_stack)

    def get_pattern_by_name(self, group_name):
        """Get original pattern string determined by group name.

        :param group_name: The group name
        :return: The substring of original pattern
        """
        start = end = step = -1
        for flag, string, pos in self._pattern_stack:
            if flag == Flags.GROUP_START:
                if step < 0:
                    start = pos
                else:
                    step += 1
            elif flag == Flags.GROUP_NAME:
                if step < 0 and string == group_name:
                    step = 0
            elif flag == Flags.GROUP_END:
                if step == 0:
                    end = pos
                    break
                elif step > 0:
                    step -= 1
        if start > -1 and end > -1:
            # `(?:P<name@@>pattern)`
            return self._pattern_str[start: end + 1]
        else:
            raise ValueError('unknown group name')

    def get_pattern_by_id(self, group_index):
        """Get original pattern string determined by group index.

        :param group_index: The index of group
        :return: The substring of original pattern
        """
        start = end = step = -1
        group_id = 0
        named = False
        if group_index == 0:
            return self._pattern_str
        for flag, string, pos in self._pattern_stack:
            if flag == Flags.GROUP_START:
                group_id += 1
                if group_id == group_index:
                    step = 0
                    start = pos
                else:
                    step += 1
            elif flag == Flags.GROUP_NAME and group_id == group_index:
                named = True
            elif flag == Flags.GROUP_END:
                if step == 0:
                    end = pos
                    break
                elif step > 0:
                    step -= 1
        if start > -1 and end > -1:
            if named:
                # `(?P<....>pattern)`
                return self._pattern_str[start: end + 1]
            else:
                # `(pattern)`
                return self._pattern_str[start: end + 1]
        else:
            raise ValueError('group index out of range')

    def get_positive_literal_sets(self):
        """Get literals grouped by sets which do not have negative sign.

        :return: literal_set_list = ['str', ['str', 'str'], ....]
        """
        # sets come after ?! ?<! => - - = + , - + = -
        literal_set_list = []
        positive = True
        set_sign = True
        in_set = False

        for flag, string, _ in self._pattern_stack:
            if flag == Flags.EXT_START:
                if string in ['?!', '?<!']:
                    positive = False
            elif flag == Flags.SET_START:
                in_set = True
                literal_set_list.append(set())
            elif flag == Flags.SET_NEG:
                set_sign = False
            elif flag == Flags.LITERAL:
                if positive and set_sign:
                    if in_set:
                        literal_set_list[-1].add(string)
                    else:
                        literal_set_list.append(set([string]))  # a set
            elif flag == Flags.SET_END:
                if len(literal_set_list[-1]) == 0:
                    literal_set_list.pop(-1)
                in_set = False
                set_sign = True
            elif flag == Flags.EXT_END:
                positive = True
        return literal_set_list


class Tokenizer(object):
    """The class to help iterate the chars of original string of pattern"""

    # this class is based on the following but modified:
    # https://github.com/python/cpython/blob/master/Lib/sre_parse.py
    # https://svn.python.org/projects/python/trunk/Lib/sre_parse.py
    # python’s SRE structure can be learned from:
    # https://blog.labix.org/2003/06/16/understanding-pythons-sre-structure

    def __init__(self, string):
        self.string = string
        self.index = 0
        self.next = None
        self.__next()

    def __next(self):
        if self.index >= len(self.string):
            self.next = None
            return
        char = self.string[self.index]
        if char[0] == "\\":
            try:
                c = self.string[self.index + 1]
            except IndexError:
                raise self.error('bad escape in end')
            char += c
        self.index += len(char)
        self.next = char

    def match(self, char, skip=True):
        if char == self.next:
            if skip:
                self.__next()
            return True
        return False

    def get(self):
        this = self.next
        self.__next()
        return this

    def get_while(self, n, charset):
        result = ''
        for _ in range(n):
            c = self.next
            if c not in charset:
                break
            result += c
            self.__next()
        return result

    def get_until(self, terminator, skip=True):
        result = ''
        while True:
            c = self.next
            self.__next()
            if c is None:
                if not result:
                    raise self.error('missing characters')
                raise self.error('missing `%s`, unterminated characters' % terminator,
                                 len(result))
            if c == terminator:
                if not result:
                    raise self.error('missing character', 1)
                if not skip:
                    self.seek(self.index - 2)
                break
            result += c
        return result

    @property
    def pos(self):
        return self.tell()

    def tell(self):
        return self.index - len(self.next or '')

    def seek(self, index):
        self.index = index
        self.__next()

    def error(self, msg, offset=0):
        position = self.tell() - offset
        # highlight the position of error
        return ValueError('%s at position %d\n%s\n%s' %
                          (msg, position, self.string, '.' * position + '^'))
