# TCP/IP Packets Sniff
This weekend project tries to solve the following problem: Imagine that you have a set of machines, in which security is crucial, and you want to know what TPC/IP traffic goes into and out of this machine. You hace a central monitoring server, to which HTTP DATA packets should be sent to be monitored. 

The presented solution is composed by the following parts:
* `src/gather.py`: The script that aims to solve the monitoring problem.
* `src/logging_http.py`: A dummy HTTP server to log the requests.
* `Dockerfile`: The Dockerfile to run the solution inside of a container. 
```
docker build -t gather -f Dockerfile .
docker run -it -d --network host gather
```
* `requirements.txt`: The requirements for the Python environment.

## Development
For the proposed solution, a class `gatherTCP` was created, which creates a gatherer object for the TCP/IP packets. The only argument that the class accepts is the URL of the endpoint in which the sniffed data will be posted, i.e. the referred as monitoring server. 
The class `gatherTCP` has one public method `run()` which creates the queue for the data objects, and both the sniff_data and http_client processes. 

The `_sniff_data` private method is in charge of sniffing the data from the packets. In order to do so, a raw socket is used to receive the packages; then, the packets are parsed and evaluated to only use TCP packets.

The `_http_client` private method is in charge of waiting for 5 minutes before sending the information present in the queue to the main monitoring server using a POST request. 
**TODO**: I know the way in which the process sleeps is not the most elegant solution, and I'm aware that I should have started asynchronous processes and use some method from the `asyncio` library.

Additionally, a simple function called `get_args_parser` is presented to handle the two flags that the script supports:
* `--url`: To determine the monitoring server URL.
* `--verbose`: To control logs verbosity. 

On the other hand, the `Dockerfile` is so simple that I belive it is self-explanatory. There are no crazy dependencies for this project, and that's why the requirements file only contains one of them.

## How to run the experiment
Here I document how I ran this experiment in order to verify that everything was working as expected.

1. Build the image:
```
docker build -t gather -f Dockerfile .
```

2. Run the container in detached mode, in `host` network mode (the container shares the host’s networking namespace), with its own pseudo-terminal and in interactive mode:
```
docker run -it -d --network host gather
```

3. Run the dummy http server to log the requests:
```
python3 logging_http_server.py
```

Every 5 minutes, a new request will be sent to the dummy server with the sniffed data.

