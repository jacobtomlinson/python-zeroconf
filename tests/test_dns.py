#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" Unit tests for zeroconf._dns. """

import logging
import socket
import time
import unittest
import unittest.mock

import zeroconf as r
from zeroconf import const, current_time_millis
from zeroconf._dns import DNSRRSet
from zeroconf import (
    DNSHinfo,
    DNSText,
    ServiceInfo,
)

log = logging.getLogger('zeroconf')
original_logging_level = logging.NOTSET


def setup_module():
    global original_logging_level
    original_logging_level = log.level
    log.setLevel(logging.DEBUG)


def teardown_module():
    if original_logging_level != logging.NOTSET:
        log.setLevel(original_logging_level)


class TestDunder(unittest.TestCase):
    def test_dns_text_repr(self):
        # There was an issue on Python 3 that prevented DNSText's repr
        # from working when the text was longer than 10 bytes
        text = DNSText('irrelevant', 0, 0, 0, b'12345678901')
        repr(text)

        text = DNSText('irrelevant', 0, 0, 0, b'123')
        repr(text)

    def test_dns_hinfo_repr_eq(self):
        hinfo = DNSHinfo('irrelevant', const._TYPE_HINFO, 0, 0, 'cpu', 'os')
        assert hinfo == hinfo
        repr(hinfo)

    def test_dns_pointer_repr(self):
        pointer = r.DNSPointer('irrelevant', const._TYPE_PTR, const._CLASS_IN, const._DNS_OTHER_TTL, '123')
        repr(pointer)

    def test_dns_address_repr(self):
        address = r.DNSAddress('irrelevant', const._TYPE_SOA, const._CLASS_IN, 1, b'a')
        assert repr(address).endswith("b'a'")

        address_ipv4 = r.DNSAddress(
            'irrelevant', const._TYPE_SOA, const._CLASS_IN, 1, socket.inet_pton(socket.AF_INET, '127.0.0.1')
        )
        assert repr(address_ipv4).endswith('127.0.0.1')

        address_ipv6 = r.DNSAddress(
            'irrelevant', const._TYPE_SOA, const._CLASS_IN, 1, socket.inet_pton(socket.AF_INET6, '::1')
        )
        assert repr(address_ipv6).endswith('::1')

    def test_dns_question_repr(self):
        question = r.DNSQuestion('irrelevant', const._TYPE_SRV, const._CLASS_IN | const._CLASS_UNIQUE)
        repr(question)
        assert not question != question

    def test_dns_service_repr(self):
        service = r.DNSService(
            'irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL, 0, 0, 80, 'a'
        )
        repr(service)

    def test_dns_record_abc(self):
        record = r.DNSRecord('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL)
        self.assertRaises(r.AbstractMethodException, record.__eq__, record)
        self.assertRaises(r.AbstractMethodException, record.write, None)

    def test_dns_record_reset_ttl(self):
        record = r.DNSRecord('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL)
        time.sleep(1)
        record2 = r.DNSRecord('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL)
        now = r.current_time_millis()

        assert record.created != record2.created
        assert record.get_remaining_ttl(now) != record2.get_remaining_ttl(now)

        record.reset_ttl(record2)

        assert record.ttl == record2.ttl
        assert record.created == record2.created
        assert record.get_remaining_ttl(now) == record2.get_remaining_ttl(now)

    def test_service_info_dunder(self):
        type_ = "_test-srvc-type._tcp.local."
        name = "xxxyyy"
        registration_name = "%s.%s" % (name, type_)
        info = ServiceInfo(
            type_,
            registration_name,
            80,
            0,
            0,
            b'',
            "ash-2.local.",
            addresses=[socket.inet_aton("10.0.1.2")],
        )

        assert not info != info
        repr(info)

    def test_service_info_text_properties_not_given(self):
        type_ = "_test-srvc-type._tcp.local."
        name = "xxxyyy"
        registration_name = "%s.%s" % (name, type_)
        info = ServiceInfo(
            type_=type_,
            name=registration_name,
            addresses=[socket.inet_aton("10.0.1.2")],
            port=80,
            server="ash-2.local.",
        )

        assert isinstance(info.text, bytes)
        repr(info)

    def test_dns_outgoing_repr(self):
        dns_outgoing = r.DNSOutgoing(const._FLAGS_QR_QUERY)
        repr(dns_outgoing)

    def test_dns_record_is_expired(self):
        record = r.DNSRecord('irrelevant', const._TYPE_SRV, const._CLASS_IN, 8)
        now = current_time_millis()
        assert record.is_expired(now) is False
        assert record.is_expired(now + (8 / 2 * 1000)) is False
        assert record.is_expired(now + (8 * 1000)) is True

    def test_dns_record_is_stale(self):
        record = r.DNSRecord('irrelevant', const._TYPE_SRV, const._CLASS_IN, 8)
        now = current_time_millis()
        assert record.is_stale(now) is False
        assert record.is_stale(now + (8 / 4.1 * 1000)) is False
        assert record.is_stale(now + (8 / 2 * 1000)) is True
        assert record.is_stale(now + (8 * 1000)) is True

    def test_dns_record_is_recent(self):
        now = current_time_millis()
        record = r.DNSRecord('irrelevant', const._TYPE_SRV, const._CLASS_IN, 8)
        assert record.is_recent(now + (8 / 4.1 * 1000)) is True
        assert record.is_recent(now + (8 / 3 * 1000)) is False
        assert record.is_recent(now + (8 / 2 * 1000)) is False
        assert record.is_recent(now + (8 * 1000)) is False


def test_dns_record_hashablity_does_not_consider_ttl():
    """Test DNSRecord are hashable."""

    # Verify the TTL is not considered in the hash
    record1 = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, const._DNS_OTHER_TTL, b'same')
    record2 = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, const._DNS_HOST_TTL, b'same')

    record_set = set([record1, record2])
    assert len(record_set) == 1

    record_set.add(record1)
    assert len(record_set) == 1

    record3_dupe = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, const._DNS_HOST_TTL, b'same')
    assert record2 == record3_dupe
    assert record2.__hash__() == record3_dupe.__hash__()

    record_set.add(record3_dupe)
    assert len(record_set) == 1


def test_dns_address_record_hashablity():
    """Test DNSAddress are hashable."""
    address1 = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 1, b'a')
    address2 = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 1, b'b')
    address3 = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 1, b'c')
    address4 = r.DNSAddress('irrelevant', const._TYPE_AAAA, const._CLASS_IN, 1, b'c')

    record_set = set([address1, address2, address3, address4])
    assert len(record_set) == 4

    record_set.add(address1)
    assert len(record_set) == 4

    address3_dupe = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 1, b'c')

    record_set.add(address3_dupe)
    assert len(record_set) == 4

    # Verify we can remove records
    additional_set = set([address1, address2])
    record_set -= additional_set
    assert record_set == set([address3, address4])


def test_dns_hinfo_record_hashablity():
    """Test DNSHinfo are hashable."""
    hinfo1 = r.DNSHinfo('irrelevant', const._TYPE_HINFO, 0, 0, 'cpu1', 'os')
    hinfo2 = r.DNSHinfo('irrelevant', const._TYPE_HINFO, 0, 0, 'cpu2', 'os')

    record_set = set([hinfo1, hinfo2])
    assert len(record_set) == 2

    record_set.add(hinfo1)
    assert len(record_set) == 2

    hinfo2_dupe = r.DNSHinfo('irrelevant', const._TYPE_HINFO, 0, 0, 'cpu2', 'os')
    assert hinfo2 == hinfo2_dupe
    assert hinfo2.__hash__() == hinfo2_dupe.__hash__()

    record_set.add(hinfo2_dupe)
    assert len(record_set) == 2


def test_dns_pointer_record_hashablity():
    """Test DNSPointer are hashable."""
    ptr1 = r.DNSPointer('irrelevant', const._TYPE_PTR, const._CLASS_IN, const._DNS_OTHER_TTL, '123')
    ptr2 = r.DNSPointer('irrelevant', const._TYPE_PTR, const._CLASS_IN, const._DNS_OTHER_TTL, '456')

    record_set = set([ptr1, ptr2])
    assert len(record_set) == 2

    record_set.add(ptr1)
    assert len(record_set) == 2

    ptr2_dupe = r.DNSPointer('irrelevant', const._TYPE_PTR, const._CLASS_IN, const._DNS_OTHER_TTL, '456')
    assert ptr2 == ptr2
    assert ptr2.__hash__() == ptr2_dupe.__hash__()

    record_set.add(ptr2_dupe)
    assert len(record_set) == 2


def test_dns_text_record_hashablity():
    """Test DNSText are hashable."""
    text1 = r.DNSText('irrelevant', 0, 0, const._DNS_OTHER_TTL, b'12345678901')
    text2 = r.DNSText('irrelevant', 1, 0, const._DNS_OTHER_TTL, b'12345678901')
    text3 = r.DNSText('irrelevant', 0, 1, const._DNS_OTHER_TTL, b'12345678901')
    text4 = r.DNSText('irrelevant', 0, 0, const._DNS_OTHER_TTL, b'ABCDEFGHIJK')

    record_set = set([text1, text2, text3, text4])

    assert len(record_set) == 4

    record_set.add(text1)
    assert len(record_set) == 4

    text1_dupe = r.DNSText('irrelevant', 0, 0, const._DNS_OTHER_TTL, b'12345678901')
    assert text1 == text1_dupe
    assert text1.__hash__() == text1_dupe.__hash__()

    record_set.add(text1_dupe)
    assert len(record_set) == 4


def test_dns_service_record_hashablity():
    """Test DNSService are hashable."""
    srv1 = r.DNSService('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL, 0, 0, 80, 'a')
    srv2 = r.DNSService('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL, 0, 1, 80, 'a')
    srv3 = r.DNSService('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL, 0, 0, 81, 'a')
    srv4 = r.DNSService('irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL, 0, 0, 80, 'ab')

    record_set = set([srv1, srv2, srv3, srv4])

    assert len(record_set) == 4

    record_set.add(srv1)
    assert len(record_set) == 4

    srv1_dupe = r.DNSService(
        'irrelevant', const._TYPE_SRV, const._CLASS_IN, const._DNS_HOST_TTL, 0, 0, 80, 'a'
    )
    assert srv1 == srv1_dupe
    assert srv1.__hash__() == srv1_dupe.__hash__()

    record_set.add(srv1_dupe)
    assert len(record_set) == 4


def test_rrset_does_not_consider_ttl():
    """Test DNSRRSet does not consider the ttl in the hash."""

    longarec = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 100, b'same')
    shortarec = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 10, b'same')
    longaaaarec = r.DNSAddress('irrelevant', const._TYPE_AAAA, const._CLASS_IN, 100, b'same')
    shortaaaarec = r.DNSAddress('irrelevant', const._TYPE_AAAA, const._CLASS_IN, 10, b'same')

    rrset = DNSRRSet([longarec, shortaaaarec])

    assert rrset.suppresses(longarec)
    assert rrset.suppresses(shortarec)
    assert not rrset.suppresses(longaaaarec)
    assert rrset.suppresses(shortaaaarec)

    verylongarec = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 1000, b'same')
    longarec = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 100, b'same')
    mediumarec = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 60, b'same')
    shortarec = r.DNSAddress('irrelevant', const._TYPE_A, const._CLASS_IN, 10, b'same')

    rrset2 = DNSRRSet([mediumarec])
    assert not rrset2.suppresses(verylongarec)
    assert rrset2.suppresses(longarec)
    assert rrset2.suppresses(mediumarec)
    assert rrset2.suppresses(shortarec)
