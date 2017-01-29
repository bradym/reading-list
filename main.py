#!/usr/bin/env python
# coding=utf-8

"""
Import saved items from reddit and ttrss into pinboard.
"""

import praw
from praw.models import Submission
import pinboard
import yaml
from unidecode import unidecode
from urlparse import urlparse
import github3
import logging
from ttrss.client import TTRClient


class ReadingList:

    settings = None

    def __init__(self):

        logging.basicConfig(format='%(asctime)s \t %(levelname)s \t %(message)s', level=logging.DEBUG)

        self.settings = yaml.safe_load(open('settings.yml'))

        self.ttrss = TTRClient(self.settings['ttrss']['url'],
                               self.settings['ttrss']['username'],
                               self.settings['ttrss']['password'],
                               auto_login=True)

        self.pb = pinboard.Pinboard(self.settings['pinboard']['apikey'])

        self.gh = github3.login(self.settings['github']['username'], self.settings['github']['password'])

    def get_tags_by_subreddit(self, subreddit):
        """
        Given a subreddit, return the tags that should be applied.
        :param subreddit: name of the subreddit
        :return: list
        """

        sub = subreddit.lower()

        tags = []

        for tag, tag_details in self.settings['tags'].iteritems():
            if tag_details is not None and 'subs' in tag_details and sub in tag_details['subs']:
                tags.append(tag)

        return tags

    def get_tags_by_domain(self, domain):
        """
        Return the tags associated with the given domain
        :param domain:  domain name
        :return: list
        """

        domain = domain.lower()

        tags = []

        for tag, tag_details in self.settings['tags'].iteritems():
            if tag_details is not None and 'domains' in tag_details and domain in tag_details['domains']:
                tags.append(tag)

        return tags

    def star_github_repo(self, url):
        """
        Star a repository in github given the url
        :param url:
        :return:
        """

        info = url.path.split('/')
        username = info[1]
        repo = info[2]

        if not self.gh.is_starred(username, repo):
            return self.gh.star(username, repo)

    def process_saved_reddit_posts(self):
        """
        Get saved posts from reddit and process
        :return:
        """

        r = praw.Reddit(username=self.settings['reddit']['username'],
                        password=self.settings['reddit']['password'],
                        client_id=self.settings['reddit']['client_id'],
                        client_secret=self.settings['reddit']['client_secret'],
                        user_agent=self.settings['reddit']['user_agent'])

        for saved in r.user.me().saved(limit=1000):

            if isinstance(saved, Submission):

                tags = self.get_tags_by_subreddit(saved.subreddit.display_name)

                if self.save_link(saved.url, saved.title, tags):
                    saved.unsave()

    def process_ttrss_stars(self):
        """
        Create bookmarks for starred articles in TTRSS
        :return:
        """

        for headline in self.ttrss.get_headlines(feed_id=-1, limit=1000):
            logging.info('Saving url to pinboard')
            tags = []

            if self.save_link(headline.link, headline.title, tags):
                logging.info('Link saved successfully')
                self.ttrss.update_article(headline.id, 0, 0)

    def save_link(self, url, title, tags):
        """
        Create bookmark in pinboard or star repo in github

        :param url:
        :param title:
        :param tags:
        :return:
        """

        logging.info('Processing URL: {}'.format(url))

        parsed_url = urlparse(url)

        if parsed_url.netloc == 'github.com':
            logging.info('URL is github repo, attempting to star repo.')
            if self.star_github_repo(parsed_url):
                logging.info('Repo starred successfully.')
                return True
        else:
            if len(tags) == 0:
                domain = parsed_url.netloc
                tags = self.get_tags_by_domain(domain)

            if len(tags) > 0:
                logging.info('Saving url to pinboard with tags: {}'.format(','.join(tags)))
            else:
                logging.info('Saving url to pinboard with no tags.')

            if self.pb.posts.add(url=url, description=unidecode(title), toread=True, tags=tags):
                return True

if __name__ == '__main__':

    rl = ReadingList()
    rl.process_saved_reddit_posts()
    rl.process_ttrss_stars()
