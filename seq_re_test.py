#!/usr/bin/env python
# coding: utf-8
"""
unit test for all modules of seq_re:

seq_re_parse.py
seq_re.py
seq_re_bootstrap.py

"""
__author__ = "GE Ning <https://github.com/gening/seq_regex>"
__copyright__ = "Copyright (C) 2017 GE Ning"

import unicodedata

import codecs
import nose
from nose.tools import assert_equals

import seq_re
import seq_re_bootstrap
import seq_re_parse


def char_width(char):
    # A	Ambiguous    不确定
    # F	Fullwidth    全宽
    # H	Halfwidth    半宽
    # N	Neutral      中性
    # Na	Narrow       窄
    # W	Wide         宽
    if unicodedata.east_asian_width(char) in ('F', 'W', 'A'):
        return 2
    else:
        return 1


def print_pattern_info(pattern):
    # print ten digit of the index number of str
    line = []
    full_width = u'０１２３４５６７８９　'
    for i in xrange(len(pattern)):
        width = char_width(pattern[i])
        if i % 10 == 0:
            line.append(str(i / 10) if width == 1 else full_width[i / 10])
        else:
            line.append(' ' if width == 1 else full_width[10])
    print ''.join(line)
    # print the digit of the index number of str
    line = []
    for i in xrange(len(pattern)):
        width = char_width(pattern[i])
        line.append(str(i % 10) if width == 1 else full_width[i % 10])
    print ''.join(line)
    # print str itself
    print pattern


def print_stack_info(pattern, pattern_stack):
    for info in pattern_stack:
        flag, string, pos = info
        if pos is not None:
            if flag == seq_re_parse.Flags.LITERAL:
                offset = (string.count(u'/') + string.count(u':') +
                          string.count(u'|') + string.count(u'\\'))
                if string == u'^' and pattern[pos] == u'\\':
                    offset += 1
                info.append(pattern[pos: pos + len(string) + offset])
            elif flag in [seq_re_parse.Flags.EX, seq_re_parse.Flags.GROUP_NAME]:
                info.append(pattern[pos: pos + len(string)])
            else:
                info.append(pattern[pos])
        print u'\t'.join([unicode(i) for i in info])


def print_debug_info(pattern, pattern_dump, pattern_stack):
    print_pattern_info(pattern)
    print pattern_dump
    print_stack_info(pattern, pattern_stack)


class TestSeqRegexParser:
    cases = []
    expectations = []

    def __init__(self):
        pass

    @classmethod
    def setup_class(cls):
        print ('====begin of SeqRegexParser test====')
        cls.sp = seq_re_parse.SeqRegexParser()
        cls.ndim = 3

    def setup(self):
        print ('====prepare cases====')
        case_filename = 'seq_re_test_case.txt'
        with codecs.open(case_filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if len(line) > 0 and line[0] != '#':
                    items = line.split('\t')
                    if len(items) == 2:
                        case, expect = items
                        self.cases.append(case)
                        self.expectations.append(expect)
                    else:
                        print 'bad test case:\n%s' % line

    def test_parse(self):
        print ('====test parse====')
        for i in xrange(len(self.cases)):
            pattern = self.cases[i]
            try:
                # noinspection PyUnusedLocal
                pattern_stack = self.sp.parse(self.ndim, pattern)
                pattern_dump = self.sp.dump()
                # print '%s\t%s' % (pattern, pattern_dump)
                # print_debug_info(self.cases[i], pattern_dump, pattern_stack)
                assert_equals(pattern_dump, self.expectations[i])
            except ValueError as e:
                # print '%s\t%s' % (pattern, e.message.split('\n')[0])
                assert_equals(e.message.split('\n')[0], self.expectations[i])

    def teardown(self):
        pass

    @classmethod
    def teardown_class(cls):
        print ('====end of SeqRegexParser test====')
        pass


class TestSeqRegex:
    ndim = 0
    tagged_lines = []

    def __init__(self):
        pass

    @classmethod
    def setup_class(cls):
        print ('====prepare corpus====')
        cls.ndim = 2
        corpus_filename = 'seq_re_test_corpus.txt'
        with codecs.open(corpus_filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # seq = [item.split('`') for item in ]
                seq = []
                for item in line.split():
                    tup = item.split('`')
                    if len(tup) == cls.ndim:
                        seq.append(tup)
                    else:
                        print 'Consistent dimension of line:\n%s' % line
                        break
                if len(seq) > 0:
                    cls.tagged_lines.append(seq)

    def test_seq_regex(self):
        print ('====begin of SeqRegex test====')

        # pattern
        pattern = ur'(?P<com1@0>/company_name/) .{0,5} (?P<com2@1>/company_name/) .{0,5} (/:verb/)'
        abbr = {u'company_name': [u'中信证券', u'美的集团'], u'verb': u'v'}

        # test
        sr = seq_re.SeqRegex(self.ndim)
        sr.compile(pattern, **abbr)
        for seq in self.tagged_lines:
            result = sr.search(pattern, seq)
            if result:
                for g in result.group_list:
                    print ' '.join(['`'.join(map(unicode, item)) for item in g[1]])
                for name in result.named_group_dict.iterkeys():
                    print name, result.format_group_to_str(name, True)

        assert True
        print ('====end of SeqRegex test====')

    def test_seq_re_bootstrap(self):
        print ('====begin of bootstrap test====')

        # pattern
        # todo: assign an default name uniquely for group
        trigger_pattern = (u'(?P<company1@@>/company_name1/) (?P<x1@@>.{0,5}) '
                           u'(?P<verb@0>/:v/) (?P<x2@@>.{0,5}) '
                           u'(?P<company2@@>/company_name2/) (?P<x3@@>.{0,5}) (?P<noun@0>/:n/)')
        trigger_dict_list = [{u'company_name1': [u'中信证券'], u'company_name2': u'美的集团'},
                             {u'company_name1': [u'中信证券股份有限公司'],
                              u'company_name2': u'中信证券'}]  # trigger tuples

        # test
        result = seq_re_bootstrap.bootstrap(self.ndim, trigger_pattern, trigger_dict_list,
                                            self.tagged_lines)
        if len(result) > 0:
            print u'freq\tpattern'
        for gen_pattern, freq in result:
            print u'%s\t%s' % (freq, gen_pattern)

        assert True
        print ('====end of bootstrap test====')


if __name__ == '__main__':
    # argv[0] is not param but the cmd name itself
    test_result = nose.run(argv=['nosetests', '-s', '-v'])
