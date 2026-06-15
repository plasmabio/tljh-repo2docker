from tljh_repo2docker.docker import (
    _embed_credentials,
    compute_image_name,
    split_url_credentials,
)


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


def test_compute_image_name_strips_trailing_separator():
    # A trailing slash in the name turns into a trailing "-" which Docker
    # rejects; it must be stripped.
    image_name, _, name = compute_image_name(
        "https://github.com/jupyter-xeus/xeus-octave/",
        "HEAD",
        "github-com-jupyter-xeus-xeus-octave-",
    )
    assert name == "github-com-jupyter-xeus-xeus-octave"
    assert image_name == "github-com-jupyter-xeus-xeus-octave:HEAD"


def test_embed_credentials_https():
    out = _embed_credentials("https://github.com/foo/bar.git", "alice", "s3cret")
    assert out == "https://alice:s3cret@github.com/foo/bar.git"


def test_embed_credentials_url_encodes_special_chars():
    # @ / : are reserved in userinfo and must be percent-encoded.
    out = _embed_credentials("https://github.com/foo/bar.git", "u", "p@ss/word:1")
    assert out == "https://u:p%40ss%2Fword%3A1@github.com/foo/bar.git"


def test_embed_credentials_preserves_port():
    out = _embed_credentials("https://gitlab.local:8443/x/y.git", "u", "p")
    assert out == "https://u:p@gitlab.local:8443/x/y.git"


def test_embed_credentials_strips_existing_userinfo():
    out = _embed_credentials("https://old@github.com/foo/bar.git", "new", "tok")
    assert out == "https://new:tok@github.com/foo/bar.git"


def test_embed_credentials_skips_non_http_scheme():
    # SSH-style URLs are returned unchanged: embedding basic-auth makes no
    # sense for them and rewriting could corrupt the URL.
    out = _embed_credentials("git@github.com:foo/bar.git", "u", "p")
    assert out == "git@github.com:foo/bar.git"


def test_split_url_credentials_extracts_user_and_password():
    url, user, password = split_url_credentials(
        "https://alice:ghp_secret@github.com/foo/bar.git"
    )
    assert url == "https://github.com/foo/bar.git"
    assert user == "alice"
    assert password == "ghp_secret"


def test_split_url_credentials_decodes_percent_encoded_creds():
    url, user, password = split_url_credentials(
        "https://foo%40bar.com:p%40ss@github.com/x/y.git"
    )
    assert url == "https://github.com/x/y.git"
    assert user == "foo@bar.com"
    assert password == "p@ss"


def test_split_url_credentials_preserves_port():
    url, _, _ = split_url_credentials(
        "https://u:p@gitlab.local:8443/x/y.git"
    )
    assert url == "https://gitlab.local:8443/x/y.git"


def test_split_url_credentials_noop_when_no_userinfo():
    url, user, password = split_url_credentials("https://github.com/foo/bar.git")
    assert url == "https://github.com/foo/bar.git"
    assert user == ""
    assert password == ""


def test_split_url_credentials_skips_non_http_scheme():
    # SSH-style URLs (no scheme) carry no basic-auth — return unchanged.
    url, user, password = split_url_credentials("git@github.com:foo/bar.git")
    assert url == "git@github.com:foo/bar.git"
    assert user == ""
    assert password == ""
