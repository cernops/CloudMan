import re 
'''This will compare the User List starting 
with 
# groups with special users
##This is at Step one first prepare the file with no empty lines
'''
def compareUserList(first , second):
    first_list =[]
    map_file = open(first)
    while 1:
        line = map_file.readline()
        if not line:
            break
        str = re.sub("\s+"," ",line)
        str_array =str.split(' ')
        first_list.append(str_array[0])
    map_file.close()
    
    second_list = []
    map_file = open(second)
    while 1:
        line = map_file.readline()
        if not line:
            break
        str = re.sub("\s+"," ",line)
        str_array =str.split(' ')
        second_list.append(str_array[0])
    map_file.close()
    
    for item in first_list:
        if item not in  second_list:
            print item

#compareUserList("/root/user.cut","/root/lsb.users.cut" )
compareUserList("/home/user.new.cut","/home/user.cut")





