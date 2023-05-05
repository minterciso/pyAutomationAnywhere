class AuthenticationError(Exception):
    """This class is responsible for showing authentication errors."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)