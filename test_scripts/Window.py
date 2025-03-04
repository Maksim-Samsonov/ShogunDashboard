import tkinter as tk
from tkinter import *
import asyncio
import threading
import Shogun
import HyperDeck


root = tk.Tk()
is_hyperdeck1 = False
is_hyperdeck2 = False


def _asyncio_thread(async_loop, task):
    async_loop.run_until_complete(do_command(task))


def start_command(async_loop, task):
    """ Button-Event-Handler starting the asyncio part. """
    threading.Thread(target=_asyncio_thread, args=(async_loop, task)).start()


async def do_command(task):
    if task == 'start':
        c_name =str(await Shogun.startcapture())
        n = c_name.find("'") + 1
        c_name =c_name[n:-2]+'_'
        print(c_name)
        if is_hyperdeck1:
            await hyperdeck1.record(c_name)
        if is_hyperdeck2:
            await hyperdeck2.record(c_name)

    elif task == 'stop':
        await Shogun.stopcapture()
        if is_hyperdeck1:
            await hyperdeck1.stop()
        if is_hyperdeck2:
            await hyperdeck2.stop()

    elif task == 'window':
        await open_new_window()

    elif task == 'get_clips':
        if is_hyperdeck1:
            await open_clips_window(hyperdeck1, entry1.get())
        if is_hyperdeck2:
            await open_clips_window(hyperdeck2, entry2.get())


async def open_clips_window(device, name):
        clips = await device.update_clips()
        print(clips)
        clip_window = Toplevel(root)
        clip_window.title('clips' + device.host)
        clip_window.geometry("400x400")
        for clip in clips:
            clip_label = Label(clip_window, text=clip)
            clip_label.pack(pady=10)


async def open_new_window():
    new_window = Toplevel(root)
    name = ''
    if not entry1.get() == '':
        ip_hyper1 = entry1.get()
        global hyperdeck1
        hyperdeck1 = HyperDeck.HyperDeck(ip_hyper1, 9993)
        await hyperdeck1.connect()
        global is_hyperdeck1
        is_hyperdeck1 = True
        name += ip_hyper1 + ' '
        print(ip_hyper1 + ' connected to ip_hyper1')

    if not entry2.get() == '':
        ip_hyper2 = entry2.get()
        global hyperdeck2
        hyperdeck2 = HyperDeck.HyperDeck(ip_hyper2, 9993)
        await hyperdeck2.connect()
        global is_hyperdeck2
        is_hyperdeck2 = True
        name += ip_hyper2
        print(ip_hyper2 + ' connected to ip_hyper2')

    async_loop = asyncio.get_event_loop()

    new_window.title(name)

    # sets the geometry of toplevel
    new_window.geometry("400x400")

    # A Label widget to show in toplevel
    Label(new_window,
          text=name).pack()
    Button(master=new_window, text='●', command=lambda: start_command(async_loop, 'start')).pack()
    Button(master=new_window, text='◼', command=lambda: start_command(async_loop, 'stop')).pack()
    Button(master=new_window, text='Get clips', command=lambda: start_command(async_loop, 'get_clips')).pack()


label = Label(root, text="Enter Both or one IP")

label.pack(pady=10)

canvas1 = tk.Canvas(root, width=400, height=300)

entry1 = tk.Entry(root)
canvas1.create_window(200, 140, window=entry1)
entry2 = tk.Entry(root)
canvas1.pack()
canvas1.create_window(200, 70, window=entry2)
canvas1.pack()
async_loop = asyncio.get_event_loop()
btn = Button(root,
             text="Click to connect",
             command=lambda: start_command(async_loop, "window"))
btn.pack(pady=10)

# mainloop, runs infinitely
mainloop()
