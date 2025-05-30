import sys

from loguru import logger

from lib.outlook.summarize import summarize_outlook

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")

if __name__ == "__main__":
    summarize_outlook()
