import numpy as np
import asyncio
import cv2

from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, TcpSocketSignaling

def channel_send(channel, message):
    channel.send(message)

async def consume_signaling(pc, signaling):
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break

async def run_answer(pc, signaling, recorder, cap):
    await signaling.connect()
    
    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)
    
        
    
    @pc.on("datachannel")
    def on_datachannel(channel):

        @channel.on("message")
        def on_message(message):
            print(message)
            if isinstance(message, str) and message.startswith("ping"):
                # reply
                channel_send(channel, "pong")
    await consume_signaling(pc, signaling)



if __name__ == '__main__':
    print("Starting Client")
    
     # create signaling object
    signaling = TcpSocketSignaling(host = "127.0.0.1", port = "8080")
    
    
    # create peer connection
    pc = RTCPeerConnection()
    
    # create recorder
    recorder = MediaBlackhole()
    
    # create video capture object
    cap = cv2.VideoCapture(0)
    
    # create event and run loop
    event = run_answer(pc,signaling, recorder, cap)
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(event)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
        
        