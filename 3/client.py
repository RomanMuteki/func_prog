import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext


async def get_messages(mreader, text_window):
    while True:
        try:
            data = await mreader.readuntil(b'\n')
            if not data:
                break
            message = data.decode('utf-8', errors='ignore').strip()
            text_window.insert(tk.END, f"{message}\n")
            text_window.see(tk.END)
            print(f"Получено сообщение: {message}")
        except asyncio.IncompleteReadError:
            break
        except Exception as e:
            print(f"Ошибка при получении сообщения: {e}")


async def send_messages(mwriter):
    while True:
        message = await get_input("")
        mwriter.write(message.encode())
        await mwriter.drain()


async def get_input(prompt):
    iloop = asyncio.get_event_loop()
    user_input = await iloop.run_in_executor(None, input, prompt)
    return user_input


def on_send_button_click():
    global writer
    global loop

    message = entry_widget.get()
    entry_widget.delete(0, tk.END)
    asyncio.run_coroutine_threadsafe(send_message(writer, message), loop)


async def send_message(mwriter, message):
    mwriter.write(message.encode())
    await mwriter.drain()


async def main(text_widget):
    global reader
    global writer
    global loop

    reader, writer = await asyncio.open_connection('127.0.0.1', 8000)
    print("Подключено к серверу")

    receive_task = asyncio.create_task(get_messages(reader, text_widget))
    send_task = asyncio.create_task(send_messages(writer))

    await receive_task
    await send_task


def start_async_loop(text_widget):
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(text_widget))


def on_enter_pressed(event):
    on_send_button_click()


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("800x800")
    root.title("Клиент")

    text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=40, width=80)
    text_widget.pack(padx=16, pady=15)

    entry_widget = tk.Entry(root, width=64)
    entry_widget.pack(padx=(100, 0), pady=15, side=tk.LEFT)
    entry_widget.bind("<Return>", on_enter_pressed)

    send_button = tk.Button(root, text="Отправить", command=on_send_button_click)
    send_button.pack(padx=60, pady=15, side=tk.LEFT)

    asyncio_thread = threading.Thread(target=start_async_loop, args=(text_widget,))
    asyncio_thread.start()

    root.mainloop()
