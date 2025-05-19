# Index of largest code marker ID
CODE_MAX = 16

ALL_KEYWORDS = {
    "FUNCTION",
    "IF",
    "THEN",
    "ELSE",
    "WHILE",
    "DO",
    "FOR",
    "PRINT",
    "RETURN",
    "ELSE IF",
    "ELSEIF",
    "END",
    "TAKE",
    "CALL",
    "WITH",
    "FROM",
    "TO",
    "STR",
    "IMPORT",
    "AS",
    "TRY",
    "CATCH",
    "FINALLY",
    "CLASS"
}

ALL_CORNER_MARKERS = {
    "Bottom Left",
    "Bottom Right",
    "Top Right",
    "Top Left",
}

# Function to map marker IDs to text
def get_keyword(index):
    match index:
        case 0:
            return "FUNCTION"
        case 1:
            return "IF"
        case 2:
            return "THEN"
        case 3:
            return "ELSE"
        case 4:
            return "WHILE"
        case 5:
            return "DO"
        case 6:
            return "FOR"
        case 7:
            return "PRINT"
        case 8:
            return "RETURN"
        case 9:
            return "ELSE IF"
        case 10:
            return "END"
        case 11:
            return "TAKE"
        case 12:
            return "CALL"
        case 13:
            return "WITH"
        case 14:
            return "FROM"
        case 15:
            return "TO"
        case 16:
            return "STR"
        case 17:
            return "IMPORT"
        case 18:
            return "AS"
        case 19:
            return "TRY"
        case 20:
            return "CATCH"
        case 21:
            return "FINALLY"
        case 22:
            return "CLASS"
        case 44:
            return "PYTHON"
        case 45:
            return "RESULTS"
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