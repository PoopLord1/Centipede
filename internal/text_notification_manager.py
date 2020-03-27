from twilio.rest import Client
import boto3

from centipede.limbs.common.personal_information import aws_sns_constants

import datetime

client = None
client = boto3.client("sns",
                      aws_access_key_id=aws_sns_constants.ACCESS_KEY,
                      aws_secret_access_key=aws_sns_constants.SECRET_KEY,
                      region_name="us-east-1")


def init_with_config(config_module):
    global ACCOUNT_ID, AUTH_TOKEN, DEST_NUMBER, TWILIO_NUMBER, client
    ACCOUNT_ID = config_module.TWILIO_ACCOUNT_ID
    AUTH_TOKEN = config_module.TWILIO_AUTH_TOKEN
    DEST_NUMBER = config_module.TWILIO_DEST_NUMBER
    TWILIO_NUMBER = config_module.TWILIO_SRC_NUMBER

    client = Client(ACCOUNT_ID, AUTH_TOKEN)

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
