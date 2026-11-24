"""Securely save AWS access keys to ~/.aws/credentials (input is hidden)."""
import configparser
import getpass
import os

path = os.path.expanduser("~/.aws/credentials")
os.makedirs(os.path.dirname(path), exist_ok=True)
key = input("AWS Access Key ID: ").strip()
secret = getpass.getpass("AWS Secret Access Key (hidden): ").strip()
cfg = configparser.ConfigParser()
cfg.read(path)
cfg["default"] = {"aws_access_key_id": key, "aws_secret_access_key": secret}
with open(path, "w") as fh:
    cfg.write(fh)
conf = os.path.expanduser("~/.aws/config")
c2 = configparser.ConfigParser()
c2.read(conf)
c2["default"] = {"region": "ap-south-1"}
with open(conf, "w") as fh:
    c2.write(fh)
print("Saved to", path, "with region ap-south-1. Now tell Claude: done")
