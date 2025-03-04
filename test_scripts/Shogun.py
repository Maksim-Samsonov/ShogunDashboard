from vicon_core_api import *
from shogun_live_api import CaptureServices


async def connect_shogun(window):
    try:
        window.shogun_client = Client('localhost')
        window.capture = CaptureServices(window.shogun_client)
        return True
    except:
        window.btn.config(text="ShogunError")
        return False


async def startcapture(window):
    try:
        window.capture.start_capture()
        return window.capture.latest_capture_name()
    except:
        await window.display(0, "error Shogun")


async def stopcapture(window):
    try:
        window.capture.stop_capture(0)
    except:
        await window.display(0, "error Shogun")


async def check_shogun(window):
    try:
        status = str(window.capture.latest_capture_state())
        status_check = status.find('Started')
        print(status)
        if status_check != -1:
            return True
    except:
        await window.display(0, "error Shogun")