def simple_error_response(msg, status, key="error"):
    return {key: msg}, status
