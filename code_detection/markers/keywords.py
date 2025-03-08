# Function to map marker IDs to text
def get_keyword(index):
    match index:
        case 0:
            return "Function"
        case 1:
            return "If"
        case 2:
            return "Then"
        case 3:
            return "Else"
        case 4:
            return "While"
        case 5:
            return "Do"
        case 6:
            return "For"
        case 7:
            return "Print"
        case 8:
            return "Return"
        case 9:
            return "Else If"
        case 10:
            return "End"
        case 11:
            return "Take"
        case 12:
            return "Call"
        case 13:
            return "With"
        case 14:
            return "From"
        case 15:
            return "To"
        case 16:
            return "Str"
        case 44:
            return "Python Code:"
        case 45:
            return "Output:"
        case 46:
            return "Bottom Left"
        case 47:
            return "Bottom Right"
        case 48:
            return "Top Right"
        case 49:
            return "Top Left"
        case _:
            return "UNKNOWN"