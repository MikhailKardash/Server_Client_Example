FROM jjanzic/docker-python3-opencv

WORKDIR /app

#Create Environment
RUN pip install numpy
RUN pip install aiortc

# Make sure the environment is activated:
RUN echo "Make sure aiortc is installed:"
RUN python -c "import aiortc"

# The code to run when container is started:
COPY client.py .
CMD ["python", "client.py"]