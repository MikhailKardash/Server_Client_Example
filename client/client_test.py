import pytest
from client import *
from av import VideoFrame
import numpy as np
import multiprocessing
from aiortc.contrib.media import MediaBlackhole


from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    RTCDataChannel
)


def test_channel_send():
    '''
    Test that channel send has strict input requirements.
    These two function calls should raise AssertionError.
    Copied from server_test.py
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
        
        
        
def test_coord_calcs():
    '''
    test coord_calcs for input typing and
    two test cases.
    First test case is zeros, and should return [trim,trim]
    Second test case has a 1 at [51,51] and should return
    the expected [51,51]
    Third test case measures x vs y, should return [51,52]
    instead of [52,51]
    '''
    queue = multiprocessing.Queue()
    frame0 = np.zeros([100,100])
    frame1 = np.zeros([100,100])
    frame1[51][51] = 200
    frame2 = np.zeros([100,100])
    frame2[50:53,50:55] = np.asarray([[0,0,1,0,0],
                                      [1,1,1,1,1],
                                      [0,0,1,0,0]])
    

    answers = [[25,25],[51,51],[51,52]]
    
    try:
        calc_coords(None,None)
    except AssertionError as error:
        pass
    
    
                         
    p = []
    for frame in [frame0,frame1,frame2]:
        process = multiprocessing.Process(target = calc_coords, 
                                          args = (queue,frame))
        p.append(process)
        process.start()
    
    for process in p:
        process.join()
    
    for ans in answers:
        coords = queue.get()
        assert(coords[0] == ans[0])
        assert(coords[1] == ans[1])
        
@pytest.mark.asyncio
async def test_run_answer():
    '''
    Test run answer for input assertions.
    There are a lot of internal functions that should
    be tested after completely restructuring the server
    and client code.
    '''
    pc_valid = RTCPeerConnection()
    signaling_valid = TcpSocketSignaling(host = "0.0.0.0", port = "8080")
    recorder_valid = MediaBlackhole() #technically there are 2 valid types here
    queue_valid = multiprocessing.Queue()
    window_valid = 'window'
    try:
        pc = 'abc'
        await run_answer(pc, signaling_valid, recorder_valid,
                         queue_valid, window_valid)
        assert(False), 'Invalid Connection type'
    except AssertionError as error:
        pass
        
    try:
        signaling = 'abc'
        await run_answer(pc_valid, signaling, recorder_valid,
                         queue_valid, window_valid)
        assert(False), 'Invalid Signaling type.'
    except AssertionError as error:
        pass
    
    try:
        recorder = 'abc'
        await run_answer(pc_valid, signaling_valid, recorder,
                         queue_valid, window_valid)
        assert(False), 'Invalid Signaling type.'
    except AssertionError as error:
        pass
    
    try:
        queue = 'abc'
        await run_answer(pc_valid, signaling_valid, recorder_valid,
                         queue, window_valid)
        assert(False), 'Invalid Signaling type.'
    except AssertionError as error:
        pass
        
    try:
        window = 123
        await run_answer(pc_valid, signaling_valid, recorder_valid,
                         queue_valid, window)
        assert(False), 'Invalid Signaling type.'
    except AssertionError as error:
        pass
    
    