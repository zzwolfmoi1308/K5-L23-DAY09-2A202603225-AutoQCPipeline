from pipeline.checks import label_format
from pipeline.common import Issue
from pipeline.steps import autofix


def err(code, image, line=None, **kw):
    return Issue("x", "error", code, image, "m", line, kw)


def lines(ds, stem):
    return ds.label_path(stem).read_text().splitlines()


def test_drop_several_lines_in_one_file_uses_original_numbers(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 .5 .5 .2 .2", "93 .5 .5 .2 .2", "1 .3 .3 .1 .1", "1 .5 .5 .2", "0 .7 .7 .1 .1"]})
    fx = autofix.fix(ds, [err("BAD_CLASS_ID", "a", 2), err("BAD_FORMAT", "a", 4)], cfg)
    assert lines(ds, "a") == ["1 .5 .5 .2 .2", "1 .3 .3 .1 .1", "0 .7 .7 .1 .1"]
    assert sorted((f["line"], f["action"]) for f in fx) == [(2, "drop_line"), (4, "drop_line")]
    assert all({"image", "line", "action", "before", "after"} <= set(f) for f in fx)


def test_clip_box(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 0.95 0.5 0.2 0.2"]})
    fx = autofix.fix(ds, [err("BOX_OUT_OF_IMAGE", "a", 1)], cfg)
    c, x, y, w, h = map(float, lines(ds, "a")[0].split())
    assert (c, round(x, 3), round(w, 3)) == (1, 0.925, 0.15) and fx[0]["action"] == "clip_box"


def test_box_fully_outside_is_dropped_not_negative(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 -0.18 0.46 0.04 0.18", "1 0.5 0.5 0.2 0.2"]})
    fx = autofix.fix(ds, [err("BOX_OUT_OF_IMAGE", "a", 1)], cfg)
    assert lines(ds, "a") == ["1 0.5 0.5 0.2 0.2"] and fx[0]["action"] == "drop_line"


def test_warnings_are_never_touched(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 .5 .5 .2 .2", "1 .5 .5 .001 .001"]})
    before = lines(ds, "a")
    fx = autofix.fix(ds, [Issue("x", "warn", "BOX_TINY", "a", "m", 2)], cfg)
    assert fx == [] and lines(ds, "a") == before


def test_rename_classes(make_ds, cfg):
    ds = make_ds(names=["car", "Person", "truck", "Bus"])
    fx = autofix.fix(ds, [err("BAD_CLASS_NAME", "data.yaml")], cfg)
    assert [ds.yaml_names()[i] for i in range(4)] == cfg["classes"] and fx[0]["action"] == "rename_classes"


def test_remove_images(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2}, labels={"a": ["1 .5 .5 .2 .2"], "b": ["1 .5 .5 .2 .2"]})
    fx = autofix.fix(ds, [err("DUP_IMAGE_EXACT", "b"), err("LEAK_TEST", "a")], cfg)
    assert ds.image_files() == [] and ds.label_files() == [] and {f["action"] for f in fx} == {"remove_image"}


def test_missing_label_goes_to_human_and_no_file_is_invented(make_ds, cfg):
    ds = make_ds(images={"a": 1})
    fx = autofix.fix(ds, [err("MISSING_LABEL_FILE", "a")], cfg)
    assert not ds.label_path("a").exists(), "không tạo file nhãn (kể cả rỗng): rỗng nghĩa là 'ảnh nền', không phải 'chưa gán'"
    assert [(f["image"], f["action"]) for f in fx] == [("a", "needs_label")]


def test_idempotent(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 .5 .5 .2 .2", "93 .5 .5 .2 .2"]})
    iss = label_format.run(ds, cfg)
    autofix.fix(ds, iss, cfg)
    assert label_format.run(ds, cfg) == [] and autofix.fix(ds, label_format.run(ds, cfg), cfg) == []


# ---- ca khó hơn: "xanh" mà logic sai thì sẽ bị bắt ở đây ----
def test_line_with_two_errors_is_dropped_once_and_not_clipped(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 .5 .5 .2 .2", "1 0.95 0.5 0.2 0.2", "0 .7 .7 .1 .1"]})
    fx = autofix.fix(ds, [err("BOX_OUT_OF_IMAGE", "a", 2), err("DUP_BOX", "a", 2)], cfg)
    assert lines(ds, "a") == ["1 .5 .5 .2 .2", "0 .7 .7 .1 .1"]
    assert [(f["line"], f["action"]) for f in fx] == [(2, "drop_line")], "dòng đã xoá thì không ghi thêm clip_box"


def test_blank_line_does_not_shift_original_line_numbers(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["1 .5 .5 .2 .2", "", "93 .5 .5 .2 .2", "0 .7 .7 .1 .1"]})
    fx = autofix.fix(ds, [err("BAD_CLASS_ID", "a", 3)], cfg)
    assert [l for l in lines(ds, "a") if l.strip()] == ["1 .5 .5 .2 .2", "0 .7 .7 .1 .1"]
    assert [(f["line"], f["action"]) for f in fx] == [(3, "drop_line")]


def test_issue_on_a_removed_image_does_not_crash_and_other_images_are_untouched(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2}, labels={"a": ["1 .5 .5 .2 .2", "93 .5 .5 .2 .2"], "b": ["1 .5 .5 .2 .2"]})
    before_b = ds.label_path("b").read_bytes()
    autofix.fix(ds, [err("DUP_IMAGE_EXACT", "a"), err("BAD_CLASS_ID", "a", 2)], cfg)
    assert [p.stem for p in ds.image_files()] == ["b"] and ds.label_path("b").read_bytes() == before_b
