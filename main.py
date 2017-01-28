import praw
from pprint import pprint
import pinboard
import yaml
from unidecode import unidecode
import urlparse
import github3
import logging
from ttrss.client import TTRClient


class ReadingList:

    settings = None

    def __init__(self):

        logging.basicConfig(format='%(asctime)s \t %(levelname)s \t %(message)s', level=logging.DEBUG)

        self.settings = yaml.safe_load(open('settings.yml'))

        self.r = praw.Reddit(username=self.settings['reddit']['username'],
                             password=self.settings['reddit']['password'],
                             client_id=self.settings['reddit']['client_id'],
                             client_secret=self.settings['reddit']['client_secret'],
                             user_agent=self.settings['reddit']['user_agent'])

        self.pb = pinboard.Pinboard(self.settings['pinboard']['apikey'])
        self.gh = github3.login(self.settings['github']['username'], self.settings['github']['password'])
        self.ttrss = TTRClient(self.settings['ttrss']['url'],
                               self.settings['ttrss']['username'],
                               self.settings['ttrss']['password']).login()

    def get_tag_by_subreddit(self, subreddit):

        sub = subreddit.lower()

        if sub in self.settings['reddit']['subs']:
            return self.settings['reddit']['subs'][sub]['tags']
        else:
            return []

    def get_tag_by_domain(self, domain):

        if domain in self.settings['domain_tags']:
            return self.settings['domain_tags'][domain]['tags']
        else:
            return False

    def get_tag_by_description(self, description):

        # for string in self.settings['tags']:
        #     pprint(string)

        pprint(self.settings['tags'])


    def star_github_repo(self, url):

        info = url.path.split('/')
        username = info[1]
        repo = info[2]

        if not self.gh.is_starred(username, repo):
            return self.gh.star(username, repo)

    def process_saved_reddit_posts(self):

        for saved in self.r.user.me().saved(limit=1000):

            if isinstance(saved, praw.models.Submission):

                tags = self.get_tag_by_subreddit(saved.subreddit.display_name)

                if self.save_link(saved.url, saved.title, tags):
                    saved.unsave()

    def ttrss_unstar(self, article_id, mode, field, data=""):

        self.ttrss.update_article(article_id, mode, field, data)

    def process_ttrss_stars(self):

        for headline in self.ttrss.get_headlines(feed_id=-1, limit=1000):
            logging.info('Saving url to pinboard')
            tags = []

            if self.save_link(headline.link, headline.title, tags):
                logging.info('Link saved successfully')
                self.ttrss_unstar(headline.id, 0, 0)

    def save_link(self, url, title, tags):

        logging.info('Processing URL: {}'.format(url))

        parsed_url = urlparse.urlparse(url)

        if parsed_url.netloc == 'github.com':
            logging.info('URL is github repo, attempting to star repo.')
            if self.star_github_repo(parsed_url):
                logging.info('Repo starred successfully.')
                return True
        else:
            if len(tags) == 0:
                domain = parsed_url = urlparse.urlparse(saved.url).netloc
                tags = self.get_tag_by_domain(domain)

            if len(tags) > 0:
                logging.info('Saving url to pinboard with tags: {}'.format(','.join(tags)))
            else:
                logging.info('Saving url to pinboard with no tags.')

            if self.pb.posts.add(url=url, description=unidecode(title), toread=True, tags=tags):
                return True

    # def main(self):
    #
    #     self.process_saved_reddit_posts()
    #     self.process_ttrss_stars()

    def main(self):

        for sub in self.r.user.subreddits(limit=1000):
            print(sub.display_name)

if __name__ == '__main__':

    rl = ReadingList()
    rl.main()
