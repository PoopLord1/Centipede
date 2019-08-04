import json


class CommentData(object):
    """
    VideoData - contains data to identify and describe one YouTube comment. Offers serialization options.
    """
    def __init__(self, input_dict=None):
        self.video_url = ""
        self.body = ""
        self.commenter = ""
        self.commenter_id = ""
        self.comment_date = None
        self.score = 0

        if input_dict:
            self.from_dict(input_dict)

    def from_dict(self, input_dict):
        """
        Assigns object attributes based on the input dict
        """
        self.video_url = input_dict["video_url"]
        self.body = input_dict["body"]
        self.commenter = input_dict["commenter"]
        self.commenter_id = input_dict["commenter_id"]
        self.comment_date = input_dict["comment_date"]
        self.score = input_dict["score"]

    def to_dict(self):
        """
        Returns a dictionary of attributes for the comment
        """
        return {"video_url": self.video_url,
                "body": self.body,
                "commenter": self.commenter,
                "commenter_id": self.commenter_id,
                "comment_date": self.comment_date,
                "score": self.score}

    def as_json(self):
        """
        Returns the comment as a JSON-serialized dictionary of attributes
        """
        return json.dumps(self.to_dict())