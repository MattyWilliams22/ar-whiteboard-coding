# Function to map marker IDs to text
def get_keyword(index):
    match index:
        case 203:
            return "IF"
        case 23:
            return "ELSE"
        case 124:
            return "FOR"
        case 62:
            return "WHILE"
        case 40:
            return "PRINT"
        case 98:
            return "RETURN"
        case _:
            return "UNKNOWN"