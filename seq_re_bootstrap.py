# coding: utf-8

import seq_re


def _prepare(ndim, pattern, trigger_dict_list):
    seq_re_list = []
    for trigger_dict in trigger_dict_list:
        sr = seq_re.SeqRegex(ndim).compile(pattern, **trigger_dict)
        seq_re_list.append(sr)
    return seq_re_list


def _generate(seq_re_list, nd_sequence):
    # prune
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


def bootstrap(trigger_pattern_ndim, trigger_pattern_str, trigger_dict_list, sequence_iter):
    seq_re_list = _prepare(trigger_pattern_ndim, trigger_pattern_str, trigger_dict_list)
    counter = dict()
    for seq in sequence_iter:
        for gen_pattern in _generate(seq_re_list, seq):
            counter[gen_pattern] = counter.get(gen_pattern, 0) + 1
    popular_patterns = sorted(counter, key=counter.get, reverse=True)
    return [(gen_pattern, counter[gen_pattern]) for gen_pattern in popular_patterns]
