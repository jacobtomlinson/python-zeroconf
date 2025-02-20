#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Unit tests for zeroconf._services.types."""

import logging
import os
import unittest
import socket
import sys
from unittest.mock import patch

import zeroconf as r
from zeroconf import Zeroconf, ServiceInfo, ZeroconfServiceTypes

from .. import _clear_cache, has_working_ipv6

log = logging.getLogger('zeroconf')
original_logging_level = logging.NOTSET


def setup_module():
    global original_logging_level
    original_logging_level = log.level
    log.setLevel(logging.DEBUG)


def teardown_module():
    if original_logging_level != logging.NOTSET:
        log.setLevel(original_logging_level)


class ServiceTypesQuery(unittest.TestCase):
    def test_integration_with_listener(self):

        type_ = "_test-listen-type._tcp.local."
        name = "xxxyyy"
        registration_name = "%s.%s" % (name, type_)

        zeroconf_registrar = Zeroconf(interfaces=['127.0.0.1'])
        desc = {'path': '/~paulsm/'}
        info = ServiceInfo(
            type_,
            registration_name,
            80,
            0,
            0,
            desc,
            "ash-2.local.",
            addresses=[socket.inet_aton("10.0.1.2")],
        )
        zeroconf_registrar.registry.add(info)
        try:
            with patch.object(
                zeroconf_registrar.engine.protocols[0], "suppress_duplicate_packet", return_value=False
            ), patch.object(
                zeroconf_registrar.engine.protocols[1], "suppress_duplicate_packet", return_value=False
            ):
                service_types = ZeroconfServiceTypes.find(interfaces=['127.0.0.1'], timeout=0.5)
                assert type_ in service_types
                _clear_cache(zeroconf_registrar)
                service_types = ZeroconfServiceTypes.find(zc=zeroconf_registrar, timeout=0.5)
                assert type_ in service_types

        finally:
            zeroconf_registrar.close()

    @unittest.skipIf(not has_working_ipv6(), 'Requires IPv6')
    @unittest.skipIf(os.environ.get('SKIP_IPV6'), 'IPv6 tests disabled')
    def test_integration_with_listener_v6_records(self):

        type_ = "_test-listenv6rec-type._tcp.local."
        name = "xxxyyy"
        registration_name = "%s.%s" % (name, type_)
        addr = "2606:2800:220:1:248:1893:25c8:1946"  # example.com

        zeroconf_registrar = Zeroconf(interfaces=['127.0.0.1'])
        desc = {'path': '/~paulsm/'}
        info = ServiceInfo(
            type_,
            registration_name,
            80,
            0,
            0,
            desc,
            "ash-2.local.",
            addresses=[socket.inet_pton(socket.AF_INET6, addr)],
        )
        zeroconf_registrar.registry.add(info)
        try:
            with patch.object(
                zeroconf_registrar.engine.protocols[0], "suppress_duplicate_packet", return_value=False
            ), patch.object(
                zeroconf_registrar.engine.protocols[1], "suppress_duplicate_packet", return_value=False
            ):
                service_types = ZeroconfServiceTypes.find(interfaces=['127.0.0.1'], timeout=0.5)
                assert type_ in service_types
                _clear_cache(zeroconf_registrar)
                service_types = ZeroconfServiceTypes.find(zc=zeroconf_registrar, timeout=0.5)
                assert type_ in service_types

        finally:
            zeroconf_registrar.close()

    @unittest.skipIf(not has_working_ipv6() or sys.platform == 'win32', 'Requires IPv6')
    @unittest.skipIf(os.environ.get('SKIP_IPV6'), 'IPv6 tests disabled')
    def test_integration_with_listener_ipv6(self):

        type_ = "_test-listenv6ip-type._tcp.local."
        name = "xxxyyy"
        registration_name = "%s.%s" % (name, type_)
        addr = "2606:2800:220:1:248:1893:25c8:1946"  # example.com

        zeroconf_registrar = Zeroconf(ip_version=r.IPVersion.V6Only)
        desc = {'path': '/~paulsm/'}
        info = ServiceInfo(
            type_,
            registration_name,
            80,
            0,
            0,
            desc,
            "ash-2.local.",
            addresses=[socket.inet_pton(socket.AF_INET6, addr)],
        )
        zeroconf_registrar.registry.add(info)
        try:
            with patch.object(
                zeroconf_registrar.engine.protocols[0], "suppress_duplicate_packet", return_value=False
            ), patch.object(
                zeroconf_registrar.engine.protocols[1], "suppress_duplicate_packet", return_value=False
            ):
                service_types = ZeroconfServiceTypes.find(ip_version=r.IPVersion.V6Only, timeout=0.5)
                assert type_ in service_types
                _clear_cache(zeroconf_registrar)
                service_types = ZeroconfServiceTypes.find(zc=zeroconf_registrar, timeout=0.5)
                assert type_ in service_types

        finally:
            zeroconf_registrar.close()

    def test_integration_with_subtype_and_listener(self):
        subtype_ = "_subtype._sub"
        type_ = "_listen._tcp.local."
        name = "xxxyyy"
        # Note: discovery returns only DNS-SD type not subtype
        discovery_type = "%s.%s" % (subtype_, type_)
        registration_name = "%s.%s" % (name, type_)

        zeroconf_registrar = Zeroconf(interfaces=['127.0.0.1'])
        desc = {'path': '/~paulsm/'}
        info = ServiceInfo(
            discovery_type,
            registration_name,
            80,
            0,
            0,
            desc,
            "ash-2.local.",
            addresses=[socket.inet_aton("10.0.1.2")],
        )
        zeroconf_registrar.registry.add(info)
        try:
            with patch.object(
                zeroconf_registrar.engine.protocols[0], "suppress_duplicate_packet", return_value=False
            ), patch.object(
                zeroconf_registrar.engine.protocols[1], "suppress_duplicate_packet", return_value=False
            ):
                service_types = ZeroconfServiceTypes.find(interfaces=['127.0.0.1'], timeout=0.5)
                assert discovery_type in service_types
                _clear_cache(zeroconf_registrar)
                service_types = ZeroconfServiceTypes.find(zc=zeroconf_registrar, timeout=0.5)
                assert discovery_type in service_types

        finally:
            zeroconf_registrar.close()
