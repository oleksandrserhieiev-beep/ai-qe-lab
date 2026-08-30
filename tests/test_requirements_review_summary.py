from write_requirements_review_summary import _cell


def test_cell_escapes_markdown_table_separator():
    assert _cell("a|b") == "a\\|b"


def test_cell_converts_newline_for_markdown_table():
    assert _cell("line one\nline two") == "line one<br>line two"
