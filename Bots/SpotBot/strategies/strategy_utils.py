import pandas as pd

def calculate_position_value(price, amount):
    '''
    calculate each position value
    '''
    return price * amount

def np_round_floor(f_str, n):
    
    # f_str = '{}'.format(f_str) 也可以转换为字符串
    f_str = str(f_str)      
    
    # a = num before ".", b = ".", c= num after "."
    a, b, c = f_str.partition('.')
    
    # 如论传入的函数有几位小数，在字符串后面都添加n为小数0
    # n is defined by user when he/she calls the function
    c = (c+"0"*n)[:n]

    return float(".".join([a, c]))

def pandas_fill(arr):
    
    df = pd.DataFrame(arr)
    df.fillna(0, axis=0, inplace=True)

    # Return the df to 1-D array
    out = df[0].values
    return out