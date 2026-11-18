from pipeline.checks import second_opinion as so


def run(make_ds, cfg, labels, preds, size=(640, 480)):
    ds = make_ds(images={"a": 1}, labels={"a": labels}, size=size)
    return [(i.code, i.line) for i in so.run(ds, cfg, preds={"a": preds})]


CAR = "0 0.5 0.5 0.3 0.4"               # nhãn: car, tâm giữa ảnh
def pred(cls=0, conf=0.9, box=(0.5, 0.5, 0.3, 0.4)):
    return [cls, conf, *box]


def test_agreement_is_silent(make_ds, cfg):
    assert run(make_ds, cfg, [CAR], [pred()]) == []


def test_possible_missing(make_ds, cfg):
    got = run(make_ds, cfg, [CAR], [pred(), pred(1, 0.95, (0.15, 0.3, 0.12, 0.3))])
    assert got == [("POSSIBLE_MISSING", None)]


def test_wrong_class(make_ds, cfg):
    assert run(make_ds, cfg, ["2 0.5 0.5 0.3 0.4"], [pred(0)]) == [("POSSIBLE_WRONG_CLASS", None)]


def test_loose_box(make_ds, cfg):
    loose = "0 0.5 0.5 0.46 0.6"          # IoU với box model ≈ 0.43 (≥ iou_missing 0.3, < iou_loose 0.6)
    assert run(make_ds, cfg, [loose], [pred()]) == [("POSSIBLE_LOOSE_BOX", None)]


def test_false_positive_reports_line_number(make_ds, cfg):
    got = run(make_ds, cfg, [CAR, "1 0.1 0.1 0.1 0.1"], [pred()])
    assert got == [("POSSIBLE_FALSE_POS", 2)]


def test_low_confidence_prediction_is_ignored_for_missing(make_ds, cfg):
    assert run(make_ds, cfg, [CAR], [pred(), pred(1, 0.3, (0.15, 0.3, 0.12, 0.3))]) == []


def test_tiny_prediction_is_ignored(make_ds, cfg):
    tiny = pred(1, 0.95, (0.15, 0.3, 0.02, 0.03))          # 0.02*640 × 0.03*480 ≈ 184 px² < 600
    assert run(make_ds, cfg, [CAR], [pred(), tiny]) == []


def test_thresholds_come_from_config(make_ds, cfg):
    cfg["second_opinion"]["conf"] = 0.99
    assert run(make_ds, cfg, ["2 0.5 0.5 0.3 0.4"], [pred(0, 0.9)]) == []


def test_image_without_label_file_or_preds_is_skipped(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2}, labels={"a": [CAR]})
    assert so.run(ds, cfg, preds={"a": [pred()]}) == []


def test_bad_lines_do_not_crash(make_ds, cfg):
    assert run(make_ds, cfg, [CAR, "garbage", "93 0.5 0.5 0.2 0.2"], [pred()]) == []
    iss = so.run(make_ds(images={"q": 1}, labels={"q": [CAR]}), cfg, preds={"q": [pred()]})
    assert all(i.severity == "warn" for i in iss)


# ---- ca khó hơn ----
def test_false_positive_uses_fp_conf_and_ignores_min_area(make_ds, cfg):
    low = pred(1, 0.3, (0.15, 0.3, 0.12, 0.3))                       # conf 0.3: dưới `conf` (0.5) nhưng trên `fp_conf` (0.25)
    tiny = pred(1, 0.95, (0.8, 0.8, 0.02, 0.03))                     # rất nhỏ (< min_area_px) nhưng vẫn là dự đoán "khớp" với nhãn
    labels = [CAR, "1 0.15 0.3 0.12 0.3", "1 0.8 0.8 0.02 0.03"]
    assert run(make_ds, cfg, labels, [pred(), low, tiny]) == []


def test_two_predictions_give_two_issues_in_prediction_order(make_ds, cfg):
    p1, p2 = pred(1, 0.9, (0.15, 0.3, 0.12, 0.3)), pred(2, 0.9, (0.85, 0.7, 0.12, 0.3))
    assert run(make_ds, cfg, [CAR], [pred(), p1, p2]) == [("POSSIBLE_MISSING", None), ("POSSIBLE_MISSING", None)]


def test_false_positive_line_number_survives_blank_lines(make_ds, cfg):
    assert run(make_ds, cfg, [CAR, "", "1 0.1 0.1 0.1 0.1"], [pred()]) == [("POSSIBLE_FALSE_POS", 3)]


def test_other_class_with_ambiguous_iou_is_silent(make_ds, cfg):
    # nhãn lớp 2, model nói lớp 0, IoU ≈ 0.43: ≥ iou_missing (0.3) nhưng < iou_match (0.5) -> không cờ gì
    assert run(make_ds, cfg, ["2 0.5 0.5 0.3 0.4"], [pred(0, 0.9, (0.62, 0.5, 0.3, 0.4))]) == []


def test_same_class_label_covers_the_object_even_if_other_class_overlaps(make_ds, cfg):
    assert run(make_ds, cfg, [CAR, "2 0.5 0.5 0.3 0.4"], [pred()]) == []
