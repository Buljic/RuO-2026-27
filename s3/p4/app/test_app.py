import socket
import unittest
from unittest.mock import patch

import redis

import app


class ProvjereAplikacije(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_health_ne_ovisi_o_redisu(self):
        with patch.object(app.ready_redis, "ping") as ping:
            ping.side_effect = redis.exceptions.ConnectionError("nedostupan")
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"ok\n")
        ping.assert_not_called()

    def test_ready_kad_redis_radi(self):
        with patch.object(app.ready_redis, "ping", return_value=True) as ping:
            with patch.object(app.r, "incr") as incr:
                response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"ok\n")
        ping.assert_called_once_with()
        incr.assert_not_called()

    def test_ready_kad_redis_ne_radi(self):
        for error in (
            redis.exceptions.ConnectionError("interna adresa"),
            redis.exceptions.TimeoutError("interna adresa"),
            redis.exceptions.AuthenticationError("interna lozinka"),
        ):
            with self.subTest(error=type(error).__name__):
                with patch.object(app.ready_redis, "ping", side_effect=error):
                    response = self.client.get("/ready")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.data, b"Redis nije dostupan\n")

    def test_ready_se_oporavi_bez_restarta(self):
        with patch.object(
            app.ready_redis, "ping",
            side_effect=[redis.exceptions.ConnectionError(), True],
        ):
            self.assertEqual(self.client.get("/ready").status_code, 503)
            self.assertEqual(self.client.get("/ready").status_code, 200)

    def test_ready_sa_stvarno_odbijenom_vezom(self):
        # Port je rezervisan, ali ne prihvata veze. Redis nije potreban.
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            probe = redis.Redis(
                host="127.0.0.1", port=reserved.getsockname()[1],
                socket_connect_timeout=0.5, socket_timeout=0.5,
            )
            try:
                with patch.object(app, "ready_redis", probe):
                    self.assertEqual(self.client.get("/health").status_code, 200)
                    self.assertEqual(self.client.get("/ready").status_code, 503)
            finally:
                probe.close()

    def test_brojac_ostaje_isti(self):
        with patch.object(app.r, "incr", return_value=7) as incr:
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"Posjeta broj 7\n")
        incr.assert_called_once_with("posjete")

    def test_provjera_spremnosti_ima_kratke_timeout_vrijednosti(self):
        options = app.ready_redis.connection_pool.connection_kwargs
        self.assertEqual(options["socket_connect_timeout"], 0.5)
        self.assertEqual(options["socket_timeout"], 0.5)


if __name__ == "__main__":
    unittest.main()
