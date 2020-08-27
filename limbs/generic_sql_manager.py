import mysql.connector

from centipede.models.channel_data import ChannelData
from centipede.models.four_chan_thread import FourChanThread
from centipede.models.video_data import VideoData
from centipede.limbs.abstract.Limb import Limb
from centipede.internal.package import Package

from datetime import date, time
import datetime

import uuid
import json


class SqlManager(Limb):

    def __init__(self, config_dict):
        self.logger = config_dict["logger"]
        self.config = config_dict

        self.conn = mysql.connector.connect(host="127.0.0.1",
                                            user="",
                                            passwd="",
                                            database="TestingSchema",
                                            auth_plugin="mysql_native_password")


    def create_table_if_not_exist(self, class_name, attr_types):
        plural_class_name = class_name + "es" if class_name[-1].lower() in ["s", "x"] else class_name + "s"

        # Check for table presence
        curs = self.conn.cursor()
        curs.execute("SHOW TABLES")

        table_exists = False
        for table in curs:
            if table[0].lower() == plural_class_name.lower():
                table_exists = True

        # Create if the table does not exist
        if not table_exists:
            query = "CREATE TABLE " + plural_class_name + " ("

            for attr in attr_types:
                query += "`" + attr + "` "
                if attr_types[attr] == str:
                    query += "varchar(255), "
                elif attr_types[attr] == int:
                    query += "int, "
                elif attr_types[attr] == float:
                    query += "float, "
                elif attr_types[attr] == bool:
                    query += "bit, "
                elif attr_types[attr] == datetime.datetime:
                    query += "datetime, "

            query = query[:-2]
            query += ");"

            curs.execute(query)
            self.conn.commit()
            curs.close()


    def fetch_object_data(self, object):
        attr_to_type = {}
        attr_to_value = {}
        for attr in object.__dict__:
            if type(object.__dict__[attr]) in [str, int, float, bool, datetime.datetime]:
                attr_type = type(object.__dict__[attr])
                attr_value = object.__dict__[attr]
            else:
                attr_type = str
                attr_value = json.dumps(object.__dict__[attr])
            attr_to_type[attr] = attr_type
            attr_to_value[attr] = attr_value

        attr_to_type["_cent_ID"] = str
        attr_to_value["_cent_ID"] = str(uuid.uuid4())

        attr_to_type["_cent_timestamp"] = datetime.datetime
        attr_to_value["_cent_timestamp"] = datetime.datetime.now()

        class_name = object.__class__.__name__

        return class_name, attr_to_type, attr_to_value


    def insert_object(self, class_name, attrs_to_types, attrs_to_values):
        plural_class_name = class_name + "es" if class_name[-1].lower() in ["s", "x"] else class_name + "s"
        insert_part = "INSERT INTO " + plural_class_name + " "
        keyword_part = "("
        value_part = "VALUES ("

        for attr in attrs_to_values:
            keyword_part += "`" + attr + "`, "
            value_part += "%(" + attr + ")s, "

        keyword_part = keyword_part[:-2] + ") "
        value_part = value_part[:-2] + ")"

        query = insert_part + keyword_part + value_part + ";"

        cursor = self.conn.cursor()
        cursor.execute(query, attrs_to_values)
        self.conn.commit()
        cursor.close()


    def scrape_from_url(self, url, package):
        get_objects_fun = self.config["get_object_fun"]
        if get_objects_fun:
            objects = get_objects_fun(package)
            for object in objects:
                class_name, attrs_to_types, attrs_to_values = self.fetch_object_data(object)
                self.create_table_if_not_exist(class_name, attrs_to_types)
                self.insert_object(class_name, attrs_to_types, attrs_to_values)



def main():
    sql_commiter = SqlManager({"logger": None,
                               "get_object_fun": lambda pkg: pkg.threads})

    thread_obj = FourChanThread(input_dict={"is_pinned": False,
                                            "op_content": "OP Content",
                                            "post_datetime": datetime.datetime.now(),
                                            "image_content": "",
                                            "abbreviated": False,
                                            "body_cut_off": False,
                                            "post_num": "1020471246",
                                            "link": "URL"})

    pkg = Package()
    pkg.threads = [thread_obj]

    sql_commiter.scrape_from_url("", pkg)


if __name__ == "__main__":
    main()