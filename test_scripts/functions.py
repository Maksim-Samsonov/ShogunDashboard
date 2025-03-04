import asyncio
import threading
import Shogun
import HyperDeck


def _asyncio_thread(async_loop, task, window):
    async_loop.run_until_complete(do_command(task, window))


def start_command(async_loop, task, window):
    """ Button-Event-Handler starting the asyncio part. """
    print('star')
    threading.Thread(target=_asyncio_thread, args=(async_loop, task, window)).start()


async def do_command(task, window):
    if task == 'start':
        c_name = str(await Shogun.startcapture(window))
        n = c_name.find("'") + 1
        c_name = c_name[n:-2] + '_'
        if window.is_hyperdeck1:
            response = await window.hyperdeck1.record(c_name)
            disp = task + ' ' + str(response)
            await window.display(1, disp)
        if window.is_hyperdeck2:
            response = await window.hyperdeck2.record(c_name)
            disp = task + ' ' + str(response)
            await window.display(2, disp)

    elif task == 'start1':
        c_name = str(await Shogun.startcapture(window))
        n = c_name.find("'") + 1
        c_name = c_name[n:-2] + '_'
        response = await window.hyperdeck1.record(c_name)
        disp = task + ' ' + str(response)
        await window.display(1, disp)

    elif task == 'start2':
        c_name = str(await Shogun.startcapture(window))
        n = c_name.find("'") + 1
        c_name = c_name[n:-2] + '_'
        response = await window.hyperdeck2.record(c_name)
        disp = task + ' ' + str(response)
        await window.display(2, disp)

    elif task == 'stop':
        await Shogun.stopcapture(window)
        if window.is_hyperdeck1:
            response = await window.hyperdeck1.stop()
            disp = task + ' ' + str(response)
            await window.display(1, disp)
        if window.is_hyperdeck2:
            response = await window.hyperdeck2.stop()
            disp = task + ' ' + str(response)
            await window.display(2, disp)

    elif task == 'stop1':
        await Shogun.stopcapture(window)
        response = await window.hyperdeck1.stop()
        disp = task + ' ' + str(response)
        await window.display(1, disp)

    elif task == 'stop2':
        await Shogun.stopcapture(window)
        response = await window.hyperdeck2.stop()
        disp = task + ' ' + str(response)
        await window.display(2, disp)

    elif task == 'get_clips':
        clips = []
        if window.is_hyperdeck1:
            clips = (await open_clips_window(window.hyperdeck1, window.name1))
            await window.get_clip(clips, 1)

        if window.is_hyperdeck2:
            clips = (await open_clips_window(window.hyperdeck2, window.name2))
            await window.get_clip(clips, 2)

    elif task == 'connect':

        shogun_connected = await Shogun.connect_shogun(window)

        if not window.entry1.get() == '':
            ip_hyper1 = window.entry1.get()
            window.hyperdeck1 = HyperDeck.HyperDeck(ip_hyper1, 9993, window, window.async_loop)
            await window.hyperdeck1.connect()
            window.is_hyperdeck1 = True
            window.name1 = ip_hyper1 + ' '
            print(' connected to ip_hyper1')

        if not window.entry2.get() == '':
            ip_hyper2 = window.entry2.get()
            window.hyperdeck2 = HyperDeck.HyperDeck(ip_hyper2, 9993, window, window.async_loop)
            await window.hyperdeck2.connect()
            window.is_hyperdeck2 = True
            window.name2 = ip_hyper2
            print(' connected to ip_hyper2')

        if shogun_connected:
            await window.connect()

    elif task == 'test':
        print('test')
        await window.connect()


async def open_clips_window(device, name):
    clippers = await device.update_clips()
    print(clippers)
    return clippers
