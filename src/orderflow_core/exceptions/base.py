class ApplicationError(Exception):
    message: str = 'Internal Application Error'

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    message: str = 'Resource not found'


class ConflictError(ApplicationError):
    message: str = 'State conflict error'
