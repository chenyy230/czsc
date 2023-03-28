# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/11/21 17:48
describe: 笔相关信号的计算
"""
from typing import List, Union
from collections import OrderedDict
from deprecated import deprecated
from czsc import analyze
from czsc.objects import Direction, BI, FakeBI, Signal
from czsc.enum import Freq
from czsc.utils.ta import RSQ


def check_three_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别由远及近的三笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的三笔形态
    :param di: 最近一笔为倒数第i笔
    :return:
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='其他', v2='其他', v3='其他')

    if len(bis) != 3:
        return v

    bi1, bi2, bi3 = bis
    if not (bi1.direction == bi3.direction):
        print(f"1,3 的 direction 不一致，无法识别三笔形态，{bi3}")
        return v

    assert bi3.direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if bi3.direction == Direction.Down:
        # 向下不重合
        if bi3.low > bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下不重合')

        # 向下奔走型
        if bi2.low < bi3.low < bi1.high < bi2.high:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下奔走型')

        # 向下收敛
        if bi1.high > bi3.high and bi1.low < bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下收敛')

        if bi1.high < bi3.high and bi1.low > bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下扩张')

        if bi3.low < bi1.low and bi3.high < bi1.high:
            if bi3.power < bi1.power:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下盘背')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向下无背')

    if bi3.direction == Direction.Up:
        if bi3.high < bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上不重合')

        if bi2.low < bi1.low < bi3.high < bi2.high:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上奔走型')

        if bi1.high > bi3.high and bi1.low < bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上收敛')

        if bi1.high < bi3.high and bi1.low > bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上扩张')

        if bi3.low > bi1.low and bi3.high > bi1.high:
            if bi3.power < bi1.power:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上盘背')

            else:
                return Signal(k1=freq.value, k2=di_name, k3='三笔形态', v1='向上无背')
    return v


def check_five_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别五笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的五笔
    :param di: 最近一笔为倒数第i笔
    :return:
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='其他', v2='其他', v3='其他')

    if len(bis) != 5:
        return v

    bi1, bi2, bi3, bi4, bi5 = bis
    if not (bi1.direction == bi3.direction == bi5.direction):
        print(f"1,3,5 的 direction 不一致，无法识别五段形态；{bi1}{bi3}{bi5}")
        return v

    direction = bi1.direction
    max_high = max([x.high for x in bis])
    min_low = min([x.low for x in bis])
    assert direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if direction == Direction.Down:
        # aAb式底背驰
        if min(bi2.high, bi4.high) > max(bi2.low, bi4.low) and max_high == bi1.high and bi5.power < bi1.power:
            if (min_low == bi3.low and bi5.low < bi1.low) or (min_low == bi5.low):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='底背驰', v2='五笔aAb式')

        # 类趋势底背驰
        if max_high == bi1.high and min_low == bi5.low and bi4.high < bi2.low and bi5.power < max(bi3.power, bi1.power):
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='底背驰', v2='五笔类趋势')

        # 上颈线突破
        if (min_low == bi1.low and bi5.high > min(bi1.high, bi2.high) > bi5.low > bi1.low) \
                or (min_low == bi3.low and bi5.high > bi3.high > bi5.low > bi3.low):
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='上颈线突破', v2='五笔')

        # 五笔三买，要求bi5.high是最高点
        if max_high == bi5.high > bi5.low > max(bi1.high, bi3.high) \
                > min(bi1.high, bi3.high) > max(bi1.low, bi3.low) > min_low:
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='类三买', v2='五笔')

    if direction == Direction.Up:
        # aAb式类一卖
        if min(bi2.high, bi4.high) > max(bi2.low, bi4.low) and min_low == bi1.low and bi5.power < bi1.power:
            if (max_high == bi3.high and bi5.high > bi1.high) or (max_high == bi5.high):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='顶背驰', v2='五笔aAb式')

        # 类趋势类一卖
        if min_low == bi1.low and max_high == bi5.high and bi5.power < max(bi1.power, bi3.power) and bi4.low > bi2.high:
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='顶背驰', v2='五笔类趋势')

        # 下颈线突破
        if (max_high == bi1.high and bi5.low < max(bi1.low, bi2.low) < bi5.high < max_high) \
                or (max_high == bi3.high and bi5.low < bi3.low < bi5.high < max_high):
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='下颈线突破', v2='五笔')

        # 五笔三卖，要求bi5.low是最低点
        if min_low == bi5.low < bi5.high < min(bi1.low, bi3.low) \
                < max(bi1.low, bi3.low) < min(bi1.high, bi3.high) < max_high:
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='类三卖', v2='五笔')

    return v


def check_five_full_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别五笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的五笔
    :param di: 最近一笔为倒数第i笔
    :return:
    """
    di_name = f"倒{di}笔"

    v = Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='其他', v2='其他', v3='其他')

    if len(bis) != 5:
        return v

    bi1, bi2, bi3, bi4, bi5 = bis
    if not (bi1.direction == bi3.direction == bi5.direction):
        print(f"1,3,5 的 direction 不一致，无法识别五段形态；{bi1}{bi3}{bi5}")
        return v

    direction = bi1.direction
    max_high = max([x.high for x in bis])
    min_low = min([x.low for x in bis])
    assert direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if direction == Direction.Down:
        if bi1.high >= bi5.high >= bi3.high and bi1.low <= bi5.low <= bi3.low == min_low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L2')

        if bi1.high >= bi5.high >= bi3.high and bi1.low >= bi3.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='笔小井', v3='X5L3')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='无', v3='X5L3')

        # 五笔二买:要求bi3.low为最高点,bi1.high为最低点
        if bi1.high > bi5.high > bi3.high and min_low == bi3.low:
            if bi5.low > bi3.high:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L1')
            elif bi1.low > bi5.low > bi3.low:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='笔小井', v3='X5L4')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L4')

        if bi3.high <= bi1.high <= bi5.high and bi1.low >= bi3.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L5')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L5')

        if bi5.high >= bi1.high >= bi3.high >= bi5.low >= bi1.low >= bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L6')

        if bi3.high < bi1.high < bi5.high:
            if bi5.low > bi1.low > bi3.low and bi5.low > bi3.high:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L7')
            elif bi1.low > bi5.low > bi3.low:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='笔小井', v3='X5L8')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L8')

        if bi1.high <= bi3.high <= bi5.high and bi1.low >= bi3.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L9')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L9')

        if bi1.high <= bi3.high <= bi5.high and bi3.low <= bi1.low <= bi5.low <= max(bi1.high, bi2.high):
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L10')

        if bi1.high < bi3.high < bi5.high:
            if bi5.low > bi1.low > bi3.low and bi5.low > max(bi1.high, bi2.high):
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L11')
            elif bi1.low > bi5.low > bi3.low:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L12')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L12')

        if bi1.high >= bi3.high >= bi5.high >= bi1.low >= bi3.low > bi5.low:
            if bi5.power_price < bi3.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='笔大井', v3='X5L13')
            elif bi3.power_price > bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='笔小井', v3='X5L13')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='无', v3='X5L13')

        if bi1.high >= bi3.high >= bi5.high >= bi1.low >= bi5.low >= bi3.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='笔小井', v3='X5L14')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L14')

        if bi1.high > bi3.high > bi5.high > bi1.low:
            if bi5.low > bi1.low > bi3.low:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L15')

        if bi5.high >= bi1.low >= bi3.low > bi5.low and bi3.high >= bi5.high >= bi1.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L16')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L16')

        if bi1.low <= bi5.high and bi3.high >= bi5.high >= bi1.high and bi5.low >= bi1.low >= bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L17')

        if bi5.high > bi1.low > bi5.low > bi3.low and bi3.high > bi5.high > bi1.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L18')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L18')

        if bi3.high >= bi1.high >= bi5.high < bi3.low <= bi1.low <= bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L19')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L19')

        if bi3.high >= bi1.high >= bi5.high >= bi1.low and bi5.low >= bi1.low >= bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L20')

        if bi3.high > bi1.high > bi5.high < bi5.low < bi1.low < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L21')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L21')

        if bi1.high > bi3.high > bi5.high and bi5.high < bi1.low:
            if bi1.low > bi3.low > bi5.low \
                    and bi5.power_price < bi3.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='类大井', v3='X5L22')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='无', v3='X5L22')

        if bi1.high >= bi3.high >= bi5.high and bi5.high <= bi1.low and bi5.low >= bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L23')

        if bi1.high < bi3.high and bi1.high < bi3.high:
            if bi1.low > bi5.low > bi3.low:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L24')

        if bi1.high <= bi3.high and bi1.high <= bi3.high and bi1.low >= bi3.low >= bi5.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L25')

        if bi1.high >= bi5.high >= bi3.high >= bi5.low >= bi3.low >= bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L26')

        if bi1.high > bi5.high > bi3.high:
            if bi3.low > bi5.low > bi1.low:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='笔小井', v3='X5L27')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L27')

        if bi1.high > bi5.high > bi3.high:
            if bi5.low > bi3.low > bi1.low:
                if bi5.low > bi2.high:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='三买', v2='无', v3='X5L28')

        if bi1.high >= bi5.high >= bi3.high and bi3.low >= bi1.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='笔小井', v3='X5L29')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='无', v3='X5L29')

        if bi1.high < bi3.high < bi5.high and bi1.high < bi3.low:
            if bi5.low > bi2.high:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L30')
            elif bi3.low > bi5.low > bi1.low:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L32')

        if bi1.high <= bi3.high <= bi5.high and bi1.high <= bi3.low and bi1.low <= bi3.low <= bi5.low <= bi2.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L31')

        if bi1.high <= bi3.high <= bi5.high and bi1.high <= bi3.low and bi3.low >= bi1.low > bi5.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L33')

        if bi5.high > bi3.high > bi1.high:
            if bi5.low > bi3.low > bi1.low:
                if bi5.low > bi2.high:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='三买', v2='无', v3='X5L36')
            elif bi3.low > bi5.low > bi1.low:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='笔小井', v3='X5L35')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L35')

        if bi5.high >= bi3.high >= bi1.high and bi3.low >= bi1.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L37')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L37')

        if bi5.high >= bi3.high >= bi1.high and bi1.low <= bi3.low <= bi5.low <= bi3.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L34')

        if bi5.high >= bi1.high >= bi3.high >= bi5.low >= bi3.low >= bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L38')

        if bi5.high > bi1.high > bi3.high:
            if bi5.low > bi3.low > bi1.low:
                if bi5.low > bi2.high:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='三买', v2='无', v3='X5L40')
            elif bi3.low > bi5.low > bi1.low:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='笔小井', v3='X5L39')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二买', v2='无', v3='X5L39')

        if bi5.high >= bi1.high >= bi3.high and bi3.low >= bi1.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L41')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L41')

        if bi1.high >= bi3.high >= bi5.high and bi5.low >= bi3.low >= bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L42')

        if bi1.high > bi3.high > bi5.high and bi3.low > bi5.low > bi1.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='笔小井', v3='X5L43')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L43')

        if bi1.high >= bi3.high >= bi5.high and bi3.low >= bi1.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='笔小井', v3='X5L44')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一买', v2='无', v3='X5L44')

        if bi2.high > bi1.high > bi3.low > bi5.low > bi1.low and bi1.high < bi5.high < bi3.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='笔小井', v3='X5L45')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L45')

        if bi2.high >= bi1.high >= bi3.low >= bi1.low > bi5.low and bi1.high <= bi5.high <= bi3.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L47')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L47')

        if bi2.high >= bi1.high >= bi3.low and bi1.high <= bi5.high <= bi3.high and bi5.low >= bi3.low >= bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L46')

        if bi1.high < bi5.high < bi3.high and bi1.high < bi3.low and bi3.low > bi5.low > bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L48')

        if bi1.high <= bi5.high <= bi3.high and bi1.high <= bi3.low and bi3.low >= bi1.low > bi5.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L50')

        if bi1.high <= bi5.high <= bi3.high and bi1.high <= bi3.low and bi5.low >= bi3.low >= bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L49')

        if bi5.high < bi1.high < bi3.high and bi3.low > bi5.low > bi1.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='笔小井', v3='X5L51')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L51')

        if bi5.high <= bi1.high <= bi3.high and bi3.low >= bi1.low > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5L53')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5L53')

        if bi5.high <= bi1.high <= bi3.high and bi5.low >= bi3.low >= bi1.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二买', v2='无', v3='X5L52')

    if direction == Direction.Up:
        # 五笔一卖:要求bi1.low为最低点,bi5.high为最高点,中间三笔任意组合.
        if bi1.low <= bi5.low <= bi3.low <= bi5.high <= bi1.high and max_high == bi3.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S2')

        if bi1.low <= bi5.low <= bi3.low and bi1.high <= bi3.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='笔小井', v3='X5S3')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='无', v3='X5S3')

        # 五笔二卖:要求bi3.high为最高点,bi1.low为最低点
        if bi1.low < bi5.low < bi3.low and max_high == bi3.high:
            if bi5.high < bi3.low:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S1')
            elif bi1.high < bi5.high < bi3.high:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='笔小井', v3='X5S4')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S4')

        if bi3.low >= bi1.low >= bi5.low and bi1.high <= bi3.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S5')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S5')

        if bi5.low <= bi1.low <= bi3.low <= bi5.high <= bi1.high <= bi3.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S6')

        if bi3.low > bi1.low > bi5.low:
            if bi5.high < bi1.high < bi3.high and bi5.high < bi3.low:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S7')
            elif bi1.high < bi5.high < bi3.high:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='笔小井', v3='X5S8')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S8')

        if bi1.low >= bi3.low >= bi5.low and bi1.high <= bi3.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S9')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S9')

        if bi1.low >= bi3.low >= bi5.low and bi3.high >= bi1.high >= bi5.high >= max(bi1.low, bi2.low):
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S10')

        if bi1.low > bi3.low > bi5.low:
            if bi5.high < bi1.high < bi3.high and bi5.high < max(bi1.low, bi2.low):
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S11')
            elif bi1.high < bi5.high < bi3.high:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S12')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S12')

        if bi1.low <= bi3.low <= bi5.low > bi3.high >= bi1.high >= bi5.low:
            if bi5.power_price < bi3.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='笔大井', v3='X5S13')
            elif bi3.power_price < bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='笔小井', v3='X5S13')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='无', v3='X5S13')

        if bi1.low <= bi3.low <= bi5.low >= bi5.high >= bi1.high >= bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='笔小井', v3='X5S14')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S14')

        if bi1.low < bi3.low < bi5.low < bi1.high:
            if bi5.high < bi1.high < bi3.high:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S15')

        if bi5.low <= bi1.high <= bi3.high < bi5.high and bi3.low <= bi5.low <= bi1.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S16')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S16')

        if bi1.high >= bi5.low and bi3.low <= bi5.low <= bi1.low and bi5.high <= bi1.high <= bi3.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S17')

        if bi5.low < bi1.high < bi5.high < bi3.high and bi3.low < bi5.low < bi1.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S18')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S18')

        if bi3.low <= bi1.low <= bi5.low > bi3.high >= bi1.high >= bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S19')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S19')

        if bi3.low <= bi1.low <= bi5.low <= bi1.high and bi5.high <= bi1.high <= bi3.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S20')

        if bi3.low < bi1.low < bi5.low > bi5.high > bi1.high > bi5.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S21')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S21')

        if bi1.low < bi3.low < bi5.low and bi1.high <= bi3.high <= bi5.high:
            if bi1.high < bi3.high < bi5.high \
                    and bi5.power_price < bi3.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='类大井', v3='X5S22')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='无', v3='X5S22')

        if bi1.low <= bi3.low <= bi5.low and bi5.low >= bi1.high and bi5.high <= bi3.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='二卖', v2='无', v3='X5S23')

        if bi1.low > bi3.low and bi1.low > bi3.low:
            if bi1.high < bi5.high < bi3.high:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S24')

        if bi1.low >= bi3.low and bi1.high <= bi3.high <= bi5.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S25')

        if bi1.low <= bi5.low <= bi3.low <= bi5.high <= bi3.high <= bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖1', v2='无', v3='X5S26')

        if bi1.low < bi5.low < bi3.low:
            if bi3.high < bi5.high < bi1.high:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='笔小井', v3='X5S27')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='无', v3='X5S27')

        if bi1.low < bi5.low < bi3.low:
            if bi5.high < bi3.high < bi1.high:
                if bi5.high < bi2.low:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='三卖', v2='无', v3='X5S28')

        if bi1.low <= bi5.low <= bi3.low and bi3.high <= bi1.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='笔小井', v3='X5S29')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='无', v3='X5S29')

        if bi1.low > bi3.low > bi5.low and bi1.low > bi3.high:
            if bi5.high < bi2.low:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S30')
            elif bi3.high < bi5.high < bi1.high:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S32')

        if bi1.low >= bi3.low >= bi5.low and bi1.low >= bi3.high and bi1.high >= bi3.high >= bi5.high >= bi2.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S31')

        if bi1.low >= bi3.low >= bi5.low and bi1.low >= bi3.high and bi3.high <= bi1.high < bi5.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S33')

        if bi5.low < bi3.low < bi1.low:
            if bi5.high < bi3.high < bi1.high:
                if bi5.high < bi2.low:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='三卖', v2='无', v3='X5S36')
            elif bi3.high < bi5.high < bi1.high:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='笔小井', v3='X5S35')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='无', v3='X5S35')

        if bi5.low <= bi3.low <= bi1.low and bi3.high <= bi1.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S37')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S37')

        if bi5.low <= bi3.low <= bi1.low and bi1.high >= bi3.high >= bi5.high >= bi3.low:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖1', v2='无', v3='X5S34')

        if bi5.low <= bi1.low <= bi3.low <= bi5.high <= bi3.high <= bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖1', v2='无', v3='X5S38')

        if bi5.low < bi1.low < bi3.low:
            if bi5.high < bi3.high < bi1.high:
                if bi5.high < bi2.low:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='三卖', v2='无', v3='X5S40')
            elif bi3.high < bi5.high < bi1.high:
                if bi5.power_price < bi1.power_price:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='笔小井', v3='X5S39')
                else:
                    return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='无', v3='X5S39')

        if bi5.low <= bi1.low <= bi3.low and bi3.high <= bi1.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S41')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S41')

        if bi1.low <= bi3.low <= bi5.low and bi5.high <= bi3.high <= bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖1', v2='无', v3='X5S42')

        if bi1.low < bi3.low < bi5.low and bi3.high < bi5.high < bi1.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='笔小井', v3='X5S43')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='无', v3='X5S43')

        if bi1.low <= bi3.low <= bi5.low and bi3.high <= bi1.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='笔小井', v3='X5S44')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='一卖', v2='无', v3='X5S44')

        if bi2.low < bi1.low < bi3.high < bi5.high < bi1.high and bi1.low > bi5.low > bi3.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='笔小井', v3='X5S45')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='无', v3='X5S45')

        if bi2.low <= bi1.low <= bi3.high <= bi1.high < bi5.high and bi1.low >= bi5.low >= bi3.low:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S47')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S47')

        if bi2.low <= bi1.low <= bi3.high and bi1.low >= bi5.low >= bi3.low and bi5.high <= bi3.high <= bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖1', v2='无', v3='X5S46')

        if bi1.low > bi5.low > bi3.low and bi1.low > bi3.high and bi3.high < bi5.high < bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S48')

        if bi1.low >= bi5.low >= bi3.low and bi1.low >= bi3.high and bi3.high <= bi1.high < bi5.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S50')

        if bi1.low >= bi5.low >= bi3.low and bi1.low >= bi3.high and bi5.high <= bi3.high <= bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S49')

        if bi5.low > bi1.low > bi3.low and bi3.high < bi5.high < bi1.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='笔小井', v3='X5S51')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖', v2='无', v3='X5S51')

        if bi5.low >= bi1.low >= bi3.low and bi3.high <= bi1.high < bi5.high:
            if bi5.power_price < bi1.power_price:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='笔小井', v3='X5S53')
            else:
                return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='无', v2='无', v3='X5S53')

        if bi5.low >= bi1.low >= bi3.low and bi5.high <= bi3.high <= bi1.high:
            return Signal(k1=freq.value, k2=di_name, k3='五笔形态', v1='类二卖1', v2='无', v3='X5S52')

    return v


def check_seven_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别七笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的七笔
    :param di: 最近一笔为倒数第i笔
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='其他', v2='其他', v3='其他')

    if len(bis) != 7:
        return v

    bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis
    max_high = max([x.high for x in bis])
    min_low = min([x.low for x in bis])
    direction = bi7.direction

    assert direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if direction == Direction.Down:
        if bi1.high == max_high and bi7.low == min_low:
            # aAbcd式底背驰
            if min(bi2.high, bi4.high) > max(bi2.low, bi4.low) > bi6.high and bi7.power < bi5.power:
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='底背驰', v2='七笔aAbcd式')

            # abcAd式底背驰
            if bi2.low > min(bi4.high, bi6.high) > max(bi4.low, bi6.low) and bi7.power < (bi1.high - bi3.low):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='底背驰', v2='七笔abcAd式')

            # aAb式底背驰
            if min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low) and bi7.power < bi1.power:
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='底背驰', v2='七笔aAb式')

            # 类趋势底背驰
            if bi2.low > bi4.high and bi4.low > bi6.high and bi7.power < max(bi5.power, bi3.power, bi1.power):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='底背驰', v2='七笔类趋势')

        # 向上中枢完成
        if bi4.low == min_low and min(bi1.high, bi3.high) > max(bi1.low, bi3.low) \
                and min(bi5.high, bi7.high) > max(bi5.low, bi7.low) \
                and max(bi4.high, bi6.high) > min(bi3.high, bi4.high):
            if max(bi1.low, bi3.low) < max(bi5.high, bi7.high):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='向上中枢完成', v2='七笔')

        # 七笔三买：1~3构成中枢，最低点在1~3，最高点在5~7，5~7的最低点大于1~3的最高点
        if min(bi1.low, bi3.low) == min_low and max(bi5.high, bi7.high) == max_high \
                and min(bi5.low, bi7.low) > max(bi1.high, bi3.high) \
                and min(bi1.high, bi3.high) > max(bi1.low, bi3.low):
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='类三买', v2='七笔')

    if direction == Direction.Up:
        # 顶背驰
        if bi1.low == min_low and bi7.high == max_high:
            # aAbcd式顶背驰
            if bi6.low > min(bi2.high, bi4.high) > max(bi2.low, bi4.low) and bi7.power < bi5.power:
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='顶背驰', v2='七笔aAbcd式')

            # abcAd式顶背驰
            if min(bi4.high, bi6.high) > max(bi4.low, bi6.low) > bi2.high and bi7.power < (bi3.high - bi1.low):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='顶背驰', v2='七笔abcAd式')

            # aAb式顶背驰
            if min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low) and bi7.power < bi1.power:
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='顶背驰', v2='七笔aAb式')

            # 类趋势顶背驰
            if bi2.high < bi4.low and bi4.high < bi6.low and bi7.power < max(bi5.power, bi3.power, bi1.power):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='顶背驰', v2='七笔类趋势')

        # 向下中枢完成
        if bi4.high == max_high and min(bi1.high, bi3.high) > max(bi1.low, bi3.low) \
                and min(bi5.high, bi7.high) > max(bi5.low, bi7.low) \
                and min(bi4.low, bi6.low) < max(bi3.low, bi4.low):
            if min(bi1.high, bi3.high) > min(bi5.low, bi7.low):
                return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='向下中枢完成', v2='七笔')

        # 七笔三卖：1~3构成中枢，最高点在1~3，最低点在5~7，5~7的最高点小于1~3的最低点
        if min(bi5.low, bi7.low) == min_low and max(bi1.high, bi3.high) == max_high \
                and max(bi7.high, bi5.high) < min(bi1.low, bi3.low) \
                and min(bi1.high, bi3.high) > max(bi1.low, bi3.low):
            return Signal(k1=freq.value, k2=di_name, k3='基础形态', v1='类三卖', v2='七笔')
    return v


def check_nine_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别九笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的九笔
    :param di: 最近一笔为倒数第i笔
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='其他', v2='其他', v3='其他')
    if len(bis) != 9:
        return v

    direction = bis[-1].direction
    bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis
    max_high = max([x.high for x in bis])
    min_low = min([x.low for x in bis])
    assert direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if direction == Direction.Down:
        if min_low == bi9.low and max_high == bi1.high:
            # aAb式类一买
            if min(bi2.high, bi4.high, bi6.high, bi8.high) > max(bi2.low, bi4.low, bi6.low, bi8.low) \
                    and bi9.power < bi1.power and bi3.low >= bi1.low and bi7.high <= bi9.high:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2='九笔aAb式')

            # aAbcd式类一买
            if min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low) > bi8.high \
                    and bi9.power < bi7.power:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2='九笔aAbcd式')

            # ABC式类一买
            if bi3.low < bi1.low and bi7.high > bi9.high \
                    and min(bi4.high, bi6.high) > max(bi4.low, bi6.low) \
                    and (bi1.high - bi3.low) > (bi7.high - bi9.low):
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2='九笔ABC式')

            # 类趋势一买
            if bi8.high < bi6.low < bi6.high < bi4.low < bi4.high < bi2.low \
                    and bi9.power < max([bi1.power, bi3.power, bi5.power, bi7.power]):
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2='九笔类趋势')

        # 九笔类一买（2~4构成中枢A，6~8构成中枢B，9背驰）
        if max_high == max(bi1.high, bi3.high) and min_low == bi9.low \
                and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                and min(bi2.low, bi4.low) > max(bi6.high, bi8.high) \
                and min(bi6.high, bi8.high) > max(bi6.low, bi8.low) \
                and bi9.power < bi5.power:
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2='九笔aAbBc式')

        # 类三买（1357构成中枢，最低点在3或5）
        if max_high == bi9.high > bi9.low \
                > max([x.high for x in [bi1, bi3, bi5, bi7]]) \
                > min([x.high for x in [bi1, bi3, bi5, bi7]]) \
                > max([x.low for x in [bi1, bi3, bi5, bi7]]) \
                > min([x.low for x in [bi3, bi5]]) == min_low:
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类三买', v2='九笔GG三买')

        # 类三买（357构成中枢，8的力度小于2，9回调不跌破GG构成三买）
        if bi8.power < bi2.power and max_high == bi9.high > bi9.low \
                > max([x.high for x in [bi3, bi5, bi7]]) \
                > min([x.high for x in [bi3, bi5, bi7]]) \
                > max([x.low for x in [bi3, bi5, bi7]]) > bi1.low == min_low:
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类三买', v2='九笔GG三买')

        if min_low == bi5.low and max_high == bi1.high and bi4.high < bi2.low:  # 前五笔构成向下类趋势
            zd = max([x.low for x in [bi5, bi7]])
            zg = min([x.high for x in [bi5, bi7]])
            gg = max([x.high for x in [bi5, bi7]])
            if zg > zd and bi8.high > gg:  # 567构成中枢，且8的高点大于gg
                if bi9.low > zg:
                    return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类三买', v2='九笔ZG三买')

                # 类二买
                if bi9.high > gg > zg > bi9.low > zd:
                    return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类二买', v2='九笔')

    if direction == Direction.Up:
        if max_high == bi9.high and min_low == bi1.low:
            # aAbBc式类一卖
            if bi6.low > min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and min(bi6.high, bi8.high) > max(bi6.low, bi8.low) \
                    and max(bi2.high, bi4.high) < min(bi6.low, bi8.low) \
                    and bi9.power < bi5.power:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2='九笔aAbBc式')

            # aAb式类一卖
            if min(bi2.high, bi4.high, bi6.high, bi8.high) > max(bi2.low, bi4.low, bi6.low, bi8.low) \
                    and bi9.power < bi1.power and bi3.high <= bi1.high and bi7.low >= bi9.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2='九笔aAb式')

            # aAbcd式类一卖
            if bi8.low > min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low) \
                    and bi9.power < bi7.power:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2='九笔aAbcd式')

            # ABC式类一卖
            if bi3.high > bi1.high and bi7.low < bi9.low \
                    and min(bi4.high, bi6.high) > max(bi4.low, bi6.low) \
                    and (bi3.high - bi1.low) > (bi9.high - bi7.low):
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2='九笔ABC式')

            # 类趋势一卖
            if bi8.low > bi6.high > bi6.low > bi4.high > bi4.low > bi2.high \
                    and bi9.power < max([bi1.power, bi3.power, bi5.power, bi7.power]):
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2='九笔类趋势')

        # 九笔三卖
        if max_high == bi1.high and min_low == bi9.low \
                and bi9.high < max([x.low for x in [bi3, bi5, bi7]]) < min([x.high for x in [bi3, bi5, bi7]]):
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类三卖', v2='九笔')

        if min_low == bi1.low and max_high == bi5.high and bi2.high < bi4.low:  # 前五笔构成向上类趋势
            zd = max([x.low for x in [bi5, bi7]])
            zg = min([x.high for x in [bi5, bi7]])
            dd = min([x.low for x in [bi5, bi7]])
            if zg > zd and bi8.low < dd:  # 567构成中枢，且8的低点小于dd
                if bi9.high < zd:
                    return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类三卖', v2='九笔ZD三卖')

                # 类二卖
                if dd < zd <= bi9.high < zg:
                    return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类二卖', v2='九笔')
    return v


def check_eleven_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别十一笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的十一笔
    :param di: 最近一笔为倒数第i笔
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='其他', v2='其他', v3='其他')
    if len(bis) != 11:
        return v

    direction = bis[-1].direction
    bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9, bi10, bi11 = bis
    max_high = max([x.high for x in bis])
    min_low = min([x.low for x in bis])
    assert direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if direction == Direction.Down:
        if min_low == bi11.low and max_high == bi1.high:
            # ABC式类一买，A5B3C3
            if bi5.low == min([x.low for x in [bi1, bi3, bi5]]) \
                    and bi9.low > bi11.low and bi9.high > bi11.high \
                    and bi8.high > bi6.low and bi1.high - bi5.low > bi9.high - bi11.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="11笔A5B3C3式")

            # ABC式类一买，A3B3C5
            if bi1.high > bi3.high and bi1.low > bi3.low \
                    and bi7.high == max([x.high for x in [bi7, bi9, bi11]]) \
                    and bi6.high > bi4.low and bi1.high - bi3.low > bi7.high - bi11.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="11笔A3B3C5式")

            # ABC式类一买，A3B5C3
            if bi1.low > bi3.low and min(bi4.high, bi6.high, bi8.high) > max(bi4.low, bi6.low, bi8.low) \
                    and bi9.high > bi11.high and bi1.high - bi3.low > bi9.high - bi11.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="11笔A3B5C3式")

            # a1Ab式类一买，a1（1~7构成的类趋势）
            if bi2.low > bi4.high > bi4.low > bi6.high > bi5.low > bi7.low and bi10.high > bi8.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="11笔a1Ab式")

        # 类二买（1~7构成盘整背驰，246构成下跌中枢，9/11构成上涨中枢，且上涨中枢GG大于下跌中枢ZG）
        if bi7.power < bi1.power and min_low == bi7.low < max([x.low for x in [bi2, bi4, bi6]]) \
                < min([x.high for x in [bi2, bi4, bi6]]) < max([x.high for x in [bi9, bi11]]) < bi1.high == max_high \
                and bi11.low > min([x.low for x in [bi2, bi4, bi6]]) \
                and min([x.high for x in [bi9, bi11]]) > max([x.low for x in [bi9, bi11]]):
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类二买', v2="11笔")

        # 类二买（1~7为区间极值，9~11构成上涨中枢，上涨中枢GG大于4~6的最大值，上涨中枢DD大于4~6的最小值）
        if max_high == bi1.high and min_low == bi7.low \
                and min(bi9.high, bi11.high) > max(bi9.low, bi11.low) \
                and max(bi11.high, bi9.high) > max(bi4.high, bi6.high) \
                and min(bi9.low, bi11.low) > min(bi4.low, bi6.low):
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类二买', v2="11笔")

        # 类三买（1~9构成大级别中枢，10离开，11回调不跌破GG）
        gg = max([x.high for x in [bi1, bi2, bi3]])
        zg = min([x.high for x in [bi1, bi2, bi3]])
        zd = max([x.low for x in [bi1, bi2, bi3]])
        dd = min([x.low for x in [bi1, bi2, bi3]])
        if max_high == bi11.high and bi11.low > zg > zd \
                and gg > bi5.low and gg > bi7.low and gg > bi9.low \
                and dd < bi5.high and dd < bi7.high and dd < bi9.high:
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类三买', v2="11笔GG三买")

    if direction == Direction.Up:
        if max_high == bi11.high and min_low == bi1.low:
            # ABC式类一卖，A5B3C3
            if bi5.high == max([bi1.high, bi3.high, bi5.high]) and bi9.low < bi11.low and bi9.high < bi11.high \
                    and bi8.low < bi6.high and bi11.high - bi9.low < bi5.high - bi1.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2="11笔A5B3C3式")

            # ABC式类一卖，A3B3C5
            if bi7.low == min([bi11.low, bi9.low, bi7.low]) and bi1.high < bi3.high and bi1.low < bi3.low \
                    and bi6.low < bi4.high and bi11.high - bi7.low < bi3.high - bi1.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2="11笔A3B3C5式")

            # ABC式类一卖，A3B5C3
            if bi1.high < bi3.high and min(bi4.high, bi6.high, bi8.high) > max(bi4.low, bi6.low, bi8.low) \
                    and bi9.low < bi11.low and bi3.high - bi1.low > bi11.high - bi9.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2="11笔A3B5C3式")

        # 类二卖：1~9构成类趋势，11不创新高
        if max_high == bi9.high > bi8.low > bi6.high > bi6.low > bi4.high > bi4.low > bi2.high > bi1.low == min_low \
                and bi11.high < bi9.high:
            return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类二卖', v2="11笔")
    return v


def check_thirteen_bi(bis: List[Union[BI, FakeBI]], freq: Freq, di: int = 1) -> Signal:
    """识别十三笔形态

    :param freq: K线周期，也可以称为级别
    :param bis: 由远及近的十三笔
    :param di: 最近一笔为倒数第i笔
    """
    di_name = f"倒{di}笔"
    v = Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='其他', v2='其他', v3='其他')
    if len(bis) != 13:
        return v

    direction = bis[-1].direction
    bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9, bi10, bi11, bi12, bi13 = bis
    max_high = max([x.high for x in bis])
    min_low = min([x.low for x in bis])

    assert direction in [Direction.Down, Direction.Up], "direction 的取值错误"

    if direction == Direction.Down:
        if min_low == bi13.low and max_high == bi1.high:
            # ABC式类一买，A5B3C5
            if bi5.low < min(bi1.low, bi3.low) and bi9.high > max(bi11.high, bi13.high) \
                    and bi8.high > bi6.low and bi1.high - bi5.low > bi9.high - bi13.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="13笔A5B3C5式")

            # ABC式类一买，A3B5C5
            if bi3.low < min(bi1.low, bi5.low) and bi9.high > max(bi11.high, bi13.high) \
                    and min(bi4.high, bi6.high, bi8.high) > max(bi4.low, bi6.low, bi8.low) \
                    and bi1.high - bi3.low > bi9.high - bi13.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="13笔A3B5C5式")

            # ABC式类一买，A5B5C3
            if bi5.low < min(bi1.low, bi3.low) and bi11.high > max(bi9.high, bi13.high) \
                    and min(bi6.high, bi8.high, bi10.high) > max(bi6.low, bi8.low, bi10.low) \
                    and bi1.high - bi5.low > bi11.high - bi13.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一买', v2="13笔A5B5C3式")

    if direction == Direction.Up:
        if max_high == bi13.high and min_low == bi1.low:
            # ABC式类一卖，A5B3C5
            if bi5.high > max(bi3.high, bi1.high) and bi9.low < min(bi11.low, bi13.low) \
                    and bi8.low < bi6.high and bi5.high - bi1.low > bi13.high - bi9.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2="13笔A5B3C5式")

            # ABC式类一卖，A3B5C5
            if bi3.high > max(bi5.high, bi1.high) and bi9.low < min(bi11.low, bi13.low) \
                    and min(bi4.high, bi6.high, bi8.high) > max(bi4.low, bi6.low, bi8.low) \
                    and bi3.high - bi1.low > bi13.high - bi9.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2="13笔A3B5C5式")

            # ABC式类一卖，A5B5C3
            if bi5.high > max(bi3.high, bi1.high) and bi11.low < min(bi9.low, bi13.low) \
                    and min(bi6.high, bi8.high, bi10.high) > max(bi6.low, bi8.low, bi10.low) \
                    and bi5.high - bi1.low > bi13.high - bi11.low:
                return Signal(k1=freq.value, k2=di_name, k3='类买卖点', v1='类一卖', v2="13笔A5B5C3式")
    return v


# 以上是信号计算的辅助函数，主要是形态识别等。
# ----------------------------------------------------------------------------------------------------------------------
# 以下是信号计算函数（前缀固定为 get_s）

@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_three_bi(c: analyze.CZSC, di: int = 1) -> OrderedDict:
    """倒数第i笔的三笔形态信号

    信号完全分类：
        Signal('日线_倒1笔_三笔形态_向上收敛_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下收敛_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下无背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上不重合_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下盘背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上扩张_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下不重合_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上盘背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下扩张_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上奔走型_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向上无背_任意_任意_0')
        Signal('日线_倒1笔_三笔形态_向下奔走型_任意_任意_0')

    :param c: CZSC 对象
    :param di: 最近一笔为倒数第i笔
    :return: 信号字典
    """
    assert di >= 1
    bis = c.finished_bis
    freq: Freq = c.freq
    s = OrderedDict()
    v = Signal(k1=str(freq.value), k2=f"倒{di}笔", k3="三笔形态", v1="其他", v2='其他', v3='其他')
    s[v.key] = v.value

    if not bis:
        return s

    if di == 1:
        three_bi = bis[-3:]
    else:
        three_bi = bis[-3 - di + 1: -di + 1]

    v = check_three_bi(three_bi, freq, di)
    s[v.key] = v.value
    return s


@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_base_xt(c: analyze.CZSC, di: int = 1) -> OrderedDict:
    """倒数第i笔的基础形态信号

    完全分类：
        Signal('日线_倒1笔_基础形态_底背驰_五笔aAb式_任意_0'),
        Signal('日线_倒1笔_基础形态_下颈线突破_五笔_任意_0'),
        Signal('日线_倒1笔_基础形态_类三买_五笔_任意_0'),
        Signal('日线_倒1笔_基础形态_向上中枢完成_七笔_任意_0'),
        Signal('日线_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0'),
        Signal('日线_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0'),
        Signal('日线_倒1笔_基础形态_上颈线突破_五笔_任意_0'),
        Signal('日线_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0'),
        Signal('日线_倒1笔_基础形态_类三买_七笔_任意_0'),
        Signal('日线_倒1笔_基础形态_类三卖_五笔_任意_0'),
        Signal('日线_倒1笔_基础形态_类三卖_七笔_任意_0'),
        Signal('日线_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0')

    :param c: CZSC 对象
    :param di: 最近一笔为倒数第i笔
    :return: 信号字典
    """
    assert di >= 1

    bis = c.finished_bis
    freq: Freq = c.freq
    s = OrderedDict()
    v = Signal(k1=str(freq.value), k2=f"倒{di}笔", k3="基础形态", v1="其他", v2='其他', v3='其他')
    s[v.key] = v.value

    if not bis:
        return s

    if di == 1:
        five_bi = bis[-5:]
        seven_bi = bis[-7:]
    else:
        five_bi = bis[-5 - di + 1: -di + 1]
        seven_bi = bis[-7 - di + 1: -di + 1]

    for v in [check_five_bi(five_bi, freq, di), check_seven_bi(seven_bi, freq, di)]:
        if "其他" not in v.value:
            s[v.key] = v.value
    return s


@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_five_bi_xt(c: analyze.CZSC, di: int = 1) -> OrderedDict:
    """倒数第i笔的基础形态信号

    完全分类：


    :param c: CZSC 对象
    :param di: 最近一笔为倒数第i笔
    :return: 信号字典
    """
    assert di >= 1

    bis = c.finished_bis
    freq: Freq = c.freq
    s = OrderedDict()
    v = Signal(k1=str(freq.value), k2=f"倒{di}笔", k3="五笔形态", v1="其他", v2='其他', v3='其他')
    s[v.key] = v.value

    if not bis:
        return s

    if di == 1:
        five_bi = bis[-5:]
    else:
        five_bi = bis[-5 - di + 1: -di + 1]

    for v in [check_five_full_bi(five_bi, freq, di)]:
        if "其他" not in v.value:
            s[v.key] = v.value
    return s


@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_like_bs(c: analyze.CZSC, di: int = 1) -> OrderedDict:
    """倒数第i笔的类买卖点信号

    :param c: CZSC 对象
    :param di: 最近一笔为倒数第i笔
    :return: 信号字典
    """
    assert di >= 1
    bis = c.finished_bis
    freq: Freq = c.freq
    s = OrderedDict()
    v = Signal(k1=str(freq.value), k2=f"倒{di}笔", k3="类买卖点", v1="其他", v2='其他', v3='其他')
    s[v.key] = v.value

    if not bis:
        return s

    if di == 1:
        nine_bi = bis[-9:]
        eleven_bi = bis[-11:]
        thirteen_bi = bis[-13:]
    else:
        nine_bi = bis[-9 - di + 1: -di + 1]
        eleven_bi = bis[-11 - di + 1: -di + 1]
        thirteen_bi = bis[-13 - di + 1: -di + 1]

    for v in [check_nine_bi(nine_bi, freq, di), check_eleven_bi(eleven_bi, freq, di),
              check_thirteen_bi(thirteen_bi, freq, di)]:
        if "其他" not in v.value:
            s[v.key] = v.value
    return s


@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_bi_status(c: analyze.CZSC) -> OrderedDict:
    """倒数第1笔的表里关系信号

    :param c: CZSC 对象
    :return: 信号字典
    """
    freq: Freq = c.freq
    s = OrderedDict()
    v = Signal(k1=str(freq.value), k2="倒1笔", k3="表里关系", v1="其他", v2='其他', v3='其他')
    s[v.key] = v.value

    if c.bi_list:
        # 表里关系的定义参考：http://blog.sina.com.cn/s/blog_486e105c01007wc1.html
        min_ubi = min([x.low for x in c.bars_ubi])
        max_ubi = max([x.high for x in c.bars_ubi])

        last_bi = c.bi_list[-1]
        v = None
        if last_bi.direction == Direction.Down:
            if min_ubi < last_bi.low:
                v = Signal(k1=str(freq.value), k2="倒1笔", k3="表里关系", v1="向下延伸")
            else:
                v = Signal(k1=str(freq.value), k2="倒1笔", k3="表里关系", v1="底分完成")
        if last_bi.direction == Direction.Up:
            if max_ubi > last_bi.high:
                v = Signal(k1=str(freq.value), k2="倒1笔", k3="表里关系", v1="向上延伸")
            else:
                v = Signal(k1=str(freq.value), k2="倒1笔", k3="表里关系", v1="顶分完成")

        if v and "其他" not in v.value:
            s[v.key] = v.value
    return s


@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_d0_bi(c: analyze.CZSC) -> OrderedDict:
    """倒数第0笔信号

    :param c: CZSC 对象
    :return: 信号字典
    """
    freq: Freq = c.freq
    s = OrderedDict()

    default_signals = [
        Signal(k1=str(freq.value), k2="倒0笔", k3="方向", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="倒0笔", k3="长度", v1="其他", v2='其他', v3='其他'),
    ]
    for signal in default_signals:
        s[signal.key] = signal.value

    bis = c.finished_bis

    if bis:
        # 倒0笔方向
        last_bi = bis[-1]
        if last_bi.direction == Direction.Down:
            v = Signal(k1=str(freq.value), k2="倒0笔", k3="方向", v1="向上")
        elif last_bi.direction == Direction.Up:
            v = Signal(k1=str(freq.value), k2="倒0笔", k3="方向", v1="向下")
        else:
            raise ValueError

        if v and "其他" not in v.value:
            s[v.key] = v.value

        # 倒0笔长度
        bars_ubi = [x for x in c.bars_raw[-20:] if x.dt >= bis[-1].fx_b.elements[0].dt]
        if len(bars_ubi) >= 9:
            v = Signal(k1=str(freq.value), k2="倒0笔", k3="长度", v1="9根K线以上")
        elif 9 > len(bars_ubi) > 5:
            v = Signal(k1=str(freq.value), k2="倒0笔", k3="长度", v1="5到9根K线")
        else:
            v = Signal(k1=str(freq.value), k2="倒0笔", k3="长度", v1="5根K线以下")

        if "其他" not in v.value:
            s[v.key] = v.value
    return s


@deprecated(version='1.0.0', reason="所有笔、分型相关信号迁移至 cxt 下")
def get_s_di_bi(c: analyze.CZSC, di: int = 1) -> OrderedDict:
    """倒数第i笔的表里关系信号

    :param c: CZSC 对象
    :param di: 最近一笔为倒数第i笔
    :return: 信号字典
    """
    assert di >= 1
    freq: Freq = c.freq
    s = OrderedDict()
    k1 = str(freq.value)
    k2 = f"倒{di}笔"

    default_signals = [
        Signal(k1=k1, k2=k2, k3="方向", v1="其他", v2='其他', v3='其他'),
        Signal(k1=k1, k2=k2, k3="长度", v1="其他", v2='其他', v3='其他'),
        Signal(k1=k1, k2=k2, k3="拟合优度", v1="其他", v2='其他', v3='其他'),
    ]
    for signal in default_signals:
        s[signal.key] = signal.value

    bis = c.finished_bis
    if not bis:
        return s

    last_bi = bis[-di]

    # 方向
    v1 = Signal(k1=k1, k2=k2, k3="方向", v1=last_bi.direction.value)
    s[v1.key] = v1.value

    # 长度
    if len(last_bi.bars) >= 15:
        v = Signal(k1=k1, k2=k2, k3="长度", v1="15根K线以上")
    elif 15 > len(c.bars_ubi) > 9:
        v = Signal(k1=k1, k2=k2, k3="长度", v1="9到15根K线")
    else:
        v = Signal(k1=k1, k2=k2, k3="长度", v1="9根K线以下")

    if "其他" not in v.value:
        s[v.key] = v.value

    # 拟合优度
    rsq = RSQ([x.close for x in last_bi.bars[1:-1]])
    if rsq > 0.8:
        v = Signal(k1=k1, k2=k2, k3="拟合优度", v1="大于0.8")
    elif rsq < 0.2:
        v = Signal(k1=k1, k2=k2, k3="拟合优度", v1="小于0.2")
    else:
        v = Signal(k1=k1, k2=k2, k3="拟合优度", v1="0.2到0.8之间")

    if "其他" not in v.value:
        s[v.key] = v.value
    return s
