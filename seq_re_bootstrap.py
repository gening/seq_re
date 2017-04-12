# coding: utf-8

import seq_re

seq_re_list = []
seq_re_index = []
seq = None

def prepare(trigger_pattern_dim, trigger_pattern_str, trigger_dict_list):
    global seq_re_list
    seq_re_list = []
    for trigger_dict in trigger_dict_list:
        sr = seq_re.SeqRegex(trigger_pattern_dim).compile(trigger_pattern_str, **trigger_dict)
        seq_re_list.append(sr)

def prune(sequence):
    global seq_re_index, seq
    seq = sequence
    seq_re_index = []
    for i, sr in enumerate(seq_re_list):
        # for literals in the negative set, not sure whether they should or should not be in the seq
        # for literals in the positive set, any one could be in the seq,
        # and their order cannot be determined in advanced
        # todo: get list of positive sets
        p_set_list = sr.get_positive_literal_sets()
        pruned = True
        for each_p_set in p_set_list:
            pruned = True
            for literal in each_p_set:
                # fixme: rembmer seq not a string but an ndarray
                if seq.find(literal) > -1:
                    pruned = False
                    break
            if pruned:
                break
        if not pruned:
            seq_re_index.append(i)

def bootstrap():
    global seq_re_list, seq_re_index, seq
    for sr_i in seq_re_index:
        sr = seq_re_list[sr_i]
        generated_pattern = []
        matches = sr.finditer(seq)
        for match in matches:
            # fixme: order is required here, not order by name
            for name in match.named_group_dict.iterkeys():
                generated_pattern.append(match.format_group_to_str(name, trimmed=True))
            yield u''.join(generated_pattern)


if __name__ == '__main__':
    trigger_pattern_dim = 2
    # fixme：whether to assign an default name uniquely for print
    trigger_pattern_str = ur'(?P<company1@@>/company_name1/) (?P<x1@@>.{0,5}) (?P<verb@0>/:v/) (?P<x2@@>.{0,5}) (?P<company2@@>/company_name2/) (?P<x3@@>.{0,5}) (?P<noun@0>/:n/)'  # trigger pattern
    trigger_dict_list = [{u'company_name1': [u'中信证券'], u'company_name2': u'美的集团'},
                         {u'company_name1': [u'中信证券股份有限公司'], u'company_name2': u'中信证券'}]  # trigger tuples

    prepare(trigger_pattern_dim, trigger_pattern_str, trigger_dict_list)

    line = (u'中信证券股份有限公司`nc company_name`n 以下`f 简称`v 中信证券`nc 或`c 保荐`v 机构`n 接受`v 美的集团`nc '
            u'的`uj 委托`n ,`x 担任`v 美的集团`nc 本次`r 非`h 公开`ad 发行`v 的`uj 上市`ns 保荐`v '
            u'机构`n')
    seq = [item.split('`') for item in line.split()]

    prune(seq)

    for generated_pattern in set(bootstrap()):
        # todo: count the duplicated gen_pattern
        print generated_pattern

