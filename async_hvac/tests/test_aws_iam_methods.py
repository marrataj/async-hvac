import json
from base64 import b64decode
from datetime import datetime
import asynctest

from async_hvac import AsyncClient


class TestAwsIamMethods(asynctest.TestCase):
    """Unit tests providing coverage for AWS (EC2) auth backend-related methods/routes."""

    @asynctest.mock.patch('async_hvac.aws_utils.datetime')
    @asynctest.mock.patch('async_hvac.v1.AsyncClient.auth')
    async def test_auth_aws_iam(self, auth_mock, datetime_mock):
        datetime_mock.utcnow.return_value = datetime(2015, 8, 30, 12, 36, 0)
        client = AsyncClient()
        await client.auth_aws_iam('AKIDEXAMPLE', 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY')

        auth_mock.assert_called()
        args, kwargs = auth_mock.call_args
        actual_params = kwargs['json']

        actual_iam_http_request_method = actual_params['iam_http_request_method']
        self.assertEqual('POST', actual_iam_http_request_method)

        actual_iam_request_url = b64decode(actual_params['iam_request_url']).decode('utf-8')
        self.assertEqual('https://sts.amazonaws.com/', actual_iam_request_url)

        expected_auth_header_parts = [
            'Credential=AKIDEXAMPLE/20150830/us-east-1/sts/aws4_request',
            'SignedHeaders=content-length;content-type;host;x-amz-date',
            'Signature=0268ea4a725deae1116f5228d6b177fb047f9f3a9e1c5fd4baa0dc1fbb0d1a99',
        ]
        expected_iam_request_headers = {
            'Authorization': ['{0} {1}'.format('AWS4-HMAC-SHA256', ', '.join(expected_auth_header_parts))],
            'Content-Length': ['43'],
            'Content-Type': ['application/x-www-form-urlencoded; charset=utf-8'],
            'Host': ['sts.amazonaws.com'],
            'X-Amz-Date': ['20150830T123600Z'],
        }
        actual_iam_request_headers = json.loads(b64decode(actual_params['iam_request_headers']))
        self.assertEqual(expected_iam_request_headers, actual_iam_request_headers)

        actual_iam_request_body = b64decode(actual_params['iam_request_body']).decode('utf-8')
        self.assertEqual('Action=GetCallerIdentity&Version=2011-06-15', actual_iam_request_body)

        actual_role = actual_params['role']
        self.assertEqual('', actual_role)
        await client.close()
