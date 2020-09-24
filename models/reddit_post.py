"""
reddit_post.py - defines a class that holds information relevant to a post on reddit
"""


class RedditPost(object):
    def __init__(self, input_dict):

        self.post_id = ""
        self.points = ""
        self.post_author = ""
        self.post_datetime = "" # TODO - this should be a datetime object, not a string
        self.title = ""
        self.comments_link = ""
        self.content_link = ""
        self.subreddit = ""
        self.source = ""
        self.rank = 0

        if input_dict:
            self.post_id = input_dict.get("post_id", "")
            self.points = input_dict.get("points", "")
            self.post_author = input_dict.get("post_author", "")
            self.post_datetime = input_dict.get("post_datetime", "")
            self.title = input_dict.get("title", "")
            self.comments_link = input_dict.get("comments_link", "")
            self.content_link = input_dict.get("content_link", "")
            self.source = input_dict.get("source", "")
            self.rank = input_dict.get("rank", 0)
            self.subreddit = input_dict.get("subreddit", "")

    def __str__(self):
        return "<RedditPost from " + str(self.post_datetime) + " with comment id " + str(self.post_id) + ">"