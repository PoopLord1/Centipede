"""
reddit_comment.py - defines a class that holds information relevant to a comment on reddit
"""


class RedditComment(object):
    def __init__(self, input_dict):

        self.comment_id = ""
        self.content = ""
        self.comment_datetime = "" # TODO - make this a datetime object
        self.comment_author = ""
        self.points = ""
        self.subreddit = ""
        self.source = ""
        self.rank = 0

        if input_dict:
            self.comment_id = input_dict.get("comment_id", "")
            self.content = input_dict.get("content", "")
            self.comment_datetime = input_dict.get("comment_datetime", "")
            self.comment_author = input_dict.get("comment_author", "")
            self.points = input_dict.get("points", False)
            self.subreddit = input_dict.get("subreddit", "")
            self.source = input_dict.get("source", "")
            self.rank = input_dict.get("rank", 0)

    def __str__(self):
        return "<RedditComment from " + str(self.comment_datetime) + " with comment id " + str(self.comment_id) + ">"