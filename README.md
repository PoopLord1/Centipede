# Centipede
Centipede is a data ingestion framework. For the time being, it is mostly used to acquire and process data scraped from the Internet. 

Centipede uses a series a of "limbs", or standardized classes, to represent a step in the ingestion process. Each limb has a series of configuration options to handle incoming data. One example is the SendText limb, which uses Twilio to send text notifications according to its configuration. Developers provide a function that accepts the current data package and returns True if it should send a text. This configuration is defined in a module-level dictionary:  


    SendText = {"get_text_flag": lambda thread: thread.is_malicious, 
                "message_template": "The thread was found to be malicious!"}

This config module is passed into the onstructor of the Centipede object. Afterwards, specify the pipeline with references to each of the classes you would like to invoke. Then "walk" along the data to process.

    import centipede_config

    def main():
        cent = Centipede(config=centipede_config)
        cent.define_limbs([FourChanScraper, DetectMaliceInText, DeepCopyPage, SendText])
        cent.walk()
        
This example code was taken from "FourChanMaliceDetection", found on my GitHub.  

### Limbs
Centipede allows the developer to architect a data ingestion pipeline using a system of "limbs", with each limb acting as a step in the pipeline. These limbs are designed to be generic enough to be repurposed for multiple projects.  

* __DeepCopyPage__ - Deeply saves an offline copy of the provided URL. Can do it under certain conditions if desired.
* __DetectMaliceInText__ - Given certain pieces of text, determines if there is a reference to a real location (specifically, a school or town)
* __FourChanScraper__ - Scrapes 4Chan to gather thread contents and other data
* __SendText__ - Conditionally sends a text to a given phone number
* __SqlManager__ - Saves Youtube-specific data to an SQL database
* __YoutubeDownloader__ - Given a Youtube video, downloads the video and saves it to a given directory
* __YoutubeScraper__ - Given the URL for a Youtube video, saves metadata for that Youtube video

