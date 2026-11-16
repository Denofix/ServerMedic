class AppError(Exception):
    def __init__(
        self, code: str, message: str, status: int = 400, headers: dict[str, str] | None = None
    ):
        self.code = code
        self.message = message
        self.status = status
        self.headers = headers or {}
        super().__init__(message)
