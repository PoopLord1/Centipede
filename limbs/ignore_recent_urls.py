"""
ignore_recent_urls.py - Prune the list of next visited URLs based on when we last visited them
"""

from centipede.internal.package import Package

import mysql.connector
import datetime

IGNORE_TIME_THRESHOLD = datetime.timedelta(hours=2)


class IgnoreRecentUrls(object):

    def __init__(self, config_dict):
        self.logger = config_dict["logger"]
        self.config = config_dict

        self.conn = mysql.connector.connect(host="127.0.0.1",
                                            user="",
                                            passwd="",
                                            database="TestingSchema",
                                            auth_plugin="mysql_native_password")


    def create_table_if_not_exist(self):
        curs = self.conn.cursor()
        curs.execute("SHOW TABLES")

        table_exists = False
        for table in curs:
            if table[0].lower() == "url_visit_times":
                table_exists = True

        if not table_exists:
            query = "CREATE TABLE url_visit_times (`url` varchar(255), `visit_time` datetime);"
            curs.execute(query)
            self.conn.commit()
            curs.close()


    def write_url_visit_time(self, url):
        cursor = self.conn.cursor(buffered=True)

        check_presence_query = "SELECT url, visit_time FROM url_visit_times WHERE url = %s;"
        cursor.execute(check_presence_query, (url, ))
        exists = False
        if cursor.fetchone():
            exists = True

        if exists:
            update_query = "UPDATE url_visit_times SET visit_time = %s WHERE url=%s;"
            cursor.execute(update_query, (datetime.datetime.now(), url))

        else:
            insert_query = "INSERT INTO url_visit_times (url, visit_time) VALUES (%s, %s);"
            cursor.execute(insert_query, (url, datetime.datetime.now()))

        self.conn.commit()
        cursor.close()


    def fetch_last_visited_time(self, next_resource):
        cursor = self.conn.cursor()
        query = "SELECT url, visit_time FROM url_visit_times WHERE url = %s;"
        cursor.execute(query, (next_resource, ))

        visit_time = None
        # TODO - fix this pile of garbage (just return the first result, or sort by visit_time?)
        for (url, this_visit_time) in cursor:
            print(url, this_visit_time)
            print("Visit time received: " + str(this_visit_time))
            visit_time = this_visit_time

        cursor.close()
        return visit_time


    def scrape_from_url(self, url, package):
        self.create_table_if_not_exist()
        self.write_url_visit_time(url)

        print("Linked Resources Before: " + str(package.linked_resources))

        for next_resource in package.linked_resources:
            last_visited_time = self.fetch_last_visited_time(next_resource)
            print("Last visit time for " + next_resource + ": " + str(last_visited_time))
            if last_visited_time and datetime.datetime.now() - last_visited_time < IGNORE_TIME_THRESHOLD:
                package.linked_resources.remove(next_resource)

        print("Linked Resources After: " + str(package.linked_resources))


if __name__ == "__main__":
    url = "d1b5f81e158880a30e9210172e21709c"
    config = {"logger": None}
    package = Package()
    package.linked_resources = ["d1b5f81e158880a30e9210172e21709c", "7a0c13eac425663e5fd6a3c7470e6dbb"]

    ignore_recent_obj = IgnoreRecentUrls(config)
    ignore_recent_obj.scrape_from_url(url, package)