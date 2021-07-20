
class ConfigFile(dict):

    def __init__(self, config_file_path):
        super().__init__()

        try:
            with open(config_file_path, 'r') as f:
                server = None

                for line in f:
                    if not line.strip():
                        # Skip blank lines.
                        continue

                    if line.strip().startswith('['):
                        # Named configurations are specified by "[name]".
                        server = line.strip()[1:-1]

                        if server in self:
                            raise ValueError(
                                f'duplicate server config: {server}')

                        continue

                    setting = line.split('=')

                    if len(setting) != 2:
                        raise ValueError(
                            f'Invalid syntax in the following line of the '
                            f'config file:\n\n'
                            f'{line}')

                    if server not in self:
                        self[server] = {}

                    settings = self[server]

                    try:
                        settings[setting[0].strip()] = int(setting[1].strip())
                    except:
                        settings[setting[0].strip()] = setting[1].strip()

        except:
            raise Exception(
                f'There was a problem getting the config file '
                f'{str(config_file_path)}')
