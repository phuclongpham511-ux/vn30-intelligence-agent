"""Online event memory. Call lookup before recording the current event."""
class EventMemory:
    def __init__(self):
        self._last = {}

    def days_since(self, ticker, event_type, replay_time):
        previous = self._last.get((ticker, event_type))
        if previous is None:
            return None
        if previous >= replay_time:
            raise ValueError("Event memory contains current/future event")
        return (replay_time.date() - previous.date()).days

    def record(self, ticker, event_type, replay_time):
        self.days_since(ticker, event_type, replay_time)
        self._last[ticker, event_type] = replay_time
