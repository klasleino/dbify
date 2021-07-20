import os

from mysql.connector import connect
from pathlib import Path
from sshtunnel import SSHTunnelForwarder

from dbify.config_file import ConfigFile


class DbServer(object):
    
    def __init__(
            self, 
            db_name,
            db_user,
            db_password,
            db_host='127.0.0.1',
            db_port=3306,
            ssh_address=None,
            ssh_user=None,
            ssh_keyfile=None,
            local_bind_host='0.0.0.0',
            local_bind_port=3307):

        self.db_name = db_name
        
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password

        self.ssh_address = ssh_address
        self.ssh_user = ssh_user
        self.ssh_keyfile = ssh_keyfile
        self.local_bind_host = local_bind_host
        self.local_bind_port = local_bind_port

        self.__ssh_tunnel = ssh_address is not None

    def __enter__(self):
        if self.__ssh_tunnel:
            self.__tunnel_forwarder = SSHTunnelForwarder(
                (self.ssh_address, 22),
                ssh_username=self.ssh_user,
                ssh_pkey=self.ssh_keyfile,
                remote_bind_address=(self.db_host, self.db_port),
                local_bind_address=(self.local_bind_host, self.local_bind_port))

            tunnel = self.__tunnel_forwarder.__enter__()

            return connect(
                user=self.db_user,
                password=self.db_password,
                host=self.local_bind_host,
                port=tunnel.local_bind_port,
                database=self.db_name,
                use_pure=True)

        else:
            return connect(
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name)

    def __exit__(self, type, value, traceback):
        if self.__ssh_tunnel:
            return self.__tunnel_forwarder.__exit__(type, value, traceback)

        else:
            return False

    @staticmethod
    def from_config(db_name, config_name=None):

        if 'DBIFY_CONFIG' not in os.environ:
            config_file_path = Path.home() / '.dbify_config'
        else:
            config_file_path = os.environ['DBIFY_CONFIG']

        config = ConfigFile(config_file_path)

        if config_name in config:
            settings = config[config_name]
        else:
            raise ValueError(f'unknown config name: {config_name}')

        if 'db_user' not in settings:
            raise ValueError('"db_user" must be set in config')
        if 'db_password' not in settings:
            raise ValueError('"db_password" must be set in config')

        if ('ssh_address' in settings or 
                'ssh_user' in settings or 
                'ssh_keyfile' in settings):

            if 'ssh_address' not in settings:
                raise ValueError(
                    '"ssh_address" must be set in config if using ssh tunnel '
                    'forwarding')
            if 'ssh_user' not in settings:
                raise ValueError(
                    '"ssh_user" must be set in config if using ssh tunnel '
                    'forwarding')
            if 'ssh_keyfile' not in settings:
                raise ValueError(
                    '"ssh_keyfile" must be set in config if using ssh tunnel '
                    'forwarding')

        return DbServer(db_name, **settings)
