from tljh_repo2docker.docker import compute_image_name


def test_compute_image_name_explicit():
    image_name, ref, name = compute_image_name(
        "https://github.com/foo/bar", "abc123", "myenv"
    )
    assert image_name == "myenv:abc123"
    assert ref == "abc123"
    assert name == "myenv"


def test_compute_image_name_truncates_long_ref():
    long_ref = "a" * 40
    image_name, ref, _ = compute_image_name(
        "https://github.com/foo/bar", long_ref, "myenv"
    )
    assert ref == "aaaaaaa"
    assert image_name == "myenv:aaaaaaa"


def test_compute_image_name_short_ref_not_truncated():
    ref_39 = "b" * 39
    _, ref, _ = compute_image_name("https://github.com/foo/bar", ref_39, "myenv")
    assert ref == ref_39


def test_compute_image_name_empty_ref_defaults_to_head():
    image_name, ref, _ = compute_image_name("https://github.com/foo/bar", "", "myenv")
    assert ref == "HEAD"
    assert image_name == "myenv:HEAD"


def test_compute_image_name_none_ref_defaults_to_head():
    _, ref, _ = compute_image_name("https://github.com/foo/bar", None, "myenv")
    assert ref == "HEAD"


def test_compute_image_name_derives_name_from_repo():
    image_name, _, name = compute_image_name(
        "https://github.com/MyOrg/MyRepo", "main", ""
    )
    assert name == "myorg/myrepo".replace("/", "-")
    assert image_name == "myorg-myrepo:main"


def test_compute_image_name_lowercases_explicit_name():
    _, _, name = compute_image_name("https://github.com/foo/bar", "main", "MyEnv")
    assert name == "myenv"
