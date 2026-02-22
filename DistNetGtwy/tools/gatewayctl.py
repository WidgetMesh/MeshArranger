#!/usr/bin/env python3
"""CLI for sending JSON commands to mesh gateway REST API."""

import argparse
import json
import sys
import urllib.error
import urllib.request


def _request(url: str, payload=None, timeout=5.0):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        if not body.strip():
            return {}
        return json.loads(body)


def _print_json(obj):
    print(json.dumps(obj, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gatewayctl")
    parser.add_argument("--host", default="mesh-gateway.local", help="Gateway host")
    parser.add_argument("--port", default=8080, type=int, help="Gateway port")
    parser.add_argument("--timeout", default=5.0, type=float, help="HTTP timeout seconds")

    sub = parser.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("health", help="GET /health")
    sub.add_parser("status", help="POST /command {cmd: status}")

    p_echo = sub.add_parser("echo", help="POST /echo")
    p_echo.add_argument("message")

    p_call = sub.add_parser("call", help="POST /command with custom cmd/args")
    p_call.add_argument("cmd")
    p_call.add_argument("--args", default="{}", help="JSON object string")

    args = parser.parse_args(argv)
    base = f"http://{args.host}:{args.port}"

    try:
        if args.subcommand == "health":
            out = _request(f"{base}/health", timeout=args.timeout)
        elif args.subcommand == "status":
            out = _request(
                f"{base}/command",
                payload={"cmd": "status", "args": {}},
                timeout=args.timeout,
            )
        elif args.subcommand == "echo":
            out = _request(
                f"{base}/echo",
                payload={"message": args.message},
                timeout=args.timeout,
            )
        else:
            try:
                cmd_args = json.loads(args.args)
                if not isinstance(cmd_args, dict):
                    raise ValueError("--args must decode to JSON object")
            except Exception as exc:
                raise SystemExit(f"Invalid --args JSON: {exc}")

            out = _request(
                f"{base}/command",
                payload={"cmd": args.cmd, "args": cmd_args},
                timeout=args.timeout,
            )

        _print_json(out)
        return 0

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 2
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 3
    except json.JSONDecodeError as exc:
        print(f"Bad JSON response: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
