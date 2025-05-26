count = 43
while count != 1:
    if count % 2 == 0:
        count = count // 2
    else:
        count = (count * 3) + 1
    print("Current count is:")
    print(str(count))