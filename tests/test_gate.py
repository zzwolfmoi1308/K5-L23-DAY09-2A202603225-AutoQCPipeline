from pipeline.common import Issue
from pipeline.steps import gate


def iss(sev, image, code="X"):
    return Issue("c", sev, code, image, "m")


STEMS = [f"i{k}" for k in range(20)]


def test_rework_when_any_error(cfg):
    d = gate.decide([iss("error", "i1")], STEMS, cfg)
    assert d["decision"] == "Rework" and d["n_errors"] == 1 and d["reasons"]


def test_error_cannot_be_hidden_by_reviewed(cfg):
    assert gate.decide([iss("error", "i1")], STEMS, cfg, reviewed={"i1"})["decision"] == "Rework"


def test_hold_at_or_above_ratio(cfg):
    d = gate.decide([iss("warn", "i1"), iss("warn", "i2")], STEMS, cfg)         # 2/20 = 10% ≥ 10%
    assert d["decision"] == "Hold" and d["n_warn_images"] == 2 and d["warn_ratio"] == 0.1


def test_release_below_ratio(cfg):
    assert gate.decide([iss("warn", "i1")], STEMS, cfg)["decision"] == "Release"


def test_counts_images_not_issues(cfg):
    d = gate.decide([iss("warn", "i1", "A"), iss("warn", "i1", "B"), iss("warn", "i1", "C")], STEMS, cfg)
    assert d["n_warn_images"] == 1 and d["decision"] == "Release"


def test_reviewed_images_and_dataset_level_issues_are_ignored(cfg):
    issues = [iss("warn", "i1"), iss("warn", "i2"), iss("warn", "<dataset>"), iss("warn", "data.yaml")]
    d = gate.decide(issues, STEMS, cfg, reviewed={"i1", "i2"})
    assert d["decision"] == "Release" and d["n_warn_images"] == 0


def test_clean(cfg):
    d = gate.decide([], STEMS, cfg)
    assert d["decision"] == "Release" and d["n_images"] == 20 and d["warn_ratio"] == 0


# ---- ca khó hơn ----
def test_empty_dataset_does_not_divide_by_zero(cfg):
    d = gate.decide([], [], cfg)
    assert d["decision"] == "Release" and d["n_images"] == 0 and d["warn_ratio"] == 0


def test_exact_ratio_boundary_with_other_denominator(cfg):
    stems = [f"i{k}" for k in range(30)]
    d = gate.decide([iss("warn", f"i{k}") for k in range(3)], stems, cfg)       # 3/30 = 10% đúng ngưỡng
    assert d["decision"] == "Hold"


def test_warning_on_image_not_in_the_dataset_is_ignored(cfg):
    assert gate.decide([iss("warn", "đã_bị_xoá"), iss("warn", "i1")], STEMS, cfg)["n_warn_images"] == 1
