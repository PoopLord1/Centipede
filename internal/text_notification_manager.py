import boto3

from centipede.limbs.common.personal_information import aws_sns_constants

import datetime

client = boto3.client("sns",
                      aws_access_key_id=aws_sns_constants.ACCESS_KEY,
                      aws_secret_access_key=aws_sns_constants.SECRET_KEY,
                      region_name="us-east-1")

def text_alert_on_exception(func):
    """
    A decorator for functions - when they fail, a text message alert is sent.
    """
    def execute_wrapped_func(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            text_body = "There was an exception in " + func.__name__ + " - " + str(e)
            send_text_alert(text_body)
            raise e

    return execute_wrapped_func


def send_text_alert(text_body):
    """
    Sends a message to me with a given body.
    """
    client.publish(PhoneNumber=aws_sns_constants.DEST_NUMBER,
                   Message=text_body)


if __name__ == "__main__":

    @text_alert_on_exception
    def invalid_testing_function():
        raise Exception("Testing Exception made at " + str(datetime.datetime.now()))

    invalid_testing_function()
