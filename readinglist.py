#!/usr/bin/env python
# coding=utf-8

"""
Import saved items from reddit and ttrss into wallabag.
"""

import logging
import os
from pprint import pprint
from urllib.parse import urlparse

import github3
import praw
import yaml
from praw.models import Submission
from ttrss.client import TTRClient
from unidecode import unidecode
from wallabag_api.wallabag import Wallabag
# import requests_toolbelt

formatter = logging.Formatter('%(asctime)s \t %(levelname)s \t %(message)s', '%Y-%m-%d %H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger()

if (logger.hasHandlers()):
    logger.handlers.clear()

logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

other_loggers = ['prawcore', 'github3', 'urllib3.connectionpool']

for logger_name in other_loggers:

    current_logger = logging.getLogger(logger_name)
    current_logger.handlers.clear()
    current_logger.addHandler(console_handler)
    current_logger.setLevel(logging.ERROR)


class ReadingList(object):
    """
    Create bookmarks in wallabag from saved items in reddit and ttrss.
    """

    def __init__(self):

        self.credentials = {}

        self.github = None
        self.reddit = None
        self.wallabag = None

        self.settings_file_path = os.path.expanduser('~/.config/readinglist/settings.yaml')
        self.load_settings()

    def load_settings(self):
        """
        Read the settings file and save to python dict
        :return:
        """
        with open(self.settings_file_path) as f:
            self.credentials = yaml.safe_load(f)

    def reddit_login(self):
        if self.reddit is None:
            logger.debug('Logging into Reddit')
            self.reddit = praw.Reddit(username=self.credentials['reddit']['username'],
                                      password=self.credentials['reddit']['password'],
                                      client_id=self.credentials['reddit']['client_id'],
                                      client_secret=self.credentials['reddit']['client_secret'],
                                      user_agent='reading-list')

    def github_login(self):
        if self.github is None:
            self.github = github3.login(self.credentials['github']['username'], self.credentials['github']['password'])
            try:
                me = self.github.me()
                logger.info('Logged into GitHub as {}'.format(me.login))
            except github3.exceptions.AuthenticationFailed as e:
                logger.error('GitHub login failed: {}'.format(e.message))
                exit(1)

    def wallabag_login(self):
        if self.wallabag is None:
            params = {
                'username': self.credentials['wallabag']['username'],
                'password': self.credentials['wallabag']['password'],
                'client_id': self.credentials['wallabag']['client_id'],
                'client_secret': self.credentials['wallabag']['client_secret'],
            }

            logger.debug('Logging into wallabag')

            host = self.credentials['wallabag']['host']
            token = Wallabag.get_token(host=host, **params)

            self.wallabag = Wallabag(
                host=host,
                client_secret=params['client_secret'],
                client_id=params['client_id'],
                token=token
            )

    def process_saved_reddit_posts(self):
        """
        Get saved posts from reddit and process
        :return:
        """
        self.reddit_login()


        logger.info('Getting saved items from reddit')

        after = None

        while True:
            for saved in self.reddit.user.me().saved(limit=50, params={'after': after}):
                if isinstance(saved, Submission):
                    if self.save_link(saved.url, saved.title):
                        saved.unsave()
                after = saved.id

            if after is None:
                logger.info('No more saved reddit items found')
                break

            logger.info('Getting more reddit posts')

    def process_ttrss_stars(self):
        """
        Create bookmarks for starred articles in TTRSS
        :return:
        """

        logger.debug('Getting starred articles from TTRSS')
        for headline in self.ttrss.get_headlines(feed_id=-1, limit=1000):
            if self.save_link(headline.link, headline.title):
                self.ttrss.update_article(headline.id, 0, 0)

    def is_github_repo(self, url):

        parsed_url = urlparse(url)

        path_list = parsed_url.path.split('/')
        depth = len(path_list)

        if parsed_url.netloc != 'github.com' or depth != 3:
            logger.debug('URL is not a github repo.')
            return False

        owner = path_list[1]
        repo_name = path_list[2]

        try:
            github3.repository(owner, repo_name)
            return True
        except github3.exceptions.NotFoundError:
            return False

    def star_github_repo(self, url):
        """
        Star a repository in github given the url
        :param url:
        :return:
        """
        self.github_login()

        info = urlparse(url).path.split('/')
        username = info[1]
        repo = info[2]

        if not self.github.is_starred(username, repo):
            if self.github.star(username, repo):
                logging.info('github repo {} starred successfully.'.format(username + '/' + repo))
        else:
            logging.info('github repo {} previously starred.'.format(username + '/' + repo))
            return True

    def save_link(self, url, title):
        """
        Create bookmark in wallabag or star repo in github

        :param url:
        :return:
        """

        self.wallabag_login()

        # TODO: add to youtube watch later playlist for youtube videos
        # TODO: Add to vimeo Watch Later Queue for vimeo videos

        logger.debug('Processing URL: {}'.format(url))

        if self.is_github_repo(url):
            logger.debug('{} is a github repo, attempting to star repo.'.format(url))
            if self.star_github_repo(url):
                return True
        else:
            if self.wallabag.post_entries(url=url, title=unidecode(title)):
                logger.info('Saved {} to wallabag'.format(url))
                return True


if __name__ == '__main__':
    rl = ReadingList()
    rl.process_saved_reddit_posts()
    # rl.process_ttrss_stars()