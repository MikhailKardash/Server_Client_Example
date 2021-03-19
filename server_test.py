import pytest
import asyncio
from server import *
from av import VideoFrame
import numpy as np


from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    RTCDataChannel
)

@pytest.mark.asyncio
async def test_video_generator_type():
    '''
    Ensure that output of recv is a CircleVideoStreamTrack
    '''
    stream = CircleVideoStreamTrack()
    frame = await stream.recv()
    assert isinstance(frame, VideoFrame)
    
@pytest.mark.asyncio
async def test_video_length():
    '''
    Ensure that the video loops every 60 frames.
    In this case, frame 0 = frame 61
    '''
    stream = CircleVideoStreamTrack()
    frame0 = await stream.recv()
    for i in range(60):
        frame = await stream.recv()
    assert(np.all(frame0.to_ndarray() == frame.to_ndarray()))
    
def test_channel_send():
    '''
    Test that channel send has strict input requirements.
    These two function calls should raise AssertionError.
    '''
    pc = RTCPeerConnection()
    valid_channel = pc.createDataChannel("chat")
    valid_message = 'abc'
    try:
        channel = 'abc'
        channel_send(channel,valid_message)
        assert(False), 'Invalid channel type'
    except AssertionError as error:
        pass
        
    try:
        message = 325
        channel_send(valid_channel,message)
        assert(False), 'No message constraint?'
    except AssertionError as error:
        pass
        
        
@pytest.mark.asyncio
async def test_run_offer():
    pc_valid = RTCPeerConnection()
    signaling_valid = TcpSocketSignaling(host = "0.0.0.0", port = "8080")
    try:
        pc = 'abc'
        await run_offer(pc, signaling_valid)
        assert(False), 'Invalid Connection type'
    except AssertionError as error:
        pass
        
    try:
        signaling = 'abc'
        await run_offer(pc_valid, signaling)
        assert(False), 'Invalid Signaling type.'
    except AssertionError as error:
        pass