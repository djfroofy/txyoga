# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Test updating elements in collections.
"""
from twisted.trial.unittest import TestCase
from twisted.web import http, http_headers

from txyoga.serializers import json
from txyoga.test import collections


class ElementUpdatingTest(collections.UpdatableCollectionMixin, TestCase):
    """
    Test the updating of elements.
    """
    uselessUpdateBody = {"color": "green"}
    usefulUpdateBody = {"maximumOccupancy": 200}


    def setUp(self):
        collections.UpdatableCollectionMixin.setUp(self)
        self.addElements()
        self.headers = http_headers.Headers()
        self.body = self.uselessUpdateBody


    def _test_updateElement(self, expectedStatusCode=http.OK):
        """
        Tries to change the color of a bikeshed.
        """
        name = self.elementArgs[0][0]
        self.getElement(name)
        expectedContent = self.responseContent

        encodedBody = json.dumps(self.body)
        self.updateElement(name, encodedBody, self.headers)

        if expectedStatusCode is http.OK:
            # A successful PUT does not have a response body
            self.assertEqual(self.request.code, expectedStatusCode)
            self._checkContentType(None)
            expectedContent["color"] = self.body["color"]
        else:
            # A failed PUT has a response body
            self._checkContentType("application/json")
            self._decodeResponse()
            self._checkBadRequest(expectedStatusCode)

        self.getElement(name)
        self.assertEqual(self.request.code, http.OK)
        self._checkContentType("application/json")
        self.assertEqual(self.responseContent, expectedContent)


    def test_updateElement(self):
        """
        Test that updating an element works.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self._test_updateElement()


    def test_updateElement_missingContentType(self):
        """
        Test that trying to update an element when not specifying the content
        type fails.
        """
        self._test_updateElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_updateElement_badContentType(self):
        """
        Test that trying to update an element when specifying a bad content
        type fails.
        """
        self.headers.setRawHeaders("Content-Type", ["ZALGO/ZALGO"])
        self._test_updateElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_updateElement_nonUpdatableAttribute(self):
        """
        Tests that updating an attribute which is not allowed to be updated
        responds that that operation is forbidden.

        Try to make the bikeshed twice as large, which won't work because that
        would be a useful change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = self.usefulUpdateBody
        self._test_updateElement(http.FORBIDDEN)


    def test_updateElement_partiallyUpdatableAttributes(self):
        """
        Tests that updates are atomic; when part of an update is not allowed,
        the entire update does not happen.

        Try to make the bikeshed twice as large and change its color.  Both
        will fail, since the useful operation blocks the entire change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = dict(self.usefulUpdateBody)
        self.body.update(self.uselessUpdateBody)
        self._test_updateElement(http.FORBIDDEN)
