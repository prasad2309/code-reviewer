# test_code.py
def add_numbers(a, b):
    return a + b

def multiply_numbers(a, b):
    result = a * b
    # Unused variable
    temp = a + b
    return result

def divide_numbers(a, b):
    # Potential bug: Division by zero
    return a / b

# Incorrect indentation
def faulty_function():
x = 10
    print(x)

# Calling functions
print(add_numbers(5, 10))
print(multiply_numbers(3, 4))
print(divide_numbers(8, 0))  # This will cause a ZeroDivisionError
