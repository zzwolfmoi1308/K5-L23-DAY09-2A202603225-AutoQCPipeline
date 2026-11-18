from pipeline.checks import missing_labels


def codes(issues):
    return [(i.code, i.image) for i in issues]


def test_missing_orphan_empty(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2, "c": 3}, labels={"a": ["0 0.5 0.5 0.2 0.2"], "c": [], "zzz": ["0 .5 .5 .1 .1"]})
    got = codes(missing_labels.run(ds, cfg))
    assert ("MISSING_LABEL_FILE", "b") in got
    assert ("EMPTY_LABEL", "c") in got
    assert ("ORPHAN_LABEL", "zzz") in got
    assert not [g for g in got if g[1] == "a"]


def test_severity(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2}, labels={"a": [], "q": ["0 .5 .5 .1 .1"]})
    sev = {i.code: i.severity for i in missing_labels.run(ds, cfg)}
    assert sev["MISSING_LABEL_FILE"] == "error"
    assert sev["EMPTY_LABEL"] == "warn" and sev["ORPHAN_LABEL"] == "warn"


def test_uppercase_extension_is_still_an_image(make_ds, cfg):
    """Bẫy trong slide: đuôi .JPG bị bỏ qua → ảnh không được kiểm."""
    ds = make_ds(images={"x": 1}, labels={}, ext=".JPG")
    assert codes(missing_labels.run(ds, cfg)) == [("MISSING_LABEL_FILE", "x")]


def test_deterministic_order(make_ds, cfg):
    ds = make_ds(images={"d": 1, "b": 2, "a": 3, "c": 4})
    imgs = [i.image for i in missing_labels.run(ds, cfg)]
    assert imgs == sorted(imgs)


def test_clean_dataset_has_no_issue(make_ds, cfg):
    ds = make_ds(images={"a": 1}, labels={"a": ["0 0.5 0.5 0.2 0.2"]})
    assert missing_labels.run(ds, cfg) == []
