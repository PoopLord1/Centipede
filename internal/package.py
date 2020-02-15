"""
Package.py - defines a class that holds
"""

class Package(object):
    """
    A simple placeholder class meant to store abstract data, dependent on
    the specific needs of the application.
    """

    def __init__(self):
        """
        The "linked resources" for this data package refers to a list of URLs
        that are pushed onto the ingestion queue.
        """
        self.linked_resources = []

    def get_linked_resources(self):
        """
        Returns the resources that should be pushed onto the ingestion queue.
        """
        return self.linked_resources