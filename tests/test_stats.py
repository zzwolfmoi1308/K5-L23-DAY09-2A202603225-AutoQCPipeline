from collections import Counter

from pipeline.checks import stats


def test_class_counts_keeps_odd_ids_as_strings(make_ds):
    ds = make_ds(images={"a": 1, "b": 2}, labels={"a": ["1 .5 .5 .1 .1", "1 .5 .5 .1 .1", "93 .5 .5 .1 .1"], "b": ["0 .5 .5 .1 .1", "", "  "]})
    assert stats.class_counts(ds) == Counter({"1": 2, "93": 1, "0": 1})


def test_rare_class_and_dense_image(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2}, labels={"a": ["1 .5 .5 .1 .1"] * 6, "b": ["0 .5 .5 .1 .1", "93 .5 .5 .1 .1"]})
    iss = stats.run(ds, cfg)
    rare = {i.extra["class"]: i for i in iss if i.code == "CLASS_RARE"}
    assert set(rare) == {"0", "93"} and rare["93"].image == "<dataset>" and rare["93"].severity == "warn"   # "1" có 6 box ≥ 3
    dense = [i for i in iss if i.code == "DENSE_IMAGE"]
    assert [(i.image, i.extra["n"]) for i in dense] == [("a", 6)]


def test_empty_dataset(make_ds, cfg):
    assert stats.run(make_ds(), cfg) == []
