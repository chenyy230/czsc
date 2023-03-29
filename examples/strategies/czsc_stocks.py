# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/2/19 22:34
describe: 股票择时策略汇总
"""
from collections import OrderedDict
from czsc.objects import Event, Position
from czsc.strategies import CzscStrategyBase
from czsc import signals
from czsc.signals.cyy import cyy_judge_struct_V230329
from czsc.signals.bxt import get_s_five_bi_xt


class CzscStocksV230329(CzscStrategyBase):
    """缠论买卖点"""

    @classmethod
    def get_signals(cls, cat) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        s.update(cyy_judge_struct_V230329(cat, di=1, max_freq='60分钟', min_freq='15分钟'))
        s.update(get_s_five_bi_xt(cat.kas['15分钟'], di=1))
        s.update(cyy_judge_struct_V230329(cat, di=1, max_freq='日线', min_freq='60分钟'))
        s.update(get_s_five_bi_xt(cat.kas['60分钟'], di=1))
        return s

    @property
    def positions(self):
        return [
            self.create_pos_a(),
        ]

    @property
    def freqs(self):
        return ['日线', '60分钟', '30分钟', '15分钟']

    def create_pos_a(self, ):
        opens = [
            {'name': '开多',
             'operate': '开多',
             'signals_all': [],
             'signals_any': [],
             'signals_not': [],
             'factors': [
                 {'name': '15分钟买点',
                  'signals_not': [],
                  'signals_all': [],
                  'signals_any1': ['日线_60分钟_D1右侧笔数_2买卖点_任意_任意_0',
                                   '日线_60分钟_D1右侧笔数_类2或3买卖点_任意_任意_0'],
                  'signals_any2': ['60分钟_15分钟_D1右侧笔数_2买卖点_任意_任意_0',
                                   '60分钟_15分钟_D1右侧笔数_类2或3买卖点_任意_任意_0',
                                   ],
                  'signals_any3': ['15分钟_倒1笔_五笔形态_二买_任意_任意_0',
                                   '15分钟_倒1笔_五笔形态_类二买_任意_任意_0',
                                   '15分钟_倒1笔_五笔形态_类二买1_任意_任意_0',
                                   '15分钟_倒1笔_五笔形态_三买_任意_任意_0',
                                   ],
                  }
             ]},
        ]
        #
        # exits = [
        #     {'name': '平多',
        #      'operate': '平多',
        #      'signals_all': ['全天_0935_1450_是_任意_任意_0'],
        #      'signals_any': [],
        #      'signals_not': ['15分钟_D1K_ZDT_跌停_任意_任意_0'],
        #      'factors': [
        #          {'name': '60分钟MACD死叉',
        #           'signals_all': ['60分钟_D1K_MACD_空头_任意_任意_0'],
        #           'signals_any': [],
        #           'signals_not': []}
        #      ]},
        #
        # ]
        pos = Position(name=f"15分钟多头", symbol=self.symbol,
                       opens=[Event.load(x) for x in opens],
                       # exits=[Event.load(x) for x in exits],
                       interval=3600 * 4, timeout=16 * 30, stop_loss=500)
        return pos


class CzscStocksV230325(CzscStrategyBase):
    @classmethod
    def get_signals(cls, cat) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})

        # 基础信号，主要是约束作用
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='全天', span=('0935', '1450')))
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='上午', span=('0935', '1130')))
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='下午', span=('1300', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))
        s.update(signals.bar_amount_acc_V230214(cat.kas['日线'], di=2, n=1, t=2))

        # Beta 策略信号
        s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=1, key='macd'))
        s.update(signals.tas_macd_base_V221028(cat.kas['60分钟'], di=5, key='macd'))

        # 信号优化
        s.update(signals.cxt_third_bs_V230319(cat.kas['日线'], di=1, timeperiod=5))
        s.update(signals.cxt_third_bs_V230319(cat.kas['日线'], di=1, timeperiod=13))
        s.update(signals.cxt_third_bs_V230319(cat.kas['日线'], di=1, timeperiod=21))
        s.update(signals.cxt_third_bs_V230319(cat.kas['日线'], di=1, timeperiod=34))

        s.update(signals.jcc_szx_V221111(cat.kas['30分钟'], di=1, th=10))
        s.update(signals.jcc_szx_V221111(cat.kas['30分钟'], di=1, th=13))
        s.update(signals.jcc_szx_V221111(cat.kas['15分钟'], di=1, th=13))
        s.update(signals.jcc_szx_V221111(cat.kas['15分钟'], di=5, th=13))

        s.update(signals.bar_single_V230214(cat.kas['日线'], di=1, t=2))

        s.update(signals.bar_accelerate_V221110(cat.kas['15分钟'], di=1, window=8))

        return s

    @property
    def positions(self):
        pos_list = [self.create_pos_f60_macd_merged()]
        signal_opts = [
            "日线_D1SMA5_BS3辅助V230319_三卖_均线新低_任意_0",
            "日线_D1SMA13_BS3辅助V230319_三卖_均线新低_任意_0",
            "日线_D1SMA21_BS3辅助V230319_三卖_均线新低_任意_0",
            "日线_D1SMA34_BS3辅助V230319_三卖_均线新低_任意_0",

            "30分钟_D1TH13_十字线_墓碑十字线_北方_任意_0",
            "30分钟_D1TH10_十字线_墓碑十字线_北方_任意_0",
            "15分钟_D5TH13_十字线_墓碑十字线_北方_任意_0",
            "15分钟_D1TH13_十字线_墓碑十字线_北方_任意_0",

            "日线_D1T20_状态_阳线_长实体_任意_0",
            "15分钟_D1W8_加速V221110_上涨_任意_任意_0",
        ]

        for signal1 in signal_opts:
            pos_list.append(self.create_pos_f60_macd(signal1))
        return pos_list

    @property
    def freqs(self):
        return ['日线', '60分钟', '30分钟', '15分钟']

    def create_pos_f60_macd(self, signal1):
        """60分钟MACD金叉死叉优化"""
        opens = [
            {'name': '60分钟MACD金叉开多',
             'operate': '开多',
             'signals_all': ['全天_0935_1450_是_任意_任意_0',
                             '60分钟_D1K_MACD_多头_任意_任意_0',
                             '60分钟_D5K_MACD_空头_任意_任意_0',
                             '日线_D2N1_累计超2千万_是_任意_任意_0'],
             'signals_any': [],
             'signals_not': ['15分钟_D1K_ZDT_涨停_任意_任意_0'],
             'factors': [
                 {'name': signal1,
                  'signals_all': [signal1],
                  'signals_any': [],
                  'signals_not': []}
             ]},
        ]

        exits = [
            {'name': '平多',
             'operate': '平多',
             'signals_all': ['全天_0935_1450_是_任意_任意_0'],
             'signals_any': [],
             'signals_not': ['15分钟_D1K_ZDT_跌停_任意_任意_0'],
             'factors': [
                 {'name': '60分钟MACD死叉',
                  'signals_all': ['60分钟_D1K_MACD_空头_任意_任意_0'],
                  'signals_any': [],
                  'signals_not': []}
             ]},

        ]
        pos = Position(name=f"60分钟MACD金叉多头#{signal1}", symbol=self.symbol,
                       opens=[Event.load(x) for x in opens],
                       exits=[Event.load(x) for x in exits],
                       interval=3600 * 4, timeout=16 * 30, stop_loss=500)
        return pos

    def create_pos_f60_macd_merged(self):
        """60分钟MACD金叉死叉优化"""
        signal_opts = [
            "日线_D1SMA5_BS3辅助V230319_三卖_均线新低_任意_0",
            "日线_D1SMA13_BS3辅助V230319_三卖_均线新低_任意_0",
            "日线_D1SMA21_BS3辅助V230319_三卖_均线新低_任意_0",
            "日线_D1SMA34_BS3辅助V230319_三卖_均线新低_任意_0",

            "30分钟_D1TH13_十字线_墓碑十字线_北方_任意_0",
            "30分钟_D1TH10_十字线_墓碑十字线_北方_任意_0",
            "15分钟_D5TH13_十字线_墓碑十字线_北方_任意_0",
            "15分钟_D1TH13_十字线_墓碑十字线_北方_任意_0",

            "日线_D1T20_状态_阳线_长实体_任意_0",
            "15分钟_D1W8_加速V221110_上涨_任意_任意_0",
        ]

        opt_open_factors = []
        for signal1 in signal_opts:
            opt_open_factors.append({'name': signal1,
                                     'signals_all': [signal1],
                                     'signals_any': [],
                                     'signals_not': []})

        opens = [
            {'name': '60分钟MACD金叉开多',
             'operate': '开多',
             'signals_all': ['全天_0935_1450_是_任意_任意_0',
                             '60分钟_D1K_MACD_多头_任意_任意_0',
                             '60分钟_D5K_MACD_空头_任意_任意_0',
                             '日线_D2N1_累计超2千万_是_任意_任意_0'],
             'signals_any': [],
             'signals_not': ['15分钟_D1K_ZDT_涨停_任意_任意_0'],
             'factors': opt_open_factors},
        ]

        exits = [
            {'name': '平多',
             'operate': '平多',
             'signals_all': ['全天_0935_1450_是_任意_任意_0'],
             'signals_any': [],
             'signals_not': ['15分钟_D1K_ZDT_跌停_任意_任意_0'],
             'factors': [
                 {'name': '60分钟MACD死叉',
                  'signals_all': ['60分钟_D1K_MACD_空头_任意_任意_0'],
                  'signals_any': [],
                  'signals_not': []}
             ]},

        ]
        pos = Position(name="60分钟MACD金叉多头合并", symbol=self.symbol,
                       opens=[Event.load(x) for x in opens],
                       exits=[Event.load(x) for x in exits],
                       interval=3600 * 4, timeout=16 * 30, stop_loss=500)
        return pos
