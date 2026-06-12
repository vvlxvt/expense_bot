from collections import defaultdict, deque


class UserQueue:
    def __init__(self):
        """Create per-user FIFO queues for pending uncategorized items."""
        # {user_id: deque([...])}
        self.users = defaultdict(deque)

    def is_empty(self, user_id):
        """Return True when a user's pending-item queue is empty."""
        return not self.users[user_id]

    def queue(self, user_id, item):
        """Append an item to a user's pending-item queue."""
        self.users[user_id].append(item)

    def dequeue(self, user_id):
        """Pop the oldest pending item for a user, if present."""
        if self.users[user_id]:
            return self.users[user_id].popleft()
        return None

    def peek(self, user_id):
        """Return the oldest pending item for a user without removing it."""
        if self.users[user_id]:
            return self.users[user_id][0]
        return None

    def clean(self, user_id):
        """Remove all pending items for a user."""
        self.users[user_id].clear()


# Создаем один глобальный экземпляр
no_subs = UserQueue()
