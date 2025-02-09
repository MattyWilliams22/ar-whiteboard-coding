def get_preprocessing_function(name):
    match name:
        case _:
            return None

def preprocess(image, steps):
    for step in steps:
        function = get_preprocessing_function(step)
        if function is not None:
            image = function(image)
        else:
            print(f"Error: Unknown preprocessing function {step}")
            return None