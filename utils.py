import numpy as np

def transform_text_to_kernel(text):
    rows = text.split("\n")
    rows = [row.split(",") for row in rows]
    if len(rows) == 0 or len(rows[0]) == 0:
        return None
    if not all(len(rows[i]) == len(rows[0]) for i in range(1, len(rows))):
        return None
    try:
        rows = [[float(el.strip()) for el in row] for row in rows]
    except:
        return None
    return rows

def create_ds_kernel(kernel):
    y_len = len(kernel)
    y_min = -1 * (y_len // 2)
    y_max = -y_min if y_len % 2 == 1 else -y_min - 1
    x_len = len(kernel[0])
    x_min = -1 * (x_len // 2)
    x_max = -x_min if x_len % 2 == 1 else -x_min - 1
    ds_kernel = kernel
    for ii, i in enumerate(range(y_min, y_max + 1)):
        for jj, j in enumerate(range(x_min, x_max + 1)):
            ds_kernel[ii][jj] = (ds_kernel[ii][jj], j, i)

    return [el for row in ds_kernel for el in row]
