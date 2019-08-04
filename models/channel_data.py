import json


class ChannelData(object):
    """
    ChannelData - contains data to identify and describe one YouTube channel. Offers serialization options.
    """
    def __init__(self, input_dict=None):
        self.name = ""
        self.url = ""
        self.num_subscribers = 0
        self.associated_channels = []
        self.join_date = None
        self.channel_views = 0
        self.description = ""
        self.all_video_ids = []
        self.num_videos = 0

        if input_dict:
            self.from_dict(input_dict)

    def from_dict(self, input_dict):
        """
        Initializes this ChannelData using a dictionary as input.
        :param input_dict: a dictionary containing channel-specific data.
        :return: None.
        """
        self.name = input_dict["name"]
        self.url = input_dict["url"]
        self.num_subscribers = input_dict["num_subscribers"]
        self.associated_channels = input_dict["associated_channels"]
        self.join_date = input_dict["join_date"]
        self.channel_views = input_dict["channel_views"]
        self.description = input_dict["description"]
        self.all_video_ids = input_dict["all_video_ids"]
        self.num_videos = len(self.all_video_ids)

    def to_dict(self):
        """
        Returns this channel's information formatted as a dictionary.
        :return: A dictionary that describes this channel.
        """
        out_dict = {"name": self.name,
                    "url": self.url,
                    "num_subscribers": self.num_subscribers,
                    "associated_channels": self.associated_channels,
                    "join_date": self.join_date,
                    "channel_views": self.channel_views,
                    "description": self.description,
                    "all_video_ids": self.all_video_ids,
                    "num_videos": self.num_videos}

        return out_dict

    def as_json(self):
        """
       Serializes the current channel object as nudes.
       :return: a JSON-formatted string of information for this channel.
       """
        return json.dumps(self.to_dict())

    def get_linked_resources(self):
        """
        Returns the resources that this resource links to
        :return: a list of new resources
        """
        return self.all_video_ids

