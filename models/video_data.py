import json


class VideoData(object):
    """
    VideoData - contains data to identify and describe one YouTube video. Offers serialization options.
    """
    def __init__(self, input_dict=None):
        self.title = ""
        self.id = ""
        self.length = ""
        self.upload_date = None
        self.views = 0
        self.likes = 0
        self.dislikes = 0
        self.description = ""
        self.comments = []
        self.channel_id = ""
        self.num_comments = 0
        self.top_related_videos = []
        self.thumbnail_base64 = ""

        if input_dict:
            self.from_dict(input_dict)

    def from_dict(self, input_dict):
        """
        Initializes this VideoData using a dictionary as input.
        :param input_dict: a dictionary containing video-specific data.
        :return: None.
        """
        self.title = input_dict["title"]
        self.id = input_dict["id"]
        self.length = input_dict["length"]
        self.upload_date = input_dict["upload_date"]
        self.views = input_dict["views"]
        self.likes = input_dict["likes"]
        self.dislikes = input_dict["dislikes"]
        self.description = input_dict["description"]
        self.comments = input_dict["comments"]
        self.channel_id = input_dict["channel_id"]
        self.num_comments = input_dict["num_comments"]
        self.top_related_videos = input_dict["top_related_videos"]
        self.thumbnail_base64 = input_dict["thumbnail"]

    def to_dict(self):
        """
        Returns this video's information formatted as a dictionary.
        :return: A dictionary that describes this video.
        """
        out_dict = {"title": self.title,
                    "id": self.id,
                    "length": self.length,
                    "upload_date": self.upload_date,
                    "views": self.views,
                    "likes": self.likes,
                    "dislikes": self.dislikes,
                    "description": self.description,
                    "comments": self.comments,
                    "channel_id": self.channel_id,
                    "num_comments": self.num_comments,
                    "top_related_videos": self.top_related_videos,
                    "thumbnail": self.thumbnail_base64}

        return out_dict

    def as_json(self, **kwargs):
        """
        Serializes the current object as JSON.
        :return: a JSON-formatted string of information for this video.
        """
        return json.dumps(self.to_dict(), **kwargs)

    def get_linked_resources(self):
        # return self.top_related_videos
        return []
