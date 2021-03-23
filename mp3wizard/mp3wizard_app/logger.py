import logging, os
print('')
print('')

print(os.getcwd())
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logging.basicConfig(filename=os.getcwd() +'/info.log', encoding='utf-8', level=logging.INFO)
logger = logging