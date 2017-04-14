# coding:utf-8

"""
Bootstrap sequence regular express pattern
==========================================

A trigger pattern and several groups of trigger phrases is given, 
the function bootstrap() will generate the new patterns through many sequences.

For example,

given that
```python
>>> trigger_pattern_ndim = 3
>>> trigger_pattern = (u'(?P<com@1>/company_name::company tag/) (?P<x1@@>.{0,5}) '
>>>                    u'(?P<v@0>/:verb/) (?P<x2@@>.{0,5}) (?P<pro@1>/product_name::product tag/)'
>>>                   )
>>> trigger_dict_list = [{u'company_name': u'Apple', u'product_name': u'iPhone'},
>>>                      {u'company_name': u'Apple',
>>>                       u'product_name': [u'iPhone 4', u'iPhone 6S plus']}
>>>                     ]
>>> bootstrap(trigger_pattern_ndim, trigger_pattern, trigger_dict_list, ...)
```
the patterns generated could be the following:
/::company tag/.{0,5}/designs/.{0,5}/::product tag/
/::company tag/.{0,5}/has released/.{0,5}/::product tag/

The group in the trigger patterns, which needs to be presented in the generated patterns, 
should be given a format string starting with `@` after its group name.

"""
# todo: assign an default name uniquely for group
# todo: deal with the group name needed to be presented in the pattern generated.

__author__ = "GE Ning <https://github.com/gening/seq_regex>"
__copyright__ = "Copyright (C) 2017 GE Ning"
__license__ = "Apache License 2.0"
__version__ = "0.1"

import seq_re


def _prepare(ndim, pattern, trigger_dict_list):
    """initialize a list of SeqRegexObject."""
    seq_re_list = []
    for trigger_dict in trigger_dict_list:
        sr = seq_re.SeqRegex(ndim).compile(pattern, **trigger_dict)
        seq_re_list.append(sr)
    return seq_re_list


def _generate(seq_re_list, nd_sequence):
    """find matches in the sequence by the useful SeqRegexObject, and generate the result pattern"""
    # prune: no need to use the re module
    seq_re_used_indices = []
    for i, sr in enumerate(seq_re_list):
        if not sr.is_useless_for(nd_sequence):
            seq_re_used_indices.append(i)
    # match
    for sr_i in seq_re_used_indices:
        sr = seq_re_list[sr_i]
        generated_pattern = []
        matches = sr.finditer(nd_sequence)
        for match in matches:
            # group index is required here, not order by name
            for name in sorted(match.named_group_dict, key=lambda g: match.named_group_dict[g][0]):
                generated_pattern.append(match.format_group_to_str(name, trimmed=True))
            yield u''.join(generated_pattern)


def bootstrap(ndim, trigger_pattern, trigger_dict_list, sequence_iter):
    """
    bootstrap sequence regular express pattern by the trigger pattern.
    :param ndim: the number of dimensions
    :param trigger_pattern: pattern string
    :param trigger_dict_list: [{placeholder_name1: p1, placeholder_name2: p2}, ...]
                              in which p1, p2 could be a str or a list of str.
    :param sequence_iter: yield one n-dimensional sequence by one
    :return: [(freq, pattern_generated), ...]
    """
    seq_re_list = _prepare(ndim, trigger_pattern, trigger_dict_list)
    counter = dict()
    # many sequences
    for seq in sequence_iter:
        for gen_pattern in _generate(seq_re_list, seq):
            counter[gen_pattern] = counter.get(gen_pattern, 0) + 1
    # sorted by the frequency
    popular_patterns = sorted(counter, key=counter.get, reverse=True)
    return [(gen_pattern, counter[gen_pattern]) for gen_pattern in popular_patterns]
