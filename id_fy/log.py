import logging

from logging.handlers import TimedRotatingFileHandler
from flask import request, Flask

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s --- %(levelname)s --- %(message)s')
log_file = "IDfy.logs"
file_handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=5)
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
logging.shutdown()


# Logger modify
def log_data(message, event_type, log_level, additional_context=None):
    """
    Log an event with contextual information.

    Parameters:
    - user_id (int): The identifier of the user triggering the event.
    - message (str): The message or details of the event.
    - event_type (str): The type or category of the event.
    - log_level (int): The severity level of the log (e.g., logging.INFO, logging.WARNING).
    - additional_context (str or None): Additional context or information related to the event (optional).

    This function generates unique request and response IDs, extracts browser information and IP address
    from the request headers, and constructs a log message. The log message is then logged using the specified log level.

    Example:
    log(5, "Mandatory ifsc is missing", "IMPS Transaction Inquiry", logging. WARNING)

    """

    browser_info = request.headers.get('User-Agent')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    log_message = (f"message: {message}  ---  Event: {event_type} --- browser_info: {browser_info} - ip_address: {ip_address} --- "
                   f"{additional_context}")

    app.logger.log(log_level, log_message)