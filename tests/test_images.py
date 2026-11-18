import io
import random

from PIL import Image

from pipeline.checks import images


def codes(iss):
    return sorted((i.code, i.image) for i in iss)


def test_good_and_uppercase_ext(make_ds, cfg):
    ds = make_ds(images={"ok": 1}, ext=".JPG")
    assert images.run(ds, cfg) == []


def test_truncated_image_detected_only_after_load(make_ds, cfg, tmp_path):
    buf = io.BytesIO()
    Image.effect_noise((640, 480), 80).convert("RGB").save(buf, "JPEG", quality=95)
    data = buf.getvalue()
    ds = make_ds(images={"cut": data[: len(data) // 2], "junk": bytes(random.Random(0).getrandbits(8) for _ in range(2048)), "good": 3})
    assert codes(images.run(ds, cfg)) == [("CORRUPT_IMAGE", "cut"), ("CORRUPT_IMAGE", "junk")]


def test_small_image(make_ds, cfg):
    ds = make_ds(images={"small": 1, "big": 2}, size=(320, 240))
    ds2 = make_ds(images={"tiny": 4}, size=(300, 150))
    got = codes(images.run(ds2, cfg))
    assert got == [("BAD_SIZE", "tiny")]                    # cạnh ngắn 150 < 200
    iss = images.run(ds2, cfg)
    assert iss[0].extra["size"] == [300, 150] and iss[0].severity == "error"


def test_min_side_is_inclusive(make_ds, cfg):
    ds = make_ds(images={"edge": 1}, size=(400, 200))
    assert images.run(ds, cfg) == []
