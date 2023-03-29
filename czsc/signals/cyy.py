# -*- coding: utf-8 -*-
"""
author: chenyiyong
email: 8665254@qq.com
create_dt:2023/3/29 8:21
describe:
"""

from loguru import logger

try:
    import talib as ta
except:
    logger.warning(f"ta-lib 没有正确安装，相关信号函数无法正常执行。"
                   f"请参考安装教程 https://blog.csdn.net/qaz2134560/article/details/98484091")
import numpy as np
from typing import List
from collections import OrderedDict
from czsc.analyze import CZSC, RawBar
from czsc.traders.base import CzscSignals
from czsc.utils.sig import get_sub_elements, create_single_signal, get_right_bi_num


def cyy_judge_struct_V230329(cat: CzscSignals, di: int = 1, max_freq: str = '60分钟', min_freq: str = '15分钟',
                             **kwargs) -> OrderedDict:
    """大小级别判断买卖点笔数V230329

        **信号逻辑：**
        判断从大级别端点右侧数，小级别有几笔，如果为2笔，就是2买，如果有3笔以上，即为类二买
        具体配合形态识别信号，如小级别五笔形态为二买的，以此可以锚定大级别的笔端点，形成真正具体的二买信号


        **信号列表：**

        - Signal('15分钟_D1MACD12#26#9回抽零轴_BS2辅助V230324_看空_任意_任意_0')
        - Signal('15分钟_D1MACD12#26#9回抽零轴_BS2辅助V230324_看多_任意_任意_0')

        :param cat: CzscSignals对象
        :return: 信号识别结果
        """

    max_freq_czsc: CZSC = cat.kas[max_freq]
    min_freq_czsc: CZSC = cat.kas[min_freq]
    k1, k2, k3, v1 = max_freq, min_freq, f'D{di}右侧笔数', '其他'

    if len(max_freq_czsc.bi_list) < 2 and len(min_freq_czsc.bi_list) < 5:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)

    num = get_right_bi_num(max_freq_czsc, min_freq_czsc)
    if num == 2:
        v1 = '2买卖点'
    elif num == 4 or num == 5 or num == 6 or num == 8 or num == 10:
        v1 = '类2或3买卖点'
    else:
        v1 = '其他'

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
