import asyncio
import tkinter as tk
from tkinter import scrolledtext
import threading


connected_clients = {}

chat_rooms = {'main': set()}


def update_widget(widget, text):
    widget.insert(tk.END, text + "\n")
    widget.see(tk.END)


async def handle_client_connection(reader, writer, client_list_widget, log_widget):
    client_ip = writer.get_extra_info('peername')
    update_widget(log_widget, f"Подключение от: {client_ip}")

    writer.write("Введите ваше имя: \n".encode())
    await writer.drain()

    client_name = (await reader.read(128)).decode().strip()
    connected_clients[writer] = client_name
    update_widget(client_list_widget, f"{client_name} ({client_ip})")

    writer.write(f"Введённое имя - {client_name}\n".encode())
    await writer.drain()

    writer.write("Отправьте \"/help\" для просмотра доступных команд): \n".encode())
    await writer.drain()

    writer.write("Вы присоединились к комнате: main\n".encode())
    await writer.drain()

    room_name = 'main'
    chat_rooms[room_name].add(writer)

    update_widget(log_widget, f"{client_name} присоединился к комнате: {room_name}")

    try:
        while True:

            message = await reader.read(256)
            if not message:
                break
            decoded_message = message.decode().strip()
            update_widget(log_widget, f"{client_name}&{room_name}: {decoded_message}")

            if decoded_message.startswith('/join'):
                room_name = decoded_message.split(' ')[1]
                await join_room(writer, room_name, log_widget)

            elif decoded_message.startswith('/leave'):
                await leave_room(writer, log_widget)

            elif decoded_message.startswith('/create'):
                room_name = decoded_message.split(' ')[1]
                await create_room(writer, room_name, log_widget)

            elif decoded_message.startswith('/current_chat'):
                await show_current_chat(writer)

            elif decoded_message.startswith('/m'):
                target_name = decoded_message.split(' ')[1]
                private_message = " ".join(decoded_message.split(' ')[2:])
                await send_private_message(writer, target_name, private_message)

            elif decoded_message.startswith('/help'):
                await show_help(writer)

            else:
                await broadcast_message(f"{client_name}: {decoded_message}\n", room_name)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        update_widget(log_widget, f"Ошибка: {e}")
    finally:
        connected_clients.pop(writer, None)
        await leave_room(writer, log_widget)
        writer.close()
        await writer.wait_closed()
        update_widget(log_widget, f"Отключение: {client_ip}")


async def join_room(writer, room_name, log_widget):
    await leave_room(writer, log_widget)

    if room_name not in chat_rooms:
        chat_rooms[room_name] = set()

    chat_rooms[room_name].add(writer)
    writer.write(f"Вы присоединились к комнате: {room_name}\n".encode())
    await writer.drain()
    update_widget(log_widget, f"{connected_clients[writer]} присоединился к комнате: {room_name}")


async def create_room(writer, room_name, log_widget):
    if room_name not in chat_rooms:
        chat_rooms[room_name] = set()

    writer.write(f"Комната '{room_name}' создана.\n".encode())
    await writer.drain()
    update_widget(log_widget, f"{connected_clients[writer]} создал комнату: {room_name}")


async def leave_room(writer, log_widget):
    for room_name, room_clients in chat_rooms.items():
        if writer in room_clients:
            room_clients.remove(writer)

            writer.write(f"Вы покинули комнату: {room_name}\n".encode())
            await writer.drain()
            update_widget(log_widget, f"{connected_clients[writer]} покинул комнату: {room_name}")
            break


async def show_current_chat(writer):
    for room_name, room_clients in chat_rooms.items():
        if writer in room_clients:
            writer.write(f"Вы находитесь в комнате: {room_name}\n".encode())
            await writer.drain()
            break


async def broadcast_message(message, room_name):
    if room_name in chat_rooms:
        for client_writer in chat_rooms[room_name]:
            try:
                client_writer.write(message.encode())
                await client_writer.drain()
            except Exception as e:
                update_widget(log_widget, f"Ошибка при отправке сообщения: {e}")


async def send_private_message(writer, target_name, message):
    target_writer = next((w for w, name in connected_clients.items() if name == target_name), None)
    if target_writer:
        try:
            sender_name = connected_clients[writer]

            writer.write(f"{sender_name} отправил личное сообщение {target_name}: {message}\n".encode())
            await writer.drain()

            target_writer.write(f"Личное сообщение от {sender_name}: {message}\n".encode())
            await target_writer.drain()

            update_widget(log_widget, f"{sender_name} отправил личное сообщение {target_name}: {message}")
        except Exception as e:
            update_widget(log_widget, f"Ошибка при отправке личного сообщения: {e}")
    else:
        writer.write("Пользователь не найден\n".encode())
        await writer.drain()


async def show_help(writer):
    help_message = (
        "/m <user> <message> - отправить личное сообщение\n"
        "/join <room> - присоединиться к комнате\n"
        "/create <room> - создать новую комнату\n"
        "/leave - покинуть текущую комнату\n"
        "/currentchat - показать текущую комнату\n"
    )
    writer.write(help_message.encode())
    await writer.drain()


async def start_server(client_list_widget, log_widget):
    server = await asyncio.start_server(
        lambda r, w: handle_client_connection(r, w, client_list_widget, log_widget),
        '127.0.0.1', 8000
    )
    async with server:
        await server.serve_forever()


def start_server_thread(client_list_window, log_tool):
    asyncio.run(start_server(client_list_window, log_tool))


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Сервер")

    client_list_widget = scrolledtext.ScrolledText(root, width=30, height=15)
    client_list_widget.pack(side=tk.LEFT, padx=10, pady=10)

    log_widget = scrolledtext.ScrolledText(root, width=50, height=15)
    log_widget.pack(side=tk.LEFT, padx=10, pady=10)

    threading.Thread(target=start_server_thread, args=(client_list_widget, log_widget), daemon=True).start()

    root.mainloop()
