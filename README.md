## Introduction

Code that creates a server and client for a video stream.

Server sends a stream, client plays the stream.

Server generates the video stream by constructing it in numpy and  turning it into a VideoStream.

The client then launches a separate process that calculates the position of the ball.
I made this implementation extremely naive to save computation. It returns the x and y of the first value of 255 it sees.
The client then sends this information to the server. 

The server calculates the current position of the server-side video. This is done based on the current frame of the server video, since we know how the position value is generated based on frame.
The server then calculates error of x and y based on the distance formula.

Pytest was run to test both client.py and server.py, more details can be found in the individual test files.

I found an image here https://hub.docker.com/r/jjanzic/docker-python3-opencv.

This was my base image that I worked off of for docker. I also made sure to install aiortc and numpy on top of this image.

The links to my two docker images are https://hub.docker.com/r/kardashm/server_example and https://hub.docker.com/r/kardashm/client_example


I could not figure out how to use MiniKube with these images as I ran minikube on windows. My containers launch, but don't appear
because Terminal isn't configured.  I can use an Ubuntu VM but I also have another Issue that needs to be addressed and that's the 
tcp ip for client and server. I use a hardcoded 0.0.0.0::8080 port but  in order for MiniKube to work, I'll have to either change
that to 127.0.0.1 or create a command line argument and somehow pass that to my containers. I don't have enough time or experties 
to figure this out yet.



## Requirements

Python, Numpy, aiortc, Docker, MiniKube

## Instructions

Run client using "python client.py"

Run server using "python server.py"

I have included a demo.mp4 that shows the script in action. Please download and view this video to see my code in action!

You can also run the Docker images that I have hosted, but they will not interact with one another due to bad TCP-IP setup.



## Limitations

This implementation will fit into containers and run, but will not work between two containers as the TCP-IP is not set up
properly to account for containerization.


Additionally, the number of client-side processes is limited to 3 in order to make computation feasible.