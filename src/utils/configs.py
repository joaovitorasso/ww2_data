import yaml

def load_config(config_path: str) -> dict:
    """
    Load the configuration from a YAML file.

    Args:
        config_path (str): The path to the YAML configuration file.
    Returns:
        dict: The configuration as a dictionary.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

if __name__ == "__main__":
    config = load_config('config/configs.yaml')
    print(config)