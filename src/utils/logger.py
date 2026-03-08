import logging
import sys

class CustomFormatter(logging.Formatter):
    teal = "\033[36m"
    yellow = "\033[33m"
    reset = "\033[0m"
    # Added the format string to the constructor call
    fmt = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    def format(self, record):
        # We create a copy so we don't permanently modify the record levelname
        orig_levelname = record.levelname
        record.levelname = f"{self.teal}{orig_levelname}{self.reset}"
        
        orig_name = record.name
        record.name = f"{self.yellow}{orig_name}{self.reset}"

        # Initialize the formatter with our format string
        formatter = logging.Formatter(self.fmt, datefmt="%Y-%m-%d %H:%M:%S")
        result = formatter.format(record)
        
        # Restore the original name so other handlers don't get messed up
        record.levelname = orig_levelname
        return result



def getLogger(name: str):
  # 1. Get the root logger
  logger = logging.getLogger(name)
  logger.setLevel(logging.INFO)
  logger.propagate = False

  # 2. Clear existing handlers (to avoid double-logging in FastAPI/Uvicorn)
  if logger.hasHandlers():
      logger.handlers.clear()

  # 3. Create and add your custom handler
  if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
  
  return logger
