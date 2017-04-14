N-dimensional Sequence Regular Expression (SEQ_RE)
==================================================

This module provides regular expression matching operations on a sequence data structure
like the following:

```
seq_m_n = [[str_11, str_12, ... str_1n],  
           [str_21, str_22, ... str_2n],  
            ...,  
           [str_m1, str_m2, ... str_mn]]
```

The sequence is a homogeneous multidimensional array (齐次多维数组).

A element in each dimension can be considered as either a string, a word, a phrase,
a char, a flag, a token or a tag, and maybe a set of tags or values (multi-values) later.

To match a pattern in an n-dimension sequence,
the SEQ_RE patterns is written like one of the examples:

```
(/::PERSON/+) /was|is/ /an/? .{0,3} (/^painter|drawing artist|画家/)

(?P<person_name@0>/::PERSON/) /:VERB Be:/ /born/ /on/ (?P<birthday@0:2>(/::NUMBER|MONTH/|/-/){2,3})
```

## The syntax of SEQ_RE pattern

A SEQ_RE pattern most looks like the ordinary regular express (RE) used in Python,
in which the delimiters `/.../` is to indicate a tuple of n dimensions.

### Inside `/.../`

- `/` is the beginning and end delimiter of the tuple, e.g. `/.../`.

- `:` separates the each dimension in the tuple, and the continuous `:` at the tail can be omitted,
e.g. `/A|B:X:/`, `/A|B:X/`.

- `|` indicates the different values of one dimension, e.g. `A|B`.
These values form a set, and any string in the set will be matched,
e.g. `A|B` will match `A` or `B`.

- `^` be the first character in one dimension,
all the string that are not in the value set of this dimension will be matched.
And `^` has no special meaning if it’s not the first character of the dimension.
If `^` comes the first character in a dimension but it is a part of a literal string,
`\^` should be used to escape it.

- The priority of above-mentioned operations:  `/` > `:` > `^` (not literal) > `|` > `^` (literal) .

- `\` is an escaping symbol before aforementioned special characters.  
Characters other than `/`, `:` or `\` lose their special meaning inside `／...／`.
To express `/`, `:` or `|` in literal, `\` should be added before `/`, `:` or `|`.
Meanwhile, to represent a literal backslash `\` before `/`, `:` or `|`,
`\\` should be used in the plain text that is to say `'\\\\'` must be used in the python code.


### Outside `/.../`

- The special meanings of special characters in the ordinary RE are only available here,
but with the limitations discussed below.

- **Not** support the following escaped special characters:
`\number`, `\A`, `\b`, `\B`, `\d`, `\D`, `\s`, `\S`, `\w`, `\W`, `\Z`,
`\a`, `\b`, `\f`, `\n`, `\r`, `\t`, `\v`, `\x`.

- **Not** support `[` and `]` as special characters to indicate a set of characters.

- **Not** support ranges of characters,
such as `[0-9A-Za-z]`, `[\u4E00-\u9FBB\u3007]` (Unihan and Chinese character `〇`)
used in ordinary RE.

- The whitespace and non-special characters are ignored.

- `.` is an abbreviation of `/:::/`.

- The named groups in the pattern are very useful.
As an extension, a format indices string starts with `@` can be followed after the group name,
to describe which dimensions of the tuples in this group will be output as the result.
For example: (?P<name@d1,d2:d3>...), in which d1, d2, d3 is the index number of a dimension.
  - `@` means the matched result in all of dimensions will be output.
  - `@0,2:4` means the matched result only in the 0th and from 2nd to 3rd of dimensions will be output.
  - `@@` means the pattern of the group itself will be output other than the matched result.

### Boolean logic in the `/.../`

Given a 3-D sequence `[[d1, d2, d3], ... ]`,
- AND
`/X::Y/` will match D1 == `X` && D2 == `Y`.
Its behavior looks like the ordinary RE pattern `(?:X.Y)`.
- OR
`/X::/|/::Y/` will match D1 == `X` || D2 == `Y`.
Its behavior looks like the ordinary RE pattern `(?:X..)|(?:..Y)`
- NOT
if `/:^P:/` will match D2 != `P`.
Its behavior looks like the ordinary RE pattern `(?:.[^P].)`.
We can also use a negative lookahead assertion of ordinary RE,
to give a negative covered the following.
e.g. `(?!/:P://Q/)/:://::/` <==> `/:^P://^Q::/`,
which behavior looks like the ordinary RE pattern`(?!(?:.P.))...`.

## In addition

- **Not** support comparing the number of figures.

- Multi-values in one dimension is not supported now, but this feature may be improved later.

## Examples

```python
import seq_re

sr = seq_re.SeqRegex(n).compile(pattern, **placeholder_dict)
match = sr.search(seq)
if match:
    for g in match.group_list:
        print ' '.join(['`'.join(g[1])])
    for name in match.named_group_dict.iterkeys():
        print name, match.format_group_to_str(name)
```
