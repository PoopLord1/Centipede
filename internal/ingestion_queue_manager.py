"""
IngestionQueueManager - Manages, autosaves, and adds to the queue of resources to ingest.
"""

import threading
import os

from centipede.internal.job import Job

class IngestionQueueManager(object):

    def __init__(self, config=None):
        # A list of urls that are in queue to be scraped.
        self.config = config
        self.queue_lock = threading.Lock()
        self.ingestion_queue = []
        # No longer load from autosave

        self.autosave_thread = None
        self.batch_ingest_thread = None

        self.is_periodic = config["periodic"]
        self.period_seconds = -1

        if "period_seconds" in config:
            self.period_seconds = config["period_seconds"]

        for data_point in config["seed_urls"]:
            new_job = Job(data_point, self.is_periodic)
            new_job.set_period(self.period_seconds)
            self.ingestion_queue.append(new_job)


    def _load_autosave(self):
        base_dir = self.config["INGESTION_QUEUE_AUTOSAVE_BASE_DIR"]
        autosave_filename = os.path.join(base_dir, "ingestion_queue.txt")

        fp = open(autosave_filename, "r")
        self.queue_lock.acquire()
        ingestion_queue = fp.readlines()
        self.queue_lock.release()
        fp.close()

        return ingestion_queue

    def has_next(self):
        return len(self.ingestion_queue) > 0

    def next_resource(self):
        """
        Returns the next resource URL to be consumed
        """

        next_job = None

        if self.ingestion_queue[0].is_ready():
            next_job = self.ingestion_queue.pop(0)

            if next_job.repeat:
                new_job = Job(next_job.data_point, next_job.repeat)
                new_job.set_period(next_job.period)
                self.queue_lock.acquire()
                self.ingestion_queue.append(new_job)
                self.queue_lock.release()

        return next_job


    def push_data_point(self, url):
        """
        Adds a resource to the ingestion queue.
        """
        self.queue_lock.acquire()
        new_job = Job(url, False)
        self.ingestion_queue.append(new_job)
        self.queue_lock.release()


    def push_resources(self, resources):
        """
        Appends multiple new resources to the ingestion queue
        """
        new_jobs = []
        for resource in resources:
            new_jobs.append(Job(resource, False))

        self.queue_lock.acquire()
        self.ingestion_queue.extend(new_jobs)
        self.queue_lock.release()


    def _autosave_queue(self):
        """
        Saves the entire ingestion_queue to a file
        """
        base_dir = self.config.INGESTION_QUEUE_AUTOSAVE_BASE_DIR
        autosave_filename = os.path.join(base_dir, "ingestion_queue.txt")

        fp = open(autosave_filename, "w+")
        self.queue_lock.acquire()
        fp.write(self.ingestion_queue.join("\n"))
        self.queue_lock.release()
        fp.close()


    def _ingest_from_file(self):
        """
        Adds all resources described in a folder to the ingestion queue.
        """
        ingestion_input_base_dir = self.config.INGESTION_QUEUE_INPUT_DIR
        for filename in os.listdir(ingestion_input_base_dir):
            full_filepath = os.path.join(ingestion_input_base_dir, filename)
            fp = open(full_filepath, "r")
            resources = fp.readlines()
            fp.close()

            os.remove(full_filepath)

            self.queue_lock.acquire()
            self.ingestion_queue.extend(resources)
            self.queue_lock.release()


    def start_periodic_tasks(self):
        """
        Creates and starts the autosave and batch ingestion threads
        """
        autosave_thread = threading.Timer(10.0, self._autosave_queue)
        batch_ingest_thread = threading.Timer(10.0, self._ingest_from_file)

        autosave_thread.start()
        batch_ingest_thread.start()
