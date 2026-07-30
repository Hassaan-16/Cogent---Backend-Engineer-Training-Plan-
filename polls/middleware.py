import logging
import time

logger = logging.getLogger(__name__)

class SlowRequestLoggerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        if duration > 1.0:
            logger.warning(
                f"SLOW REQUEST: {request.path} took {duration:.2f} seconds."
            )

        return response
    