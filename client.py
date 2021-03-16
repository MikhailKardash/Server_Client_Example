import numpy as np
import asyncio
import cv2
import multiprocessing

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

async def run_answer(pc, signaling, recorder, queue, window):
    await signaling.connect()
    
    
    @pc.on("track")
    async def on_track(track):
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)
        while True:
            frame = await track.recv()
            frame = frame.to_ndarray()
            queue.put(frame)
            #channel_send(channel, 'got_frame')
            cv2.imshow(window,frame)
            cv2.waitKey(1)
    
    channel = pc.createDataChannel("chat")
    
    @channel.on("open")
    def on_open():
        channel_send(channel,'test')
    
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str):
                print(message)           
    
    #await pc.setLocalDescription(await pc.createAnswer())
    #await signaling.send(pc.localDescription)    
    
    while True:
        obj = await signaling.receive()
        
        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()
            
            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break
            
            
def calc_coords(frame):
    pass



if __name__ == '__main__':
    print("Starting Client")
    
     # create signaling object
    signaling = TcpSocketSignaling(host = "127.0.0.1", port = "8080")
    
    
    # create peer connection
    pc = RTCPeerConnection()
    
    # create recorder
    recorder = MediaBlackhole()
    
    # video window name
    window_name = 'VideoStream'
    #cv2.imshow(window_name,np.zeros([255,255,3]))
    #cv2.waitKey(1)
    
    # create multiprocessing process
    queue = multiprocessing.Queue()
    #process = multiprocessing.Process(target = calc_coords, args = (queue,window_name))
    #process.start()
    
    # create event and run loop
    event = run_answer(pc,signaling, recorder, queue, window_name)
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(event)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
        cv2.destroyAllWindows()
        queue.close()
        while not queue.empty():
            queue.get_nowait()
        
        