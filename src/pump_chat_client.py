import websocket
import threading
import json
import time
import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PumpChatClient:
    def __init__(self, room_id, buffer_size=10, username="anonymous", message_history_limit=100):
        self.room_id = room_id
        self.buffer_size = buffer_size
        self.username = username
        self.message_history_limit = message_history_limit
        self.ws = None
        self.message_history = []
        self.is_connected = False
        self.ack_id = 0
        self.pending_acks = {}
        self.ping_timer = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_lock = threading.Lock()
        self.message_seq = 0  # Счетчик для сообщений

    def get_connection_status(self):
        return self.is_connected

    def on_open(self, ws):
        print("Connected to pump.fun chat")
        self.is_connected = True
        self.reconnect_attempts = 0

    def on_message(self, ws, message):
        type_message = message[:4]

        # print("ON_MESSAGE:", type_message)
        if type_message.startswith("0"):
            connect_data = json.loads(message[1:])
            if 'pingInterval' in connect_data:
                interval = connect_data['pingInterval'] / 1000.0
                self.start_ping(interval)
            self.send(f'40{{"origin":"https://pump.fun","timestamp":{int(time.time()*1000)},"token":null}}')

        elif type_message.startswith("40"):
            self.join_room()

        elif type_message.startswith("42"):
            self.handle_event(message[2:])

        elif type_message.startswith("43"):
            # Обрабатываем acknowledgment messages (43X где X может быть цифрой или пустым)
            if len(message) > 2 and message[2].isdigit():
                # Это numbered acknowledgment (430-439)
                self.handle_numbered_ack(message)
            else:
                # Это generic acknowledgment (43)
                self.handle_event_with_ack(message[2:])

        elif (
            type_message.startswith("430") or type_message.startswith("431") or
            type_message.startswith("432") or type_message.startswith("433") or
            type_message.startswith("434") or type_message.startswith("435") or
            type_message.startswith("436") or type_message.startswith("437") or
            type_message.startswith("438") or type_message.startswith("439")
        ):
            self.handle_numbered_ack(message)

        elif type_message.startswith("2"):
            self.send("3")

    def on_close(self, ws, close_status_code, close_msg):
        print("Disconnected from chat:")
        self.is_connected = False
        self.stop_ping()
        self.attempt_reconnect()

    def on_error(self, ws, error):
        print("Error:", error)

    def connect(self):
        self.ws = websocket.WebSocketApp(
            "wss://livechat.pump.fun/socket.io/?EIO=4&transport=websocket",
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )
        self.ws.run_forever()
        return True

    def disconnect(self):
        self.on_close()

    def stop(self):
        print("Stop from chat:")
        self.is_connected = False
        self.stop_ping()

    def send(self, data):
        if self.is_connected and self.ws:
            self.ws.send(data)
        else:
            print("Not connected. Cannot send data.")

    def attempt_reconnect(self):
        if not self.is_connected:
            return
        with self.reconnect_lock:
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                delay = min(2 ** self.reconnect_attempts, 30)
                print(f"Попытка переподключения #{self.reconnect_attempts} через {delay} сек...")

                def delayed_reconnect():
                    print("Идет переподключение...")
                    self.connect()

                timer = threading.Timer(delay, delayed_reconnect)
                timer.start()
            else:
                print("Достигнуто максимальное количество попыток переподключения")

    def join_room(self):
        ack_id = self.get_next_ack_id()
        join_json = json.dumps(["joinRoom", {"roomId": self.room_id, "username": self.username}])
        msg = f"42{ack_id}{join_json}"
        self.pending_acks[ack_id] = {"event": "joinRoom", "timestamp": time.time()}
        self.send(msg)

    def get_next_ack_id(self):
        current = self.ack_id
        self.ack_id = (self.ack_id + 1) % 10
        return current

    def start_ping(self, interval_seconds):
        if self.ping_timer:
            self.ping_timer.cancel()

        def ping_loop():
            if self.is_connected:
                self.send("2")

        self.ping_timer = threading.Timer(interval_seconds, ping_loop)
        self.ping_timer.start()

    def stop_ping(self):
        if self.ping_timer:
            self.ping_timer.cancel()
            self.ping_timer = None

    def set_paused(self, is_paused: bool):
        if is_paused:
            self.stop()
        elif not self.ping_timer and not self.is_connected:
            try:
                self.connect()
            except Exception as e:
                print(f"[PumpChatClient] Error connect for Pump.fun: {e}")

    def handle_event(self, json_str):
        try:
            event = json.loads(json_str)
            event_name = event[0]
            payload = event[1]

            if event_name == "newMessage":
                # Добавляем локальную временную метку и монотонно возрастающий ID
                try:
                    payload['timestamp'] = time.time()
                except Exception:
                    pass

                self.message_seq += 1
                payload['_id'] = self.message_seq

                # Поддерживаем лимит истории сообщений
                if len(self.message_history) >= self.message_history_limit:
                    self.message_history.pop(0)

                if payload.get('message') and len(payload['message'] ) > self.buffer_size:
                    payload['message'] = payload["message"][:self.buffer_size]

                self.message_history.append(payload)
                # print(f"[{payload.get('username')}]: {payload.get('message')}")

            elif event_name == "setCookie":
                self.request_message_history()

            elif event_name == "userLeft":
                pass
                # print(f"User left: {payload}")

        except Exception as e:
            print("Error handling event:", e)

    def handle_event_with_ack(self, json_str):
        """
        Обрабатывает acknowledgment messages без специфических ID (тип "43").
        Это обычно ответы на запросы без acknowledgment ID.
        Реализация на основе оригинального JavaScript кода.
        """
        try:
            # Парсим данные ответа (json_str уже без префикса "43")
            ack_data = json.loads(json_str)

            print(f"Received generic acknowledgment: {json_str[:100]}...")  # Логируем для отладки

            # Получаем первый элемент данных
            event_data = ack_data[0] if ack_data and len(ack_data) > 0 else None

            # Обрабатываем разные форматы ответов для истории сообщений
            if event_data and isinstance(event_data, dict) and 'messages' in event_data:
                # Ответ содержит массив сообщений в объекте
                messages = event_data['messages']
                if isinstance(messages, list):
                    print(f"Received message history via eventWithAck (format 1): {len(messages)} messages")
                    self._process_message_history(messages)

            elif isinstance(event_data, list):
                # Ответ напрямую является массивом сообщений
                print(f"Received message history via eventWithAck (format 2): {len(event_data)} messages")
                self._process_message_history(event_data)

            elif isinstance(ack_data, list) and len(ack_data) > 0 and isinstance(ack_data[0], list):
                # Ответ обернут в дополнительный массив
                messages = ack_data[0]
                print(f"Received message history via eventWithAck (format 3): {len(messages)} messages")
                self._process_message_history(messages)

            else:
                print(f"Unknown eventWithAck format: {type(event_data)}")

        except json.JSONDecodeError as e:
            print(f"Error parsing eventWithAck JSON: {e}")
        except Exception as e:
            print(f"Error handling eventWithAck: {e}")

    def _process_message_history(self, messages):
        """
        Вспомогательная функция для обработки истории сообщений.
        Добавляет уникальные ID и обновляет message_history.
        """
        if not isinstance(messages, list):
            return

        # Добавляем уникальные ID к историческим сообщениям
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            if '_id' not in msg:
                self.message_seq += 1
                msg['_id'] = self.message_seq
            if 'message' in msg and len(msg["message"]) > self.buffer_size:
                msg['message'] = msg["message"][:self.buffer_size]

        # Обновляем историю сообщений
        if not self.message_history:
            # Если история пустая, заполняем историческими сообщениями
            self.message_history = messages[-self.message_history_limit:]
        else:
            # Объединяем с существующей историей
            combined_history = messages + self.message_history
            self.message_history = combined_history[-self.message_history_limit:]

        print(f"Message history updated: {len(self.message_history)} total messages")

    def handle_numbered_ack(self, message):
        """
        Обрабатывает пронумерованные подтверждения (430-439).
        """
        try:
            # Извлекаем тип сообщения (например, "431" из "431[...]")
            match = re.match(r'^(\d+)', message)
            if not match:
                return

            message_type = match.group(1)

            # Получаем ID подтверждения (последняя цифра: 0-9)
            if len(message_type) >= 3:
                ack_id = int(message_type[-1])
            else:
                return

            # Ищем ожидающее подтверждение
            pending_ack = self.pending_acks.get(ack_id)

            if pending_ack:
                # Удаляем из списка ожидающих
                del self.pending_acks[ack_id]
                print(f"Received ack {message_type} for {pending_ack['event']}")

            # Парсим данные ответа (удаляем 3-символьный префикс)
            try:
                ack_data = json.loads(message[3:])
            except json.JSONDecodeError:
                print(f"Failed to parse ack data: {message[3:]}")
                return

            # Обрабатываем ответ в зависимости от типа оригинального запроса
            if pending_ack and pending_ack['event'] == "joinRoom":
                # Успешно присоединились к комнате, запрашиваем историю сообщений
                print("Successfully joined room, requesting message history...")
                self.request_message_history()

            elif pending_ack and pending_ack['event'] == "getMessageHistory":
                # Получили историю сообщений
                messages = ack_data[0] if ack_data and len(ack_data) > 0 else []

                if isinstance(messages, list):
                    print(f"Received {len(messages)} historical messages via numbered ack")
                    self._process_message_history(messages)
                else:
                    print(f"Unexpected message history format in numbered ack: {type(messages)}")

            elif pending_ack and pending_ack['event'] == "sendMessage":
                # Обрабатываем ответ на отправку сообщения
                if ack_data and len(ack_data) > 0 and isinstance(ack_data[0], dict):
                    if 'error' in ack_data[0]:
                        print(f"Server error: {ack_data[0]}")

        except Exception as e:
            print(f"Error parsing numbered acknowledgment: {e}")

    def request_message_history(self, limit=None):
        """Запрашивает историю сообщений с сервера"""
        ack_id = self.get_next_ack_id()
        limit_history = limit if limit else self.message_history_limit

        history_json = json.dumps(["getMessageHistory", {
            "roomId": self.room_id, 
            "before": None,
            "limit": limit_history
        }])

        msg = f"42{ack_id}{history_json}"
        self.pending_acks[ack_id] = {"event": "getMessageHistory", "timestamp": time.time()}

        print(f"Requesting message history with limit {limit_history}")
        self.send(msg)

    def get_count_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get messages from last count position"""
        if len(self.message_history) > 0:
            return self.message_history[-count:] if count <= len(self.message_history) else self.message_history
        return []

    def get_new_messages(self, last_id: int, limit: int) -> tuple:
        """Return messages with _id greater than last_id, up to limit. Also returns max _id seen."""
        new_messages = []
        max_id = last_id

        for msg in self.message_history:
            msg_id = msg.get('_id', 0)
            if msg_id > last_id:
                new_messages.append(msg)
                if len(new_messages) >= limit:
                    break
            if msg_id > max_id:
                max_id = msg_id

        return new_messages, max_id

    def get_message_history(self) -> List[Dict[str, Any]]:
        """Возвращает полную историю сообщений"""
        return self.message_history.copy()

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает последние сообщения"""
        return self.message_history[-limit:] if limit <= len(self.message_history) else self.message_history

    def get_latest_message(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнее сообщение или None если сообщений нет"""
        return self.message_history[-1] if self.message_history else None