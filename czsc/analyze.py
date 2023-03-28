# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/3/10 11:21
describe: 缠论分型、笔的识别
"""
import os
import webbrowser
import numpy as np
from loguru import logger
from typing import List, Callable
from collections import OrderedDict
from czsc.enum import Mark, Direction
from czsc.objects import BI, FX, RawBar, NewBar
from czsc.utils.echarts_plot import kline_pro
from czsc import envs
from datetime import datetime
import pandas as pd
from czsc.utils.ta import MACD
import talib as ta
from czsc.objects import Macd

logger.disable('czsc.analyze')


def remove_include(k1: NewBar, k2: NewBar, k3: RawBar):
    """去除包含关系：输入三根k线，其中k1和k2为没有包含关系的K线，k3为原始K线"""
    if k1.high < k2.high:
        direction = Direction.Up
    elif k1.high > k2.high:
        direction = Direction.Down
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4

    # 判断 k2 和 k3 之间是否存在包含关系，有则处理
    if (k2.high <= k3.high and k2.low >= k3.low) or (k2.high >= k3.high and k2.low <= k3.low):
        if direction == Direction.Up:
            high = max(k2.high, k3.high)
            low = max(k2.low, k3.low)
            dt = k2.dt if k2.high > k3.high else k3.dt
        elif direction == Direction.Down:
            high = min(k2.high, k3.high)
            low = min(k2.low, k3.low)
            dt = k2.dt if k2.low < k3.low else k3.dt
        else:
            raise ValueError

        if k3.open > k3.close:
            open_ = high
            close = low
        else:
            open_ = low
            close = high
        vol = k2.vol + k3.vol
        # 这里有一个隐藏Bug，len(k2.elements) 在一些及其特殊的场景下会有超大的数量，具体问题还没找到；
        # 临时解决方案是直接限定len(k2.elements)<=100
        elements = [x for x in k2.elements[:100] if x.dt != k3.dt] + [k3]
        k4 = NewBar(symbol=k3.symbol, id=k2.id, freq=k2.freq, dt=dt, open=open_,
                    close=close, high=high, low=low, vol=vol, elements=elements)
        return True, k4
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4


def check_fx(k1: NewBar, k2: NewBar, k3: NewBar):
    """查找分型"""
    fx = None
    if k1.high < k2.high > k3.high and k1.low < k2.low > k3.low:
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.G, high=k2.high,
                low=k2.low, fx=k2.high, elements=[k1, k2, k3])

    if k1.low > k2.low < k3.low and k1.high > k2.high < k3.high:
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.D, high=k2.high,
                low=k2.low, fx=k2.low, elements=[k1, k2, k3])

    return fx


def check_fxs(bars: List[NewBar]) -> List[FX]:
    """输入一串无包含关系K线，查找其中所有分型"""
    fxs = []
    for i in range(1, len(bars) - 1):
        fx: FX = check_fx(bars[i - 1], bars[i], bars[i + 1])
        if isinstance(fx, FX):
            # 这里可能隐含Bug，默认情况下，fxs本身是顶底交替的，但是对于一些特殊情况下不是这样，这是不对的。
            # 临时处理方案，强制要求fxs序列顶底交替
            if len(fxs) >= 2 and fx.mark == fxs[-1].mark:
                if envs.get_verbose():
                    logger.info(f"\n\ncheck_fxs: 输入数据错误{'+' * 100}")
                    logger.info(f"当前：{fx.mark}, 上个：{fxs[-1].mark}")
                    for bar in fx.raw_bars:
                        logger.info(f"{bar}\n")

                    logger.info(f'last fx raw bars: \n')
                    for bar in fxs[-1].raw_bars:
                        logger.info(f"{bar}\n")
            else:
                fxs.append(fx)
    return fxs


def check_bi(bars: List[NewBar], Macddata, bars_raw: List[RawBar] = None, benchmark: float = None):
    """输入一串无包含关系K线，查找其中的一笔

    :param bars: 无包含关系K线列表
    :param benchmark: 当下笔能量的比较基准
    :return:
    """
    min_bi_len = envs.get_min_bi_len()
    fxs = check_fxs(bars)
    if len(fxs) < 2:
        return None, bars

    fx_a = fxs[0]
    try:
        if fxs[0].mark == Mark.D:
            direction = Direction.Up
            fxs_b = [x for x in fxs if x.mark == Mark.G and x.dt > fx_a.dt and x.fx > fx_a.fx]
            if not fxs_b:
                return None, bars

            fx_b = fxs_b[0]
            for fx in fxs_b[1:]:
                if fx.high >= fx_b.high:
                    fx_b = fx

        elif fxs[0].mark == Mark.G:
            direction = Direction.Down
            fxs_b = [x for x in fxs if x.mark == Mark.D and x.dt > fx_a.dt and x.fx < fx_a.fx]
            if not fxs_b:
                return None, bars

            fx_b = fxs_b[0]
            for fx in fxs_b[1:]:
                if fx.low <= fx_b.low:
                    fx_b = fx
        else:
            raise ValueError
    except:
        logger.exception("笔识别错误")
        return None, bars

    bars_a = [x for x in bars if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
    bars_b = [x for x in bars if x.dt >= fx_b.elements[0].dt]

    bars_raw_a = [x for x in bars_raw if fx_a.elements[1].dt <= x.dt <= fx_b.elements[1].dt]

    bar_low = min([x.low for x in bars_raw])
    bar_high = max([x.high for x in bars_raw])
    fd_macd = [x for x in Macddata if fx_a.dt <= x.dt <= fx_b.dt]
    dif_a = fd_macd[0].dif
    dif_b = fd_macd[-1].dif
    # 判断fx_a和fx_b价格区间是否存在包含关系
    ab_include = (fx_a.high > fx_b.high and fx_a.low < fx_b.low) \
                 or (fx_a.high < fx_b.high and fx_a.low > fx_b.low)

    # 判断当前笔的涨跌幅是否超过benchmark的一定比例
    if benchmark and abs(fx_a.fx - fx_b.fx) > benchmark * envs.get_bi_change_th():
        power_enough = True
    else:
        power_enough = False

    if (dif_a < 0 < dif_b and len(bars_a) >= 5) or (dif_a > 0 > dif_b and (len(bars_a) >= 5)):
        macd_up = [x.macd for x in fd_macd if x.macd > 0]
        macd_down = [x.macd for x in fd_macd if x.macd < 0]
        if direction == Direction.Up:
            macd_length = 0 if len(macd_up) == 0 else abs(max(macd_up))
            max_dea = abs(max([x.dea for x in fd_macd]))
            max_dif = abs(max([x.dif for x in fd_macd]))

        else:
            macd_length = 0 if len(macd_down) == 0 else abs(min(macd_down))
            max_dea = abs(min([x.dea for x in fd_macd]))
            max_dif = abs(min([x.dif for x in fd_macd]))

        # 成笔的条件：1）顶底分型之间没有包含关系；2）笔长度大于等于min_bi_len 或 当前笔的涨跌幅已经够大
        # if (not ab_include) and (len(bars_a) >= min_bi_len or power_enough):
        #
        #     bi = BI(symbol=fx_a.symbol, fx_a=fx_a, fx_b=fx_b, fxs=fxs_, direction=direction, bars=bars_a)
        fxs_ = [x for x in fxs if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
        bi = BI(symbol=fx_a.symbol, fx_a=fx_a, fx_b=fx_b, fxs=fxs_,
                direction=direction, bars=bars_a, macd_length=macd_length,
                max_dea=max_dea, max_dif=max_dif, bar_high=bar_high, bar_low=bar_low
                )

        low_ubi = min([x.low for x in bars_b])
        high_ubi = max([x.high for x in bars_b])
        if (bi.direction == Direction.Up and high_ubi > bi.high) \
                or (bi.direction == Direction.Down and low_ubi < bi.low):
            return None, bars
        else:
            return bi, bars_b
    else:
        return None, bars


def get_sub_bi(c1, c0) -> int:
    """获取子区间（这是进行多级别联立分析的关键步骤）
    """
    start_dt = c1.bi_list[-1].sdt
    end_dt = c1.bi_list[-1].edt
    sub = []
    right_bi = []
    bis = c0.bi_list[-20:]
    # right_kn = [x for x in c0.bi_list if start_dt <= x.fx_a.dt <= end_dt]
    for bi in bis:
        if bi.fx_b.dt > start_dt > bi.fx_a.dt:
            sub.append(bi)
        elif start_dt <= bi.fx_a.dt < bi.fx_b.dt <= end_dt:
            sub.append(bi)
        elif bi.fx_a.dt < end_dt < bi.fx_b.dt:
            sub.append(bi)
        elif end_dt <= bi.fx_a.dt < bi.fx_b.dt:
            right_bi.append(bi)
        else:
            continue

    if len(sub) > 0 and sub[0].direction != c1.bi_list[-1].direction:
        sub = sub[1:]
    if len(sub) > 0 and sub[-1].direction != c1.bi_list[-1].direction:
        sub = sub[:-1]
    if len(right_bi) > 0 and right_bi[0] == c1.bi_list[-1].direction:
        right_bi = right_bi[1:]

    sub1: int = len(sub)
    right_di: int = len(right_bi)
    return sub1


def get_sub_bi_right_num(c2, c1, c0) -> tuple:
    """获取子区间（这是进行多级别联立分析的关键步骤）
    """
    start_dt_c2 = c2.bi_list[-1].sdt
    end_dt_c2 = c2.bi_list[-1].edt
    sub_c2 = []
    right_bi_c2 = []
    bis_c1 = c1.bi_list[-20:]
    # right_kn_c1 = [x for x in c1.bi_list if start_dt_c2 <= x.fx_a.dt <= end_dt_c2]

    for bi in bis_c1:
        if bi.fx_b.dt > start_dt_c2 > bi.fx_a.dt:
            sub_c2.append(bi)
        elif start_dt_c2 <= bi.fx_a.dt < bi.fx_b.dt <= end_dt_c2:
            sub_c2.append(bi)
        elif bi.fx_a.dt < end_dt_c2 < bi.fx_b.dt:
            sub_c2.append(bi)
        elif end_dt_c2 <= bi.fx_a.dt < bi.fx_b.dt:
            right_bi_c2.append(bi)
        else:
            continue

    if len(sub_c2) > 0 and sub_c2[0].direction != c2.bi_list[-1].direction:
        sub_c2 = sub_c2[1:]
    if len(sub_c2) > 0 and sub_c2[-1].direction != c2.bi_list[-1].direction:
        sub_c2 = sub_c2[:-1]
    if len(right_bi_c2) > 0 and right_bi_c2[0] == c2.bi_list[-1].direction:
        right_bi_c2 = right_bi_c2[1:]

    # 笔终点前次级别笔数
    sub_c2_1: int = len(sub_c2)
    # 笔终点后次级别笔数
    right_bi_c2_1: int = len(right_bi_c2)

    start_dt = c1.bi_list[-1].sdt
    end_dt = c1.bi_list[-1].edt
    sub = []
    right_bi = []
    bis = c0.bi_list[-20:]
    # right_kn = [x for x in c0.bi_list if start_dt <= x.fx_a.dt <= end_dt]
    for bi in bis:
        if bi.fx_b.dt > start_dt > bi.fx_a.dt:
            sub.append(bi)
        elif start_dt <= bi.fx_a.dt < bi.fx_b.dt <= end_dt:
            sub.append(bi)
        elif bi.fx_a.dt < end_dt < bi.fx_b.dt:
            sub.append(bi)
        elif end_dt <= bi.fx_a.dt < bi.fx_b.dt:
            right_bi.append(bi)
        else:
            continue

    if len(sub) > 0 and sub[0].direction != c1.bi_list[-1].direction:
        sub = sub[1:]
    if len(sub) > 0 and sub[-1].direction != c1.bi_list[-1].direction:
        sub = sub[:-1]
    if len(right_bi) > 0 and right_bi[0] == c1.bi_list[-1].direction:
        right_bi = right_bi[1:]

    # 大级别笔终点前次级别笔数
    sub_1: int = len(sub)
    # 大级别笔终点后次级别笔数
    right_bi_1: int = len(right_bi)
    return right_bi_c2_1, sub_c2_1, right_bi_1, sub_1


def get_sub_span(bis: List[BI], start_dt: [datetime, str], end_dt: [datetime, str], direction: Direction) -> List[BI]:
    """获取子区间（这是进行多级别联立分析的关键步骤）

    :param bis: 笔的列表
    :param start_dt: 子区间开始时间
    :param end_dt: 子区间结束时间
    :param direction: 方向
    :return: 子区间
    """
    start_dt = pd.to_datetime(start_dt)
    end_dt = pd.to_datetime(end_dt)
    sub = []
    for bi in bis:
        if bi.fx_b.dt > start_dt > bi.fx_a.dt:
            sub.append(bi)
        elif start_dt <= bi.fx_a.dt < bi.fx_b.dt <= end_dt:
            sub.append(bi)
        elif bi.fx_a.dt < end_dt < bi.fx_b.dt:
            sub.append(bi)
        else:
            continue

    if len(sub) > 0 and sub[0].direction != direction:
        sub = sub[1:]
    if len(sub) > 0 and sub[-1].direction != direction:
        sub = sub[:-1]
    return sub


def get_sub_bis(bis: List[BI], bi: BI) -> List[BI]:
    """获取大级别笔对象对应的小级别笔走势

    :param bis: 小级别笔列表
    :param bi: 大级别笔对象8
    :return:
    """
    sub_bis = get_sub_span(bis, start_dt=bi.fx_a.dt, end_dt=bi.fx_b.dt, direction=bi.direction)
    if not sub_bis:
        return []
    return sub_bis


class CZSC:
    def __init__(self,
                 bars: List[RawBar],
                 get_signals: Callable = None,
                 max_bi_num=envs.get_max_bi_num(),
                 level: int = 1,
                 macd_params=(8, 16, 4),
                 ma_params=(4, 8, 16, 77, 177),
                 atr_length=22,
                 ):
        """

        :param bars: K线数据
        :param max_bi_num: 最大允许保留的笔数量
        :param get_signals: 自定义的信号计算函数
        """
        self.verbose = envs.get_verbose()
        self.max_bi_num = max_bi_num
        self.bars_raw: List[RawBar] = []  # 原始K线序列
        self.bars_ubi: List[NewBar] = []  # 未完成笔的无包含K线序列
        self.bi_list: List[BI] = []
        self.symbol = bars[0].symbol
        self.level = level
        self.ma_params = ma_params
        self.macd_params = macd_params
        self.atr_length = atr_length
        self.macd = []
        self.ma = []
        self.freq = bars[0].freq
        self.get_signals = get_signals
        self.signals = None
        # cache 是信号计算过程的缓存容器，需要信号计算函数自行维护
        self.cache = OrderedDict()
        if bars != None:
            self.symbol = bars[0].symbol
            self.freq = bars[0].freq
            self.start_date = bars[0].dt
            self.end_date = bars[-1].dt
            self.latest_price = bars[-1].close
        for bar in bars:
            self.update(bar)

    def __repr__(self):
        return "<CZSC~{}~{}>".format(self.symbol, self.freq.value)

    def __update_bi(self):
        bars_ubi = self.bars_ubi
        if len(bars_ubi) < 3:
            return

        # 查找笔
        if not self.bi_list:
            # 第一笔的查找
            fxs = check_fxs(bars_ubi)
            if not fxs:
                return

            fx_a = fxs[0]
            fxs_a = [x for x in fxs if x.mark == fx_a.mark]
            for fx in fxs_a:
                if (fx_a.mark == Mark.D and fx.low <= fx_a.low) \
                        or (fx_a.mark == Mark.G and fx.high >= fx_a.high):
                    fx_a = fx
            bars_ubi = [x for x in bars_ubi if x.dt >= fx_a.elements[0].dt]
            bars_raw = [x for x in self.bars_raw if bars_ubi[-1].dt >= x.dt >= bars_ubi[0].dt]

            bi, bars_ubi_ = check_bi(bars=bars_ubi, Macddata=self.macd, bars_raw=bars_raw)
            if isinstance(bi, BI):
                self.bi_list.append(bi)
            self.bars_ubi = bars_ubi_
            return

        if self.verbose and len(bars_ubi) > 100:
            logger.info(f"{self.symbol} - {self.freq} - {bars_ubi[-1].dt} 未完成笔延伸数量: {len(bars_ubi)}")

        if envs.get_bi_change_th() > 0.5 and len(self.bi_list) >= 5:
            benchmark = min(self.bi_list[-1].power_price, np.mean([x.power_price for x in self.bi_list[-5:]]))
        else:
            benchmark = None

        last_bi = self.bi_list[-1]
        if (last_bi.direction == Direction.Up and bars_ubi[-1].high > last_bi.high) \
                or (last_bi.direction == Direction.Down and bars_ubi[-1].low < last_bi.low):
            bars_ubi_a = last_bi.bars[:-1] + [x for x in bars_ubi if x.dt >= last_bi.bars[-1].dt]
            self.bi_list.pop(-1)
        else:
            bars_ubi_a = bars_ubi

        if self.verbose and len(bars_ubi_a) > 100:
            print(f"{self.symbol} - {self.freq} - {bars_ubi_a[-1].dt} 未完成笔延伸超长，延伸数量: {len(bars_ubi_a)}")
        bars_raw_a = [x for x in self.bars_raw if bars_ubi_a[-1].dt >= x.dt >= bars_ubi_a[0].dt]
        bi, bars_ubi_ = check_bi(bars=bars_ubi_a, Macddata=self.macd, bars_raw=bars_raw_a, benchmark=benchmark)
        self.bars_ubi = bars_ubi_
        if isinstance(bi, BI):
            self.bi_list.append(bi)

    def update(self, bar: RawBar):
        """更新分析结果

        :param bar: 单根K线对象
        """
        # 更新K线序列
        self.symbol = bar.symbol
        self.freq = bar.freq
        if not self.bars_raw or bar.dt != self.bars_raw[-1].dt:
            self.bars_raw.append(bar)
            last_bars = [bar]
        else:
            # 当前 bar 是上一根 bar 的时间延伸
            self.bars_raw[-1] = bar
            if len(self.bars_ubi) >= 3:
                edt = self.bars_ubi[-2].dt
                self.bars_ubi = [x for x in self.bars_ubi if x.dt <= edt]
                last_bars = [x for x in self.bars_raw[-50:] if x.dt > edt]
            else:
                last_bars = self.bars_ubi[-1].elements
                last_bars[-1] = bar
                self.bars_ubi.pop(-1)

        # 去除包含关系
        bars_ubi = self.bars_ubi
        for bar in last_bars:
            if len(bars_ubi) < 2:
                bars_ubi.append(NewBar(symbol=bar.symbol, id=bar.id, freq=bar.freq, dt=bar.dt,
                                       open=bar.open, close=bar.close,
                                       high=bar.high, low=bar.low, vol=bar.vol, elements=[bar]))
            else:
                k1, k2 = bars_ubi[-2:]
                has_include, k3 = remove_include(k1, k2, bar)
                if has_include:
                    bars_ubi[-1] = k3
                else:
                    bars_ubi.append(k3)
        self.bars_ubi = bars_ubi

        # 这里
        self._update_ta()

        # 更新笔
        self.__update_bi()

        # 根据最大笔数量限制完成 bi_list, bars_raw 序列的数量控制
        self.bi_list = self.bi_list[-self.max_bi_num:]
        if self.bi_list:
            sdt = self.bi_list[0].fx_a.elements[0].dt
            s_index = 0
            for i, bar in enumerate(self.bars_raw):
                if bar.dt >= sdt:
                    s_index = i
                    break
            self.bars_raw = self.bars_raw[s_index:]

        # 如果有信号计算函数，则进行信号计算
        if self.get_signals:
            self.signals = self.get_signals(c=self)
        else:
            self.signals = OrderedDict()

        self.end_date = self.bars_raw[-1].dt
        self.latest_price = self.bars_raw[-1].close
        self.symbol = bar.symbol

    def _update_ta(self):
        """更新辅助技术指标
               """
        level = self.level
        if not self.ma:
            ma_temp = dict()
            close_ = np.array([x.close for x in self.bars_raw], dtype=np.double)
            for p in self.ma_params:
                ma_temp['ma%i' % p] = ta.SMA(close_, p)
            for i in range(len(self.bars_raw)):
                ma_ = {'ma%i' % p: ma_temp['ma%i' % p][i] for p in self.ma_params}
                ma_.update({"dt": self.bars_raw[i].dt})
                self.ma.append(ma_)
        else:
            ma_ = {'ma%i' % p: round(sum([x.close for x in self.bars_raw[-p:]]) / p, 1)
                   for p in self.ma_params}
            ma_.update({"dt": self.bars_raw[-1].dt})
            if len(self.bars_raw) > 1 and self.bars_raw[-2].dt == self.ma[-1]['dt']:
            # if self.bars_raw[-2].dt == self.ma[-1]['dt']:
                self.ma.append(ma_)
            else:
                self.ma[-1] = ma_

        if not self.macd:
            close_ = np.array([x.close for x in self.bars_raw], dtype=np.double)
            high_ = np.array([x.high for x in self.bars_raw], dtype=np.double)
            low_ = np.array([x.low for x in self.bars_raw], dtype=np.double)
            dif, dea, macd = MACD(close=close_, fastperiod=self.macd_params[0] * level,
                                  slowperiod=self.macd_params[1] * level,
                                  signalperiod=self.macd_params[2] * level)
            atr = ta.ATR(high=high_, low=low_, close=close_, timeperiod=self.atr_length)

            for i in range(len(self.bars_raw)):
                self.macd.append(
                    Macd(dt=self.bars_raw[i].dt, dif=round(dif[i], 2), dea=round(dea[i], 2), macd=round(macd[i], 2),
                         atr=round(atr[-1], 2)))
        else:
            close_ = np.array([x.close for x in self.bars_raw[-(self.macd_params[1] * level) - 2:]], dtype=np.double)
            high_ = np.array([x.high for x in self.bars_raw[-(self.macd_params[1] * level) - 2:]], dtype=np.double)
            low_ = np.array([x.low for x in self.bars_raw[-(self.macd_params[1] * level) - 2:]], dtype=np.double)
            dif, dea, macd = MACD(close=close_, fastperiod=self.macd_params[0] * level,
                                  slowperiod=self.macd_params[1] * level, signalperiod=self.macd_params[2] * level)
            atr = ta.ATR(high=high_, low=low_, close=close_, timeperiod=self.atr_length)
            macd_ = Macd(dt=self.bars_raw[-1].dt, dif=round(dif[-1], 2), dea=round(dea[-1], 2),
                         macd=round(macd[-1], 2), atr=round(atr[-1], 2))
            if len(self.bars_raw) > 1 and self.bars_raw[-2].dt == self.macd[-1].dt:
            # if self.bars_raw[-2].dt == self.macd[-1].dt:
                self.macd.append(macd_)
            else:
                self.macd[-1] = macd_

    def to_echarts(self, width: str = "1400px", height: str = '580px', bs=None):
        """绘制K线分析图

        :param width: 宽
        :param height: 高
        :param bs: 交易标记，默认为空
        :return:
        """
        kline = [x.__dict__ for x in self.bars_raw]
        if len(self.bi_list) > 0:
            bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in self.bi_list] + \
                 [{'dt': self.bi_list[-1].fx_b.dt, "bi": self.bi_list[-1].fx_b.fx}]
            fx = [{'dt': x.dt, "fx": x.fx} for x in self.fx_list]
        else:
            bi = None
            fx = None
        chart = kline_pro(kline, bi=bi, fx=fx, width=width, height=height, bs=bs,
                          title="{}-{}".format(self.symbol, self.freq.value))
        return chart

    def to_plotly(self):
        """使用 plotly 绘制K线分析图"""
        import pandas as pd
        from czsc.utils.plotly_plot import KlineChart

        bi_list = self.bi_list
        df = pd.DataFrame(self.bars_raw)
        kline = KlineChart(n_rows=3, title="{}-{}".format(self.symbol, self.freq.value))
        kline.add_kline(df, name="")
        kline.add_sma(df, ma_seq=(5, 10, 21), row=1, visible=True, line_width=1.2)
        kline.add_sma(df, ma_seq=(34, 55, 89, 144), row=1, visible=False, line_width=1.2)
        kline.add_vol(df, row=2)
        kline.add_macd(df, row=3)

        if len(bi_list) > 0:
            bi = pd.DataFrame([{'dt': x.fx_a.dt, "bi": x.fx_a.fx, "text": x.fx_a.mark.value} for x in bi_list] +
                              [{'dt': bi_list[-1].fx_b.dt, "bi": bi_list[-1].fx_b.fx,
                                "text": bi_list[-1].fx_b.mark.value[0]}])
            fx = pd.DataFrame([{'dt': x.dt, "fx": x.fx} for x in self.fx_list])
            kline.add_scatter_indicator(fx['dt'], fx['fx'], name="分型", row=1, line_width=2)
            kline.add_scatter_indicator(bi['dt'], bi['bi'], name="笔", text=bi['text'], row=1, line_width=2)
        return kline.fig

    def open_in_browser(self, width: str = "1400px", height: str = '580px'):
        """直接在浏览器中打开分析结果

        :param width: 图表宽度
        :param height: 图表高度
        :return:
        """
        home_path = os.path.expanduser("~")
        file_html = os.path.join(home_path, "temp_czsc.html")
        chart = self.to_echarts(width, height)
        chart.render(file_html)
        webbrowser.open(file_html)

    @property
    def last_bi_extend(self):
        """判断最后一笔是否在延伸中，True 表示延伸中"""
        if self.bi_list[-1].direction == Direction.Up \
                and max([x.high for x in self.bars_ubi]) > self.bi_list[-1].high:
            return True

        if self.bi_list[-1].direction == Direction.Down \
                and min([x.low for x in self.bars_ubi]) < self.bi_list[-1].low:
            return True

        return False

    @property
    def finished_bis(self) -> List[BI]:
        """已完成的笔"""
        if not self.bi_list:
            return []
        if len(self.bars_ubi) < 5:
            return self.bi_list[:-1]
        return self.bi_list

    @property
    def ubi_fxs(self) -> List[FX]:
        """bars_ubi 中的分型"""
        if not self.bars_ubi:
            return []
        else:
            return check_fxs(self.bars_ubi)

    @property
    def fx_list(self) -> List[FX]:
        """分型列表，包括 bars_ubi 中的分型"""
        fxs = []
        for bi_ in self.bi_list:
            fxs.extend(bi_.fxs[1:])
        ubi = self.ubi_fxs
        for x in ubi:
            if not fxs or x.dt > fxs[-1].dt:
                fxs.append(x)
        return fxs
