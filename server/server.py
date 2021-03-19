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
    RTCDataChannel
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, TcpSocketSignaling


class CircleVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns a moving circle.
    I hardcode this to have height, width of 480x640
    Circle has a radius of 50.
    Animation lasts 60 frames, 30 moving in one direction
    and 30 moving in the opposite direction.
    Construction is done in numpy.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0 #frame state.
        height, width = 480, 640
        radius = 50

        # generate circle
        data_bgr = self._create_circle(radius, (255,255,255)).astype(np.float32)
        
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
        """
        Async function that advances the frame state.
        """
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter % 60]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame
        
    def _create_circle(self, radius, color):
        """
        Helper function that draws a circle in RGB/BGR.
        Circle has diameter of 2*radius + 1.
        """
        data_bgr = np.zeros((radius*2+1, radius*2+1, 3), np.uint8)
        cx, cy = radius + 1, radius + 1
        y, x = np.ogrid[-radius:radius,-radius:radius]
        index = x**2 + y**2 <= radius**2
        data_bgr[cy-radius:cy+radius, cx-radius:cx+radius][index] = color
        return data_bgr


def channel_send(channel, message):
    """
    Send message over specified channel.
    :param channel: RTCPeerConnection CHANNEL object
    :param message: String message
    """
    assert isinstance(message,str)
    assert isinstance(channel,RTCDataChannel)
    channel.send(message)

async def run_offer(pc, signaling):
    """
    Function that handles all signaling.
    Creates chat channel and track channel.
    Constantly pings clients for responses.
    Sends video stream to client.
    Leaves connection open to client, waiting
    for responses.
    """
    assert isinstance(pc,RTCPeerConnection)
    assert isinstance(signaling,TcpSocketSignaling)
    
    
    #create channel and reference stream.
    channel = pc.createDataChannel("chat")
    reference = CircleVideoStreamTrack()
    
    def add_tracks():
        """
        function that adds video stream track
        to signal.
        """
        pc.addTrack(CircleVideoStreamTrack())
    
    def calc_coords(frame_count):
        """
        Calculate coordinates.
        This is closed form since we know where every point
        is in the video.
        :param frame: video frame in numpy format.
        """
        radius = 50
        k = frame_count
        if k < 30:
            k = k
        else:
            k = 59-k
        map_x = radius + 5 + 10 * k
        map_y = radius + 5 + 10 * k
        return map_x , map_y

    await signaling.connect()
    
    async def send_pings():
        """
        function that constantly sends pings
        through chat channel.
        """
        while True:
            channel_send(channel, "ping")
            await asyncio.sleep(1)

    @channel.on("open")
    def on_open():
        """
        Function that makes sure that pings keep
        being sent.
        """
        asyncio.ensure_future(send_pings())

    @channel.on("message")
    def on_message(message):
        """
        Function that processes feedback from client.
        If feedback is pong, do nothing.
        If feedback is coordinates, process current frame
        and then calculate error.
        """
        if isinstance(message,str):
            if message == 'pong':
                pass
            elif ',' in message:
                coords = message.split(',')
                x = int(coords[0])
                y = int(coords[1])
                compx, compy = calc_coords(count)
                print('Coords Received: ' + message)
                print('Coords Server: ' + str(compx) + ',' + str(compy))
                print('Error: ' + str(np.sqrt((x-compx)**2 + (y-compy)**2)))
            else:
                pass
                

    # send offer  
    # add media player
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)
    
    # keep connection open.
    while True:
        #advance frame with server tick.
        _ = await reference.recv()
        #get frame counter
        count = reference.counter
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
    
    

    


if __name__ == '__main__':
    print("Starting Server")
    
    # create signaling object
    signaling = TcpSocketSignaling(host = "127.0.0.1", port = "8080")
    
    
    # create peer connection
    pc = RTCPeerConnection()
    
    # create event and run loop
    event = run_offer(pc,signaling)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(event)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
        cv2.destroyAllWindows()
