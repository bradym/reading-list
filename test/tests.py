import readinglist.main
from urlparse import urlparse
from mock import MagicMock


from pprint import pprint

rl = readinglist.main.ReadingList()
rl.settings['tags'] = {
    'boardgames': {
        'domains': ['boardgamegeek.com'],
        'subs': ['boardgames', 'dominion']
    }
}


def test_is_github_url_pass():
    """
    Test a valid github url
    :return:
    """
    url = urlparse('https://github.com/nose-devs/nose')
    assert (rl.is_github_url(url) is True)


def test_is_github_url_fail():
    """
    Test a non-github url
    :return:
    """
    url = urlparse('http://example.com')
    assert (rl.is_github_url(url) is False)


def test_get_tags_by_subreddit_pass():
    """
    Test that a single tag is returned for a sub that is included
    :return:
    """
    sub = 'dominion'
    expected = ['boardgames']
    actual = rl.get_tags_by_subreddit(sub)
    assert (expected == actual)


def test_get_tags_by_subreddit_fail():
    """
    Check that no tags are returned for a sub that is not included
    :return:
    """
    sub = '7wonders'
    expected = ['boardgames']
    actual = rl.get_tags_by_subreddit(sub)
    assert (expected != actual)


def test_get_tags_by_domain_pass():
    """
    Check that a single tag is returned for a domain that is included
    :return:
    """
    domain = 'boardgamegeek.com'
    expected = ['boardgames']
    actual = rl.get_tags_by_domain(domain)
    assert (expected == actual)


def test_get_tags_by_domain_fail():
    """
    Check that a no tags are returned for a domain that is not included
    :return:
    """
    domain = 'example.com'
    expected = ['boardgames']
    actual = rl.get_tags_by_domain(domain)
    assert (expected != actual)
