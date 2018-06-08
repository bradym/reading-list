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


class ReadingList(object):
    """
    Create bookmarks in wallabag from saved items in reddit and ttrss.
    """

    settings = None

    def __init__(self):
        logging.basicConfig(format='%(asctime)s \t %(levelname)s \t %(message)s', level=logging.DEBUG)

        self.credentials = {}
        self.domain_tags = {}
        self.subreddit_tags = {}

        self.gh = None

        self.settings_file_path = os.path.expanduser('~/.config/readinglist/settings.yaml')
        self.load_settings()

    def load_settings(self):
        """
        Read the settings file and save to python dict
        :return:
        """
        with open(self.settings_file_path) as f:
            data = yaml.safe_load(f)

        tags = data['tags']
        sub_tags = {}
        domain_tags = {}

        for current_tag in tags:
            for sub in tags[current_tag]['subreddits']:
                if sub not in sub_tags:
                    sub_tags[sub] = []
                sub_tags[sub].append(current_tag)

            for domain in tags[current_tag]['domains']:
                if domain not in domain_tags:
                    domain_tags[domain] = []
                domain_tags[domain].append(current_tag)

        self.credentials = data['credentials']
        self.subreddit_tags = sub_tags
        self.domain_tags = domain_tags

    def get_subreddit_tags(self, subreddit):
        """
        Given a subreddit, return the tags that should be applied.
        :param subreddit: name of the subreddit
        :return: list
        """

        return self.subreddit_tags[subreddit.lower()]

    def get_domain_tags(self, domain):
        """
        Return the tags associated with the given domain
        :param domain:  domain name
        :return: list
        """

        return self.domain_tags[domain.lower()]

    def process_saved_reddit_posts(self):
        """
        Get saved posts from reddit and process
        :return:
        """

        r = praw.Reddit(username=self.credentials['reddit']['username'],
                        password=self.credentials['reddit']['password'],
                        client_id=self.credentials['reddit']['client_id'],
                        client_secret=self.credentials['reddit']['client_secret'],
                        user_agent=self.credentials['reddit']['user_agent'])

        for saved in r.user.me().saved(limit=1000):
            if isinstance(saved, Submission):
                tags = self.get_subreddit_tags(saved.subreddit.display_name)
                if self.save_link(saved.url, saved.title, tags):
                    saved.unsave()

    def process_ttrss_stars(self):
        """
        Create bookmarks for starred articles in TTRSS
        :return:
        """

        for headline in self.ttrss.get_headlines(feed_id=-1, limit=1000):
            logging.info('Saving url to wallabag')
            tags = []

            if self.save_link(headline.link, headline.title, tags):
                logging.info('Link saved successfully')
                self.ttrss.update_article(headline.id, 0, 0)

    def is_github_repo(self, url):
        path_list = url.path.split('/')
        depth = len(path_list)

        if url.netloc != 'github.com' or depth != 3:
            logging.info('URL is not a github repo.')
            return False

        owner = path_list[1]
        repo_name = path_list[2]

        try:
            github3.repository(owner, repo_name)
            return True
        except github3.exceptions.NotFoundError:
            return False

    def github_login(self):
        if self.gh is None:
            self.gh = github3.login(self.credentials['github']['username'], self.credentials['github']['password'])
            try:
                me = self.gh.me()
                logging.info('Logged into GitHub as {}'.format(me.login))
            except github3.exceptions.AuthenticationFailed as e:
                logging.error('GitHub login failed: {}'.format(e.message))
                exit(1)

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

        if not self.gh.is_starred(username, repo):
            if self.gh.star(username, repo):
                logging.info('Repo starred successfully.')
        else:
            logging.info('Repo previously starred.')
            return True

    def save_link(self, url, title, tags):
        """
        Create bookmark in wallabag or star repo in github

        :param url:
        :param title:
        :param tags:
        :return:
        """

        logging.info('Processing URL: {}'.format(url))

        parsed_url = urlparse(url)

        if self.is_github_repo(parsed_url):
            logging.info('URL is github repo, attempting to star repo.')
            if self.star_github_repo(parsed_url):
                return True
        else:
            if len(tags) == 0:
                domain = parsed_url.netloc
                tags = self.get_domain_tags(domain)

            if len(tags) > 0:
                logging.info('Saving url to wallabag with tags: {}'.format(','.join(tags)))
            else:
                logging.info('Saving url to wallabag with no tags.')

            if self.wb.post_entries(url=url, title=unidecode(title), tags=tags):
                return True


def main():
    """
    CLI entry point
    :return:
    """

    rl = ReadingList()
    rl.process_saved_reddit_posts()
    rl.process_ttrss_stars()

if __name__ == '__main__':
    main()
