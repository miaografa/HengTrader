def calculate_position_value(price, amount):
    '''计算base currency持仓的价值'''
    return price * amount

def np_round_floor(f_str, n):
    f_str = str(f_str)      # f_str = '{}'.format(f_str) 也可以转换为字符串
    a, b, c = f_str.partition('.')
    c = (c+"0"*n)[:n]       # 如论传入的函数有几位小数，在字符串后面都添加n为小数0
    return float(".".join([a, c]))
