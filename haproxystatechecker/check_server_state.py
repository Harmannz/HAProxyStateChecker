#!/usr/bin/env python3
# A script to check the draining of a given backend server in HAProxy

import argparse
import csv
import subprocess
import time
from io import StringIO


class ServerNotFoundError(Exception):
    pass


class ServerNotEnabledError(Exception):
    pass


class ServerNotDrainedError(Exception):
    pass


class CheckServerState:

    def __init__(self, backend):
        self.backend = backend

    @staticmethod
    def __get_haproxy_stats():
        return StringIO(subprocess.check_output('echo "show stat" | sudo socat /var/run/haproxy.sock stdio', shell=True).decode())

    def __get_session_count(self):
        current_sessions = []
        csv_data = self.__get_haproxy_stats()
        csv_reader = csv.DictReader(csv_data)
        for row in csv_reader:
            if row and row['svname'] == self.backend:
                current_sessions.append(int(row['scur']))

        if len(current_sessions) == 0:
            raise ServerNotFoundError(f"Server status not found for {self.backend}")
        else:
            return sum(current_sessions)

    def __get_server_states(self):
        server_states = []
        csv_data = self.__get_haproxy_stats()
        csv_reader = csv.DictReader(csv_data)
        for row in csv_reader:
            # grab occurrences of the backend server
            if row and row['svname'] == self.backend:
                # grab the server status
                server_states.append(row['status'])

        if len(server_states) == 0:
            raise ServerNotFoundError(f"Server status not found for {self.backend}")
        else:
            return server_states

    def check_server_sessions_drained(self, sleep_for=20, loop_for=15):
        server_states = self.__get_server_states()

        for status in server_states:
            if status == "UP":
                raise ServerNotDrainedError(f"Server {self.backend} must not be in ready state")

        max_sessions = 0
        loop_count = 0
        while loop_count <= loop_for:
            current_sessions = self.__get_session_count()

            if current_sessions > max_sessions:
                max_sessions = current_sessions

            if current_sessions == 0:
                break

            loop_count += 1
            print(f"{current_sessions} Sessions found, sleeping for {sleep_for} seconds")
            time.sleep(sleep_for)

        if loop_count <= loop_for:
            print(f"{max_sessions} Sessions Drained over {(loop_count * sleep_for)}(+/-{sleep_for}) seconds")
        else:
            print(f"Found active sessions after {loop_for * sleep_for} seconds, shutdown anyway")

    def check_server_enabled(self):
        server_states = self.__get_server_states()
        invalid_state = False
        invalid_states = []
        for status in server_states:
            if status != "UP":
                invalid_state = True
                invalid_states.append(status)
                print(f"ERROR: Server {self.backend} status is {status}")

        if invalid_state:
            raise ServerNotEnabledError(f"{len(invalid_states)} of {len(server_states)} {self.backend} servers are not enabled")
        else:
            print(f"{len(server_states)} of {len(server_states)} {self.backend} servers are enabled")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--drain", action='store_true', help="check server's sessions have drained")
    group.add_argument("--ready", action='store_true', help="check server is UP")

    args = parser.parse_args()

    checker = CheckServerState(args.backend)

    if args.ready:
        checker.check_server_enabled()
    elif args.drain:
        checker.check_server_sessions_drained()


if __name__ == "__main__":
    main()
