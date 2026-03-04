
# page size is 2 records
page_size : int = 9                           # 3 pointers and 2 values
read_size = 23                                 # number of bytes in page
node_size = 5
number_size = 4
class Buffer:
    def __init__(self, file_name, page_count : int):
        self.file_name = file_name
        self.current_open_page = None
        self.current_open_number = 0
        self.page_count = page_count
        self.redundant_pages = []
    def read_page(self, number : int):
        f = open(self.file_name, "rb")
        f.seek(number*read_size)
        chunk = f.read(read_size)
        self.current_open_page = chunk
        self.current_open_number = number
        f.seek(0)
        f.close()
        return chunk
    def get_page(self):
        if len(self.redundant_pages) > 0:
            ret = self.redundant_pages.pop(0)
        else:
            self.page_count += 1
            ret = self.page_count
        return ret
    def free_page(self, id):
        self.redundant_pages.append(id)
    def write_page(self, chunk, position):
        if position == -1:
            f = open(self.file_name, "ab+")
            f.write(chunk)
            f.close()
            self.page_count+=1
        else:
            f = open(self.file_name, "rb")
            file = b''
            page = 0
            while True:
                temp = f.read(read_size)
                if page == position:
                    file += chunk
                else:
                    file += temp
                page += 1
                if temp == b'':
                    break
            f.close()
            f = open(self.file_name, "wb")
            f.write(file)
            f.close()



class B_tree_node:
    def __init__(self, page, page_number):
        self.page_nr = page_number
        self.values = []
        self.pointers = []
        self.root = 0
        current_type = 0                     # data type we are reading now is a pointer :)
        curr = 0
        prev = 0
        temp = 0
        if page is not None:
            for i in page:
                if i == 10:
                    if current_type == 0:
                        self.pointers.append(temp)
                    else:
                        self.values.append(temp)
                    temp = 0
                    current_type = ( current_type + 1 )%2
                elif i != 13 and i != 45 and i != 44:
                    temp = i - 48 + temp * 10
        else:
            for i in range(0, node_size):
                self.values.append(0)
                self.pointers.append(0)
            self.pointers.append(0)
    def print_to_binary(self):
        res = ""
        indices = [0,0]
        for i in range(0, page_size):
            if i%2 == 0:
                res += int_to_string(self.pointers[indices[0]]) + "\r\n"
                indices[0] += 1
            else:
                res += int_to_string(self.values[indices[1]]) + "\r\n"
                indices[1] += 1
        res += ",\r\n"
        return bytearray(res.encode())
    def get_size(self):
        count = 0
        for val in self.values:
            if val != 0: count+=1
        return count
    def add_to_node(self, key):
        new_values = []
        test = 0
        for i in range(0, self.get_size()):
            if key > self.values[i] and test == 0:
                new_values.append(key)
                new_values.append(self.values[i])
                test = 1
            else:
                new_values.append(self.values[i])
        if test == 0:
            new_values.append(key)
        while len(new_values) < node_size:
            new_values.append(0)
        self.values = new_values
        buffer.write_page(self.print_to_binary(), self.page_nr)
        # do dokladania do noda ktory nie jest lisciem bedzie osobna funkcja
    def is_leaf(self):
        test = 0
        for pointer in self.pointers:
            if pointer != 0:
                test = 1
        if test == 0:
            return True
        return False
    def delete_node(self, key : int):
        new_values = []
        i = 0
        res = 0
        for val in self.values:
            if val != key:
                new_values.append(val)
            else:
                res = i
            i += 1
        new_values.append(0)
        self.values = new_values
        return res
    def print_node(self, level : int):
        space = ""
        count = 0
        for i in range(0, level):
            space += "\t"

        for i in range(self.get_size()):
            if self.pointers[i] != 0:
                node = B_tree_node(buffer.read_page(self.pointers[i]),self.pointers[i])
                node.print_node(level + 1)
            if i == 0:
                print(space, "n")
            print(space, self.values[i])
            count += 1
        print(space, "u")
        if self.pointers[count] != 0:
            node = B_tree_node(buffer.read_page(self.pointers[count]), self.pointers[count])
            node.print_node(level + 1)



class B_tree:
    def __init__(self, buffer : Buffer):
        self.root : int = 0                         # root page number
        self.buffer : Buffer = buffer
        self.path_buffer = []
    def display_tree(self):
        node = B_tree_node(self.buffer.read_page(self.root), self.root)
        node.print_node(1)
    def search_key(self, key : int):
        self.path_buffer = []
        node = B_tree_node(self.buffer.read_page(self.root), self.root)
        test = 0
        result = 0
        while True:
            self.path_buffer.append(node.page_nr)
            size = node.get_size()
            for i in range(0, size):
                val = node.values[i]
                if val == key:
                    test = 1
                    return node.page_nr
                    break
                if val < key:
                    if node.pointers[i] == 0:
                        result = -1                 # key not found
                    else:
                        node = B_tree_node(buffer.read_page(node.pointers[i]), node.pointers[i])
                    test = 1
                    break
            if test == 0:
                if node.pointers[size] == 0:
                    result = -1  # key not found
                else:
                    node = B_tree_node(buffer.read_page(node.pointers[size]), node.pointers[size])
            else:
                test = 0
            if result != 0:
                break
        if result != -1:
            return result
        else:
            return -1                               # mam zapamietana ostatnia odczytana strone

    def insert(self, key : int):
        if self.search_key(key) != -1:
            print("key already in base")
        else:
            i = -1
            passing_pointer = None
            node = B_tree_node(self.buffer.current_open_page, self.buffer.current_open_number)
            while True:
                if node.get_size() < node_size:
                    print("adding to base")
                    node.add_to_node(key)
                    break
                else:
                    test = self.insert_compensation(key,i, passing_pointer)
                    if test == -1:
                        new_key, passing_pointer = self.split_node(key, i, passing_pointer)
                        if new_key == 0:
                            break
                        else:
                            key = new_key
                            i -= 1
                            ind = self.path_buffer[i]
                            node = B_tree_node(self.buffer.read_page(ind), ind)
                    else:
                        break
    def delete_from_not_leaf(self, key : int, ind :int):
        ret_key = 0
        path = []

        i = self.path_buffer[ind]
        node = B_tree_node(self.buffer.read_page(i), i)
        ptr = node.delete_node(key)
        if node.pointers[ptr] != 0:
            i = node.pointers[ptr]
            while True:
                source_node = B_tree_node(self.buffer.read_page(i), i)
                path.append(i)
                if source_node.is_leaf():
                    ret_key = source_node.values[source_node.get_size()-1]      #last of values, no problem with pointers because leaf
                    break
                else:
                    i = source_node.pointers[source_node.get_size()]
            node.values.insert(ptr, ret_key)
        else:
            print("SOMETHING IS REALLY WRONG")
        buffer.write_page(node.print_to_binary(), node.page_nr)
        return ret_key, path

    def delete_from_leaf(self, key: int, path, ind:int):
        index = ind
        mode = 0
        i = self.path_buffer[index]
        if len(path) != 0:
            mode = -1
            i = path.pop(mode)
        else:
            index -= 1
        node = B_tree_node(self.buffer.read_page(i), i)
        node.delete_node(key)

        # point of return if underflow on merge
        while True:
            if node.get_size() + 1 < node_size/2:
                if node.page_nr == self.root:
                    if node.get_size() > 0:
                        break
                    else:
                        print("ALERT - moze sie wyjebac")
                        self.root = node.pointers[0]
                        self.buffer.free_page(node.page_nr)
                        break
                print("compensation")
                # todo - add pointers to compensation
                i = self.path_buffer[index]
                if len(path) != 0:
                    i = path.pop(mode)
                else:
                    index -= 1
                parent_node = B_tree_node(self.buffer.read_page(i), i)
                comp_test = 0
                test = -1
                for j in range(0, parent_node.get_size() + 1):
                    if parent_node.pointers[j] == node.page_nr:
                        if j - 1 >= 0:
                            neighbour_node = B_tree_node(buffer.read_page(parent_node.pointers[j - 1]), parent_node.pointers[j - 1])
                            if neighbour_node.get_size() > node_size / 2:
                                # ostatni
                                node.values.insert(0, parent_node.values[j - 1])
                                node.values.pop(-1)
                                parent_node.values[j - 1] = neighbour_node.values.pop(neighbour_node.get_size()-1)

                                node.pointers.insert(0,  neighbour_node.pointers.pop(neighbour_node.get_size()))
                                node.pointers.pop(0)
                                neighbour_node.pointers.append(0)
                                comp_test = 1
                                buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                                buffer.write_page(node.print_to_binary(), node.page_nr)
                                buffer.write_page(neighbour_node.print_to_binary(), neighbour_node.page_nr)
                                test = 0
                        if j + 1 < node_size and test == -1:
                            neighbour_node = B_tree_node(buffer.read_page(parent_node.pointers[j + 1]),
                                                         parent_node.pointers[j + 1])
                            if neighbour_node.get_size() > node_size / 2:
                                # pierwszy
                                node.values.insert(node.get_size(), parent_node.values[j])
                                node.values.pop(-1)
                                parent_node.values[j] = neighbour_node.values.pop(0)

                                node.pointers.insert(node.get_size(), neighbour_node.pointers.pop(0))
                                neighbour_node.pointers.append(0)
                                node.pointers.pop(-1)

                                comp_test = 1
                                buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                                buffer.write_page(node.print_to_binary(), node.page_nr)
                                buffer.write_page(neighbour_node.print_to_binary(), neighbour_node.page_nr)
                if comp_test == 1:
                    print("compensation successful")
                    break
                else:
                    print("starting merge")
                    for j in range(0, parent_node.get_size()+1):
                        if parent_node.pointers[j] == node.page_nr:
                            if j-1>=0:
                                k = parent_node.pointers[j - 1]
                                neighbour_node = B_tree_node(buffer.read_page(k), k)
                                # values in neighbour node are bigger
                                temp = neighbour_node.get_size()
                                for l in range(0, node.get_size()):
                                    neighbour_node.values[neighbour_node.get_size()] = node.values[l]
                                    neighbour_node.pointers[neighbour_node.get_size()] = node.pointers[l]
                                neighbour_node.pointers[neighbour_node.get_size()+1] = node.pointers[node.get_size()]
                                # trzeba dodac wartosc z noda wyzej
                                neighbour_node.values.insert(temp, parent_node.values.pop(j-1))
                                parent_node.pointers.pop(j)
                                parent_node.pointers.append(0)
                                #free page
                                buffer.free_page(node.page_nr)
                                buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                                buffer.write_page(neighbour_node.print_to_binary(), neighbour_node.page_nr)
                            elif j + 1 < parent_node.get_size() + 1:
                                k = parent_node.pointers[j + 1]
                                neighbour_node = B_tree_node(buffer.read_page(k), k)
                                #values in neighbour node are smaller
                                temp = node.get_size()
                                for l in range(0, neighbour_node.get_size()):
                                    node.values[node.get_size()] = neighbour_node.values[l]
                                    node.pointers[node.get_size()] = neighbour_node.pointers[l]
                                node.pointers[node.get_size()+1] = neighbour_node.pointers[neighbour_node.get_size()]
                                #trzeba dodac wartosc z noda wyzej
                                node.values.insert(temp, parent_node.values.pop(j))
                                parent_node.pointers.pop(j+1)
                                parent_node.pointers.append(0)
                                buffer.free_page(neighbour_node.page_nr)
                                buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                                buffer.write_page(node.print_to_binary(), node.page_nr)
                            node = parent_node
                            break
            else:
                buffer.write_page(node.print_to_binary(), node.page_nr)
                return
    def delete(self, key : int):
        print("delete")
        if self.search_key(key) == -1:
            print("key not in base")
        else:
            node = B_tree_node(self.buffer.current_open_page, self.buffer.current_open_number)

            if node.is_leaf():
                self.delete_from_leaf(key, [], -1)
            else:
                new_key, path = self.delete_from_not_leaf(key, -1)
                self.delete_from_leaf(new_key, path, -1)

    def insert_compensation(self, key : int, ind, passing_pointer):
        if len(self.path_buffer) + ind == 0:
            return -1
        print("compensating")
        i = self.path_buffer[ind]
        overflown_node = B_tree_node(buffer.read_page(i), i)
        if passing_pointer is not None:
            overflown_node.pointers.insert(0,passing_pointer)
        i = self.path_buffer[ind - 1]
        parent_node = B_tree_node(buffer.read_page(i), i)
        ret = -1
        for i in range(0, parent_node.get_size()+1):
            if parent_node.pointers[i] == overflown_node.page_nr:
                if i - 1 >= 0:
                    k = parent_node.pointers[i-1]
                    destination_node = B_tree_node(buffer.read_page(k), k)
                    if destination_node.get_size() < node_size:
                        destination_node.values[destination_node.get_size()] = parent_node.values[i-1]  # przepisuje z rodzica do destination
                        destination_node.values.pop(-1)
                        destination_node.pointers.insert(destination_node.get_size(), overflown_node.pointers.pop(0))
                        destination_node.pointers.pop(-1)
                        overflown_node.pointers.append(0)
                        temp = overflown_node.values[0]
                        if temp > key:
                            parent_node.values[i-1] = overflown_node.values.pop(0)
                            overflown_node.add_to_node(key)
                        else:
                            parent_node.values[i-1] = key
                        buffer.write_page(overflown_node.print_to_binary(), overflown_node.page_nr)
                        buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                        buffer.write_page(destination_node.print_to_binary(), destination_node.page_nr)
                        ret = 0
                    else:
                        ret = -1
                if i + 1 < parent_node.get_size() + 1 and ret == -1:
                    k = parent_node.pointers[i+1]
                    destination_node = B_tree_node(buffer.read_page(k), k)
                    if destination_node.get_size() < node_size:
                        destination_node.values.insert(0,parent_node.values.pop(i))
                        parent_node.values.append(0)
                        destination_node.values.pop(-1)
                        destination_node.pointers.insert(0, overflown_node.pointers.pop(-1))
                        destination_node.pointers.pop(-1)
                        overflown_node.pointers.append(0)
                        temp = overflown_node.values[overflown_node.get_size()-1]
                        if temp < key:
                            parent_node.values.insert(i,overflown_node.values.pop(overflown_node.get_size()-1))
                            parent_node.values.pop(-1)
                            overflown_node.add_to_node(key)
                        else:
                            parent_node.values.insert(i, key)
                            parent_node.values.pop(-1)

                        buffer.write_page(overflown_node.print_to_binary(), overflown_node.page_nr)
                        buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                        buffer.write_page(destination_node.print_to_binary(), destination_node.page_nr)
                        ret = 0
                        break
                    else:
                        return -1
                else:
                    return ret
        print("success")
        return 0
    def split_root_node(self, key:int, node:B_tree_node):
        print("splitting root")
        #overflown_node = B_tree_node(buffer.read_page(index), index)
        #buffer.page_count += 1
        i = buffer.get_page()
        left_node = B_tree_node(None, i)
        i = buffer.get_page()
        rigth_node = B_tree_node(None,i)
        i = 0
        while i < node_size/2 - 1:
            left_node.values[i] = node.values.pop(0)
            left_node.pointers[i] = node.pointers.pop(0)
            i+=1
        left_node.pointers[i] = node.pointers.pop(0)
        i = 0
        #while i < node_size/2 - 1:
        temp = node.get_size()
        while i < temp -1:
            rigth_node.values[i] = node.values.pop(1)
            rigth_node.pointers[i] = node.pointers.pop(0)
            i+=1
        rigth_node.pointers[i] = node.pointers.pop(0)
        while len(node.pointers) <= node_size:
            node.pointers.append(0)
        while len(node.values) < node_size:
            node.values.append(0)
        node.pointers[0] = left_node.page_nr
        node.pointers[1] = rigth_node.page_nr

        buffer.write_page(node.print_to_binary(),node.page_nr)
        buffer.write_page(left_node.print_to_binary(),left_node.page_nr)
        buffer.write_page(rigth_node.print_to_binary(),rigth_node.page_nr)



    def split_node(self, key : int, ind, passing_pointer):
        print("splitting")
        i = self.path_buffer[ind]
        overflown_node = B_tree_node(buffer.read_page(i), i)
        if passing_pointer is not None:
            overflown_node.pointers.insert(0,passing_pointer)
        overflown_node.add_to_node(key)
        overflown_node.pointers.append(0)
        if len(self.path_buffer) + ind == 0:
            self.split_root_node(key, overflown_node)
            return 0, None
        i = self.path_buffer[ind-1]
        parent_node = B_tree_node(buffer.read_page(i), i)
        j = i
        test = 0
        ret = 0
        temp = 0
        for temp in range(0, len(parent_node.pointers)):
            if parent_node.pointers[temp] == overflown_node.page_nr:
                break
        #while test == 0:
        #buffer.page_count += 1
        i = buffer.get_page()
        new_node = B_tree_node(None, i)
        for i, val in enumerate(overflown_node.values):
            if i < node_size/2:
                new_node.values[i] = overflown_node.values.pop(0)
                overflown_node.values.append(0)
                new_node.pointers[i] = overflown_node.pointers.pop(0)
                overflown_node.pointers.append(0)
            elif i == int(node_size/2)+1:
                new_node.pointers[i] = overflown_node.pointers.pop(0)
                #parent_node.pointers.pop(-1)
                if parent_node.get_size() < node_size:
                    parent_node.pointers.insert(temp, new_node.page_nr)
                    parent_node.pointers.pop(-1)
                    # nie ma przepelnienia i mozna normalnie kontynuowac
                    test = 1
                    parent_node.add_to_node(overflown_node.values.pop(0))   #zdejmujemy pierwsze bo poprzednie juz zostaly zdjete
                    #parent_node.pointers[i] = new_node
                    # todo - potencjalnie sie zepsuje
                    self.buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                    self.buffer.write_page(overflown_node.print_to_binary(), overflown_node.page_nr)
                    self.buffer.write_page(new_node.print_to_binary(), new_node.page_nr)
                    ret = 0 # <- wyszstko jest ok, nie trzeba przesuwac sie wyzej
                    return ret, None
                else:
                    ret = overflown_node.values.pop(0)
                    parent_node.pointers.insert(temp, new_node.page_nr)
                    passing_pointer = parent_node.pointers.pop(0)
                    self.buffer.write_page(overflown_node.print_to_binary(), overflown_node.page_nr)
                    self.buffer.write_page(new_node.print_to_binary(), new_node.page_nr)
                    self.buffer.write_page(parent_node.print_to_binary(), parent_node.page_nr)
                    return ret, passing_pointer


def int_to_string(i : int):
    res = ""
    if i == 0:
        res = "----"
    elif i < 10:
        res = "000" + str(i)
    elif i < 100:
        res = "00" + str(i)
    elif i < 1000:
        res = "0" + str(i)
    else:
        res = str(i)
    return res
def count_read_size():
    res = (2+number_size)*(2*node_size+1)+3
    return res
def count_page_size():
    res = 2*node_size+1
    return res

page_size = count_page_size()
read_size = count_read_size()
buffer = Buffer("file.txt", 0)
tree = B_tree(buffer)
tree.display_tree()

i = 2
while i < 100:
    tree.insert(i)
    tree.display_tree()
    i+=1




file = open("operations.txt", "r")

while True:
    line = file.readline()
    if line == "":
        break
    if line[0] == 'i':
        res = 0
        for l in line:
            if l == ' ':
                res = 0
            elif l != 'i' and l != 'd' and l != '\n':
                res = res*10 + int(l)
        tree.insert(res)
    elif line[0] == 's':
        tree.display_tree()
    elif line[0] == 'd':
        res = 0
        for l in line:
            if l == ' ':
                res = 0
            elif l != 'i' and l != 'd' and l != '\n':
                res = res*10 + int(l)
        tree.delete(res)


file.close()
print("end")