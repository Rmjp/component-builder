class ComponentError(Exception):
    def __init__(self, errors=None, message=''):
        self.message = f"Wire {errors} does not exists in graph. Wire initialized must be used."\
            if message == '' else message
        self.errors = errors
        super().__init__(message)
    def __str__(self):
        return self.message


class WireError(Exception):
    def __init__(self, errors=None, message=''):
        self.message = message
        self.errors = errors
        super().__init__(message)
    def __str__(self):
        return self.message
