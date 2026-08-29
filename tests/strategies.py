"""Hypothesis strategies. Imported directly, never registered as a plugin."""

from collections.abc import Mapping

from hypothesis import strategies as st

DATA_ESCAPES: Mapping[str, str] = {'%': '%25', '\r': '%0D', '\n': '%0A'}
PROPERTY_ESCAPES: Mapping[str, str] = {**DATA_ESCAPES, ':': '%3A', ',': '%2C'}

HOSTILE_CHUNKS = list('%\r\n:,=<>abc ') + [
    '%25',
    '%0D',
    '%0A',
    'ghadelimiter_',
    'EOF',
    '<<',
]

hostile_text = st.lists(st.sampled_from(HOSTILE_CHUNKS), max_size=12).map(''.join)

arbitrary_text = st.text(max_size=200)

command_names = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20
)

property_maps = st.dictionaries(command_names, hostile_text, max_size=5)

env_var_names = st.text(
    alphabet=st.characters(blacklist_categories=('Cs',)),
    min_size=1,
    max_size=50,
)

output_values = st.one_of(
    st.text(max_size=100),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=3),
    st.lists(st.integers(), max_size=3),
)

heading_levels = st.one_of(st.integers(min_value=-5, max_value=12), st.text(max_size=5))

posix_paths = st.lists(command_names, min_size=1, max_size=5).map('/'.join)
win32_paths = st.lists(command_names, min_size=1, max_size=5).map('\\'.join)
