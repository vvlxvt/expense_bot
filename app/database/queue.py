from collections import defaultdict, deque


class UserQueue:
    def __init__(self):
        # {user_id: deque([...])}
        self.users = defaultdict(deque)

    def is_empty(self, user_id):
        return not self.users[user_id]

    def queue(self, user_id, item):
        self.users[user_id].append(item)

    def dequeue(self, user_id):
        if self.users[user_id]:
            return self.users[user_id].popleft()
        return None

    def peek(self, user_id):
        if self.users[user_id]:
            return self.users[user_id][0]
        return None

    def clean(self, user_id):
        self.users[user_id].clear()


# Создаем один глобальный экземпляр
no_subs = UserQueue()
# user_1 = 12345
# user_2 = 11111
# no_subs.queue(user_1, "кофе 10")
# print(no_subs.peek(user_1))
#
# no_subs.queue(user_2, "кофе 20")
# print(no_subs.peek(user_2))
