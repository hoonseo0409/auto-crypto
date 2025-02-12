import mytest2

# class Test():
#     def __init__(self):
#         print("created")
#
# iCSVHandler = CSVHandler.CSVHandler()
# print(iCSVHandler.setMessage.__name__)
print(len({'a':1, 'b':2}))
print('imported 1')

test_var = 'hi'

test_lst = [1, 2, 3, 4, 5]
test_lst_2 = [6, 7, 8]

print(*test_lst, *test_lst_2)

class Class_test:
    def __init__(self, test_instance_var):
        self.test_instance_var = test_instance_var


class Class_test_2:
    def __init__(self, iClass_test):
        self.iClass_test = iClass_test

    def inc_iClass_test(self):
        self.iClass_test.test_instance_var = self.iClass_test.test_instance_var + 1

iClass_test = Class_test(3)
print(iClass_test.test_instance_var)
iClass_test_2 = Class_test_2(iClass_test)
iClass_test_2.inc_iClass_test()
print(iClass_test.test_instance_var)
print(iClass_test_2.iClass_test.test_instance_var)