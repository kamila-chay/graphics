import numpy as np

def transform_kernel_to_np(text): # maybe here it should be only odd possible, maybe do return it in numpy and then simply multiply element wise by 
    # the image values
    rows = text.split("\n")
    rows = [row.split(",") for row in rows]
    if not all(len(rows[i]) == len(rows[0]) for i in range(1, len(rows))):
        return None
    try:
        rows = [[float(el.strip()) for el in row] for row in rows]
    except:
        return None
    return np.array(rows)