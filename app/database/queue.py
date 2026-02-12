class UserQueue:
    def __init__(self):
        # Храним данные в формате {user_id: [список_объектов]}
        self.users = {}

    def is_empty(self, user_id):
        return len(self.users.get(user_id, [])) == 0

    def queue(self, user_id, item):
        if user_id not in self.users:
            self.users[user_id] = []
        self.users[user_id].append(item)

    def dequeue(self, user_id):
        if not self.is_empty(user_id):
            return self.users[user_id].pop(0)
        return None

    def peek(self, user_id):
        if not self.is_empty(user_id):
            return self.users[user_id][0]
        return None

    def clean(self, user_id):
        self.users[user_id] = []


# Создаем один глобальный экземпляр
no_subs = UserQueue()
