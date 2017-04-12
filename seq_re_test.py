# coding: utf-8
"""
单元测试
#   test case

#    sub
0.23	0(?:...)23
(.23	unbalanced parenthesis `(` at position 0
).23	unbalanced parenthesis `)` at position 0
012(	unbalanced parenthesis `(` at position 3
012)	unbalanced parenthesis `)` at position 3
012(456	unbalanced parenthesis `(` at position 3
012)456	unbalanced parenthesis `)` at position 3
012\\456	invalid escape expression `\` at position 3
012345[	invalid set indicator `[` at position 6
]123456	invalid set indicator `]` at position 0

# group
(123)	(123)
(123)56	(123)56
0(2)4	0(2)4
(?:3)5	(?:3)5
(?:34)	(?:34)
(?P<45>78)0	(?P<45>78)0
(?P=45)7	(?P=45)7
(?#34)6	6
(?=34)6	(?=34)6
(?<=45)7	(?<=45)7
(?(34)67)9	(?(34)67)9
(?(34)67|90)	(?(34)67|90)2
(?23)5  (?23)5
(?:34	unbalanced parenthesis `(` at position 0
(?P<45>78	unbalanced parenthesis `(` at position 0
(?P=45	missing `)`, unterminated characters at position 4
(?#34	missing `)`, unterminated characters at position 3
(?=34	unbalanced parenthesis `(` at position 0
(?<=45	unbalanced parenthesis `(` at position 0
(?<345  unknown extension ?<3 at position 1
(?(34)67	unbalanced parenthesis `(` at position 0
(?(34	missing `)`, unterminated characters at position 3
(?23 unbalanced parenthesis `(` at position 0
(?:)4	(?:)4
(?#)4	4
(?=)4	(?=)4
(?<=)5	(?<=)5
(?<)4	unknown extension ?<) at position 1
(?) 	unknown extension ?) at position 1
(?:	 unbalanced parenthesis `(` at position 0
(?#	 missing ), unterminated comment at position 0
(?<    unexpected end of pattern at position 2
(?	unexpected end of pattern at position 2

#   nested group
0(2)4(6)(9)1(2(4)6)8    0(2)4(6)(9)1(3(5)7)9
(1(3)5) (1(3)5)
(1(3)5  unbalanced parenthesis `(` at position 0
0(2)4)  unbalanced parenthesis `)` at position 5
(1(3    unbalanced parenthesis `(` at position 2
0)2)    unbalanced parenthesis `)` at position 1
0(?P<45>7(?P<23>5))8    0(?P<56>8(?P<34>6))9

# tuple
0/2:4:6/8    0(?:"2""4""6")8
0(/34:6:8/)0   0((?:"34""6""8"))0
0(?P<56>/90:23:56/)90     0(?P<56>(?:"90""23""56"))90
/1:3:5:7/    out of dimension range at position 7
/1:3:5:/     out of dimension range at position 7
/1:3:5/    (?:"1""3""5")
/1:3:/    (?:"1""3".)
/:2:4/    (?:."2""4")
/:2:/   (?:."2".)
/::3/   (?:.."3")
/1::/   (?:"1"..)
/:2/    (?:."2".)
/1:/    (?:"1"..)
/1/ (?:"1"..)
.123    (?:...)123
//      (?:...)
/:/     (?:...)
/::/    (?:...)
/\:\/\|\\\\/0    (?:":/|\"..)0
/\:\/\|\\\\9/1  (?:":/|\9"..)1
/\:\/\|\8/0     (?:":/|\8"..)0
/.()[]*+?/  (?:".()[]*+?"..)

0(?P<56>/90:23:56)90     0(?P<56>(?:"90""23""56"))90
/1:3:5:7    out of dimension range at position 7
/1:3:5:     out of dimension range at position 7
/1:3:5    unbalanced slash `/` at position 0
/1:3:    unbalanced slash `/` at position 0
/:2:4    unbalanced slash `/` at position 0
/:2:   unbalanced slash `/` at position 0
/::3   unbalanced slash `/` at position 0
/1::   unbalanced slash `/` at position 0
/1     unbalanced slash `/` at position 0
/      unbalanced slash `/` at position 0
/:     unbalanced slash `/` at position 0


# element boolean logic
/1|3/   (?:["1""3"]..)
/1|/    (?:"1"..)
/|2/    (?:"2"..)
/|/     (?:...)
/^2|4^:7^9:^2/      (?:[^"2""4^"]"7^9"[^"2"])
/^2/    (?:[^"2"]..)
/^2|/   (?:[^"2"]..)
/^|3/   (?:[^"3"]..)
/^|/    unexpected negative sign `^` at position 1
/^/     unexpected negative sign `^` at position 1
/1:\^:6/    (?:"1""^""6")

"""

p_test = u'/\:\/\|\\\\/0'
import seq_re_parse
import seq_re


# todo
# smoke test: design test case, full unit test

def sp():
    ps = [u'(/::PERSON/ +) /was|is/ /an/?.{0, 5} /painter|drawing artist/',
          u'( /::PERSON/). /:verb_be/... /born/ /on/ (/::DATE/)..',
          u'( /::CONCEPT/).{0, 5} /:^|包括|^|涉\及|\/\:\|/.{0, 5} /::PRODUCT|CONCEPT/',
          u'(( /::CONCEPT/).{0, 5}( /:verb:/ )).{0, 5} /::PRODUCT/',
          u'( /:number:/ +) ( /\./ ) ( /:number:/ +)',
          u'///::\|//:|://:abc|//:abc://::^abc|//:abc^|://::^a//::^abc//\^//\.//./']
    rs = [
        u'((?:.."PERSON")+)(?:["was""is"]..)(?:"an"..)?(?:...){0,5}(?:["painter""drawing artist"]..)',
        u'((?:.."PERSON"))(?:...)(?:."verb_be".)(?:...)(?:...)(?:...)(?:"born"..)(?:"on"..)((?:.."DATE"))(?:...)(?:...)',
        u'((?:.."CONCEPT"))(?:...){0,5}(?:.[^"包括""^""涉\及""/:|"].)(?:...){0,5}(?:..["PRODUCT""CONCEPT"])',
        u'(((?:.."CONCEPT"))(?:...){0,5}((?:."verb".)))(?:...){0,5}(?:.."PRODUCT")',
        u'((?:."number".)+)((?:"\."..))((?:."number".)+)',
        u'(?:...)(?:.."|")(?:...)(?:."abc".)(?:."abc".)(?:..[^"abc"])(?:."abc^".)(?:..[^"a"])(?:..[^"abc"])(?:"^"..)(?:"\."..)(?:"."..)']
    sp = seq_re_parse.SeqRegexParser()
    for r, p in enumerate(ps):
        # global p_test
        # p = p_test
        pattern_stack = sp.parse(3, p)
        pattern_string = sp.dump()
        print "%s: [%s]" % (r + 1, pattern_string == rs[r])
        line = []
        fullwidth = u'０１２３４５６７８９　'
        for i in xrange(len(p)):
            width = char_width(p[i])
            if i % 10 == 0:
                line.append(str(i / 10) if width == 1 else fullwidth[i / 10])
            else:
                line.append(' ' if width == 1 else fullwidth[10])
        print ''.join(line)
        line = []
        for i in xrange(len(p)):
            width = char_width(p[i])
            line.append(str(i % 10) if width == 1 else fullwidth[i % 10])
        print ''.join(line)
        print p
        print pattern_string
        for info in pattern_stack:
            flag, string, pos = info
            if pos is not None:
                if flag == seq_re_parse.Flags.LITERAL:
                    offset = (string.count(u'/') + string.count(u':') +
                              string.count(u'|') + string.count(u'\\'))
                    if string == u'^' and p[pos] == u'\\':
                        offset += 1
                    info.append(p[pos: pos + len(string) + offset])
                elif flag in [seq_re_parse.Flags.EX, seq_re_parse.Flags.GROUP_NAME]:
                    info.append(p[pos: pos + len(string)])
                else:
                    info.append(p[pos])
            print u'\t'.join([unicode(i) for i in info])
        print '\n'


def sr():
    sr = seq_re.SeqRegex(2)

    pattern = ur'(?P<com1@@>/company_name/) .{0,5} (?P<com2@@>/company_name/) .{0,5} (/:verb/)'
    abbr = {u'company_name': [u'中信证券', u'美的集团'], u'verb': u'v'}
    sr.compile(pattern, **abbr)

    line = (u'中信证券股份有限公司`nc company_name`n 以下`f 简称`v 中信证券`nc 或`c 保荐`v 机构`n 接受`v 美的集团`nc '
            u'的`uj 委托`n ,`x 担任`v 美的集团`nc 本次`r 非`h 公开`ad 发行`v 的`uj 上市`ns 保荐`v '
            u'机构`n')
    seq = [item.split('`') for item in line.split()]
    result = sr.search(pattern, seq)
    if result:
        for g in result.group_list:
            print ' '.join(['`'.join(map(lambda s: s.encode('utf-8'), item)) for item in g[0]])
        for name in result.named_group_dict.iterkeys():
            print name, result.format_group_to_str(name, True)


import unicodedata


def char_width(c):
    # A	Ambiguous    不确定
    # F	Fullwidth    全宽
    # H	Halfwidth    半宽
    # N	Neutral      中性
    # Na	Narrow       窄
    # W	Wide         宽
    if (unicodedata.east_asian_width(c) in ('F', 'W', 'A')):
        return 2
    else:
        return 1


if __name__ == '__main__':
    """
    测试用例
    """
    sp()
    sr()
