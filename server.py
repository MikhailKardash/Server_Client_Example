import numpy as np
import asyncio
from av import VideoFrame
import cv2
import datetime
import multiprocessing

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, TcpSocketSignaling


class CircleVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        height, width = 480, 640
        radius = 50

        # generate circle
        data_bgr = self._create_circle(radius, (255,0,255)).astype(np.float32)
        
        # generate background
        background = np.zeros((height, width, 3))

        self.frames = []
        for k in range(30):
            map_x = radius + 5 + 10 * k
            map_y = radius + 5 + 10 * k
            temp = background.copy()
            temp[map_y-radius:map_y+radius+1,map_x-radius:map_x+radius+1,:] = data_bgr
            self.frames.append(
                VideoFrame.from_ndarray(
                    temp.astype(np.uint8), format="bgr24"
                )
            )
        for k in range(29,-1,-1):
            map_x = radius + 5 + 10 * k
            map_y = radius + 5 + 10 * k
            temp = background.copy()
            temp[map_y-radius:map_y+radius+1,map_x-radius:map_x+radius+1,:] = data_bgr
            self.frames.append(
                VideoFrame.from_ndarray(
                    temp.astype(np.uint8), format="bgr24"
                )
            )
            
    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter % 60]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame
        
    def _create_circle(self, radius, color):
        data_bgr = np.zeros((radius*2+1, radius*2+1, 3), np.uint8)
        cx, cy = radius + 1, radius + 1
        y, x = np.ogrid[-radius:radius,-radius:radius]
        index = x**2 + y**2 <= radius**2
        data_bgr[cy-radius:cy+radius, cx-radius:cx+radius][index] = color
        return data_bgr


def channel_send(channel, message):
    channel.send(message)

async def run_offer(pc, signaling, window_name):
    channel = pc.createDataChannel("chat")
    reference = CircleVideoStreamTrack()
    frame = await reference.recv()
    
    def add_tracks():
        pc.addTrack(CircleVideoStreamTrack())

    await signaling.connect()
    
    async def get_video():
        while True:
            frame = await track.recv()
            frame = frame.to_ndarray()
            cv2.imshow(window,frame)
            cv2.waitKey(1)
    
    async def send_pings():
        while True:
            channel_send(channel, "ping")
            await asyncio.sleep(1)

    @channel.on("open")
    def on_open():
        asyncio.ensure_future(send_pings())

    @channel.on("message")
    def on_message(message):
        if isinstance(message,str):
            print(message)
            if message == 'pong':
                pass
            else:
                coords = message.split(',')
                print(coords)
                x = int(message[0])
                y = int(message[1])
                compx, compy = calc_coords(frame)
                print('Error: ' + str(np.sqrt((x-compx)**2 + (y-compy)**2)))
                

    # send offer  
    # add media player
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)
    while True:
        frame = await reference.recv()
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
            else:
                await pc.setLocalDescription(await pc.createOffer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break

def calc_coords(frame):
    frame = frame[10:480,10:640]
    for y in range(frame.shape[0]):
        for x in range(frame.shape[1]):
            if frame[y,x] > 50:
                return x,y
    return 0,0


if __name__ == '__main__':
    print("Starting Server")
    
    # create signaling object
    signaling = TcpSocketSignaling(host = "127.0.0.1", port = "8080")
    
    
    # create peer connection
    pc = RTCPeerConnection()
    
    # video window name
    window_name = 'ServerStream'
    
    # create event and run loop
    event = run_offer(pc,signaling, window_name)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(event)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
        cv2.destroyAllWindows()
