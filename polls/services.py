import time

def send_vote_analytics(choice_id):
    """
    Simulates a slow network call to an external analytics API.
    """
    print(
        f"--- Firing network request to Analytics API for choice {choice_id} ---"
    )
    time.sleep(2) # Simulating an API call

    return True
