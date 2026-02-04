import argparse
import json
import time

import paho.mqtt.client as mqtt


BROKER = "10.215.255.119"
PORT = 1883
TOPIC_ALERT = "cx/iotbox01/alert"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Publish a mock alert to MQTT for testing the web UI."
    )
    parser.add_argument("--broker", default=BROKER, help="MQTT broker address")
    parser.add_argument("--port", type=int, default=PORT, help="MQTT broker port")
    parser.add_argument("--topic", default=TOPIC_ALERT, help="Alert topic")
    parser.add_argument("--command", default="window", help="Alert command/type")
    parser.add_argument(
        "--reason",
        default="Unhealthy CO2 Level.",
        help="Alert reason/message",
    )
    parser.add_argument(
        "--plain-text",
        action="store_true",
        help="Send a plain-text payload instead of JSON",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.plain_text:
        payload = args.reason
    else:
        payload = json.dumps({"command": args.command, "reason": args.reason})

    client = mqtt.Client()
    client.connect(args.broker, args.port, 60)
    client.loop_start()

    client.publish(args.topic, payload)
    print(f"Published to {args.topic}: {payload}")

    time.sleep(0.2)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
