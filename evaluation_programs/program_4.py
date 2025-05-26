try:
    # Risky operation
    result = 10 / 0
except Exception:
    print("An error occurred")
else:
    print("Operation successful, result is:")
    print(str(result))
finally:
    print("Cleanup actions")
