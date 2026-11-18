from pipeline.checks import label_format


def find(issues, code):
    return [(i.image, i.line) for i in issues if i.code == code]


def run(make_ds, cfg, lines, size=(640, 480)):
    ds = make_ds(images={"a": 1}, labels={"a": lines}, size=size)
    return label_format.run(ds, cfg)


def test_clean_lines(make_ds, cfg):
    assert run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "0 0.1 0.6 0.15 0.25"]) == []   # biên trái 0.1-0.075=0.025 ổn


def test_bad_format_and_line_numbers(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "1 0.5 0.5 0.2", "x 0.5 0.5 0.2 0.3", "1 nan 0.5 0.2 0.3", "1 0.5 0.5 0.2 0.3 0.9"])
    assert find(iss, "BAD_FORMAT") == [("a", 2), ("a", 3), ("a", 4), ("a", 5)]


def test_bad_class_id(make_ds, cfg):
    iss = run(make_ds, cfg, ["93 0.5 0.5 0.2 0.3", "4 0.5 0.5 0.2 0.3", "-1 0.5 0.5 0.2 0.3", "3 0.5 0.5 0.2 0.3"])
    assert find(iss, "BAD_CLASS_ID") == [("a", 1), ("a", 2), ("a", 3)]
    assert all(i.severity == "error" for i in iss if i.code == "BAD_CLASS_ID")


def test_overflow_vs_tolerance(make_ds, cfg):
    # dòng 2 tràn 0.05 (báo); dòng 3 tràn 0.0005 < tol 0.001 (không báo); dòng 4 biên đúng 1.0 (không báo)
    iss = run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "2 0.95 0.5 0.2 0.3", "1 0.9005 0.5 0.2 0.3", "1 0.9 0.5 0.2 0.3"])
    assert find(iss, "BOX_OUT_OF_IMAGE") == [("a", 2)]
    over = [i.extra["overflow"] for i in iss if i.code == "BOX_OUT_OF_IMAGE"][0]
    assert abs(over - 0.05) < 1e-3


def test_overflow_all_four_edges(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.05 0.5 0.2 0.3", "1 0.5 0.05 0.2 0.3", "1 0.95 0.5 0.2 0.3", "1 0.5 0.95 0.2 0.3"])
    assert find(iss, "BOX_OUT_OF_IMAGE") == [("a", 1), ("a", 2), ("a", 3), ("a", 4)]


def test_zero_size(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.5 0 0.3", "1 0.5 0.5 0.2 0.0"])
    assert find(iss, "BOX_ZERO") == [("a", 1), ("a", 2)]


def test_duplicate_box_reports_later_line(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "0 0.2 0.2 0.1 0.1", "1 0.501 0.5 0.2 0.3", "2 0.5 0.5 0.2 0.3"])
    assert find(iss, "DUP_BOX") == [("a", 3)]            # cùng lớp 1, IoU cao; dòng 4 khác lớp nên không tính


def test_tiny_and_huge_are_warnings(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.5 0.01 0.3", "1 0.5 0.5 0.99 0.99"], size=(640, 480))
    tiny = [i for i in iss if i.code == "BOX_TINY"]
    assert [(i.line, i.severity) for i in tiny] == [(1, "warn")]      # 0.01*640 = 6.4px < 12px
    assert find(iss, "BOX_HUGE") == [("a", 2)]


def test_blank_lines_keep_original_numbers(make_ds, cfg):
    ds = make_ds(images={"a": 1})
    (ds.labels_dir / "a.txt").write_text("1 0.5 0.5 0.2 0.3\n\n\n93 0.5 0.5 0.2 0.3\n")
    assert find(label_format.run(ds, cfg), "BAD_CLASS_ID") == [("a", 4)]


def test_broken_line_does_not_crash_and_other_lines_still_checked(make_ds, cfg):
    iss = run(make_ds, cfg, ["garbage", "1 0.97 0.5 0.2 0.3"])
    assert find(iss, "BAD_FORMAT") == [("a", 1)] and find(iss, "BOX_OUT_OF_IMAGE") == [("a", 2)]


# ---- ca khó hơn ----
def test_tiny_when_the_short_side_is_the_height(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.5 0.5 0.01"])                 # cao 0.01*480 = 4.8 px
    assert find(iss, "BOX_TINY") == [("a", 1)]


def test_overflow_at_bottom_edge_and_exact_boundary(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.97 0.2 0.1", "1 0.5 0.95 0.2 0.1"])   # dòng 1 chạm y=1.02 (tràn); dòng 2 chạm đúng 1.0 (ổn)
    assert find(iss, "BOX_OUT_OF_IMAGE") == [("a", 1)]


def test_blank_line_keeps_original_line_numbers(make_ds, cfg):
    iss = run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "", "93 0.5 0.5 0.2 0.3"])
    assert find(iss, "BAD_CLASS_ID") == [("a", 3)]


def test_duplicate_box_needs_the_same_class(make_ds, cfg):
    same = run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "1 0.5 0.5 0.2 0.3"])
    diff = run(make_ds, cfg, ["1 0.5 0.5 0.2 0.3", "2 0.5 0.5 0.2 0.3"])
    assert find(same, "DUP_BOX") == [("a", 2)] and find(diff, "DUP_BOX") == []
