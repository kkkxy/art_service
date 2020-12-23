a = [1, 2, 3, 4]
b = a
print(id(a))  # id >>>4506684544

print(id(b))  # id  >>>4506684544
a.append(5)
print('\n', a)
print(b)  # 此时b也会跟改变
b.append(6)
print('\n', a)
print(b)
