import os
import time
import socket
import random
import threading
import aiohttp
import asyncio
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from uvicorn import Config, Server
import logging
import argparse

# Args 
parser = argparse.ArgumentParser(description="HTTP server and client with rate-controlled requests")
parser.add_argument('--stats-interval', type=float, default=10, help='Statistics logging interval in seconds (default: 10)')
parser.add_argument('--connections-per-interval', type=int, default=100, help='Number of connections to send per stats interval (default: 10)')
parser.add_argument('--batch-size', type=int, default=5, help='Number of concurrent requests per batch (default: 5)')
parser.add_argument('--no-namespaces', type=int, default=10, help='Number of namespaces (gc-ns-1 to gc-ns-NO_NAMESPACES) (default: 3)')
parser.add_argument('--no-deployments', type=int, default=5, help='Number of deployments per namespace (default: 3)')
parser.add_argument('--same-ns-ratio', type=float, default=50, help='Percentage of connections to same namespace, next deployment (default: 60)')
args = parser.parse_args()


logging.getLogger().handlers.clear()  
logger = logging.getLogger()  

def init_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logging.getLogger('uvicorn').handlers.clear()
    logging.getLogger('uvicorn').propagate = False
    logging.getLogger('uvicorn.access').handlers.clear()
    logging.getLogger('uvicorn.access').propagate = False
    logging.getLogger('uvicorn.error').handlers.clear()
    logging.getLogger('uvicorn.error').propagate = False
    logging.getLogger('fastapi').handlers.clear()
    logging.getLogger('fastapi').propagate = False

app = FastAPI()

request_id = 0
connection_count = 0

# HOSTNAME = os.getenv('HOSTNAME')  
HOSTNAME = 'gc-ns-1-rs-2-dkjdn' # for debug 

if not HOSTNAME:
    logger.error("HOSTNAME environment variable not set")
    raise ValueError("HOSTNAME environment variable required")

SERVICE_PORT = 8000
SERVER_PORT  = 8000 
NO_NAMESPACES = args.no_namespaces     # total namespaces workloads
NO_DEPLOYMENTS = args.no_deployments   # total deployment per namespace
SAME_NS_RATIO = args.same_ns_ratio     # % connection in the namespace but to the next deployment 
STATS_INTERVAL = args.stats_interval   # statistic sliding window
CONNECTIONS_PER_INTERVAL = args.connections_per_interval  # Number of connections to send per STATS_INTERVAL
TARGET_CYCLE_TIME = STATS_INTERVAL / CONNECTIONS_PER_INTERVAL  # Target time per request (0.05s)
BATCH_SIZE = args.batch_size           # send concurrent connections 
RETRY_ATTEMPTS = 3  # Number of retries for failed requests
RETRY_DELAY = 1  # Seconds to wait between retries

def parse_pod_indices():
    try:
        parts = HOSTNAME.split('-')
        if len(parts) < 6 or parts[0] != 'gc' or parts[1] != 'ns' or parts[3] != 'rs':
            raise ValueError("Invalid pod name format")
        x = int(parts[2])  # Namespace index
        y = int(parts[4])  # Deployment index
        return x, y
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse pod name {HOSTNAME}: {e}")
        raise
    
SOURCE_X, SOURCE_Y = parse_pod_indices()


@app.post("/echo/{from_pod_name}/{req_id}")
async def echo(from_pod_name: str, req_id: int):
    logger.debug(f"<- /echo/{from_pod_name}/{req_id}")
    return PlainTextResponse(f'{HOSTNAME=}, {req_id=}')

async def log_stats():
    global connection_count
    last_count = 0  # Track connections counted in previous windows
    while True:
        await asyncio.sleep(STATS_INTERVAL)
        # Log connections sent in the last STATS_INTERVAL seconds
        current_count = connection_count
        recent_connections = current_count - last_count
        logger.info(f"Connections sent in last {STATS_INTERVAL} seconds: {recent_connections}")
        last_count = current_count  # Update last_count for next window


async def send_post_request(session, url, from_pod_name):
    global connection_count
    for attempt in range(RETRY_ATTEMPTS):
        try:
            async with session.post(url, json={}) as response:
                connection_count += 1
                if response.status == 200:
                    await response.text()
                    logger.info(f"-> {url}, status: {response.status}")
                    return
                else: 
                    break   # dont retry on HTTP errors 4xx, 5xx
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed for {url}: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"-> Error: {url}: {e}")

async def log_stats():
    global connection_count
    last_count = 0  # Track connections counted in previous windows
    try:
        while True:
            await asyncio.sleep(STATS_INTERVAL)
            # Log connections sent in the last STATS_INTERVAL seconds
            current_count = connection_count
            recent_connections = current_count - last_count
            logger.info(f"Connections sent in last {STATS_INTERVAL} seconds: {recent_connections}")
            last_count = current_count  # Update last_count for next window
    except asyncio.CancelledError:
        # Log final stats on shutdown
        current_count = connection_count
        recent_connections = current_count - last_count
        logger.info(f"Final connections sent in last {STATS_INTERVAL} seconds: {recent_connections}")
        

async def send_random_requests():
    async with aiohttp.ClientSession() as session:
        global request_id
        stats_task = asyncio.create_task(log_stats())
        try:
            while True:
                tasks = []
                for _ in range(BATCH_SIZE):
                    x = SOURCE_X
                    y = SOURCE_Y
                    from_pod_name = HOSTNAME  # e.g., gc-ns-1-rs-2-kjk332
                    
                    r = random.uniform(0, 100)
                    if r < SAME_NS_RATIO:
                        # SAME_NS_RATIO% to same namespace, next deployment
                        target_x = x
                        target_y = y + 1 if y < NO_DEPLOYMENTS else 1  # Wrap around to 1
                    else:
                        # (100-SAME_NS_RATIO)% to next namespace, same deployment
                        target_x = x + 1 if x < NO_NAMESPACES else 1  # Wrap around to 1
                        target_y = y
                    service_name = f"gc-ns-{target_x}-svc-{target_y}.gc-ns-{target_x}.svc.cluster.local"
                    # service_name = 'localhost'  # for testing 
                    request_id += 1
                    url = f"http://{service_name}:{SERVICE_PORT}/echo/{HOSTNAME}/{request_id}"
                    tasks.append(send_post_request(session, url, HOSTNAME))
                # Measure time taken for the batch
                start_time = time.time()
                await asyncio.gather(*tasks)
                elapsed_time = time.time() - start_time
                
                # Adjust sleep to maintain target cycle time per request
                target_total_time = TARGET_CYCLE_TIME * BATCH_SIZE
                sleep_time = max(0, target_total_time - elapsed_time)
                await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            # Cancel stats task on shutdown
            stats_task.cancel()
            await stats_task  # Ensure final stats are logged

def run_request_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_random_requests())
    loop.close()

async def main():
    init_logger()
    request_thread = threading.Thread(target=run_request_thread, daemon=True)
    request_thread.start()

    config = Config(app=app, host="0.0.0.0", port=SERVER_PORT, log_config=None)
    server = Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())