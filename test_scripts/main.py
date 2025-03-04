from tkinter import *
from tkinter.messagebox import askyesno
import functions
import asyncio
import time
import threading
import tkinter.font as font
import Shogun
import nest_asyncio
nest_asyncio.apply()


class MainWindow(object):
    def __init__(self):
        self.canvas = None
        self.root = None
        self.window1 = None
        self.window2 = None
        self.btn = None
        self.hyperdeck1 = None
        self.hyperdeck2 = None
        self.is_hyperdeck1 = False
        self.is_hyperdeck2 = False
        self.clips = None
        self.async_loop = None
        self.entry1 = None
        self.entry2 = None
        self.name = ''
        self.clip_window = None
        self.second_frame = None
        self.name1 = None
        self.name2 = None
        self.text0 = None
        self.text1 = None
        self.text2 = None
        self.my_listbox1 = None
        self.my_listbox2 = None
        self.titlebar = None
        self.shogun_client = None
        self.capture = None
        self.btn1_red = False
        self.btn2_red = False
        self.btn_shogun_red = False
        self.btn1 = None
        self.btn2 = None
        self.btn_shogun = None

    async def get_clip(self, clips, device):
        listbox = None
        if device == 1:
            listbox = self.my_listbox1
        elif device == 2:
            listbox = self.my_listbox2
        try:
            listbox.delete(0, END)
        except:
            print('pooling')

        for clip in clips:
            id = clip['id']
            name = ' ' + clip['name'] + ' '
            timecode = clip['timecode'] + ' '
            duration = clip['duration']
            n = id + name + timecode + duration
            listbox.insert(0, n)

    async def connect(self):

        print('connect')
        self.canvas.delete(self.window1)
        self.canvas.delete(self.window2)
        self.btn.destroy()
        self.root.geometry("1920x80")
        myFont1 = font.Font(size=25)
        myFont2 = font.Font(size=30)

        # UI for first device
        if self.is_hyperdeck1:
            self.btn1 = Button(self.title_bar, text=self.name1, fg='#fff', bg='#808080')
            self.btn1.pack(side=LEFT, padx=(0, 0))

            self.hyperdeck1_frame = Frame(self.canvas)

            Button(self.hyperdeck1_frame, text='●', fg='#FF0000', bg='#808080',
                   command=lambda: functions.start_command(self.async_loop, 'start1', self)).pack(side=LEFT, anchor=NW,
                                                                                                  fill=Y)

            Button(self.hyperdeck1_frame, text='◼', fg='#fff', bg='#808080',
                   command=lambda: functions.start_command(self.async_loop, 'stop1', self)).pack(side=LEFT, anchor=NW,
                                                                                                 fill=Y)
            Button(self.hyperdeck1_frame, text='Clips', fg='#fff', bg='#808080',
                   command=lambda: functions.start_command(self.async_loop, 'get_clips', self)).pack(side=LEFT,
                                                                                                     anchor=NW, fill=Y)

            scrollbar1 = Scrollbar(self.hyperdeck1_frame, orient=VERTICAL, command=self.canvas.yview)
            self.my_listbox1 = Listbox(self.hyperdeck1_frame, yscrollcommand=scrollbar1.set, height=3, width=80,
                                       fg='#fff', bg='#808080')
            self.text1 = Text(self.hyperdeck1_frame, height=3, width=20, fg='#fff', bg='#808080')
            # configure
            scrollbar1.config(command=self.my_listbox1.yview)
            self.hyperdeck1_frame.config(background="#808080")
            # pack
            self.text1.pack(side=LEFT)
            self.my_listbox1.pack(side=LEFT)
            scrollbar1.pack(side=RIGHT, fill=Y)
            self.hyperdeck1_frame.pack(side=LEFT, fill=Y)
        # UI for second device
        if self.is_hyperdeck2:
            self.btn2 = Button(self.title_bar, text=self.name2, fg='#fff', bg='#808080')
            self.btn2.pack(side=LEFT, padx=(650, 0))

            self.hyperdeck2_frame = Frame(self.canvas)
            Button(self.hyperdeck2_frame, text='●', fg='#FF0000', bg='#808080',
                   command=lambda: functions.start_command(self.async_loop, 'start2', self)).pack(side=LEFT, anchor=NW,
                                                                                                  fill=Y)
            Button(self.hyperdeck2_frame, text='◼', fg='#fff', bg='#808080',
                   command=lambda: functions.start_command(self.async_loop, 'stop2', self)).pack(side=LEFT, anchor=NW,
                                                                                                 fill=Y)
            Button(self.hyperdeck2_frame, text='Clips', fg='#fff', bg='#808080',
                   command=lambda: functions.start_command(self.async_loop, 'get_clips', self)).pack(side=LEFT,
                                                                                                     anchor=NW, fill=Y)

            scrollbar2 = Scrollbar(self.hyperdeck2_frame, orient=VERTICAL, command=self.canvas.yview)
            self.my_listbox2 = Listbox(self.hyperdeck2_frame, yscrollcommand=scrollbar2.set, height=3, width=80,
                                       fg='#fff', bg='#808080')
            self.text2 = Text(self.hyperdeck2_frame, height=3, width=20, fg='#fff', bg='#808080')
            # configure
            scrollbar2.config(command=self.my_listbox2.yview)
            self.hyperdeck2_frame.config(background="#808080")
            # pack
            self.text2.pack(side=LEFT)
            self.my_listbox2.pack(side=LEFT)
            scrollbar2.pack(side=RIGHT, fill=Y)
            self.hyperdeck2_frame.pack(side=LEFT)
        # Main UI
        self.btn_shogun = Button(self.title_bar, text='shogun', fg='#fff', bg='#808080')
        self.btn_shogun.pack(side=LEFT, padx=(1000, 0))
        buttons_frame = Frame(self.canvas)
        self.text0 = Text(buttons_frame, height=3, width=30, fg='#fff', bg='#808080')
        self.text0.pack(side=LEFT)

        stop_button = Button(buttons_frame, text='◼', fg='#fff', bg='#808080',
                             command=lambda: functions.start_command(self.async_loop, 'stop', self))
        stop_button['font'] = myFont1
        stop_button.pack(side=RIGHT, anchor=N, fill=Y)
        start_button = Button(buttons_frame, text='●', fg='#FF0000', bg='#808080',
                              command=lambda: functions.start_command(self.async_loop, 'start', self))
        start_button['font'] = myFont2
        start_button.pack(side=RIGHT, anchor=N, fill=Y)

        buttons_frame.pack(side=RIGHT)
        buttons_frame.config(background="#808080")
        # check status
        self.async_loop.run_until_complete(self.check_state())

    async def display(self, device, message):
        try:
            message = str(message)
        except:
            print('error')
            return
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        if device == 1:
            self.text1.insert(0.0, current_time + ' ' + '\n')
            self.text1.insert(0.0, message + '\n')

        elif device == 2:
            self.text2.insert(0.0, current_time + ' ' + '\n')
            self.text2.insert(0.0, message + '\n')

        elif device == 0:
            self.text0.insert(0.0, message + '\n' + current_time + '\n')

    async def check_state(self):
        while True:
            if self.is_hyperdeck1:
                if self.hyperdeck1.code.find('cord') != -1:
                    self.btn1.config(background="#FF0000")
                    self.btn1_red = True
                elif self.btn1_red:
                    self.btn1.config(background="#808080")
                    self.btn1_red = False

            if self.is_hyperdeck2:
                if self.hyperdeck2.code.find('cord') != -1:
                    self.btn2.config(background="#FF0000")
                    self.btn2_red = True
                elif self.btn2_red:
                    self.btn2.config(background="#808080")
                    self.btn2_red = False
            result = await Shogun.check_shogun(self)
            if result:
                if not self.btn_shogun_red:
                    self.btn_shogun.config(background="#FF0000")
                    self.btn_shogun_red = True
            elif self.btn_shogun_red:
                self.btn_shogun.config(background="#808080")
                self.btn_shogun_red = False
            await asyncio.sleep(2)

    def move_window(self, event):
        self.root.geometry('+{0}+{1}'.format(event.x_root, event.y_root))

    def close(self):
        self.async_loop.stop()
        self.root.destroy()

    def enter_button(self, event):
        print("enter_pressed")
        functions.start_command(self.async_loop, 'connect', self)


def main():
    window = MainWindow()
    window.root = Tk()
    window.root.configure(background='#666')
    window.root.attributes('-topmost', True)
    window.root.update()
    window.async_loop = asyncio.get_event_loop()

    window.root.overrideredirect(True)
    window.root.geometry('400x400+200+200')
    # window.root.title('HyperDeckController')

    window.canvas = Canvas(window.root, bg='#808080')

    window.title_bar = Frame(window.root, relief='raised', bd=1, bg='#666')

    # put a close button on the title bar
    close_button = Button(window.title_bar, text='X', command=lambda: window.close(), bg='#808080', fg='#fff')
    window.title_bar.pack(expand=1, fill=X, side=TOP)
    close_button.pack(side=RIGHT)

    # bind title bar motion to the move window function
    window.title_bar.bind('<B1-Motion>', window.move_window)

    window.entry1 = Entry(window.root)
    window.window1 = window.canvas.create_window(200, 70, window=window.entry1)
    window.entry1.bind("<Return>", window.enter_button)

    window.entry2 = Entry(window.root)
    window.window2 = window.canvas.create_window(200, 140, window=window.entry2)
    window.entry2.bind("<Return>", window.enter_button)

    window.btn = Button(window.root, text="Click to connect", bg='#808080', fg='#fff',
                        command=lambda: functions.start_command(window.async_loop, 'connect', window))
    # pack
    window.canvas.pack(fill=BOTH, expand=1)
    window.btn.pack(side=TOP, pady=10)
    window.root.mainloop()


if __name__ == "__main__":
    main()
