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
    """
    Send message over specified channel.
    :param channel: RTCPeerConnection CHANNEL object
    :param message: String message
    """
    channel.send(message)

async def run_answer(pc, signaling, recorder, queue, window):
    """
    Function that handles all signaling.
    Defines reactive behavior when given two types of offers.
    Chat channel offer: respond with string message
    Track offer: play video
    Then, leaves the connection open.
    """
    processes = []
    rets = []
    await signaling.connect()
    @pc.on("track")
    async def on_track(track):
        """
        After receiving track, play the track video and append frames.
        Take those frames and send them to a process.
        Also displays current frame using cv2. imshow.
        :param track: VideoStreamTrack 
        """
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)
        while True:
            frame = await track.recv()
            frame = frame.to_ndarray()
            process = multiprocessing.Process(target = calc_coords,
                                              args = (queue,frame))
            processes.append(process)
            process.start()
            cv2.imshow(window,frame[10:480,10:640])
            cv2.waitKey(50)
    
    @pc.on("datachannel")
    def on_datachannel(channel):
        """
        behavior on receiving a text message.
        Either send back pong or the image coordinates.
        """
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str):
                print(message)
                for p in processes:
                    ret = queue.get()
                    rets.append(ret)
                
                for p in processes:
                    p.join()
                
                if rets:
                    x,y = rets.pop(0)
                    output = str(x) + ',' + str(y)
                    print(output)
                    channel_send(channel,output)
                else:
                    output = 'pong'
                    print(output)
                    channel_send(channel,output)
      
    # leave the connection open or close it if necessary.
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
            
            
def calc_coords(queue,frame):
    """
    Calculate coordinates.
    Make sure that it is consistent with server side
    processing method.
    :param queue: multiprocessing queue.
    :param frame: video frame in numpy format.
    """
    frame = frame[10:480,10:640]
    for y in range(frame.shape[0]):
        for x in range(frame.shape[1]):
            if frame[y,x] > 50:
                queue.put([x,y])
                return x,y
    return 0,0


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
 
    # create multiprocessing queue
    queue = multiprocessing.Queue(5)
    
    
    
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
        