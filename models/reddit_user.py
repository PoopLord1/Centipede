"""
reddit_user.py - defines a class that holds information relevant to a user on Reddit
"""


class RedditUser(object):
    def __init__(self, input_dict):

        self.user_id = ""
        self.total_karma = ""
        self.cake_day_datetime = None

        if input_dict:
            self.user_id = input_dict.get("user_id", "")
            self.total_karma = input_dict.get("total_karma", "")
            self.cake_day_datetime = input_dict.get("cake_day_datetime", None)


    def __str__(self):
        return "<RedditUser from " + str(self.cake_day_datetime) + " with comment id " + str(self.user_id) + ">"