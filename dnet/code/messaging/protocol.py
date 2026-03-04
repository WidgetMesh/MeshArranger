from . import schema
from .codec import MessageCodec
from .registry import ServiceRegistry

try:
    import logging
except Exception:
    logging = None


class MessagingEndpoint:
    """
    Transport adapter for sending/receiving capability messages.

    Expected transport methods:
    - send(peer_id, payload_str_or_bytes)
    - recv() -> (peer_id, payload_str_or_bytes) or (None, None)
    """

    def __init__(self, node_id, transport, codec=None, registry=None):
        self.node_id = str(node_id)
        self.transport = transport
        self.codec = codec or MessageCodec()
        self.registry = registry or ServiceRegistry()
        self._logger = None
        if logging is not None:
            try:
                self._logger = logging.getLogger("dnet.messaging.endpoint")
            except Exception:
                self._logger = None

    def send_advertise(self, peer_id, profile_hash, service_ids):
        payload = self.codec.encode_advertise(self.node_id, profile_hash, service_ids)
        self.transport.send(peer_id, payload)
        return payload

    def send_query(self, peer_id, service_id):
        payload = self.codec.encode_query(self.node_id, service_id)
        self.transport.send(peer_id, payload)
        return payload

    def send_query_result(self, peer_id, service_id, providers):
        payload = self.codec.encode_query_result(self.node_id, service_id, providers)
        self.transport.send(peer_id, payload)
        return payload

    def send_get_profile(self, peer_id, target_node_id):
        payload = self.codec.encode_get_profile(self.node_id, target_node_id)
        self.transport.send(peer_id, payload)
        return payload

    def send_profile(self, peer_id, profile_hash, services, name=None, role=None, firmware=None, meta=None):
        payload = self.codec.encode_profile(
            self.node_id,
            profile_hash,
            services,
            name=name,
            role=role,
            firmware=firmware,
            meta=meta,
        )
        self._log_debug(
            "send_profile node={} peer={} hash={} services={} bytes={}".format(
                self.node_id, peer_id, profile_hash, len(services), len(payload)
            )
        )
        self.transport.send(peer_id, payload)
        self._log_debug("send_profile dispatched peer={} bytes={}".format(peer_id, len(payload)))
        return payload

    def poll(self):
        """
        Receive one message and update registry.
        Returns (peer_id, decoded_message) or (None, None).
        """
        peer_id, payload = self.transport.recv()
        if payload is None:
            return None, None

        try:
            message = self.codec.decode(payload)
        except Exception as exc:
            raw_len = len(payload) if hasattr(payload, "__len__") else -1
            preview = payload[:80] if isinstance(payload, (str, bytes, bytearray)) else payload
            self._log_debug(
                "poll decode failed peer={} bytes={} preview={} err={}".format(
                    peer_id, raw_len, preview, exc
                )
            )
            raise
        mtype = message[schema.F_TYPE]
        self._log_debug("poll decoded peer={} type={} bytes={}".format(peer_id, mtype, len(payload)))

        if mtype == schema.TYPE_ADVERTISE:
            self.registry.register_advertisement(message)
            self._log_debug("registry updated advertise node={}".format(message.get(schema.F_NODE_ID)))
        elif mtype == schema.TYPE_PROFILE:
            self.registry.register_profile(message)
            self._log_debug(
                "registry updated profile node={} services={}".format(
                    message.get(schema.F_NODE_ID), len(message.get(schema.F_SERVICES, []))
                )
            )

        return peer_id, message

    def _log_debug(self, msg):
        if self._logger is not None and hasattr(self._logger, "debug"):
            self._logger.debug(msg)
            return
        print("DEBUG MessagingEndpoint: {}".format(msg))

    def find_providers(self, service_id):
        return self.registry.find_service(service_id)
