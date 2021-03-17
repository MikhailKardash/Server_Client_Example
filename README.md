## Introduction

Code that creates a server and client for a video stream.

Server sends a stream, client plays the stream.

Server generates the video stream by constructing it in numpy and  turning it into a VideoStream.

The client then launches a separate process that calculates the position of the ball.
I made this implementation extremely naive to save computation. It returns the x and y of the first value of 255 it sees.
The client then sends this information to the server. 

The server calculates the current position of the server-side video. This is done based on the current frame of the server video, since we know how the position value is generated based on frame.
The server then calculates error of x and y based on the distance formula.



## Requirements

Python, Numpy, aiortc

## Instructions

Run client using "python client.py"

Run server using "python server.py"

I have included a demo.mp4 that shows the script in action. Please download and view this video to see my code in action!



## Limitations

I have not unit tested these functions.

Additionally, the number of client-side processes is limited to 3 in order to make computation feasible.