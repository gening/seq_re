# coding:utf-8

"""
Bootstrap sequence regular express pattern
==========================================

A trigger pattern and several groups of trigger phrases is given,
the function bootstrap() will generate the new patterns through many sequences.

Examples
--------

For example, given that

>>> import seq_re
>>> len_tuple = 3
>>> trigger_pattern = ('(?P<com@1>[company_name;;company tag]) (?P<x1@@>.{0,5}) '
>>>                    '(?P<v@0>[;verb]) (?P<x2@@>.{0,5}) (?P<pro@1>[product_name;;product tag])'
>>>                   )
>>> trigger_dict_list = [{'company_name': 'Apple', 'product_name': 'iPhone'},
>>>                      {'company_name': 'Apple',
>>>                       'product_name': ['iPhone 4', 'iPhone 6S plus']}
>>>                     ]
>>> list_of_sequence = [..., ..., ...]
>>> seq_re.bootstrap(len_tuple, trigger_pattern, trigger_dict_list, list_of_sequence)

the patterns generated could be the following::

    [;;company tag].{0,5}[designs].{0,5}[;;product tag]

    [;;company tag].{0,5}[has released].{0,5}[;;product tag]

The group in the trigger patterns, which needs to be presented in the generated patterns,
should be given a format string starting with ``@`` after its group name.

"""
# todo: assign an default name uniquely for group
# todo: deal with the group name needed to be presented in the pattern generated.

__author__ = "GE Ning <https://github.com/gening/seq_regex>"
__copyright__ = "Copyright (C) 2017 GE Ning"
__license__ = "LGPL-3.0"
__version__ = "1.0"

import seq_re_main


def _prepare(len_tuple, pattern, trigger_dict_list):
    """Initialize a list of SeqRegexObject."""
    seq_re_list = []
    for trigger_dict in trigger_dict_list:
        sr = seq_re_main.SeqRegex(len_tuple).compile(pattern, **trigger_dict)
        seq_re_list.append(sr)
    return seq_re_list


def _generate(seq_re_list, sequence):
    """Find matches in the sequence by the useful SeqRegexObject,
    and generate the result pattern."""
    # prune: no need to use the re module
    seq_re_used_indices = []
    for i, sr in enumerate(seq_re_list):
        if not sr.is_useless_for(sequence):
            seq_re_used_indices.append(i)
    # match
    for sr_i in seq_re_used_indices:
        sr = seq_re_list[sr_i]
        generated_pattern = []
        matches = sr.finditer(sequence)
        for match in matches:
            # group index is required here, not order by name
            for name in sorted(match.named_group_dict, key=lambda g: match.named_group_dict[g][0]):
                generated_pattern.append(match.format_group_to_str(name, trimmed=True))
            yield ''.join(generated_pattern)


def bootstrap(len_tuple, trigger_pattern, trigger_dict_list, sequences_iter):
    """Bootstrap sequence regular express pattern by the trigger pattern.

    :param len_tuple: The length of the tuple
    :param trigger_pattern: The pattern string
    :param trigger_dict_list: [{placeholder_name1: p1, placeholder_name2: p2}, ...]
                              in which p1, p2 could be a str or a list of str.
    :param sequences_iter: Yield one 2-dimensional sequence by one
    :return: [(pattern_generated, freq), ...]
    """
    seq_re_list = _prepare(len_tuple, trigger_pattern, trigger_dict_list)
    counter = dict()
    # many sequences
    for seq in sequences_iter:
        for gen_pattern in _generate(seq_re_list, seq):
            counter[gen_pattern] = counter.get(gen_pattern, 0) + 1
    # sorted by the frequency
    popular_patterns = sorted(counter.items(), key=lambda t: t[1], reverse=True)
    return popular_patterns
