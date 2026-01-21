#!/usr/bin/env python
import sys
import os
import time
import signal
import psutil
import platform
import pynvml
import collections
from datetime import datetime

# Import only the modules for LCD communication
sys.path.insert(0, 'turing-smart-screen-python') 
from library.lcd.lcd_comm_rev_a import LcdCommRevA, Orientation

REFRESH_PERIOD = 1

VRAM_BUFFER_COUNT = 10

COM_PORT = "/dev/ttyACM0"

WIDTH, HEIGHT = 320, 480

assert WIDTH <= HEIGHT, "Indicate display width/height for PORTRAIT orientation: width <= height"

stop = False

gb = 1024**3

gpu_vram_buffers = [
    collections.deque(maxlen=VRAM_BUFFER_COUNT),
    collections.deque(maxlen=VRAM_BUFFER_COUNT),
    collections.deque(maxlen=VRAM_BUFFER_COUNT),
    collections.deque(maxlen=VRAM_BUFFER_COUNT)
]

if __name__ == "__main__":

    def sighandler(signum, frame):
        global stop
        stop = True

    # Set the signal handlers, to send a complete frame to the LCD before exit
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)
    is_posix = os.name == 'posix'
    if is_posix:
        signal.signal(signal.SIGQUIT, sighandler)

    # Build your LcdComm object based on the HW revision
    lcd_comm = LcdCommRevA(com_port=COM_PORT, display_width=WIDTH, display_height=HEIGHT)

    # Reset screen in case it was in an unstable state (screen is also cleared)
    lcd_comm.Reset()

    # Send initialization commands
    lcd_comm.InitializeComm()

    # Set brightness in % (warning: revision A display can get hot at high brightness! Keep value at 50% max for rev. A)
    lcd_comm.SetBrightness(level=20)

    # Set backplate RGB LED color (for supported HW only)
    lcd_comm.SetBackplateLedColor(led_color=(255, 255, 255))

    # Set orientation (screen starts in Portrait)
    lcd_comm.SetOrientation(orientation=Orientation.REVERSE_LANDSCAPE)

    # Define background picture
    background = f"res/background.png"

    # Display background
    lcd_comm.DisplayBitmap(background)

    # Get PC name
    pc_name = platform.node()

    # Display PC name
    lcd_comm.DisplayText(pc_name, 140, 0, 200, 20,
                         font="res/font.ttf",
                         font_size=18,
                         font_color=(100, 207, 213),
                         anchor="ma",
                         background_image=background)

    # Save starting time
    target_time = time.perf_counter()

    # Check if functions is available
    temperature_supported = hasattr(psutil, "sensors_temperatures")

    # Save names
    if temperature_supported:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            if "cpu" in name.lower() or "coretemp" in name.lower():
                temperature_cpu_name = name
                break

    # Get NVidia GPU count
    nvidia_gpu_count = 0

    try:
        pynvml.nvmlInit()
        nvidia_gpu_count = pynvml.nvmlDeviceGetCount()
    except pynvml.NVMLError as e:
        print(f"An NVML error occurred: {e}")

    if os.name == 'nt':
        disk_path = 'C:\\'
    else:
        disk_path = '/'

    # Display changing values
    while not stop:
        target_time += REFRESH_PERIOD

        # Calculate date and time
        current_datetime = datetime.now()
        current_date = current_datetime.strftime("%d.%m.%Y")
        current_time = current_datetime.strftime("%H:%M:%S")

        # Display date
        lcd_comm.DisplayText(current_date, 4, 0, 80, 20,
                            font="res/font.ttf",
                            font_size=18,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # Display time
        lcd_comm.DisplayText(current_time, 416, 0, 66, 20,
                            font="res/font.ttf",
                            font_size=18,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)
        
        # Calculate cpu load
        cpu_load = psutil.cpu_percent(interval=None)

        # Display CPU load
        lcd_comm.DisplayText(f"{cpu_load:.0f}%", 47, 46, 30, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="ma",
                            background_image=background)

        # Display CPU load bar
        lcd_comm.DisplayProgressBar(18, 66,
                                    width=84, height=5,
                                    min_value=0, max_value=100, value=cpu_load,
                                    bar_color=(249, 100, 0), bar_outline=False,
                                    background_image=background)

        # Calculate cpu temperature
        cpu_temp = 0

        if temperature_supported and temperature_cpu_name:
            temps = psutil.sensors_temperatures()
            cpu_temp = temps[temperature_cpu_name][0].current

        # Display CPU temperature
        lcd_comm.DisplayText(f"{cpu_temp:.1f}°C", 47, 76, 30, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="ma",
                            background_image=background)

        # Display CPU temperature bar
        lcd_comm.DisplayProgressBar(18, 96,
                                    width=84, height=5,
                                    min_value=0, max_value=100, value=cpu_temp,
                                    bar_color=(249, 100, 0), bar_outline=False,
                                    background_image=background)

        # Calculate ram
        ram = psutil.virtual_memory()

        percent_used_ram = ram.percent
        used_ram_gb = ram.used / gb
        free_ram_gb = ram.free / gb

        # Display RAM used percentage
        lcd_comm.DisplayText(f"{percent_used_ram:.0f}%", 167, 46, 30, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="ma",
                            background_image=background)

        # Display RAM used percentage bar
        lcd_comm.DisplayProgressBar(138, 66,
                                    width=84, height=5,
                                    min_value=0, max_value=100, value=percent_used_ram,
                                    bar_color=(249, 100, 0), bar_outline=False,
                                    background_image=background)

        # Display used RAM
        lcd_comm.DisplayText(f"{used_ram_gb:.1f} GB", 164, 76, 40, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # Display free RAM
        lcd_comm.DisplayText(f"{free_ram_gb:.1f} GB", 164, 90, 40, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # Calculate swap
        swap = psutil.swap_memory()

        percent_used_swap = swap.percent
        used_swap_gb = swap.used / gb
        free_swap_gb = swap.free / gb

        # Display swap used percentage
        lcd_comm.DisplayText(f"{percent_used_swap:.0f}%", 287, 46, 30, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="ma",
                            background_image=background)

        # Display swap used percentage bar
        lcd_comm.DisplayProgressBar(258, 66,
                                    width=84, height=5,
                                    min_value=0, max_value=100, value=percent_used_swap,
                                    bar_color=(249, 100, 0), bar_outline=False,
                                    background_image=background)

        # Display used swap
        lcd_comm.DisplayText(f"{used_swap_gb:.1f} GB", 284, 76, 40, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # Display free swap
        lcd_comm.DisplayText(f"{free_swap_gb:.1f} GB", 284, 90, 40, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # Calculate disk space
        disk = psutil.disk_usage(disk_path)

        percent_used_disk = disk.percent
        used_disk_gb = disk.used / gb
        free_disk_gb = disk.free / gb

        # Display disk used space percentage
        lcd_comm.DisplayText(f"{percent_used_disk:.0f}%", 407, 46, 30, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="ma",
                            background_image=background)

        # Display disk used space percentage bar
        lcd_comm.DisplayProgressBar(378, 66,
                                    width=84, height=5,
                                    min_value=0, max_value=100, value=percent_used_disk,
                                    bar_color=(249, 100, 0), bar_outline=False,
                                    background_image=background)

        # Display used space on disk
        lcd_comm.DisplayText(f"{used_disk_gb:.1f} GB", 404, 76, 40, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # Display free space on disk
        lcd_comm.DisplayText(f"{free_disk_gb:.1f} GB", 404, 90, 40, 16,
                            font="res/font.ttf",
                            font_size=12,
                            font_color=(249, 100, 0),
                            anchor="la",
                            background_image=background)

        # For each gpu:
        for gpu_num in range(4):

            # Calculate GPU stats
            gpu_vram_percent = 0
            gpu_load_percent = 0
            gpu_temp = 0

            if gpu_num < nvidia_gpu_count:
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_num)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

                gpu_vram_percent = utilization.memory
                gpu_load_percent = utilization.gpu
                gpu_temp = temp

            # Add value to plot
            gpu_vram_buffers[gpu_num].append(gpu_vram_percent)
            
            # Display VRAM usage
            lcd_comm.DisplayText(f"{gpu_vram_percent:.0f}%", (47+gpu_num*120), 141, 30, 16,
                                font="res/font.ttf",
                                font_size=12,
                                font_color=(249, 100, 0),
                                anchor="ma",
                                background_image=background)

            # Display VRAM usage bar
            lcd_comm.DisplayProgressBar((18+gpu_num*120), 161,
                                        width=84, height=5,
                                        min_value=0, max_value=100, value=gpu_vram_percent,
                                        bar_color=(249, 100, 0), bar_outline=False,
                                        background_image=background)

            # Display VRAM usage graph
            lcd_comm.DisplayLineGraph((18+gpu_num*120), 178, 86, 60,
                                    values=list(gpu_vram_buffers[gpu_num]),
                                    min_value=0,
                                    max_value=100,
                                    autoscale=False,
                                    line_color=(249, 100, 0),
                                    line_width=3,
                                    graph_axis=False,
                                    background_image=background)

            # Display GPU usage
            lcd_comm.DisplayText(f"{gpu_load_percent:.0f}%", (47+gpu_num*120), 246, 30, 16,
                                font="res/font.ttf",
                                font_size=12,
                                font_color=(249, 100, 0),
                                anchor="ma",
                                background_image=background)

            # Display GPU usage bar
            lcd_comm.DisplayProgressBar((18+gpu_num*120), 266,
                                        width=84, height=5,
                                        min_value=0, max_value=100, value=gpu_load_percent,
                                        bar_color=(249, 100, 0), bar_outline=False,
                                        background_image=background)

            # Display GPU temp
            lcd_comm.DisplayText(f"{gpu_temp:.0f}°C", (47+gpu_num*120), 276, 30, 16,
                                font="res/font.ttf",
                                font_size=12,
                                font_color=(249, 100, 0),
                                anchor="ma",
                                background_image=background)

            # Display GPU temp bar
            lcd_comm.DisplayProgressBar((18+gpu_num*120), 296,
                                        width=84, height=5,
                                        min_value=0, max_value=100, value=gpu_temp,
                                        bar_color=(249, 100, 0), bar_outline=False,
                                        background_image=background)

        # Calculate if sleep needed
        now = time.perf_counter()
        sleep_time = target_time - now

        # Sleep remaining time
        if sleep_time > 0:
            time.sleep(sleep_time)
        

    # Close serial connection at exit
    lcd_comm.closeSerial()

    # Shutdown pynvml connection at exit
    pynvml.nvmlShutdown()

