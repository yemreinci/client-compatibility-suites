import os
import time
import unittest
from os.path import abspath

import hazelcast
import logging
import random

from hazelcast import HazelcastClient
from hazelcast.discovery import HazelcastCloudDiscovery
from hzrc.client import HzRemoteController
from hzrc.ttypes import CloudCluster


class TestStandardClusterTestsWithSsl(unittest.TestCase):
    cluster: CloudCluster = None
    client: HazelcastClient = None
    rc: HzRemoteController = None
    HazelcastCloudDiscovery._CLOUD_URL_BASE = os.getenv('baseUrl').replace("https://", "")

    @classmethod
    def setUpClass(cls) -> None:
        cls.rc = HzRemoteController("127.0.0.1", 9701)
        cls.cluster = cls.rc.createStandardCluster(os.getenv('hzVersion'), True)
        cls.client = hazelcast.HazelcastClient(
            cluster_name=cls.cluster.nameForConnect,
            cloud_discovery_token=cls.cluster.token,
            statistics_enabled=True,
            ssl_enabled=True,
            ssl_cafile=abspath(os.path.join(cls.cluster.certificatePath + "ca.pem")),
            ssl_certfile=abspath(os.path.join(cls.cluster.certificatePath + "cert.pem")),
            ssl_keyfile=abspath(os.path.join(cls.cluster.certificatePath + "key.pem")),
            ssl_password=cls.cluster.tlsPassword)

    def test_try_connect_ssl_cluster_without_certificates(self):
        value = False
        try:
            hazelcast.HazelcastClient(
                cluster_name=self.cluster.nameForConnect,
                cloud_discovery_token=self.cluster.token,
                cluster_connect_timeout=10)
        except:
            value = True
        self.assertTrue(value, "Client shouldn't able to connect to ssl cluster without certificates")

    def test_connect_ssl_cluster_with_certificates(self):

        map1 = self.client.get_map("map_for_test_connect_ssl_cluster_with_certificates").blocking()
        map1.clear()
        while map1.size() < 20:
            random_key = random.randint(1, 100000)
            try:
                map1.put("key" + str(random_key), "value" + str(random_key))
            except:
                logging.exception("Put operation failed!")

        self.assertEqual(map1.size(), 20, "Map size should be 20")

    def test_scale_up_ssl_cluster(self):
        self.rc.scaleUpDownStandardCluster(self.cluster.id, 4)
        map2 = self.client.get_map("map_for_test_scale_up_ssl_cluster").blocking()
        while map2.size() < 20:
            random_key = random.randint(1, 100000)
            try:
                map2.put("key" + str(random_key), "value" + str(random_key))
            except:
                logging.exception("Put operation failed!")

        self.assertEqual(map2.size(), 20, "Map size should be 20")

        self.rc.scaleUpDownStandardCluster(self.cluster.id, -4)
        while map2.size() < 40:
            random_key = random.randint(1, 100000)
            try:
                map2.put("key" + str(random_key), "value" + str(random_key))
            except:
                logging.exception("Put operation failed!")

        self.assertEqual(map2.size(), 40, "Map size should be 20")

    def test_restart_cluster(self):
        self.rc.stopCluster(self.cluster.id)
        self.rc.resumeCluster(self.cluster.id)
        time.sleep(10)
        map3 = self.client.get_map("map_for_test_restart_cluster").blocking()
        while map3.size() < 20:
            random_key = random.randint(1, 100000)
            try:
                map3.put("key" + str(random_key), "value" + str(random_key))
            except:
                logging.exception("Put operation failed!")

        self.assertEqual(map3.size(), 20, "Map size should be 20")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.rc.deleteCluster(cls.cluster.id)