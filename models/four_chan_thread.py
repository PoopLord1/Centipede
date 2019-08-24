"""
four_chan_thread.py - defines a class that holds information relevant to a scraped 4chan thread
"""


class FourChanThread(object):
    def __init__(self, input_dict):

        self.is_pinned = False
        self.op_content = ""
        self.post_datetime = None
        self.image_contents = None
        self.abbreviated = False
        self.body_cut_off = False
        self.post_num = None
        self.link = ""

        if input_dict:
            self.is_pinned = input_dict.get("is_pinned", False)
            self.op_content = input_dict.get("op_content", "")
            self.post_datetime = input_dict.get("post_datetime", None)
            self.image_contents = input_dict.get("image_content", "")
            self.abbreviated = input_dict.get("abbreviated", False)
            self.body_cut_off = input_dict.get("body_cut_off", False)
            self.post_num = input_dict.get("post_num", None)
            self.link = input_dict.get("link", "")

    def __str__(self):
        return "<FourChanThread from " + str(self.post_datetime) + " with post number " + str(self.post_num) + ">"