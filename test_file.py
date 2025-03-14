import time

def inefficient_loop(n):
    for i in range(len(range(n))):
        print(i) 

def unused_variable():
    x = 42 

def division_by_zero():
    try:
        result = 10 / 0  
    except ZeroDivisionError:
        print("Cannot divide by zero!")

def mutable_default_arg(data=[]):
    data.append("test")
    return data

def sleep_in_loop():
    for i in range(5):
        print("Sleeping...")
        time.sleep(2)

if __name__ == "__main__":
    inefficient_loop(5)
    unused_variable()
    division_by_zero()
    print(mutable_default_arg())
    sleep_in_loop()
