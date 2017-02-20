# coding=utf-8

"""
Unit tests for readinglist
"""

import readinglist
from urlparse import urlparse
import mock

settings = {
    'reddit': {
        'username': 'fake',
        'password': 'fake',
        'client_id': 'fake',
        'client_secret': 'fake',
        'user_agent': 'reading-list'
    },

    'pinboard': {
        'apikey': 'fake'
    },

    'github': {
        'username': 'fake',
        'password': 'fake',
    },

    'ttrss': {
        'url': 'fake',
        'username': 'fake',
        'password': 'fake',
    },
    'tags': {
        'boardgames': {
            'domains': ['boardgamegeek.com'],
            'subs': ['boardgames', 'dominion']
        }
    }
}


@mock.patch('readinglist.readinglist.ReadingList.get_settings')
def test_is_github_url_pass(mock_get_settings):
    """
    Test a valid github url
    :return:
    """

    mock_get_settings.return_value = settings
    rl = readinglist.readinglist.ReadingList()

    url = urlparse('https://github.com/nose-devs/nose')
    assert rl.is_github_url(url) is True


@mock.patch('readinglist.readinglist.ReadingList.get_settings')
def test_is_github_url_fail(mock_get_settings):
    """
    Test a non-github url
    :return:
    """

    mock_get_settings.return_value = settings
    rl = readinglist.readinglist.ReadingList()

    url = urlparse('http://example.com')
    assert (rl.is_github_url(url) is False)


@mock.patch('readinglist.readinglist.ReadingList.get_settings')
def test_get_tags_by_subreddit_pass(mock_get_settings):
    """
    Test that a single tag is returned for a sub that is included
    :return:
    """

    mock_get_settings.return_value = settings
    rl = readinglist.readinglist.ReadingList()

    sub = 'dominion'
    expected = ['boardgames']
    actual = rl.get_tags_by_subreddit(sub)
    assert (expected == actual)


@mock.patch('readinglist.readinglist.ReadingList.get_settings')
def test_get_tags_by_subreddit_fail(mock_get_settings):
    """
    Test that no tags are returned for a sub that is not included
    :return:
    """

    mock_get_settings.return_value = settings
    rl = readinglist.readinglist.ReadingList()
    rl.settings = settings

    sub = '7wonders'
    expected = ['boardgames']
    actual = rl.get_tags_by_subreddit(sub)
    assert (expected != actual)


@mock.patch('readinglist.readinglist.ReadingList.get_settings')
def test_get_tags_by_domain_pass(mock_get_settings):
    """
    Check that a single tag is returned for a domain that is included
    :return:
    """

    mock_get_settings.return_value = settings
    rl = readinglist.readinglist.ReadingList()

    domain = 'boardgamegeek.com'
    expected = ['boardgames']
    actual = rl.get_tags_by_domain(domain)
    assert (expected == actual)


@mock.patch('readinglist.readinglist.ReadingList.get_settings')
def test_get_tags_by_domain_fail(mock_get_settings):
    """
    Check that a no tags are returned for a domain that is not included
    :return:
    """

    mock_get_settings.return_value = settings
    rl = readinglist.readinglist.ReadingList()

    domain = 'example.com'
    expected = ['boardgames']
    actual = rl.get_tags_by_domain(domain)
    assert (expected != actual)


@mock.patch('github3.GitHub.is_starred')
def test_star_github_repo_already_starred(mock_is_starred):
    """
    Check for correct behavior when a repo is already starred.
    :param mock_is_starred:
    :return:
    """

    mock_is_starred.return_value = True
    rl = readinglist.readinglist.ReadingList()

    repo = urlparse('https://github.com/bradym/reading-list')
    expected = True
    actual = rl.star_github_repo(repo)
    assert expected == actual


@mock.patch('github3.GitHub.is_starred')
def test_star_github_repo_already_starred(mock_is_starred):
    """
    Check for correct behavior when a repo is already starred.
    :param mock_is_starred:
    :return:
    """

    mock_is_starred.return_value = False
    rl = readinglist.readinglist.ReadingList()

    repo = urlparse('https://github.com/bradym/reading-list')
    expected = True
    actual = rl.star_github_repo(repo)
    assert expected == actual
