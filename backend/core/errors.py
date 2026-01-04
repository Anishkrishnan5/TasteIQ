class BadRequestError(Exception):
    """
    Raised when the client sends invalid input that
    should result in a 400 response.
    """
    def __init__(self, message: str):
        self.message = message
