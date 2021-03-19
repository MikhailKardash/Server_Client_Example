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

processes = []
rets = []


def channel_send(channel, message):
    """
    Send message over specified channel.
    :param channel: RTCPeerConnection CHANNEL object
    :param message: String message
    """
    assert isinstance(message,str)
    channel.send(message)

async def run_answer(pc, signaling, recorder, queue, window):
    """
    Function that handles all signaling.
    Defines reactive behavior when given two types of offers.
    Chat channel offer: respond with string message
    Track offer: play video
    Then, leaves the connection open.
    """

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
            if len(processes) < 3:
                process = multiprocessing.Process(target = calc_coords, args = (queue,frame))
                process.start()
                processes.append(process)
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
                if not rets:
                    for p in processes:
                        ret = queue.get()
                        rets.append(ret)
                    for p in processes:
                        p.join()
                if rets:
                    x,y = rets.pop(0)
                    processes.pop(0)
                    output = str(x) + ',' + str(y)
                    print("Estimate: " + output)
                    channel_send(channel,output)
                    
                else:
                    output = 'pong'
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
    Image needs to be trimmed because of noisy video.
    Then, argmax both rows and columns to get furthermost points
    of the circle.
    
    
    :param queue: multiprocessing queue.
    :param frame: video frame in numpy format.
    """
    
    assert isinstance(frame, np.ndarray)
    #assert isinstance(queue, multiprocessing.Queue)
    
    # trim off the white video borders
    trim = 25
    frame = frame[trim:480-trim,trim:640-trim]
    
    #argmax the rows and columns.
    maxx = np.argmax(frame, axis = 0)
    maxy = np.argmax(frame, axis = 1)
    
    # take the cornermost indices.
    x = np.max(maxx)
    y = np.max(maxy)
    
    #throw these indices onto the queue and add trim to keep it zero based.
    queue.put([x + trim, y + trim])


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
        cv2.destroyAllWindows()
        queue.close()
        for el in queue():
            queue.release()
        pass
    finally:
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
        cv2.destroyAllWindows()
        queue.close()
        