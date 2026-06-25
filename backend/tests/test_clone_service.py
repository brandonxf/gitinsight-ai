import pytest

from app.services.clone_service import CloneError, parse_github_url


@pytest.mark.parametrize(
    "url,owner,name",
    [
        ("https://github.com/owner/repo", "owner", "repo"),
        ("https://github.com/owner/repo.git", "owner", "repo"),
        ("https://github.com/owner/repo/", "owner", "repo"),
        ("  https://github.com/Some-Org/my.repo_v2  ", "Some-Org", "my.repo_v2"),
    ],
)
def test_parse_github_url_valid(url, owner, name):
    ref = parse_github_url(url)
    assert ref.owner == owner
    assert ref.name == name
    assert ref.url == f"https://github.com/{owner}/{name}"


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/owner/repo",  # no HTTPS
        "https://gitlab.com/owner/repo",  # no es github
        "https://github.com/owner",  # falta repo
        "https://github.com/owner/repo/extra",  # ruta extra (anti-SSRF)
        "ftp://github.com/owner/repo",
        "https://github.com.evil.com/owner/repo",  # host falsificado
        "",
        "not a url",
    ],
)
def test_parse_github_url_invalid(url):
    with pytest.raises(CloneError):
        parse_github_url(url)
