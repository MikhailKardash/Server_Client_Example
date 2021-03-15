import numpy as np

from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling






if __name__ == '__main__':
    print("Starting Server")
    
    # create signaling object
    signaling = create_signaling()
    
    
    # create peer connection
    pc = RTCPeerConnection()