#!/usr/bin/env python3

import unittest
from unittest.mock import patch

import haproxystatechecker.check_server_state as target


class CheckServerStateTest(unittest.TestCase):

    def setUp(self):
        self.backend = "my-server-backend-name"
        self.checker = target.CheckServerState(self.backend)

    @patch('subprocess.check_output')
    def test_server_to_enable_is_not_found(self, mock_subprocess):
        """
        Test server to enable is not found.
        Expect: server not found exception to be thrown
        """

        # Mock response of haproxy stats where server does not exist
        mock_subprocess.return_value = b'# pxname,svname,qcur,qmax,scur,status\nidm,ARandomBackend,0,0,0,UP'

        with self.assertRaises(target.ServerNotFoundError) as error:
            self.checker.check_server_enabled()

        self.assertEqual(f"Server status not found for {self.backend}", str(error.exception))
        mock_subprocess.assert_called()

    @patch('builtins.print')
    @patch('subprocess.check_output')
    def test_server_to_enable_is_not_enabled(self, mock_subprocess, mock_print):
        """
        Test server to enable is found but is not enabled.
        Expect:
        - Report that 1 of 2 servers are enabled
        - Report that 1 servers is in MAINT state
        - Server not enabled exception to be thrown
        """
        # Mock response of haproxy stats where the server is UP and MAINT
        mock_subprocess.return_value = b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,0,UP\nig-business,%(backend)s,0,0,0,MAINT' % {b'backend': self.backend.encode('utf-8')}
        with self.assertRaises(target.ServerNotEnabledError) as error:
            self.checker.check_server_enabled()

        self.assertEqual(f"1 of 2 {self.backend} servers are not enabled", str(error.exception))
        mock_subprocess.assert_called()
        mock_print.assert_called_with(f"ERROR: Server {self.backend} status is MAINT")

    @patch('builtins.print')
    @patch('subprocess.check_output')
    def test_server_to_enable_is_enabled(self, mock_subprocess, mock_print):
        """
        Test server to enable is found and is enabled
        Expect:
        - Report that servers are enabled
        """
        # Mock response of haproxy stats without excessive information
        mock_subprocess.return_value = b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,0,UP' % {b'backend': self.backend.encode('utf-8')}
        self.checker.check_server_enabled()

        mock_subprocess.assert_called()
        mock_print.assert_called_with(f"1 of 1 {self.backend} servers are enabled")

    @patch('subprocess.check_output')
    def test_server_to_drain_is_not_found(self, mock_subprocess):
        """
        Test server to drain is not found
        Expect:
        - Server not found exception to be thrown
        """
        # Mock response of haproxy stats where server does not exist
        mock_subprocess.return_value = b'# pxname,svname,qcur,qmax,scur,status\nidm,ARandomBackendServer,0,0,0,UP'

        with self.assertRaises(target.ServerNotFoundError) as error:
            self.checker.check_server_sessions_drained()

        self.assertEqual(f"Server status not found for {self.backend}", str(error.exception))
        mock_subprocess.assert_called()

    @patch('builtins.print')
    @patch('subprocess.check_output')
    def test_server_to_drain_is_drained(self, mock_subprocess, mock_print):
        """
        Test server to drain is eventually drained
        Except:
        - Report found sessions
        - Report sessions successfully drained
        """
        # Side effect iterable that reduces the current connections of oig to 0
        mock_subprocess.side_effect = [b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,2,DRAIN\nig-business,%(backend)s,0,0,0,MAINT' % {b'backend': self.backend.encode('utf-8')},
                                       b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,2,DRAIN\nig-business,%(backend)s,0,0,0,MAINT' % {b'backend': self.backend.encode('utf-8')},
                                       b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,1,DRAIN\nig-business,%(backend)s,0,0,0,MAINT' % {b'backend': self.backend.encode('utf-8')},
                                       b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,0,DRAIN\nig-business,%(backend)s,0,0,0,MAINT' % {b'backend': self.backend.encode('utf-8')}]

        self.checker.check_server_sessions_drained(sleep_for=0.001)
        mock_subprocess.assert_called()
        mock_print.assert_called_with('2 Sessions Drained over 0.002(+/-0.001) seconds')

    @patch('subprocess.check_output')
    def test_server_to_drain_does_not_have_drain_status(self, mock_subprocess):
        """
        Test server to drain is enabled.
        Expect:
        - Server not drained exception to be thrown
        """
        # Mock response of haproxy stats where the server is DRAIN and UP
        mock_subprocess.return_value = b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,0,DRAIN\nig-business,%(backend)s,0,0,0,UP' % {b'backend': self.backend.encode('utf-8')}

        with self.assertRaises(target.ServerNotDrainedError) as error:
            self.checker.check_server_sessions_drained()

        self.assertEqual(f"Server {self.backend} must not be in ready state", str(error.exception))

        mock_subprocess.assert_called()

    @patch('builtins.print')
    @patch('subprocess.check_output')
    def test_server_to_drain_is_not_drained(self, mock_subprocess, mock_print):
        """
        Test Server to drain does not drain in the specified time.
        Expect:
        - Report that active sessions remain after specified time
        """
        # Side effect iterable where each call returns non-drained server
        mock_subprocess.side_effect = [b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,2,DRAIN' % {b'backend': self.backend.encode('utf-8')},
                                       b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,2,DRAIN' % {b'backend': self.backend.encode('utf-8')},
                                       b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,1,DRAIN' % {b'backend': self.backend.encode('utf-8')},
                                       b'# pxname,svname,qcur,qmax,scur,status\nig-business,%(backend)s,0,0,1,DRAIN' % {b'backend': self.backend.encode('utf-8')}]

        self.checker.check_server_sessions_drained(sleep_for=0.001, loop_for=2)
        mock_subprocess.assert_called()
        mock_print.assert_called_with('Found active sessions after 0.002 seconds, shutdown anyway')


if __name__ == '__main__':
    unittest.main()
