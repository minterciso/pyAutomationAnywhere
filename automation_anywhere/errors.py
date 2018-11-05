class Error(Exception):
    """
    This class defines the Automation Anywhere API Error Exception

    :param message: The message to show as an error
    """

    def __init__(self, message):
        self.message = message