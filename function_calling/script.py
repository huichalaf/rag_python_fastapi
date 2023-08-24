import functions
import time

start = time.time()
for i in range(100):
   functions.auth_user('papo9292@gmail.com', 'ac45f74f1b4d9aff7708c4d84e57193c9bafda01b4c98e6210b2799858a02f80')
print(time.time()-start)
