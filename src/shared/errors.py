class AppError(Exception):
  def __init__(self, message: str, code: str = "AppError"):
    self.message = message
    self.code = code

class CancellationError(AppError):
  def __init__(self, message, code = "Cancelled"):
    super().__init__(message, code)
