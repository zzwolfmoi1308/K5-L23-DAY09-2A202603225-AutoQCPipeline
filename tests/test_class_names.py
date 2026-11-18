from pipeline.checks import class_names


def test_ok(make_ds, cfg):
    assert class_names.run(make_ds(), cfg) == []


def test_unknown_name(make_ds, cfg):
    iss = class_names.run(make_ds(names=["car", "pedestrian", "truck", "bus"]), cfg)
    assert len(iss) >= 1 and all(i.code == "BAD_CLASS_NAME" and i.severity == "error" and i.image == "data.yaml" for i in iss)
    assert any("pedestrian" in i.message for i in iss)


def test_capitalised(make_ds, cfg):
    iss = class_names.run(make_ds(names=["Car", "person", "truck", "Bus"]), cfg)
    assert len(iss) == 2


def test_valid_name_wrong_position(make_ds, cfg):
    iss = class_names.run(make_ds(names=["person", "car", "truck", "bus"]), cfg)
    assert len(iss) >= 1


def test_missing_or_extra_class(make_ds, cfg):
    assert class_names.run(make_ds(names=["car", "person", "truck"]), cfg)
    assert class_names.run(make_ds(names=["car", "person", "truck", "bus", "bike"]), cfg)


def test_unreadable_names(make_ds, cfg):
    ds = make_ds()
    ds.yaml_path.write_text("path: .\n")
    assert class_names.run(ds, cfg)
