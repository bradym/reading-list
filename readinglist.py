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
import requests_toolbelt


class ReadingList(object):
    """
    Create bookmarks in wallabag from saved items in reddit and ttrss.
    """

    def __init__(self):
        logging.basicConfig(format='%(asctime)s \t %(levelname)s \t %(message)s', level=logging.DEBUG)

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
            self.reddit = praw.Reddit(username=self.credentials['reddit']['username'],
                                      password=self.credentials['reddit']['password'],
                                      client_id=self.credentials['reddit']['client_id'],
                                      client_secret=self.credentials['reddit']['client_secret'],
                                      user_agent=self.credentials['reddit']['user_agent'])

    def github_login(self):
        if self.github is None:
            self.github = github3.login(self.credentials['github']['username'], self.credentials['github']['password'])
            try:
                me = self.github.me()
                logging.info('Logged into GitHub as {}'.format(me.login))
            except github3.exceptions.AuthenticationFailed as e:
                logging.error('GitHub login failed: {}'.format(e.message))
                exit(1)

    def wallabag_login(self):
        if self.wallabag is None:
            params = {
                'username': self.credentials['wallabag']['username'],
                'password': self.credentials['wallabag']['password'],
                'client_id': self.credentials['wallabag']['client_id'],
                'client_secret': self.credentials['wallabag']['client_secret'],
            }
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
        self.reddit_login(self)

        for saved in self.reddit.user.me().saved(limit=1000):
            if isinstance(saved, Submission):
                if self.save_link(saved.url, saved.title):
                    saved.unsave()

    def process_ttrss_stars(self):
        """
        Create bookmarks for starred articles in TTRSS
        :return:
        """

        for headline in self.ttrss.get_headlines(feed_id=-1, limit=1000):
            if self.save_link(headline.link, headline.title):
                self.ttrss.update_article(headline.id, 0, 0)

    def is_github_repo(self, url):

        parsed_url = urlparse(url)

        path_list = parsed_url.path.split('/')
        depth = len(path_list)

        if parsed_url.netloc != 'github.com' or depth != 3:
            logging.info('URL is not a github repo.')
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

        info = url.path.split('/')
        username = info[1]
        repo = info[2]

        if not self.github.is_starred(username, repo):
            if self.github.star(username, repo):
                logging.info('Repo starred successfully.')
        else:
            logging.info('Repo previously starred.')
            return True

    def save_link(self, url):
        """
        Create bookmark in wallabag or star repo in github

        :param url:
        :return:
        """

        # TODO: add to youtube watch later playlist for youtube videos
        # TODO: Add to vimeo Watch Later Queue for vimeo videos

        logging.info('Processing URL: {}'.format(url))

        if self.is_github_repo(parsed_url):
            logging.info('{} is a github repo, attempting to star repo.'.format(url))
            if self.star_github_repo(parsed_url):
                return True
        else:
            logging.info('Saving {} to wallabag'.format(url))

            if self.wb.post_entries(url=url, title=unidecode(title), tags=tags):
                return True


if __name__ == '__main__':
    rl = ReadingList()
    rl.get_subreddits()
    rl.wallabag_login()
    rl.get_tags()

    pprint(rl.subreddit_tags)
    pprint(rl.wallabag_tags)


# self.ttrss = TTRClient(self.settings['ttrss']['url'],
#                        self.settings['ttrss']['username'],
#                        self.settings['ttrss']['password'],
#                        auto_login=True)
