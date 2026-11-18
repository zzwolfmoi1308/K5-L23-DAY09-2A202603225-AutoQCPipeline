import shutil

from PIL import Image

from pipeline.checks import duplicates
from conftest import save, smooth_image


def by(iss):
    return {i.image: i.code for i in iss}


def test_exact_duplicate_keeps_first(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2})
    shutil.copy(ds.images_dir / "a.jpg", ds.images_dir / "c.jpg")
    iss = duplicates.run(ds, cfg)
    assert by(iss) == {"c": "DUP_IMAGE_EXACT"} and iss[0].extra["of"] == "a" and iss[0].severity == "error"


def test_near_duplicate_after_resize(make_ds, cfg):
    ds = make_ds(images={"a": 1, "b": 2})
    im = Image.open(ds.images_dir / "a.jpg")
    save(im.resize((int(im.width * 0.9), int(im.height * 0.9))), ds.images_dir / "z_small.jpg", q=70)
    iss = duplicates.run(ds, cfg)
    assert by(iss) == {"z_small": "DUP_IMAGE_NEAR"}      # md5 khác nhau → md5 một mình KHÔNG bắt được (câu hỏi trong slide)
    assert "dist" in iss[0].extra


def test_unrelated_images_not_flagged(make_ds, cfg):
    ds = make_ds(images={f"i{k}": 100 + k for k in range(8)})
    assert duplicates.run(ds, cfg) == []


def test_threshold_is_read_from_config(make_ds, cfg):
    ds = make_ds(images={"a": 1})
    im = Image.open(ds.images_dir / "a.jpg")
    save(im.resize((160, 120)).crop((10, 8, 150, 112)).resize((320, 240)), ds.images_dir / "b.jpg", q=60)
    cfg["duplicates"]["phash_dist"] = 0
    strict = duplicates.run(ds, cfg)
    cfg["duplicates"]["phash_dist"] = 30
    loose = duplicates.run(ds, cfg)
    assert len(loose) >= len(strict) and by(loose) == {"b": "DUP_IMAGE_NEAR"}


def test_leak_into_test_set(make_ds, cfg, tmp_path):
    ref = tmp_path / "test_images"
    ref.mkdir()
    save(smooth_image(7), ref / "t1.jpg")
    cfg["intake"]["reference_dirs"] = [str(ref)]
    ds = make_ds(images={"a": 1, "leak": 7})
    got = by(duplicates.run(ds, cfg))
    assert got == {"leak": "LEAK_TEST"}


def test_corrupt_image_is_skipped_not_crash(make_ds, cfg):
    ds = make_ds(images={"a": 1, "bad": b"not an image at all"})
    assert duplicates.run(ds, cfg) == []
