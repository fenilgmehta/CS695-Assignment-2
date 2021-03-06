import json
fifo_file_name = json.load(open('client.conf', 'r'))['fifo_communication_file']
fifo_file_obj = open(fifo_file_name, 'a')
while user_input := input("Enter your client manipulation command: "):
    fifo_file_obj.write(user_input)
    fifo_file_obj.flush()
