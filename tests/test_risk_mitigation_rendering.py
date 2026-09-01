from run_risk_analysis_batch import _join


def test_risk_register_list_fields_render_readably():
    assert _join(["ground generation", "reject unsupported facts"]) == "ground generation; reject unsupported facts"
    assert _join([]) == "-"
