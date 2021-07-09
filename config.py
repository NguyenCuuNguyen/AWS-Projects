import yaml
from yaml.loader import SafeLoader

with open('test.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)

print('table1:', data['table1'])
