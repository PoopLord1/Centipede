import mysql.connector

from centipede.models.channel_data import ChannelData
from centipede.models.comment_data import CommentData
from centipede.models.video_data import VideoData

from datetime import date, time


class SqlManager(object):

    def __init__(self):
        self.conn = mysql.connector.connect(host="",
                                            user="",
                                            passwd="",
                                            database="")

        self.create_tables_if_not_exist()

    def create_tables_if_not_exist(self):
        video_data_create_query = """CREATE TABLE video_data 
                                    ( 
                                    video_id int NOT NULL AUTO_INCREMENT, 
                                    url varchar(100) NOT NULL, 
                                    title varchar(100) NOT NULL, 
                                    channel_id varchar(100) NOT NULL, 
                                    length time NOT NULL,
                                    views long NOT NULL,
                                    date_uploaded date NOT NULL,
                                    likes long NOT NULL,
                                    dislikes long NOT NULL,
                                    PRIMARY KEY (video_id)
                                    );"""

        channel_data_create_query = """CREATE TABLE channel_data
                                        (
                                        channel_id int NOT NULL AUTO_INCREMENT,
                                        name varchar(100) NOT NULL,
                                        url varchar(100) NOT NULL,
                                        num_subscribers long NOT NULL, 
                                        num_videos long NOT NULL,
                                        date_created date NOT NULL,
                                        PRIMARY KEY (channel_id)
                                        );"""

        related_videos_create_query = """CREATE TABLE related_videos
                                        (
                                        src_video_id varchar(100) NOT NULL,
                                        related_video_id varchar(100) NOT NULL
                                        );"""

        associated_channels_create_query = """CREATE TABLE associated_channels
                                              (
                                              src_channel_id varchar(100) NOT NULL,
                                              associated_channel_id varchar(100) NOT NULL
                                              );"""

        comments_create_query = """CREATE TABLE comments
                                    (
                                    comment_id int NOT NULL AUTO_INCREMENT,
                                    video_url varchar(100) NOT NULL,
                                    body varchar(255) NOT NULL,
                                    commenter varchar(100) NOT NULL,
                                    commenter_id varchar(100) NOT NULL,
                                    comment_date date NOT NULL,
                                    score int NOT NULL,
                                    PRIMARY KEY (comment_id)
                                    );"""

        curs = self.conn.cursor()
        curs.execute("SHOW TABLES")

        has_video_data = False
        has_channel_data = False
        has_related_videos = False
        has_associated_channels = False
        has_comments = False

        for table in curs:
            if table[0].lower() == "video_data":
                has_video_data = True
            elif table[0].lower() == "channel_data":
                has_channel_data = True
            elif table[0].lower() == "related_videos":
                has_related_videos = True
            elif table[0].lower() == "associated_channels":
                has_associated_channels = True
            elif table[0].lower() == "comments":
                has_comments = True

        if not has_video_data:
            curs.execute(video_data_create_query)
        if not has_channel_data:
            curs.execute(channel_data_create_query)
        if not has_related_videos:
            curs.execute(related_videos_create_query)
        if not has_associated_channels:
            curs.execute(associated_channels_create_query)
        if not has_comments:
            curs.execute(comments_create_query)

    def insert_comments(self, comments):
        add_comment_q = ("INSERT INTO comments "
                         "(video_url, body, commenter, commenter_id, comment_date, score) "
                         "VALUES (%(video_url)s, %(body)s, %(commenter)s, %(commenter_id)s, %(comment_date)s, %(score)s)")

        cursor = self.conn.cursor()
        for comment in comments:
            cursor.execute(add_comment_q, comment.to_dict())

        self.conn.commit()
        cursor.close()

    def insert_video(self, video):
        add_video_q = ("INSERT INTO video_data "
                       "(url, title, channel_id, length, views, date_uploaded, likes, dislikes, animated, has_watermark) "
                       "VALUES (%(id)s, %(title)s, %(channel_id)s, %(length)s, %(views)s, %(upload_date)s, %(likes)s, %(dislikes)s, 0, 0)")

        cursor = self.conn.cursor()
        video_data = video.to_dict()
        del video_data["top_related_videos"]
        del video_data["comments"]
        cursor.execute(add_video_q, video_data)

        add_rel_video_q = ("INSERT INTO related_videos "
                           "(src_video_id, related_video_id) "
                           "VALUES (%(src_video_id)s, %(related_video_id)s)")
        for related_video in video.top_related_videos:
            cursor.execute(add_rel_video_q, {"src_video_id": video.id, "related_video_id": related_video})

        self.conn.commit()
        cursor.close()

    def insert_channel(self, channel):
        add_channel_q = ("INSERT INTO channel_data "
                         "(name, url, num_subscribers, num_videos, date_created) "
                         "VALUES (%(name)s, %(url)s, %(num_subscribers)s, %(num_videos)s, %(join_date)s)")

        cursor = self.conn.cursor()
        channel_data = channel.to_dict()
        del channel_data["associated_channels"]
        del channel_data["all_video_ids"]
        cursor.execute(add_channel_q, channel_data)

        add_assoc_channel_q = ("INSERT INTO associated_channels "
                               "(src_channel_id, associated_channel_id) "
                               "VALUES (%(src_channel_id)s, %(associated_channel_id)s)")
        for associated_channel in channel.associated_channels:
            cursor.execute(add_assoc_channel_q, {"src_channel_id": channel.url, "associated_channel_id": associated_channel})

        self.conn.commit()
        cursor.close()

    def insert(self, data):
        if isinstance(data, ChannelData):
            self.insert_channel(data)
        if isinstance(data, VideoData):
            self.insert_video(data)
            self.insert_comments(data.comments)


def main():
    sql_commiter = SqlManager()

    testing_comment = CommentData(input_dict={
        "video_url": "DEADBEEF",
        "body": "comment_body",
        "commenter": "commenter_name",
        "commenter_id": "DEADBEEF",
        "comment_date": date(2019, 5, 1),
        "score": -1
    })

    testing_video = VideoData(input_dict={
        "title": "Testing Title",
        "id": "DEADBEEF",
        "upload_date": date(2019, 5, 1),
        "length": time(0, 10, 30),
        "views": -1,
        "likes": -1,
        "dislikes": -1,
        "description": "Testing Description",
        "comments": [testing_comment],
        "channel_id": "DEADBEEF",
        "num_comments": 0,
        "top_related_videos": ["RELATED_1", "RELATED_2"],
        "video_filepath": "/does_not_exist.mp4",
        "thumbnail": "DEADBEEF"})

    testing_channel = ChannelData(input_dict={
        "name": "Channel1",
        "url": "DEADBEEF",
        "num_subscribers": -1,
        "associated_channels": ["DEADBEEF_related_channel"],
        "join_date": date(2019, 5, 1),
        "channel_views": -1,
        "description": "dummy description",
        "all_video_ids": ["DEADBEEF"]
    })

    sql_commiter.insert(testing_video)
    sql_commiter.insert(testing_channel)


if __name__ == "__main__":
    main()